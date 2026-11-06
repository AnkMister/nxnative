#!/usr/bin/env python3
"""Count source-level waste candidates in completed shader-cache entries.

Snapshot (read-only input): dmsh_mine.py snapshot <cas folder|cas.db> <corpus> [--per-stage 1024]
Report: dmsh_mine.py report <corpus> <report.json>
Compile four A/B pairs: dmsh_mine.py compare <report.json> <new output folder>
Counts are static source sites in main0 (plus mesh/object dm_stage_body), not GPU
instructions or execution frequencies. Raw cost 80 assumes a full pool search;
hint hits are cheaper. Other cost guesses only prioritize compiler experiments.
"""
import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import dmsh_cbuf
import dmsh_wide


ID = r'_[0-9A-Za-z_]+'
CBUF = re.compile(r'\(\*spvDescriptorSet0\.[a-z]p_c\d+\)\._m0\[\d+\]\.[xyzw]')
ROUNDTRIP = re.compile(r'as_type<(int|uint|float)>\(as_type<(?:int|uint|float)>\((' + ID + r')\)\)')
DIM = re.compile(r'spvDescriptorSet0\.\w+\.get_(?:width|height|depth|array_size|num_mip_levels)\([^()]*\)')
# Relative instruction-equivalent guesses only. No latency or frame-time prediction.
COST = {'raw_scalar_calls': 80, 'duplicate_cbuf': 4, 'bitcast_roundtrip': 0,
        'duplicate_texture_dimensions': 4, 'optnone_fadd_calls': 8,
        'local_array_256_words': 0, 'precise_minmaxclamp': 0, 'storage_runs_saved_addresses': 6, 'cbuf_reuse_removed_reads': 4}


def _body(src, start):
    start = src.find('{', start); depth = 1
    for i in range(start + 1, len(src)):
        depth += {'{': 1, '}': -1}.get(src[i], 0)
        if not depth: return src[start + 1:i]
    return ''


def main_body(src):
    """Primary entry plus its mesh/object stage body, excluding output variants."""
    m = re.search(r'(?:\b(?:fragment|vertex|kernel)|\[\[(?:mesh|object)\]\])\s+\w+\s+main0\s*\(', src)
    if not m: return ''
    body = _body(src, m.end())
    helper = re.search(r'\bvoid dm_stage_body\s*\(', src)
    if helper and 'dm_stage_body(' in body: body += '\n' + _body(src, helper.end())
    return body


def counts(src):
    body = main_body(src)
    c = collections.Counter()
    reused = main_body(dmsh_cbuf.reuse_words(src))
    c['cbuf_reuse_removed_reads'] = len(CBUF.findall(body)) - len(CBUF.findall(reused))
    widened = main_body(dmsh_wide.wide_loads(src, offset_runs=True))
    c['storage_runs_saved_addresses'] = sum(int(n) - 1 for n in re.findall(r'packed_uint([234]) _dmr\d+ =', widened))
    # A brace ends the repeated-expression window. These are candidates for compiler CSE.
    for block in re.split(r'[{}]', body):
        for key, rx in (('duplicate_cbuf', CBUF), ('duplicate_texture_dimensions', DIM)):
            c[key] += sum(n - 1 for n in collections.Counter(rx.findall(block)).values())
    c['bitcast_roundtrip'] = len(ROUNDTRIP.findall(body))
    c['optnone_fadd_calls'] = len(re.findall(r'\bspvFAdd\(', body)) if '[[clang::optnone]] T spvFAdd' in src else 0
    c['precise_minmaxclamp'] = len(re.findall(r'precise::(?:min|max|clamp)\(', body))
    sizes = re.findall(r'^\s*(?:float|uint|int) \w+\[(\d+)\];', body, re.M)
    sizes += re.findall(r'^\s*spvUnsafeArray<(?:float|uint|int), (\d+)> \w+;', body, re.M)
    c['local_array_256_words'] = sum(int(n) >= 256 for n in sizes)
    helpers = re.findall(r'int (\w+)\(thread const int& \w+, thread const int& \w+, device \w+& \w+\)', src)
    for helper in helpers:
        if 'reinterpret_cast<device uint*>' in src:
            c['raw_scalar_calls'] += len(re.findall(r'\b' + re.escape(helper) + r'\(', body))
    return dict(c)


def db_entries(path, reader):
    # Reuse the repository reader, but prohibit its schema setup and damage recovery writes.
    spec = importlib.util.spec_from_file_location('shader_cache', reader)
    if spec is None or spec.loader is None: raise ValueError('cannot load cache reader: ' + str(reader))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    class ReadOnly(module.Store):
        def _open(self): self.db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', isolation_level=None)
        def _damage(self, error): raise error
    def read(name):
        source = ReadOnly(path)
        try: return source.get(name)
        finally: source.close()
    store = ReadOnly(path)
    try:
        names = store.names('shader/')
        for index in sorted(store.names('index/')):
            if not index.endswith('.json'): continue
            key = Path(index).stem; digest = json.loads(store.get(index))['digest']
            name = f'shader/{digest}/mac/{key}_b.metal'; refl = name[:-6] + '.json'
            if all(n in names for n in (name, refl, name[:-6] + '.metallib')):
                yield name, json.loads(store.get(refl)), lambda name=name: read(name)
    finally: store.close()


def folder_entries(path):
    # Load only the repo's read-only cache inspection functions, never its build.
    tree = ast.parse(Path(dmsh_wide.__file__).with_name('dmsh_build.py').read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('cache_path', 'cache_outputs')]
    reader = {'os': os, 'CAS': str(path), 'out': str(path), 'IOSOUT': None, 'TARGETS': {'mac'}}
    exec(compile(tree, 'dmsh_build.py (cache reader only)', 'exec'), reader)
    # publish_cache writes this index atomically LAST, after all immutable outputs.
    for index in sorted((path / 'index').glob('*.json')):
        meta = json.loads(index.read_text()); key = index.stem
        root = path / 'shader' / meta['digest'] / 'mac'
        msl, refl = root / (key + '_b.metal'), root / (key + '_b.json')
        if reader['cache_outputs'](key, meta['digest'], cached=True):
            yield str(msl.relative_to(path)), json.loads(refl.read_text()), msl.read_bytes


def snapshot(cache, corpus, per_stage, reader):
    if corpus.resolve().is_relative_to(cache.resolve()): raise ValueError('corpus must be outside the read-only cache')
    entries = db_entries(cache, reader) if cache.is_file() else folder_entries(cache)
    stages = collections.defaultdict(list)
    for name, refl, read in entries:
        key = refl['dm_ctl']; stage = refl['stage']
        stages[stage].append((hashlib.sha256(key.encode()).hexdigest(), key, name, refl, read))
    if not stages: raise ValueError('no completed published shaders in ' + str(cache))
    corpus.mkdir(parents=True, exist_ok=False)
    manifest = {'cache': str(cache), 'available': {s: len(xs) for s, xs in stages.items()},
                'selection': 'lowest SHA256(shader id) per stage among published entries at snapshot', 'per_stage': per_stage, 'shaders': []}
    for stage, entries in sorted(stages.items()):
        for _, key, name, refl, read in sorted(entries)[:per_stage]:
            data = read(); (corpus / (key + '.metal')).write_bytes(data)
            manifest['shaders'].append({'id': key, 'stage': stage, 'entry': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'source': refl.get('source'), 'chain': refl['chain']})
    (corpus / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'available': manifest['available'], 'selected': dict(collections.Counter(s['stage'] for s in manifest['shaders']))}))


def report(corpus, output):
    manifest = json.loads((corpus / 'manifest.json').read_text()); rows = {}
    for shader in manifest['shaders']:
        data = (corpus / (shader['id'] + '.metal')).read_bytes()
        if hashlib.sha256(data).hexdigest() != shader['sha256']: raise ValueError('corpus changed: ' + shader['id'])
        for pattern, n in counts(data.decode()).items():
            row = rows.setdefault(pattern, {'pattern': pattern, 'stages': {}, 'shaders': 0, 'count': 0, 'example': None, 'example_count': 0, 'examples_by_stage': {}})
            row['count'] += n; row['shaders'] += bool(n)
            row['stages'][shader['stage']] = row['stages'].get(shader['stage'], 0) + n
            if n > row['examples_by_stage'].get(shader['stage'], {}).get('count', 0): row['examples_by_stage'][shader['stage']] = {'id': shader['id'], 'count': n}
            if n > row['example_count']: row.update(example=shader['id'], example_count=n)
    for row in rows.values():
        row['unit_cost_guess'] = COST[row['pattern']]
        row['hot_score_guess'] = (row['stages'].get('cs', 0) + row['stages'].get('ps', 0)) * row['unit_cost_guess']
    result = {'corpus': str(corpus), 'available': manifest['available'], 'selected': dict(collections.Counter(s['stage'] for s in manifest['shaders'])),
              'cost_note': 'static candidates, instruction-equivalent guesses; compiler may eliminate them; no invocation or loop weighting, no measured GPU saving',
              'patterns': sorted(rows.values(), key=lambda x: -x['hot_score_guess'])}
    output.write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result, indent=2))


def compare(report_file, output):
    """Compile four real before/after pairs, then count primary-entry AIR opcodes."""
    report = json.loads(report_file.read_text()); corpus = Path(report['corpus'])
    patterns = {r['pattern']: r for r in report['patterns']}
    output.mkdir(parents=True, exist_ok=False); results = []
    for pattern, stage, transform in (
            ('cbuf_reuse_removed_reads', 'ps', dmsh_cbuf.reuse_words),
            ('cbuf_reuse_removed_reads', 'cs', dmsh_cbuf.reuse_words),
            ('storage_runs_saved_addresses', 'ps', lambda s: dmsh_wide.wide_loads(s, offset_runs=True)),
            ('storage_runs_saved_addresses', 'ms', lambda s: dmsh_wide.wide_loads(s, offset_runs=True))):
        example = patterns[pattern]['examples_by_stage'].get(stage)
        if not example: continue
        key = example['id']; source = (corpus / (key + '.metal')).read_text()
        record = {'id': key, 'stage': stage, 'pattern': pattern, 'source_sites': example['count'], 'variants': {}}
        for variant, text in (('before', source), ('after', transform(source))):
            path = output / (key + '-' + variant + '.metal'); path.write_text(text)
            for mode, extra, suffix in (('-c', [], '.air'), ('-S', ['-emit-llvm'], '.ll')):
                command = ['xcrun', '-sdk', 'macosx', 'metal', mode, '-O1', '-fpreserve-invariance', *extra, str(path), '-o', str(path.with_suffix(suffix))]
                result = subprocess.run(command, capture_output=True, text=True)
                path.with_suffix(suffix + '.log').write_text(result.stdout + result.stderr)
                if result.returncode: raise RuntimeError('Metal failed: ' + str(path))
            ir = path.with_suffix('.ll').read_text()
            entry = re.search(r'^define [^\n]* @main0\(.*?^}', ir, re.M | re.S)
            ops = collections.Counter(re.findall(r'^  (?:%[\w.]+ = )?(?:tail )?(\w+)\b', entry[0] if entry else ir, re.M))
            record['variants'][variant] = {'opcodes': dict(sorted(ops.items())), 'instructions': sum(ops.values())}
        results.append(record)
        print(json.dumps(record), flush=True)
    (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__); commands = p.add_subparsers(dest='command', required=True)
    s = commands.add_parser('snapshot'); s.add_argument('cache', type=Path); s.add_argument('corpus', type=Path)
    s.add_argument('--per-stage', type=int, default=1024); s.add_argument('--reader', type=Path)
    r = commands.add_parser('report'); r.add_argument('corpus', type=Path); r.add_argument('output', type=Path)
    c = commands.add_parser('compare'); c.add_argument('report', type=Path); c.add_argument('output', type=Path)
    a = p.parse_args()
    if a.command == 'snapshot':
        if a.per_stage < 1: p.error('--per-stage must be positive')
        if a.cache.is_file() and not a.reader: p.error('cas.db needs --reader <repo dm/tools/shader_cache.py>')
        snapshot(a.cache, a.corpus, a.per_stage, a.reader)
    elif a.command == 'report': report(a.corpus, a.output)
    else: compare(a.report, a.output)


if __name__ == '__main__': main()

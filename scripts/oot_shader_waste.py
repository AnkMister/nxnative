#!/usr/bin/env python3
"""Read-only shader census. Scores are inspection priorities, never GPU timings.

Usage: oot_shader_waste.py BUILD --out NEW_DIRECTORY [--profile PROFILE]
No imports of the build driver, shader compilation, game launches or installs.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
import csv
import hashlib
import json
import math
import mmap
import os
from pathlib import Path
import re
import struct
import sys

REPO = Path(__file__).resolve().parents[1]
TITLE = '0400486024DEC000'
# Source-site weights only. Unknown loops assume four trips for ranking, not bounds.
UNKNOWN_TRIPS = 4
METRICS = ('raw_loads', 'raw_stores', 'raw_atomics', 'texture_samples',
           'texture_reads', 'storage_loads', 'pool_table_loads', 'statements')
FUNC = re.compile(r'^\s*(?:template<[^\n]+>\s*)?(?:static\s+|inline\s+|__attribute__\(\([^\n]*?\)\)\s*|\n)*'
                  r'(?:\[\[\w+\]\]\s*)?(?:kernel\s+|fragment\s+|vertex\s+)?(?:\w+(?:<[^;{}\n]*>)?[&*]?\s+)'
                  r'(\w+)\s*\(', re.M)
CALL = re.compile(r'\b([A-Za-z_]\w*)\s*\(')
COMMENTS = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"', re.S)
LOOP = re.compile(r'\b(for|while|do)\b')
STORAGE = re.compile(r'(?:\(\*spvDescriptorSet0\.(\w+)\)|\b(\w+))\._m0\[')
RAW = re.compile(r'reinterpret_cast<\s*(?:const\s+)?device\s+\w+\s*\*>')


def clean(source):
    return COMMENTS.sub(lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), source)


def pairs(source):
    result, stack = {}, []
    for i, c in enumerate(source):
        if c in '({[': stack.append((c, i))
        elif c in ')}]':
            if not stack or stack[-1][0] != {')': '(', '}': '{', ']': '['}[c]:
                raise ValueError(f'unbalanced source at {i}')
            _, at = stack.pop(); result[at] = i
    if stack: raise ValueError('unterminated source')
    return result


def functions(source):
    brackets, found = pairs(source), {}
    for m in FUNC.finditer(source):
        start = m.end() - 1
        end = brackets[start] + 1
        # Metal entry attributes follow the parameters.
        while end < len(source) and source[end].isspace(): end += 1
        if source.startswith('[[', end): end = brackets[end] + 1
        while end < len(source) and source[end].isspace(): end += 1
        if end < len(source) and source[end] == '{':
            found[m[1]] = (end + 1, brackets[end])
    return found


def loop_info(body, line0=0, lane_width=None):
    brackets = pairs(body)
    loops, tails = [], set()
    for m in LOOP.finditer(body):
        if m.start() in tails: continue
        pos = m.end()
        while pos < len(body) and body[pos].isspace(): pos += 1
        header, trips, trip_range = '', None, None
        if m[1] != 'do':
            if pos not in brackets or body[pos] != '(': continue
            stop = brackets[pos]; header = body[pos + 1:stop]; pos = stop + 1
            while pos < len(body) and body[pos].isspace(): pos += 1
        if pos >= len(body): continue
        if body[pos] == '{': stop = brackets[pos] + 1
        else: stop = body.find(';', pos) + 1
        if stop <= pos: continue
        if m[1] == 'do':
            tail = re.match(r'\s*while\s*\(', body[stop:])
            if tail:
                opening = stop + tail.end() - 1
                header = body[opening + 1:brackets[opening]]
                tails.add(stop + tail[0].index('while'))
                if header.strip() in ('false', '0'): trips = 1
        elif m[1] == 'for':
            simple = re.fullmatch(r'(?:uint|int)?\s*(\w+)\s*=\s*(\d+)u?\s*;\s*\1\s*(<|<=)\s*(\d+)u?\s*;\s*(?:\1\+\+|\+\+\1|\1\s*\+=\s*(\d+)u?)\s*', header)
            if simple:
                var, first, cmp, last, step = simple.groups()
                # A body write or break can invalidate the literal trip count.
                inner = body[pos:stop]
                if not re.search(r'\b(?:break|return)\b|\b' + var + r'\s*(?:[+\-*/]?=|\+\+|--)', inner):
                    trips = max(0, math.ceil((int(last) + (cmp == '<=') - int(first)) / int(step or 1)))
        if m[1] == 'for' and lane_width:
            lane = re.fullmatch(r'(?:uint|int)\s+(\w+)\s*=\s*dm_lid\s*;\s*\1\s*<\s*(\d+)u?\s*;\s*\1\s*\+=\s*(\d+)u?\s*', header)
            if lane and int(lane[3]) == lane_width and not re.search(r'\b(?:break|return)\b|\b' + lane[1] + r'\s*(?:[+\-*/]?=|\+\+|--)', body[pos:stop]):
                n = int(lane[2]); trip_range = [n // lane_width, math.ceil(n / lane_width)]
                if trip_range[0] == trip_range[1]: trips = trip_range[0]
        depth = 1 + sum(x['start'] <= m.start() < x['end'] for x in loops)
        loops.append(dict(kind=m[1], line=line0 + body.count('\n', 0, m.start()) + 1,
                          header=header.strip(), start=m.start(), end=stop,
                          depth=depth, trips=trips, trip_range=trip_range,
                          empty=not body[pos:stop].strip('{}; \n\t') and not re.search(r'\w+\s*\(|\+\+|--|=(?!=)', header)))
    return loops


def weight(at, loops, unknown=UNKNOWN_TRIPS):
    return math.prod(min(x['trips'] if x['trips'] is not None else x['trip_range'][1] if x['trip_range'] else unknown, 256)
                     for x in loops if x['start'] <= at < x['end'])


def analyze(source, meta):
    text = clean(source); funcs = functions(text)
    if 'main0' not in funcs: raise ValueError('no main0 entry')
    pool = {x['msl_name'] for x in meta.get('bindings', []) if x['kind'] == 'gmem_map'}
    storage = {x['msl_name'] for x in meta.get('bindings', []) if x['kind'] in ('sbuf', 'sbuf_ubo', 'ubo_ptr')}
    memo, details = {}, {}

    def visit(name, active=()):
        if name in memo: return memo[name]
        if name in active: raise ValueError('recursive helper: ' + name)
        a, b = funcs[name]; body = text[a:b]; loops = loop_info(body, text.count('\n', 0, a), (meta.get('mesh_stage') or {}).get('threads'))
        sites, est, once = Counter(), Counter(), Counter()
        events = []; local_pairs = pairs(body)
        for m in RAW.finditer(body):
            tail = body[m.end():body.find(';', m.end())]
            kind = 'raw_atomics' if 'atomic_' in body[max(0, m.start()-120):m.start()] else 'raw_stores' if re.search(r'\)\s*=\s*(?!=)', tail) else 'raw_loads'
            events.append((m.start(), kind))
        for pattern, kind in ((r'\.(?:sample|sample_compare|gather|gather_compare)\s*\(', 'texture_samples'),
                              (r'\.read\s*\(', 'texture_reads'), (r';', 'statements')):
            events.extend((m.start(), kind) for m in re.finditer(pattern, body))
        for m in STORAGE.finditer(body):
            binding = m[1] or m[2]
            if binding not in pool | storage: continue
            end = local_pairs[m.end()-1]
            tail = body[end+1:]
            if re.match(r'\s*(?:\.[xyzw]+)?\s*=(?!=)', tail): continue
            prefix = body[max(0,m.start()-80):m.start()]
            if re.search(r'&\s*$', prefix) and not re.search(r'\*\(const device packed_uint[234]\*\)&\s*$', prefix): continue
            events.append((m.start(), 'pool_table_loads' if binding in pool else 'storage_loads'))
        for at, kind in events:
            sites[kind] += 1; est[kind] += weight(at, loops); once[kind] += weight(at, loops, 1)
        for m in CALL.finditer(body):
            child = m[1]
            if child in funcs and not child.startswith('spv'):
                cs, ce, co = visit(child, (*active, name))
                for k in METRICS:
                    sites[k] += cs[k]; est[k] += ce[k] * weight(m.start(), loops); once[k] += co[k] * weight(m.start(), loops, 1)
        repeated = Counter(re.findall(r'\b(?:spvDescriptorSet0\.)?\w+c\d+\)?\._m0\[\d+\]\.[xyzw]', body))
        details[name] = dict(line=text.count('\n', 0, a)+1, loops=loops,
                             raw_helper=bool(RAW.search(body) and any(x + '._m0[' in body for x in pool)),
                             repeated_constant_candidates=sum(n-1 for n in repeated.values()),
                             self_assignments=len(re.findall(r'\b(\w+)\s*=\s*\1\s*;', body)),
                             local_arrays=[int(x) for x in re.findall(r'spvUnsafeArray<\w+, (\d+)>\s+\w+\s*;', body)])
        memo[name] = sites, est, once
        return memo[name]

    sites, est, once = visit('main0')
    # main0_z / integer-output / alpha variants are alternatives, not added work.
    reachable = sorted(details)
    loops = [dict(function=n, **x) for n in reachable for x in details[n]['loops']]
    result = {}
    result.update(sites=dict(sites), estimated=dict(est), unknown_once=dict(once),
                loops=loops, max_loop_depth=max((x['depth'] for x in loops), default=0),
                functions=details, reachable=reachable,
                repeated_constant_candidates=sum(x['repeated_constant_candidates'] for x in details.values()),
                self_assignments=sum(x['self_assignments'] for x in details.values()),
                local_array_words=sum(sum(x['local_arrays']) for x in details.values()))
    return result


def opcode_tables():
    root = REPO / 'dm/third_party/ryujinx/src/Ryujinx.Graphics.Shader/Instructions'
    sources = '\n'.join(x.read_text() for x in sorted(root.glob('InstEmitAmpere*.cs')))
    const = dict(re.findall(r'public const int (\w+) = (0x[0-9a-f]+);', sources))
    exact, alu = {}, {}
    for m in re.finditer(r'\b(X|Alu|x|alu)\((0x[0-9a-f]+|AmpereOpcodes\.\w+),\s*InstName\.(\w+)', sources):
        code = const[m[2].split('.')[1]] if '.' in m[2] else m[2]
        (alu if m[1].lower() == 'alu' else exact)[int(code, 16)] = m[3]
    for op in (0x918, 0x91a, 0x945, 0x941, 0x942, 0x948, 0x9ab): exact[op] = 'NopOrSync'
    return exact, alu


def sass_stats(rec, stage, tables, listing=False):
    ci = rec.find(bytes.fromhex('34127698'))
    if ci < 0 or struct.unpack_from('<I', rec, ci+4)[0] != 0xc9: raise ValueError('not NVN2')
    size = struct.unpack_from('<I', rec, ci+0x38)[0]
    code = rec[0x38:0x38+size]; start = 0 if stage == 'compute' else 0x80
    hist, lines = Counter(), []
    for at in range(start, len(code)-15, 16):
        lo, hi = struct.unpack_from('<QQ', code, at); op = lo & 0xfff
        name = tables[0].get(op, tables[1].get(op & 0x1ff, f'UNKNOWN_{op:03x}'))
        hist[name] += 1
        if listing:
            pred = (lo >> 12) & 15
            args = f'Rd={(lo>>16)&255} Ra={(lo>>24)&255} Rb={(lo>>32)&255} Rc={hi&255}'
            if op in (0x947, 0x944):
                off = ((hi << 64 | lo) >> 34) & ((1 << 48)-1)
                if off & (1<<47): off -= 1<<48
                args += f' target={at+16+off*4-start:#x}'
            lines.append(f'{at-start:06x} {hi:016x}{lo:016x} pred={pred:x} {name:16s} {args}')
    return dict(guest_registers=struct.unpack_from('<I', rec, ci+0x4c)[0],
                instructions=sum(hist.values()), opcodes=dict(hist),
                guest_local_loads=hist['Ldl'], guest_local_stores=hist['Stl']), lines


def read_map(profile):
    with (profile/'shader_map.tsv').open() as f:
        return list(csv.DictReader((x for x in f if not x.startswith('#')), delimiter='\t'))


def pipelines(path):
    if not path.exists(): return {}, {}
    data = json.loads(path.read_text()); links = defaultdict(list); counts = {}
    for kind, entries in data['pipeline_descriptors'].items():
        counts[kind] = len(entries)
        for index, desc in enumerate(entries):
            for field, value in desc.items():
                if field.endswith('function_descriptor') and isinstance(value, str):
                    key = re.search(r'[0-9a-f]{16}', value)
                    if key: links[key[0]].append(dict(kind=kind, index=index, field=field, function=value))
    return dict(links), counts


def program_names(build, rows):
    """Declared BAHS program names, read through the existing read-only container readers."""
    sys.path.insert(0, str(REPO/'dm/tools')); sys.path.insert(0, str(REPO/'dm/gfx/tools'))
    import romfs
    previous = os.environ.get('DM_GAME'); os.environ['DM_GAME'] = TITLE
    try:
        import shader_split as split
    finally:
        if previous is None: os.environ.pop('DM_GAME', None)
        else: os.environ['DM_GAME'] = previous
    image = build/'extract/v131072/RomFS.img'
    if not image.is_file(): return {}
    split.ZDICTS = split.zs_dicts(str(image))
    grouped, names = defaultdict(list), {}
    for row in rows:
        if '#BAHS@' in row['source']: grouped[row['source'].split('#')[0]].append(row)
    for source, shaders in grouped.items():
        container, sep, member = source.partition('.zs/')
        raw = romfs.Path(str(image)+container+('.zs' if sep else '')).read_bytes()
        if raw[:4] == bytes.fromhex('28b52ffd'):
            did = split.zs_dict_id(raw)
            raw = split.unzs_dict(raw, did, source) if did else split.zstd_mod().decompress(raw)
        if sep: raw = dict(split.sarc_members(raw))[member]
        entries = split.bahs_shaders(raw,source)
        arr = min(int(e[0].rsplit('@',1)[1],16) for e in entries)-0x18
        asz, count = struct.unpack_from('<II',raw,arr); pos = arr+8; records = []
        for _ in range(count):
            size, _kind = struct.unpack_from('<II',raw,pos)
            if size < 0x20: raise ValueError('invalid BAHS record: '+source)
            records.append(pos+0x10); pos += size
        if pos != arr+asz: raise ValueError('invalid BAHS binary array: '+source)
        psz, count = struct.unpack_from('<II',raw,pos); q = pos+8; programs = []
        for _ in range(count):
            size, nlen, _mask, first = struct.unpack_from('<IIII',raw,q)
            if size < 16 or nlen > size-16: raise ValueError('invalid BAHS program: '+source)
            name = raw[q+16:q+16+nlen].rstrip(b'\0').decode('utf-8','replace')
            programs.append((first,name)); q += size
        if q != pos+psz: raise ValueError('invalid BAHS program array: '+source)
        programs.append((len(records),'')); indices = {at:i for i,at in enumerate(records)}
        for row in shaders:
            idx = indices.get(int(row['source'].rsplit('@',1)[1],16))
            if idx is None: continue
            for (first,name),(end,_) in zip(programs,programs[1:]):
                if first <= idx < end: names[row['dm_ctl_sha16']] = name; break
    return names


def priority(row):
    src = row['source'].lower(); stage = row['stage']
    if 'foliage' in src: factor, why = 8, 'foliage, repeated geometry and overdraw inferred'
    elif any(x in src for x in ('ndsr', 'post', 'ssao', 'bloom', 'tonemap', 'deferred', 'ambientocclusion')):
        factor, why = 8, 'screen effect inferred from source name'
    elif stage == 'compute': factor, why = 4, 'compute dispatch coverage unknown'
    elif stage == 'pixel': factor, why = 3, 'fragment coverage unknown'
    else: factor, why = 1, 'geometry invocation count unknown'
    def cost(v):
        return (80*(v.get('raw_loads',0)+v.get('raw_stores',0)+v.get('raw_atomics',0))
                + 16*v.get('texture_samples',0)+8*v.get('texture_reads',0)
                + 4*v.get('storage_loads',0)+v.get('statements',0))
    return dict(frequency_weight=factor, frequency_reason=why,
                score=cost(row['analysis']['estimated'])*factor,
                score_unknown_once=cost(row['analysis']['unknown_once'])*factor)


def inspect_shader(args):
    item, cache = args
    if item['status'] != 'ok': return item
    key = item['key']; path = cache/(key+'_b.metal'); refl = cache/(key+'_b.json')
    before = (path.stat(), refl.stat()); source = path.read_bytes(); metadata = json.loads(refl.read_bytes())
    after = (path.stat(), refl.stat())
    if any((x.st_size,x.st_mtime_ns)!=(y.st_size,y.st_mtime_ns) for x,y in zip(before,after)):
        raise ValueError('input changed during scan: '+key)
    item.update(msl_path=str(path), msl_bytes=len(source), msl_sha256=hashlib.sha256(source).hexdigest(),
                metallib_bytes=(cache/(key+'_b.metallib')).stat().st_size,
                metal_registers=None, metal_spills=None, analysis=analyze(source.decode(), metadata))
    item.update(priority(item))
    return item


def scan(build, profile, out, pass_map=None, jobs=2):
    build, out = build.resolve(), out.resolve()
    if out == build or build in out.parents: raise ValueError('output must be outside the read-only build')
    if out.exists(): raise ValueError('output must be a new directory')
    caches = sorted((build/'shader/cache').glob('b-*'))
    if len(caches) != 1: raise ValueError('expected exactly one chain directory')
    cache = caches[0]; rows = read_map(profile)
    names = json.loads(pass_map.read_text()) if pass_map else program_names(build, rows)
    links, counts = pipelines(build/'pso/mac-work/bases.mtl4-json')
    statuses = json.loads((cache/'_b_build.json').read_text())
    statuses = {x['key']:x for x in statuses}
    out.mkdir(parents=True)
    (out/'pass-names.json').write_text(json.dumps(names, indent=2)+'\n')
    tables = opcode_tables(); result, failures = [], []
    manifest = hashlib.sha256(); changed = []
    with (out/'shaders.jsonl').open('w') as sink, ProcessPoolExecutor(max_workers=jobs) as pool:
        for package in sorted({r['package'] for r in rows}):
            selected = [r for r in rows if r['package'] == package]
            with (build/'shader/pkg'/package).open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
                offsets = [m.start() for m in re.finditer(b'BTCDBTCD', data)] + [len(data)]
                pending = iter(selected)
                while batch := list(islice(pending, 32)):
                    work = []
                    for row in batch:
                        key = row['dm_ctl_sha16']; index = int(row['index'])
                        rec = data[offsets[index]:offsets[index+1]]
                        sass, _ = sass_stats(rec, row['stage'], tables)
                        item = dict(key=key, stage=row['stage'], package=package, index=index,
                                    source=row['source'], pass_name=names.get(key), sass=sass, pipelines=links.get(key, []),
                                    status=statuses[key]['st'], error=statuses[key]['err'])
                        work.append((item,cache))
                    for item in pool.map(inspect_shader, work):
                        if item['status'] != 'ok': failures.append(item); continue
                        manifest.update(f"{item['key']}\t{item['msl_sha256']}\n".encode())
                        sink.write(json.dumps(item, separators=(',',':'))+'\n')
                        analysis = item['analysis']
                        result.append({k:v for k,v in item.items() if k != 'analysis'} |
                                      {'analysis':{k:v for k,v in analysis.items() if k not in ('functions','loops')}})
            print(f'{package}: {len(selected)} inspected', flush=True)
    ranked = sorted(result, key=lambda x:(-x['score'],x['key']))
    for row in ranked[:5]:
        package, index = row['package'], row['index']
        with (build/'shader/pkg'/package).open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
            offsets = [m.start() for m in re.finditer(b'BTCDBTCD', data)]+[len(data)]
            rec = data[offsets[index]:offsets[index+1]]
            _, lines = sass_stats(rec, row['stage'], tables, True)
            (out/(row['key']+'.sass.txt')).write_text('# Partial SASS decode using vendored Ampere tables. Rd/Ra/Rb/Rc are raw fields, not all operands.\n'+'\n'.join(lines)+'\n')
    # New outputs do not contaminate the census, including a partial rerun.
    summary = dict(build=str(build), profile=str(profile.resolve()), chain=cache.name,
                   mapped=len(rows), translated=len(result), failed=len(failures),
                   stage_counts=dict(Counter(x['stage'] for x in result)), pipeline_counts=counts,
                   source_manifest_sha256=manifest.hexdigest(), changed_inputs=changed,
                   pass_map=str(pass_map.resolve()) if pass_map else None,
                   assumptions=dict(unknown_loop_trips=UNKNOWN_TRIPS, loop_rank_cap=256,
                                    raw_access_weight=80, texture_sample_weight=16, texture_read_weight=8,
                                    storage_load_weight=4, statement_weight=1),
                   totals={k:sum(x['analysis']['sites'].get(k,0) for x in result) for k in METRICS},
                   top30=ranked[:30], failures=failures)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (out/'ranked.tsv').open('w') as f:
        fields = ['rank','key','stage','score','score_unknown_once','frequency_weight','msl_bytes','raw_loads','raw_stores','raw_atomics','texture_samples','texture_reads','storage_loads','max_loop_depth','guest_registers','pipelines','source']
        writer = csv.DictWriter(f,fields,delimiter='\t'); writer.writeheader()
        for rank,row in enumerate(ranked,1):
            writer.writerow(dict(rank=rank,**{k:row[k] for k in ('key','stage','score','score_unknown_once','frequency_weight','msl_bytes','source')},
                                 **{k:row['analysis']['sites'].get(k,0) for k in METRICS if k in fields},
                                 max_loop_depth=row['analysis']['max_loop_depth'],guest_registers=row['sass']['guest_registers'],pipelines=len(row['pipelines'])))
    print(json.dumps({k:summary[k] for k in ('mapped','translated','failed','stage_counts','pipeline_counts','totals')}))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('build',type=Path); p.add_argument('--out',type=Path,required=True)
    p.add_argument('--profile',type=Path,default=REPO/'dm/games'/TITLE)
    p.add_argument('--jobs', type=int, choices=(1,2,3), default=2, help='at most three analysis workers')
    p.add_argument('--pass-map', type=Path, help='optional JSON shader key to declared program name')
    args = p.parse_args()
    scan(args.build,args.profile,args.out,args.pass_map,args.jobs)


if __name__ == '__main__': main()

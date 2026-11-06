#!/usr/bin/env python3
"""Copy the current profile and add only blend-fusion wants proven by the census."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
GAME = '0400486024DEC000'


def prepare(repo):
    repo = repo.resolve()
    source = repo / 'dm/games' / GAME
    names = subprocess.check_output(
        ['git', '-C', str(repo), 'ls-files', '--', f'dm/games/{GAME}'], text=True).splitlines()
    files = {}
    for name in names:
        path = repo / name
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f'Expected a regular profile source file: {path}')
        files[str(path.relative_to(source))] = path.read_bytes()
    if 'game.tsv' not in files or 'shader_map.tsv' not in files:
        raise SystemExit('The registered game profile is incomplete.')
    pixels = set()
    for line in files['shader_map.tsv'].decode().splitlines():
        c = line.split('\t')
        if len(c) == 5 and c[2] == 'pixel': pixels.add(c[3])
    wanted, evidence = set(), []
    user = ROOT / 'pso_user.tsv'
    for number, line in enumerate(user.read_text().splitlines(), 1):
        c = line.split('\t')
        if not c or c[0] != 'R': continue
        if len(c) != 2 or len(c[1]) not in (864, 880, 1008):
            raise SystemExit(f'Unsupported native render-key layout at row {number}.')
        try: key = bytes.fromhex(c[1])
        except ValueError: raise SystemExit(f'Invalid native render key at row {number}.')
        # Stable pso_skey prefix from nvn_pso_skey.h: vs[24], fs[24],
        # vs_stage, fs_stage, merged, fz, then fz_desc.kind and fbmask.
        if not key[51]: continue
        if key[49] != 1 or key[52] != 1:
            raise SystemExit(f'Unsupported specialized fragment at native row {number}.')
        shader = key[24:48].split(b'\0', 1)[0].decode('ascii')
        if not re.fullmatch(r'[0-9a-f]{16}_b', shader) or shader[:-2] not in pixels:
            raise SystemExit(f'Unknown blend-fusion pixel shader at row {number}: {shader}')
        wanted.add(shader[:-2])
        evidence.append(dict(input='pso_user.tsv', row=number, shader=shader[:-2], kind=key[52]))
    seen = ROOT / 'pso_seen.jsonl'
    for number, line in enumerate(seen.read_text().splitlines(), 1):
        if not line or line.startswith('#'): continue
        ref = json.loads(line).get('fragment', [])
        if ref and re.fullmatch(r'[0-9a-f]{16}_bf', ref[0]):
            shader = ref[0][:-3]
            if shader not in pixels: raise SystemExit(f'Unknown portable BF pixel shader: {shader}')
            wanted.add(shader)
            evidence.append(dict(input='pso_seen.jsonl', row=number, shader=shader))
    original = files.get('bf_want.tsv', b'')
    existing = {line.strip() for line in original.decode().splitlines()
                if line.strip() and not line.lstrip().startswith('#')}
    added = sorted(wanted - existing)
    if added:
        files['bf_want.tsv'] = original + (b'\n' if original and not original.endswith(b'\n') else b'')
        files['bf_want.tsv'] += b'# Build-only additions from the frozen pipeline census.\n'
        files['bf_want.tsv'] += ('\n'.join(added) + '\n').encode()
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode() + b'\0' + data + b'\0')
    profile_root = ROOT.parent / 'build-profile' / digest.hexdigest()[:16]
    target = profile_root / GAME
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    source_hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                     for name in files if (source / name).is_file()}
    report = dict(source=str(source), source_head=subprocess.check_output(
        ['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
        profile_root=str(profile_root), profile=str(target), added_bf_wants=added,
        existing_bf_wants=sorted(existing), evidence=evidence, source_sha256=source_hashes,
        census_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (user, seen)})
    (ROOT / 'bf-profile.json').write_text(json.dumps(report, indent=2) + '\n')
    print(profile_root)


if __name__ == '__main__':
    if len(sys.argv) != 2: raise SystemExit('usage: prepare-profile.py <source checkout>')
    prepare(Path(sys.argv[1]))

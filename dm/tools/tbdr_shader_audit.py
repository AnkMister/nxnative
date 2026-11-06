"""Audit a profile's generated reflection for unresolved texture readers. No GPU or game launch.

The allow-list names stages whose texture reads the submission index can resolve
from slots. It does not declare any attachment dead: command order, aliases and
the next full clear still need a runtime proof. Missing reflection is unsafe.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

# These set rf.bindless/rf.dyn in nvn_refl.m, or are tested directly by sdx_walk.
UNKNOWN_READ = {'tex_ubo', 'samp_ubo', 'img_ubo', 'tbuf_ubo', 'tex_pool',
                'samp_pool', 'tex_c2a'}
SLOT_RESOLVABLE = {'tex', 'img', 'tbuf', 'samp', 'samp_tex', 'samp_id', 'samp_c2a',
                   'cbuf', 'sbuf', 'sbuf_ubo', 'support', 'c1', 'drvcb', 'gmem_map',
                   'gmem_log', 'geometry', 'ubo_ptr', 'border'}


def slot_reads_resolved(j):
    if j.get('route') != 'B':
        return False
    for b in j['bindings']:
        if b['kind'] in UNKNOWN_READ or b['kind'] not in SLOT_RESOLVABLE:
            return False
        if (b.get('msl_name', '').endswith('_cb0_40000000')
                and b.get('msl_type', '').startswith('array<')):
            return False
        if b['kind'] in {'tex', 'img', 'tbuf'} and (not isinstance(b.get('reg'), int) or b['reg'] < 0):
            return False
    return True


def audit(profile, reflection):
    captured = datetime.now(timezone.utc).isoformat()
    available = {p.name[:-7] for p in reflection.glob('*_b.json')}
    with (profile / 'shader_map.tsv').open() as f:
        rows = list(csv.DictReader((s for s in f if not s.startswith('#')), delimiter='\t'))
    keys = {r['dm_ctl_sha16'] for r in rows}
    stages = {r['dm_ctl_sha16']: r['stage'] for r in rows}
    facts = {}
    for line in (profile / 'shader_facts.tsv').read_text().splitlines():
        if line and not line.startswith('#'):
            key, value = line.split('\t', 1)
            facts[key] = json.loads(value)
    kinds, by_stage, chains = Counter(), Counter(), Counter()
    allowed, unresolved, missing = [], [], []
    digest = hashlib.sha256()
    for key in sorted(keys):
        path = reflection / f'{key}_b.json'
        if key not in available:
            missing.append(key)
            continue
        raw = path.read_bytes()
        digest.update(key.encode() + raw)
        j = json.loads(raw)
        ks = {b['kind'] for b in j['bindings']}
        kinds.update(ks)
        chains[j.get('chain', 'unknown')] += 1
        unknown = not slot_reads_resolved(j)
        (unresolved if unknown else allowed).append(key)
        by_stage[f"{stages[key]}:{'unresolved' if unknown else 'slot_resolvable'}"] += 1
    return dict(captured_utc=captured, profile_keys=len(keys), fact_rows=len(facts),
                fact_fields=dict(Counter(k for v in facts.values() for k in v)),
                reflection_sha256=digest.hexdigest(), chains=dict(chains),
                shaders_by_binding_kind=dict(sorted(kinds.items())), by_stage=dict(sorted(by_stage.items())),
                slot_resolvable_keys=allowed, unresolved_keys=unresolved, missing_keys=missing)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', type=Path)
    p.add_argument('reflection', type=Path, help='one stamped b-<chain> directory, read-only')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.profile, a.reflection)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: len(v) if k.endswith('_keys') and isinstance(v, list) else v
                      for k, v in result.items()}, indent=2))


if __name__ == '__main__':
    main()

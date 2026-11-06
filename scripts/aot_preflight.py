#!/usr/bin/env python3
"""Report static AOT coverage after packing. No game launch or compilation."""
import argparse
import json
from pathlib import Path


def report(bundle):
    bundle = Path(bundle)
    pso = bundle / 'Contents/Resources/pso' if bundle.suffix == '.app' else bundle
    source = pso / 'aot-preflight.json'
    if not source.is_file():
        return {'complete': False, 'archive_verified': False, 'gaps': {'expanded AOT inventory': 'not packed'}}
    result = json.loads(source.read_text())
    result['archives'] = {p.name: p.stat().st_size for p in sorted(pso.glob('*.mtl4a'))}
    result['archive_verified'] = False
    if not result['archives']: result.setdefault('gaps', {})['archive'] = 'none packed'
    result['verification'] = 'Static inventory only; startup archive-only prewarm must confirm device/OS/library compatibility.'
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('bundle', help='packed .app or pipeline archive folder')
    ap.add_argument('--out', type=Path)
    a = ap.parse_args(argv)
    result = report(a.bundle)
    text = json.dumps(result, indent=2) + '\n'
    if a.out: a.out.write_text(text)
    print('AOT preflight: ' + json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

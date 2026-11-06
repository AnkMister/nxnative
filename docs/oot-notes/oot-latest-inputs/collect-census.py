#!/usr/bin/env python3
"""Freeze completed play censuses and combine every observed pipeline row."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[2] / 'nxnative'
SAVES = WORK / 'oot-saves'
LIVE = Path.home() / 'Library/Application Support/nxnative/0400486024DEC000'


def collect():
    if subprocess.run(['pgrep', '-x', 'dmhost'], stdout=subprocess.DEVNULL).returncode == 0:
        raise SystemExit('Quit dmhost before freezing the live pipeline census.')
    required = SAVES / 'session2-0120/pso_user.tsv'
    if not required.is_file(): raise SystemExit(f'Missing final session census: {required}')
    inputs = []
    for session in sorted(SAVES.glob('session1-*')) + [required.parent]:
        for name in ('pso_user.tsv', 'pso_seen.jsonl'):
            if (session / name).is_file(): inputs.append((session.name, session / name))
    for name in ('pso_user.tsv', 'pso_seen.jsonl'):
        if (LIVE / name).is_file(): inputs.append(('live-after-quit', LIVE / name))
    if not (LIVE / 'pso_user.tsv').is_file(): raise SystemExit('Missing live pipeline census after quit.')
    saved_json = WORK / 'playtest-1/live/pso_seen.jsonl'
    if saved_json.is_file(): inputs.append(('playtest-1', saved_json))
    snapshots = ROOT / 'snapshots'; snapshots.mkdir(parents=True, exist_ok=True)
    native, portable, sources = {}, {}, []
    for label, source in inputs:
        before = source.stat(); data = source.read_bytes(); after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise SystemExit(f'Census changed during snapshot; retry after the game exits: {source}')
        digest = hashlib.sha256(data).hexdigest()
        target = snapshots / f'{label}-{digest[:16]}-{source.name}'
        if target.exists():
            if target.read_bytes() != data: raise SystemExit(f'Snapshot hash collision: {target}')
        else:
            target.write_bytes(data); target.chmod(0o444)
        rows = [line for line in data.decode('utf-8').splitlines() if line and not line.startswith('#')]
        if source.suffix == '.tsv':
            for line in rows: native.setdefault(line, None)
            classes = dict(Counter(line.split('\t', 1)[0] for line in rows))
        else:
            for line in rows:
                row = json.loads(line)
                if not isinstance(row, dict): raise SystemExit(f'Invalid portable census row: {source}')
                portable.setdefault(json.dumps(row, sort_keys=True, separators=(',', ':')), row)
            classes = dict(Counter(json.loads(line).get('class', 'unknown') for line in rows))
        sources.append(dict(source=str(source), snapshot=str(target.relative_to(ROOT)), sha256=digest,
                            bytes=len(data), rows=len(rows), unique_rows=len(set(rows)), classes=classes))
    user = ('\n'.join(native) + '\n').encode()
    seen = ('\n'.join(portable) + '\n').encode()
    (ROOT / 'pso_user.tsv').write_bytes(user)
    (ROOT / 'pso_seen.jsonl').write_bytes(seen)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), sources=sources,
                  merged_native=dict(rows=len(native), classes=dict(Counter(line.split('\t', 1)[0] for line in native)), sha256=hashlib.sha256(user).hexdigest()),
                  merged_portable=dict(rows=len(portable), classes=dict(Counter(row.get('class', 'unknown') for row in portable.values())), sha256=hashlib.sha256(seen).hexdigest()))
    (ROOT / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('merged_native', 'merged_portable')}, sort_keys=True))


if __name__ == '__main__': collect()

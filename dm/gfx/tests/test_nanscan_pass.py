"""Check production Metal 4 pass ordering through the VQA parser."""
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from oot_vqa import summarize_log

if __name__ == '__main__':
    env = dict(os.environ, MTL_DEBUG_LAYER='1')
    run = subprocess.run([str(Path(sys.argv[1]).resolve())], env=env, text=True, capture_output=True, timeout=30)
    print(run.stdout, end=''); print(run.stderr, end='', file=sys.stderr)
    assert run.returncode == 0, f'pass scan failed with {run.returncode}'
    events = summarize_log(run.stderr.splitlines())
    assert events['nan_scanned_targets'] == 2, events
    assert [(e['pass'], e['nonfinite']) for e in events['nan_hits']] == [(1, 256)], events
    assert not events['red_types'], events
    off = subprocess.run([str(Path(sys.argv[1]).resolve()), 'off'], env=env, text=True, capture_output=True, timeout=30)
    assert off.returncode == 0, off.stderr
    assert '[nanscan]' not in off.stderr, off.stderr
    print('Default-off scan: no scan events')
    print('Production pass scan: two stored targets, one hit before overwrite; checks passed')

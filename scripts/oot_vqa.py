#!/usr/bin/env python3
"""Read-only visual-quality and pacing report for a host run or oot_ab run folder.

No game launches. Log counts are observed messages, not inferred GPU work.
Uses bench.py's timing selection/percentiles, also used by oot_ab.py.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics

import bench

KEY = r'(?<![0-9a-fA-F])[0-9a-fA-F]{16}(?![0-9a-fA-F])'
NAN = re.compile(r'\[nanscan\] frame=(\d+) pass=(\d+) c=(\d+) ser=(\d+) lv=(\d+) layer=(\d+) nonfinite=(\d+) pixels=(\d+) keys=(\S+)')
LONG = re.compile(r'frame (\d+) \(([\d.]+) s\).*?new pipelines (\d+) \+ shader libraries (\d+), ([\d.]+) ms in all')


def event_type(text):
    text = re.sub(KEY, '<key>', text)
    text = re.sub(r'0x[0-9a-fA-F]+', '<addr>', text)
    return re.sub(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', '<n>', text)


def summarize_log(lines):
    groups = {k: Counter() for k in ('skipped_draws', 'missing_shader_keys', 'untranslated_shaders', 'red_types')}
    hits, stalls, skips, scanned, colour = [], [], Counter(), 0, []
    first = None
    for number, line in enumerate(lines, 1):
        if 'present colour:' in line or '[vqa] display colour:' in line or '[vqa] present source ' in line or '[vqa] QueryDisplayHdr' in line:
            colour.append(dict(log_line=number, message=line.strip()))
        if 'draw skipped: no render pipeline' in line:
            groups['skipped_draws'][line[line.index('draw skipped:'):].strip()] += 1
        if 'is not in the shader map' in line or 'missing shader key' in line:
            groups['missing_shader_keys'].update(re.findall(KEY, line))
        if re.search(r'shader .*failed to load|failed to load shader|untranslated shader|shader .*has no library|no (?:translated )?library.*shader', line, re.I):
            keys = re.findall(KEY, line)
            groups['untranslated_shaders'].update(keys or [line.strip()])
        if '[RED] ' in line:
            groups['red_types'][event_type(line.split('[RED] ', 1)[1].strip())] += 1
        m = NAN.search(line)
        if m:
            names = ('frame', 'pass', 'attachment', 'serial', 'level', 'layer', 'nonfinite', 'pixels')
            entry = dict(zip(names, map(int, m.groups()[:8])))
            entry.update(keys=m[9].split(','), log_line=number)
            scanned += 1
            if entry['nonfinite']:
                hits.append(entry)
                # Completion callbacks can arrive out of log order. Use GPU replay order.
                if first is None or (entry['frame'], entry['pass']) < (first['frame'], first['pass']): first = entry
        if '[nanscan] skip ' in line:
            reason = re.search(r'reason=(\S+)', line)
            skips[reason[1] if reason else 'unknown'] += 1
        m = LONG.search(line)
        if m and float(m[5]) > 0:
            stalls.append(dict(frame=int(m[1]), t_s=float(m[2]), pipelines=int(m[3]),
                               libraries=int(m[4]), compile_ms=float(m[5]), log_line=number))
    return dict(**{k: dict(v.most_common()) for k, v in groups.items()}, nan_scanned_targets=scanned,
                nan_hits=hits, nan_first_observed_pass=first, nan_skipped_targets=dict(skips),
                pipeline_compile_on_long_frames=stalls, colour_pipeline=colour)


def frame_rows(path, start, end):
    # bench.frames returns value lists; retain frame identity here for clusters.
    rows = {}
    with Path(path).open(errors='replace') as f:
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) != 3 or not c[1].startswith('@'): continue
            try: frame, value = int(c[0]), float(c[2])
            except ValueError: continue
            if frame >= 0 and math.isfinite(value): rows.setdefault(frame, {})[c[1]] = value
    return [(f, r) for f, r in sorted(rows.items()) if start <= r.get('@t_s', -1) < end]


def pacing(path, start=0., end=math.inf, fps=30.):
    rows = frame_rows(path, start, end)
    ft, shown, gpu, dropped, n = bench.frames(path, start, end)
    ft, shown, gpu = ([x for x in xs if math.isfinite(x)] for xs in (ft, shown, gpu))
    budget = 1000 / fps
    summary = bench.summary(ft, shown, gpu, dropped, n, end - start if math.isfinite(end) else 0, budget)
    # No frame-rate estimate for an unbounded/incomplete measurement window.
    if not math.isfinite(end): summary['fps'] = None
    boundaries = [0, .5, 1, 1.5, 2, 3, math.inf]
    hist = [{'min_ms': a * budget, 'max_ms': b * budget if math.isfinite(b) else None,
             'frames': sum(a * budget < x <= b * budget for x in ft)} for a, b in zip(boundaries, boundaries[1:])]
    clusters = []
    for frame, r in rows:
        ms = r.get('@frame_ms', 0)
        if ms <= 1.5 * budget: continue
        if clusters and frame == clusters[-1]['last_frame'] + 1:
            c = clusters[-1]; c['last_frame'] = frame; c['frames'] += 1; c['max_ms'] = max(c['max_ms'], ms)
        else: clusters.append(dict(first_frame=frame, last_frame=frame, frames=1, max_ms=ms))
    errors = [x - budget for x in shown]
    jitter = dict(samples=len(shown), missing_intervals=n - len(shown) - dropped,
                  rms_error_ms=math.sqrt(statistics.mean(x*x for x in errors)) if errors else None,
                  stddev_ms=statistics.pstdev(shown) if shown else None,
                  p95_abs_error_ms=bench.pct([abs(x) for x in errors], 95),
                  max_abs_error_ms=max(map(abs, errors), default=None))
    compiles = [dict(frame=f, compile_ms=r['@compile_ms'], pipelines=r.get('@pso_new'), libraries=r.get('@lib_new'))
                for f, r in rows if r.get('@compile_ms', 0) > 0]
    return dict(summary=summary, target_fps=fps, target_ms=budget, histogram=hist, stutter_clusters=clusters,
                present_interval_jitter=jitter, compile_frames=compiles)


def markdown(report):
    log = report['log']; lines = ['# Ocarina VQA', '', 'Observed log messages. Counts may be limited by host logging or pass-dump selection.',
        'Log events cover the whole run; pacing uses the selected window. Compilation on a long frame is evidence of compile work, not proof it caused the stall.', '']
    for key in ('skipped_draws', 'missing_shader_keys', 'untranslated_shaders', 'red_types'):
        lines += [f'## {key}', '']
        lines += [f'- {count} × `{text}`' for text, count in log[key].items()] or ['No messages observed.']
        lines.append('')
    lines += ['## Colour pipeline', ''] + ['- ' + e['message'] for e in log['colour_pipeline']] + ['']
    lines += ['## Non-finite scan', '', f"Scanned target slices: {log['nan_scanned_targets']}. Hits: {len(log['nan_hits'])}. Skips: {sum(log['nan_skipped_targets'].values())}."]
    if not log['nan_scanned_targets']: lines += ['Coverage unavailable. Zero hits is not a clean scan.']
    if log['nan_first_observed_pass']: lines += ['First observed pass: `' + json.dumps(log['nan_first_observed_pass']) + '`']
    lines += ['Shader keys are candidates for that pass. Existing contents, compute writes and earlier draws can be the source.', '', '## Pipeline compile work on long frames', '']
    lines += ['- `' + json.dumps(e) + '`' for e in log['pipeline_compile_on_long_frames']] or ['No messages observed.']
    p = report.get('pacing')
    if p:
        lines += ['', '## Pacing', '', '`' + json.dumps(p['summary']) + '`', '', '| Frame interval, ms | Frames |', '|---|---:|']
        lines += [f"| ({h['min_ms']:.3f}, {format(h['max_ms'], '.3f') if h['max_ms'] is not None else '∞'}] | {h['frames']} |" for h in p['histogram']]
        lines += ['', 'Consecutive frame IDs above 1.5× target form one stutter cluster.', '', '`' + json.dumps(p['stutter_clusters']) + '`', '', 'Present-interval jitter against the target period:', '', '`' + json.dumps(p['present_interval_jitter']) + '`', '', f"Frames with synchronous compile work: {len(p['compile_frames'])}."]
    else: lines += ['', 'Pacing unavailable. Supply frames.tsv from DM_NVN_TSV. Sparse long-frame log messages cannot form a histogram.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path, help='log file or oot_ab A-1/B-1 folder (log.txt, frames.tsv)')
    ap.add_argument('--frames', type=Path)
    ap.add_argument('--window', help='start,length in seconds, identical to oot_ab')
    ap.add_argument('--fps', type=float, default=30.)
    ap.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    ap.add_argument('--out', type=Path, help='write report here instead of stdout')
    args = ap.parse_args(argv)
    try:
        if not math.isfinite(args.fps) or args.fps <= 0: raise ValueError('--fps must be positive and finite')
        start, end = 0., math.inf
        if args.window:
            start, length = map(float, args.window.split(',')); end = start + length
            if not all(map(math.isfinite, (start, length, end))) or start < 0 or length <= 0: raise ValueError('invalid --window')
        log = args.run / 'log.txt' if args.run.is_dir() else args.run
        frames = args.frames or log.with_name('frames.tsv')
        with log.open(errors='replace') as f: events = summarize_log(f)
        report = dict(log_path=str(log), frames_path=str(frames) if frames.is_file() else None,
                      window=[start, end if math.isfinite(end) else None], log=events)
        if args.frames or frames.is_file(): report['pacing'] = pacing(frames, start, end, args.fps)
        text = json.dumps(report, indent=2, allow_nan=False) + '\n' if args.format == 'json' else markdown(report)
        if args.out:
            if args.out.resolve() in {log.resolve(), frames.resolve()}: raise ValueError('--out must differ from log and frame inputs')
            args.out.write_text(text)
        else: print(text, end='')
        return 0
    except (OSError, ValueError) as e: ap.error(str(e))


if __name__ == '__main__':
    raise SystemExit(main())

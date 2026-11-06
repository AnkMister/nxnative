#!/usr/bin/env python3
"""Mac-only, 30 fps Ocarina efficiency comparison. No builds or cache cleanup.

A/B inputs are --a/--b <id>_build folders (optional --a-host/--b-host), or
Mac .app bundles. Each run copies --save into its own output directory.
Smoke TSV parsing and frame/GPU percentile reading come from regress.py/bench.py.
Counters are sampled over the same window as frames, before terminating the host.
Billed energy is an opaque kernel counter, NOT joules or whole-machine energy.
"""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import time

import regress

GID = '0400486024DEC000'
SCRATCH = Path('/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch')
# sys/resource.h rusage_info_v6: UUID, 47 uint64 fields, nine reserved words.
FIELDS = '''user_time system_time pkg_idle_wkups interrupt_wkups pageins wired_size
resident_size phys_footprint proc_start_abstime proc_exit_abstime child_user_time
child_system_time child_pkg_idle_wkups child_interrupt_wkups child_pageins
child_elapsed_abstime diskio_bytesread diskio_byteswritten cpu_time_qos_default
cpu_time_qos_maintenance cpu_time_qos_background cpu_time_qos_utility
cpu_time_qos_legacy cpu_time_qos_user_initiated cpu_time_qos_user_interactive
billed_system_time serviced_system_time logical_writes lifetime_max_phys_footprint
instructions cycles billed_energy serviced_energy interval_max_phys_footprint
runnable_time flags user_ptime system_ptime pinstructions pcycles energy_nj
penergy_nj secure_time_in_system secure_ptime_in_system neural_footprint
lifetime_max_neural_footprint interval_max_neural_footprint'''.split()


class RusageV6(ctypes.Structure):
    _fields_ = [('ri_uuid', ctypes.c_uint8 * 16)] + [
        ('ri_' + name, ctypes.c_uint64) for name in FIELDS
    ] + [('ri_reserved', ctypes.c_uint64 * 9)]


class Timebase(ctypes.Structure):
    _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]


class ProcUsage:
    def __init__(self):
        self.lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        tb = Timebase()
        system = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        system.mach_timebase_info.argtypes = [ctypes.POINTER(Timebase)]
        if system.mach_timebase_info(ctypes.byref(tb)) or not tb.denom:
            raise OSError('mach_timebase_info failed')
        self.seconds_per_tick = tb.numer / tb.denom / 1e9
        self.lib.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        self.lib.proc_pid_rusage.restype = ctypes.c_int

    def read(self, pid):
        value = RusageV6()
        if self.lib.proc_pid_rusage(pid, 6, ctypes.byref(value)):
            err = ctypes.get_errno()
            raise OSError(err, f'proc_pid_rusage(V6), pid {pid}: {os.strerror(err)}')
        return {name: getattr(value, 'ri_' + name) for name in FIELDS}


def env_file(path):
    """Literal KEY=VALUE, optional shell quotes. Never execute or expand text."""
    out = {}
    if path is None: return out
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'): continue
        key, sep, value = line.strip().partition('=')
        if not sep or not re.fullmatch(r'DM_[A-Z0-9_]+', key):
            raise ValueError(f'{path}:{n}: expected DM_NAME=VALUE')
        parts = shlex.split(value, comments=False)
        if len(parts) > 1: raise ValueError(f'{path}:{n}: quote values containing spaces')
        out[key] = parts[0] if parts else ''
    return out


def build_paths(path, host=None):
    path = Path(path).expanduser().resolve()
    if path.suffix == '.app':
        res = path / 'Contents/Resources'
        mod = res / 'dm'
        exe = path / 'Contents/MacOS/dmhost'
        romfs = res / ('romfs.img' if (res / 'romfs.img').is_file() else 'romfs')
        env = env_file(mod / 'env.txt') if (mod / 'env.txt').is_file() else {}
        env.update(DM_ROMFS=str(romfs), DM_MSL_DIR=str(res / 'msl'),
                   DM_FONT_DIR=str(mod / 'font'), DM_NVN_SHMAP=str(mod / 'shader_map.tsv'))
        if (res / 'pso').is_dir(): env['DM_PSO_BUNDLE'] = str(res / 'pso')
        if (res / 'aoc').is_dir(): env['DM_AOC_DIR'] = str(res / 'aoc')
        return exe, mod, env
    exe = Path(host).expanduser().resolve() if host else path / 'tools/dmhost'
    mod = path / 'patched_v131072'
    romfs = regress.bench.rfs.source(path / 'extract/v131072')
    prof = path / 'profile' / GID
    if not prof.is_dir(): prof = regress.REPO / 'dm/games' / GID
    env = dict(DM_ROMFS=str(romfs), DM_MSL_DIR=str(path / 'shader/cache'),
               DM_FONT_DIR=str(path / 'font'), DM_NVN_SHMAP=str(prof / 'shader_map.tsv'))
    if (path / 'pso/mac').is_dir(): env['DM_PSO_BUNDLE'] = str(path / 'pso/mac')
    if (path / 'aoc').is_dir(): env['DM_AOC_DIR'] = str(path / 'aoc')
    return exe, mod, env


def route_for(args):
    route = dict(keys='f2600:A,f2950:A', secs=180., window=(120., 58.),
                 hang=20., reach=(2951, 115.), save='run')
    if args.route:
        route.update(regress.read_route(Path(args.route)))
        if route['window'] is None: route['window'] = (route['secs'] / 2, route['secs'] / 2 - 2)
    if args.seconds is not None: route['secs'] = args.seconds
    if args.window: route['window'] = tuple(float(x) for x in args.window.split(','))
    start, length = route['window']
    if (not all(math.isfinite(x) for x in (start, length, route['secs'], route['hang']))
            or start < 0 or length <= 0 or start + length > route['secs'] - .5 or route['hang'] <= 0):
        raise ValueError('window must be positive and end at least 0.5 s before the deadline')
    if route['reach'] and route['reach'][1] > route['secs']:
        raise ValueError('reach deadline exceeds run length; supply a matching --route')
    if args.save: route['source_save'] = Path(args.save).expanduser().resolve()
    elif route['save'] == 'new': route['source_save'] = None
    else:
        if args.route and route['save'] != 'run':
            raise ValueError('use --save to resolve a named smoke save folder')
        route['source_save'] = Path(args.a).expanduser().resolve() / 'run/save'
    return route


def counter_metrics(first, last, seconds_per_tick):
    def delta(k):
        if last[k] < first[k]: raise ValueError(f'counter {k} went backwards')
        return last[k] - first[k]
    return dict(cpu_s=(delta('user_time') + delta('system_time')) * seconds_per_tick,
                pkg_idle_wkups=delta('pkg_idle_wkups'), interrupt_wkups=delta('interrupt_wkups'),
                billed_energy=delta('billed_energy'), phys_footprint_mb=last['phys_footprint'] / 1048576,
                peak_footprint_mb=last['lifetime_max_phys_footprint'] / 1048576)


def run_process(command, env, out, route, sampler=None):
    """regress.run_watched's deadline/progress watchdog, with windowed V6 sampling.

    Kept separate: run_watched also cleans caches and pauses for other jobs, neither
    appropriate while the user works alongside this efficiency benchmark.
    """
    sampler = sampler or ProcUsage()
    start, length = route['window']
    samples = []
    status, max_frame, last_new, pos = 'ok', -1, None, 0
    p = None
    t0 = time.monotonic()
    try:
        with (out / 'log.txt').open('w') as log:
            p = subprocess.Popen([str(x) for x in command], cwd=out, env=env,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        t0 = time.monotonic()
        while p.poll() is None:
            elapsed = time.monotonic() - t0
            usage = sampler.read(p.pid)
            samples.append(dict(t=elapsed, usage=usage))
            frames = out / 'frames.tsv'
            if frames.is_file():
                with frames.open() as f:
                    f.seek(pos); chunk = f.read(); cut = chunk.rfind('\n') + 1
                    pos += len(chunk[:cut].encode())
                for line in chunk[:cut].splitlines():
                    c = line.split('\t')
                    if len(c) == 3 and c[1] == '@t_s' and c[0].isdigit() and int(c[0]) > max_frame:
                        max_frame, last_new = int(c[0]), elapsed
            if elapsed >= route['secs']: break
            if route.get('reach'):
                frame, deadline = route['reach']
                if elapsed >= deadline and max_frame < frame:
                    status = f'missed reach {frame}@{deadline}'; break
            if last_new is not None and elapsed - last_new > route['hang']:
                status = 'hang'; break
            time.sleep(.1)
        else: status = f'early exit {p.returncode}'
    finally:
        if p is not None:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
                try: p.wait(5)
                except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()
    result = dict(status=status, max_frame=max_frame, samples=samples,
                  cpu_seconds_per_tick=sampler.seconds_per_tick)
    # First sample at/after the start, first at/after the end: endpoint skew < poll interval.
    before = next((s for s in samples if s['t'] >= start), None)
    after = next((s for s in samples if s['t'] >= start + length), None)
    if before and after:
        result.update(counter_metrics(before['usage'], after['usage'], sampler.seconds_per_tick))
        result['counter_window'] = [before['t'], after['t']]
        result['peak_footprint_mb'] = max(s['usage']['lifetime_max_phys_footprint'] for s in samples) / 1048576
    else: result['status'] = status if status != 'ok' else 'incomplete counter window'
    frames = out / 'frames.tsv'
    if frames.is_file():
        ft, shown, gpu, dropped, count = regress.bench.frames(frames, start, start + length)
        result.update(frames=count, fps_p50=statistics.median([1000 / x for x in ft]) if ft else None,
                      frame_p99_ms=regress.bench.pct(ft, 99), gpu_p50_ms=regress.bench.pct(gpu, 50),
                      fps_mean=count / length, dropped=dropped)
    if not result.get('frames') and result['status'] == 'ok': result['status'] = 'no measured frames'
    if result.get('fps_mean', 0) > 31.5 or (result.get('fps_p50') or 0) > 31.5:
        result['status'] = '30 fps cap not observed (>31.5 fps)'
    return result


METRICS = ('fps_p50', 'frame_p99_ms', 'gpu_p50_ms', 'cpu_s', 'pkg_idle_wkups',
           'interrupt_wkups', 'billed_energy', 'phys_footprint_mb', 'peak_footprint_mb')


def markdown(results):
    lines = ['30 fps cap. Cells: median [min, max]. Delta = B − A.',
             'Spread = max(A range, B range). Significant only with ≥2 complete runs each and |delta| > spread.',
             'Billed energy uses kernel counter units; peak footprint is the process lifetime peak.',
             '', '| Metric | A | B | Delta | Exceeds spread |', '|---|---:|---:|---:|:---:|']
    for key in METRICS:
        values = [[r[key] for r in results[label] if r['status'] == 'ok' and r.get(key) is not None] for label in ('A', 'B')]
        def cell(xs):
            return f'{statistics.median(xs):.4g} [{min(xs):.4g}, {max(xs):.4g}]' if xs else 'unavailable'
        delta, sig = 'unavailable', 'no'
        if all(values):
            d = statistics.median(values[1]) - statistics.median(values[0])
            delta = f'{d:+.4g}'
            if all(len(v) == len(results[label]) and len(v) >= 2 for label, v in zip(('A', 'B'), values)):
                sig = 'yes' if abs(d) > max(max(v) - min(v) for v in values) else 'no'
            else: sig = 'insufficient runs'
        lines.append(f'| {key} | {cell(values[0])} | {cell(values[1])} | {delta} | {sig} |')
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    for label in ('a', 'b'):
        ap.add_argument('--' + label, required=True, help='Mac build folder or .app')
        ap.add_argument('--' + label + '-host', help='override build folder dmhost')
        ap.add_argument('--' + label + '-env', help='literal DM_NAME=VALUE file')
    ap.add_argument('--save', help='same immutable save source for both builds; copied per run')
    ap.add_argument('--route', help='regress.py smoke.tsv (shots/prebuild not used)')
    ap.add_argument('--seconds', type=float, help='override route wall deadline')
    ap.add_argument('--window', help='measurement start,length in seconds')
    ap.add_argument('--runs', type=int, default=3, help='runs PER BUILD, order A B A B …')
    ap.add_argument('--out', required=True, help='new output directory, outside input builds')
    ap.add_argument('--dry-run', action='store_true', help='print plan; no writes or launches')
    args = ap.parse_args(argv)
    try:
        if args.runs < 1: raise ValueError('--runs must be positive')
        route = route_for(args)
        out = Path(args.out).expanduser().resolve()
        if out.exists(): raise ValueError('--out must be a new directory')
        builds = {}
        for label in ('a', 'b'):
            source = Path(getattr(args, label)).expanduser().resolve()
            if out == source or source in out.parents: raise ValueError('--out must be outside input builds')
            exe, mod, env = build_paths(source, getattr(args, label + '_host'))
            env.update(env_file(getattr(args, label + '_env')))
            builds[label.upper()] = (exe, mod, env)
        print(f'30 fps; keys={route["keys"]}; deadline={route["secs"]} s; window={route["window"]}; save={route["source_save"]}', flush=True)
        for i in range(1, args.runs + 1):
            for label, (exe, mod, flags) in builds.items():
                print(f'{label}-{i}: {shlex.join([str(exe), str(mod)])} → {out / f"{label}-{i}"}', flush=True)
        for label, (_, _, flags) in builds.items():
            print(f'{label} input flags: {json.dumps(flags, sort_keys=True)}', flush=True)
        print('Forced: DM_FPS_TARGET=30, HUD/audio off, per-run save/temp/archive and frame TSV.', flush=True)
        if args.dry_run: return 0
        if sys.platform != 'darwin': raise ValueError('rusage V6 requires macOS')
        for exe, mod, env in builds.values():
            if not exe.is_file() or not os.access(exe, os.X_OK) or not mod.is_dir():
                raise ValueError(f'incomplete build: {exe}, {mod}')
            if not Path(env['DM_ROMFS']).exists(): raise ValueError('missing RomFS')
        save = route['source_save']
        if save is not None and not save.is_dir(): raise ValueError(f'missing save {save}; use --save or a route with save=new')
        SCRATCH.mkdir(parents=True, exist_ok=True)
        out.mkdir(parents=True)
        (out / 'plan.json').write_text(json.dumps(dict(
            route={k: str(v) if isinstance(v, Path) else v for k, v in route.items()},
            builds={label: dict(host=str(exe), modules=str(mod), flags=flags)
                    for label, (exe, mod, flags) in builds.items()}, runs=args.runs), indent=2) + '\n')
        results = {'A': [], 'B': []}
        for i in range(1, args.runs + 1):
            for label, (exe, mod, flags) in builds.items():
                run = out / f'{label}-{i}'; run.mkdir()
                if save is None: (run / 'save').mkdir()
                else: shutil.copytree(save, run / 'save')
                (run / 'temp').mkdir(); (run / 'ctl').touch()
                # Remove inherited DM switches so an interactive session cannot bias one side.
                env = {k: v for k, v in os.environ.items() if not k.startswith('DM_')}
                env.update(flags)
                env.update(DM_ROOT=str(run), DM_SAVE=str(run / 'save'), DM_TEMP=str(run / 'temp'),
                           DM_NVN_TSV=str(run / 'frames.tsv'), DM_NVN_TSV_CALLS='0', DM_CTL=str(run / 'ctl'),
                           DM_KEYS=route['keys'], DM_FPS_TARGET='30', DM_WINDOW='1', DM_WINDOW_TOP='1',
                           DM_FOCUS_KEEP='1', DM_AUDIO='0', DM_METAL_HUD='0', DM_PSO_PREBUILD='0',
                           DM_PSO_USER=str(run / 'pso_user.tsv'), DM_PSO_ARCHIVE=str(run / 'pso_archive'), TMPDIR=str(SCRATCH))
                result = run_process([exe, mod], env, run, route)
                results[label].append(result)
                (run / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
                print(f'{label}-{i}: {result["status"]}', flush=True)
        report = markdown(results)
        (out / 'results.md').write_text(report + '\n')
        print(report)
        return 0 if all(r['status'] == 'ok' for rs in results.values() for r in rs) else 1
    except (OSError, ValueError, regress.HarnessError) as e:
        ap.error(str(e))


if __name__ == '__main__':
    sys.exit(main())

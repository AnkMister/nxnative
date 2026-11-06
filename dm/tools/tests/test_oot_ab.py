"""No game, GPU, sudo or package dependencies. Run with the task's uv Python."""
import ctypes
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scripts'))
import oot_ab as ab


class OotAB(unittest.TestCase):
    def test_v6_layout(self):
        self.assertEqual(ctypes.sizeof(ab.RusageV6), 464)
        for name, offset in [('user_time', 16), ('pkg_idle_wkups', 32),
                             ('phys_footprint', 72), ('lifetime_max_phys_footprint', 240),
                             ('billed_energy', 264), ('reserved', 392)]:
            self.assertEqual(getattr(ab.RusageV6, 'ri_' + name).offset, offset)

    def test_v6_self(self):
        usage = ab.ProcUsage().read(os.getpid())
        self.assertGreater(usage['phys_footprint'], 0)
        self.assertGreaterEqual(usage['lifetime_max_phys_footprint'], usage['phys_footprint'])
        self.assertGreater(usage['user_time'], 0)

    def test_invalid_pid_is_error(self):
        with self.assertRaises(OSError): ab.ProcUsage().read(2147483647)

    def test_counter_units(self):
        first = {k: 100 for k in ab.FIELDS}
        last = dict(first, user_time=1000000100, system_time=500000100,
                    pkg_idle_wkups=113, interrupt_wkups=107, billed_energy=109,
                    phys_footprint=1048576, lifetime_max_phys_footprint=2097152)
        r = ab.counter_metrics(first, last, 1e-9)
        self.assertEqual(r['cpu_s'], 1.5)
        self.assertEqual(r['pkg_idle_wkups'], 13)
        self.assertEqual(r['interrupt_wkups'], 7)
        self.assertEqual(r['billed_energy'], 9)
        self.assertEqual(r['peak_footprint_mb'], 2)

    def test_counter_reset_is_error(self):
        with self.assertRaises(ValueError):
            ab.counter_metrics(dict.fromkeys(ab.FIELDS, 10), dict.fromkeys(ab.FIELDS, 0), 1e-9)

    def test_spread_and_missing_runs(self):
        def run(x): return dict(status='ok', cpu_s=x)
        report = ab.markdown({'A': [run(10), run(12)], 'B': [run(11), run(13)]})
        self.assertIn('| cpu_s | 11 [10, 12] | 12 [11, 13] | +1 | no |', report)
        report = ab.markdown({'A': [run(10), run(12)], 'B': [run(15), run(17)]})
        self.assertIn('| +5 | yes |', report)
        report = ab.markdown({'A': [run(10)], 'B': [run(15)]})
        self.assertIn('insufficient runs', report)
        report = ab.markdown({'A': [run(10), dict(status='hang', cpu_s=200)], 'B': [run(15), run(17)]})
        self.assertNotIn('| +6 | yes |', report)

    def test_env_literal(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / 'env'
            f.write_text('# flags\nDM_FOO="a b"\nDM_BAR=$(false)\nDM_EMPTY=\n')
            self.assertEqual(ab.env_file(f), dict(DM_FOO='a b', DM_BAR='$(false)', DM_EMPTY=''))
            f.write_text('PATH=bad\n')
            with self.assertRaises(ValueError): ab.env_file(f)

    def fake_run(self, source, seconds=1.5, reach=None, hang=2):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            host = out / 'fake.py'; host.write_text(source)
            route = dict(window=(.3, .6), secs=seconds, hang=hang, reach=reach)
            result = ab.run_process([sys.executable, host], dict(os.environ), out, route)
            return result

    def test_fake_cpu_and_sleep(self):
        r = self.fake_run('''import os, time
from pathlib import Path
t0 = time.monotonic()
with Path('frames.tsv').open('w', buffering=1) as f:
    n = 0
    while True:
        t = time.monotonic()
        while time.monotonic() - t < .005: pass
        f.write(f'{n}\\t@t_s\\t{time.monotonic()-t0}\\n{n}\\t@frame_ms\\t33.333333\\n{n}\\t@gpu_ms\\t4\\n')
        n += 1
        time.sleep(.028)
''')
        self.assertEqual(r['status'], 'ok')
        self.assertGreater(r['cpu_s'], .02)
        self.assertGreater(r['peak_footprint_mb'], 0)
        self.assertAlmostEqual(r['fps_p50'], 30, places=4)
        self.assertEqual(r['gpu_p50_ms'], 4)
        self.assertEqual(r['frame_p99_ms'], 33.333333)
        self.assertGreater(r['counter_window'][1], .9)
        self.assertLess(r['counter_window'][0], .5)
        self.assertTrue(all(k in r for k in ('pkg_idle_wkups', 'interrupt_wkups', 'billed_energy')))

    def test_fake_uncapped_is_invalid(self):
        r = self.fake_run("from pathlib import Path\nimport time\nwith Path('frames.tsv').open('w') as f:\n    for n in range(100):\n        f.write(f'{n}\\t@t_s\\t{n/60}\\n{n}\\t@frame_ms\\t16.667\\n')\ntime.sleep(10)")
        self.assertIn('cap not observed', r['status'])

    def test_cpu_timebase_matches_process_clock(self):
        import time
        sampler = ab.ProcUsage()
        before = sampler.read(os.getpid()); start = time.process_time()
        while time.process_time() - start < .05: pass
        elapsed = time.process_time() - start
        after = sampler.read(os.getpid())
        measured = ab.counter_metrics(before, after, sampler.seconds_per_tick)['cpu_s']
        self.assertAlmostEqual(measured, elapsed, delta=.015)

    def test_fake_early_exit(self):
        r = self.fake_run('import sys; sys.exit(3)')
        self.assertIn('early exit', r['status'])
        self.assertNotIn('cpu_s', r)

    def test_fake_missing_route_progress(self):
        r = self.fake_run('import time; time.sleep(10)', reach=(10, .4))
        self.assertIn('missed reach', r['status'])

    def test_fake_hang(self):
        r = self.fake_run("from pathlib import Path\nimport time\nPath('frames.tsv').write_text('1\\t@t_s\\t0.1\\n')\ntime.sleep(10)", hang=.2)
        self.assertEqual(r['status'], 'hang')

    def test_dry_run_no_writes_or_launch(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'uncreated'
            with patch.object(ab.subprocess, 'Popen', side_effect=AssertionError('launch')):
                self.assertEqual(ab.main(['--a', '/missing/A', '--b', '/missing/B', '--out', str(out), '--dry-run']), 0)
            self.assertFalse(out.exists())

    def test_app_paths(self):
        with tempfile.TemporaryDirectory() as td:
            app = Path(td) / 'game.app'; mod = app / 'Contents/Resources/dm'
            mod.mkdir(parents=True); (mod / 'env.txt').write_text('DM_TEST=1\n')
            exe, modules, env = ab.build_paths(app)
            self.assertEqual(modules, mod)
            self.assertEqual(exe, app / 'Contents/MacOS/dmhost')
            self.assertEqual(env['DM_TEST'], '1')


if __name__ == '__main__': unittest.main()

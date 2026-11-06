import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
import oot_vqa as vqa


class Vqa(unittest.TestCase):
    def test_actual_messages_and_grouping(self):
        events = vqa.summarize_log('''[nvn] Z 42 draw skipped: no render pipeline (vertex 0123456789abcdef fragment -)
[nvn] [RED] shader 0123456789abcdef is not in the shader map (DM_NVN_SHDUMP=directory saves its control section and code area)
[nvn] [RED] shader 1234567890abcdef is not in the shader map (DM_NVN_SHDUMP=directory saves its control section and code area)
[nvn] [RED] shader 0000000000000001 (pixel) failed to load: build the shaders with dm/gfx/tools/dmsh_build.py first
[longframe] frame 8 (2.50 s) whole frame 90.0 ms, new pipelines 2 + shader libraries 1, 25.5 ms in all
'''.splitlines())
        self.assertEqual(sum(events['skipped_draws'].values()), 1)
        self.assertEqual(len(events['missing_shader_keys']), 2)
        self.assertEqual(events['untranslated_shaders'], {'0000000000000001': 1})
        self.assertEqual(sorted(events['red_types'].values()), [1, 2])
        self.assertEqual(events['pipeline_compile_on_long_frames'][0]['compile_ms'], 25.5)

    def test_nan_earliest_replay_order_and_zero_coverage(self):
        events = vqa.summarize_log([
            '[nanscan] frame=2 pass=40 c=0 ser=4 lv=1 layer=2 nonfinite=3 pixels=256 keys=0123456789abcdef',
            '[nanscan] frame=1 pass=20 c=0 ser=3 lv=0 layer=0 nonfinite=0 pixels=256 keys=-',
            '[nanscan] frame=1 pass=21 c=1 ser=3 lv=0 layer=0 nonfinite=2 pixels=256 keys=a,b',
            '[nanscan] skip frame=1 pass=22 c=0 ser=4 reason=unreadable-or-discarded-target'])
        self.assertEqual(events['nan_scanned_targets'], 3)
        self.assertEqual(len(events['nan_hits']), 2)
        self.assertEqual(events['nan_first_observed_pass']['pass'], 21)
        self.assertEqual(events['nan_first_observed_pass']['keys'], ['a', 'b'])
        self.assertIn('Coverage unavailable', vqa.markdown({'log': vqa.summarize_log([])}))

    def test_tsv_window_histogram_clusters_and_jitter(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'frames.tsv'
            values = [(9, 9., 90., 90.), (10, 10., 33., 33.), (11, 11., 50., -1.),
                      (12, 12., 60., 40.), (13, 13., 70., 30.), (15, 14., 100., 50.), (16, 15., 500., 500.)]
            path.write_text('\n'.join(f'{f}\t@{key}\t{v}' for f, ts, ft, shown in values
                                      for key, v in [('t_s', ts), ('frame_ms', ft), ('presented_ms', shown)]))
            p = vqa.pacing(path, 10, 15)
            self.assertEqual(p['summary']['frames'], 5)
            self.assertEqual(p['summary']['over_budget'], 3) # exactly 50 is not >1.5x
            self.assertEqual(p['summary']['dropped'], 1)
            self.assertEqual(sum(x['frames'] for x in p['histogram']), 5)
            self.assertEqual([(x['first_frame'], x['last_frame']) for x in p['stutter_clusters']], [(12, 13), (15, 15)])
            self.assertEqual(p['present_interval_jitter']['samples'], 4)
            self.assertAlmostEqual(p['present_interval_jitter']['max_abs_error_ms'], 50 - 1000/30)

    def test_cli_json_folder_and_missing_timings(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d); (folder / 'log.txt').write_text('[RED] test 123')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(vqa.main([d, '--format', 'json']), 0)
            report = json.loads(out.getvalue()); self.assertIsNone(report['frames_path'])
            self.assertNotIn('pacing', report)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): vqa.main([d, '--fps', 'nan'])

    def test_library_suffix_and_colour_evidence(self):
        events = vqa.summarize_log([
            '[RED] failed to load shader 0123456789abcdef_b: no reflection json',
            'present colour: srgb, BGRA8Unorm, SDR full range',
            '[vqa] QueryDisplayHdrStatus: on=0 format=0 peak=0 (host SDR)'])
        self.assertEqual(events['untranslated_shaders'], {'0123456789abcdef': 1})
        self.assertEqual(len(events['colour_pipeline']), 2)

    def test_empty_malformed_nonfinite_rows(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'frames.tsv'
            path.write_text('frame\tmetric\tvalue\nnot a row\n1\t@frame_ms\tnan\n1\t@t_s\t1\n1\t@presented_ms\tinf\n')
            p = vqa.pacing(path)
            self.assertEqual(p['stutter_clusters'], [])
            self.assertEqual(p['present_interval_jitter']['samples'], 0)
            self.assertIsNone(p['summary']['frame_p50'])
            json.dumps(p, allow_nan=False)


if __name__ == '__main__': unittest.main()

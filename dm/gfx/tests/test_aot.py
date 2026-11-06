"""Small, real Metal archives. Enable with DM_TEST_AOT=<built t_aot>."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'dm/gfx/tools'))
import pso_offline as po
import pso_aot
import shader_lib


def render(chain, kind='render'):
    row = dict(version=1, chain=chain, **{'class': kind}, samples=1, a2c=False, raster=True, depth=0, stencil=0,
               colors=[[70, 15, False, 1, 0, 0, 1, 0, 0]] + [[0, 15, False, 1, 0, 0, 1, 0, 0]] * 7,
               fragment=['f_b', 'main0'])
    if kind == 'render': row.update(vertex=['v_b', 'main0'], topology=0, amp=1, attrs=[[0, 0, 0]] * 31, layouts=[[0, 1, 1]] * 31)
    else: row.update(mesh=['m_b', 'main0'], object=['t_b', 'main0'], mesh_threads=1, object_threads=1, payload=16, mesh_grid=0, mesh_multiple=False, object_multiple=False)
    return row


class Planning(unittest.TestCase):
    def test_explicit_constant_values_and_rebase(self):
        row = render('old'); row['fragment'].append([[0, 'int', -2], [32, 'bool', True]])
        self.assertEqual(pso_aot.validate(row, 'new', rebase=True)['fragment'][2], [[0, 'int', -2], [32, 'bool', True]])
        row['fragment'][2].append([0, 'int', 3])
        with self.assertRaisesRegex(ValueError, 'duplicate'): pso_aot.validate(row, 'old')

    def test_startup_manifest_keeps_profile_and_all_user_rows(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); (p / 'seed').write_text('# seed\nS\tv_b\t0\n')
            (p / 'user').write_text('S\tv_b\t0\nC\tc_b\nM\t-\t0102\nR\t0304\n')
            self.assertEqual(pso_aot.manifest(p / 'seed', [p / 'user']).splitlines()[1:], ['S\tv_b\t0', 'C\tc_b', 'M\t-\t0102', 'R\t0304'])
    def test_validate_stale_chain_and_paths(self):
        row = render('x'); self.assertEqual(pso_aot.validate(row, 'x'), row)
        with self.assertRaises(ValueError): pso_aot.validate(row, 'old')
        row['vertex'] = ['/private/library', 'main0']
        with self.assertRaises(ValueError): pso_aot.validate(row, 'x')

    def test_preflight_never_claims_completeness(self):
        spec = importlib.util.spec_from_file_location('aot_preflight', ROOT / 'scripts/aot_preflight.py')
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(mod.report(td)['complete'])

    @unittest.skipUnless(os.getenv('DM_TEST_AOT'), 'set DM_TEST_AOT to the Metal fixture probe')
    def test_real_archive_and_learning(self):
        chain = (ROOT / 'dm/gfx/nvn/dmsh_chain.h').read_text().split('"')[1]
        with tempfile.TemporaryDirectory(prefix='aot-fixture-') as td:
            root = Path(td); lib = root / ('b-' + chain); lib.mkdir()
            shaders = {
                'v': 'struct V {float4 p [[position]];}; vertex V main0(uint i [[vertex_id]]) { return {float4(float(i),0,0,1)}; }',
                'f': 'fragment float4 main0() {return float4(1);}',
                'q': 'constant int v [[function_constant(0)]]; constant bool enabled [[function_constant(32)]]; fragment float4 main0() {return float4(enabled ? float(v)/16.0 : 0.0);}',
                'l': 'struct V {float4 p [[position]]; uint layer [[render_target_array_index]];}; vertex V main0(uint i [[vertex_id]]) {return {float4(float(i),0,0,1),0};}',
                'c': 'kernel void main0(device uint *p [[buffer(0)]], uint i [[thread_position_in_grid]]) {p[i]=i;}',
                'm': 'struct V {float4 p [[position]];}; [[mesh]] void main0(metal::mesh<V,void,3,1,metal::topology::triangle> o) {o.set_vertex(0,{float4(0,0,0,1)}); o.set_vertex(1,{float4(1,0,0,1)}); o.set_vertex(2,{float4(0,1,0,1)}); o.set_index(0,0); o.set_index(1,1); o.set_index(2,2); o.set_primitive_count(1);}',
                't': '[[object]] void main0(metal::mesh_grid_properties g) {g.set_threadgroups_per_grid(uint3(1));}',
            }
            for key, src in shaders.items():
                metal = lib / (key + '_b.metal'); metal.write_text('#include <metal_stdlib>\nusing namespace metal;\n' + src)
                subprocess.run(['xcrun', 'metal', '-std=metal3.0', str(metal), '-o', str(lib / (key + '_b.metallib'))], check=True, capture_output=True)
                (lib / (key + '_b.json')).write_text(json.dumps(dict(chain=chain, stage={'c': 'cs', 'm': 'ms', 't': 'ts'}.get(key, key), entry='main0', **({'mesh_stage': {'threads': 1, 'payload': 16, 'task': True}} if key in ('m', 't') else {}))))
            constant = render(chain); constant['fragment'] = ['q_b', 'main0', [[0, 'int', 7], [32, 'bool', True]]]
            seen = root / 'seen.jsonl'; seen.write_text('\n'.join(json.dumps(r) for r in [render(chain), render(chain, 'mesh'), constant]) + '\n')
            pairs = root / 'pairs.tsv'; pairs.write_text('v\tf\nl\tf\n')
            shader_map = root / 'shader_map.tsv'; shader_map.write_text('pkg\t0\tmesh\tm\tprogram#var0\npkg\t0\ttask\tt\tprogram#var0\npkg\t0\tpixel\tf\tprogram#var0\npkg\t0\tvertex\tv\tother\npkg\t0\tcompute\tc\tcompute\n')
            # Probe device architecture without launching the host or a game.
            arch_src = root / 'arch.m'; arch_src.write_text('#import <Metal/Metal.h>\nint main(){@autoreleasepool{puts(MTLCreateSystemDefaultDevice().architecture.name.UTF8String);}}')
            subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-framework', 'Metal', '-framework', 'Foundation', str(arch_src), '-o', str(root / 'arch')], check=True, capture_output=True)
            arch = subprocess.check_output([str(root / 'arch')], text=True).strip()
            args = ['--platform', 'macos', '--gpu', arch, '--msl', str(lib), '--pairs', str(pairs), '--out', str(root / 'out'), '--work', str(root / 'work'), '--aot', '--shader-map', str(shader_map), '--seen', str(seen), '--batch-size', '8', '--host', os.environ['DM_TEST_AOT']]
            self.assertEqual(po.main(args), 0)
            preflight = json.loads((root / 'out/aot-preflight.json').read_text())
            self.assertEqual(preflight['layer_bases'], 1)
            self.assertEqual(preflight['classes']['mesh'], 2)
            learned = root / 'learned.jsonl'
            run = subprocess.run([os.environ['DM_TEST_AOT'], str(lib), str(root / 'out'), str(learned)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('[RED] AOT phase=gameplay class=render', run.stderr)
            self.assertIn('strict miss counted', run.stderr)
            self.assertGreater(len(learned.read_text().splitlines()), 2)
            first = learned.read_bytes()
            again = subprocess.run([os.environ['DM_TEST_AOT'], str(lib), str(root / 'out'), str(learned)], capture_output=True, text=True)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(learned.read_bytes(), first, 'repeat launches must not append duplicate descriptors')
            # The live failure used a packed image. Replay exactly that library
            # path, including host library identities and descriptor recording.
            shader_lib.pack(lib)
            packed = root / 'packed-seen.jsonl'
            packed_run = subprocess.run([os.environ['DM_TEST_AOT'], str(lib), str(root / 'out'), str(packed)], capture_output=True, text=True)
            self.assertEqual(packed_run.returncode, 0, packed_run.stderr)
            packed_rows = [json.loads(line) for line in packed.read_text().splitlines()]
            self.assertTrue(any(r.get('vertex', [''])[0] == 'v_b' for r in packed_rows))
            self.assertTrue(any(r.get('mesh', [''])[0] == 'm_b' for r in packed_rows))
            # Feed real producer output back to the planner. Dedup and new state survive.
            rows, _ = pso_aot.plan(shader_lib.view(lib), chain, [learned], po.functions, pso_aot.HOST_DIR)
            self.assertTrue(any(r.get('colors', [[0]])[0][0] == 115 for r in rows))
            self.assertEqual(po.main(args + ['--seen', str(learned), '--user', str(learned) + '.tsv']), 0)
            imported = [json.loads(line) for line in (root / 'work/pso-import-0.jsonl').read_text().splitlines()]
            self.assertEqual({row['class'] for row in imported}, {'render', 'mesh', 'compute'})
            self.assertIn('R\t', (root / 'out/pso_manifest.tsv').read_text())
            # One old key and one unsupported row must not destroy accepted
            # states or leak refused rows into the startup manifest.
            mixed = root / 'mixed.tsv'
            mixed.write_text(Path(str(learned) + '.tsv').read_text() + 'C\tstale_b\nR\tnot-a-native-key\n')
            accepted = pso_aot.import_user(os.environ['DM_TEST_AOT'], shader_lib.view(lib), shader_map, [mixed], root / 'work', False)[0]
            audit = json.loads(Path(str(accepted) + '.refused.json').read_text())
            self.assertEqual([row['stale'] for row in audit], [True, False])
            self.assertEqual({json.loads(line)['class'] for line in accepted.read_text().splitlines()}, {'render', 'mesh', 'compute'})
            manifest = Path(str(accepted) + '.manifest.tsv').read_text()
            self.assertNotIn('stale_b', manifest); self.assertNotIn('not-a-native-key', manifest)
            bad = render(chain); bad['fragment'] = ['q_b', 'main0', [[99, 'int', 7], [32, 'bool', True]]]
            refused = root / 'refused.jsonl'; refused.write_text(json.dumps(bad) + '\n')
            self.assertEqual(po.main(args + ['--seen', str(refused)]), 0)
            denied = json.loads((root / 'out' / f'aot-refused.{arch}.json').read_text())
            self.assertEqual(len(denied), 1); self.assertEqual(denied[0]['descriptor'], bad)
            self.assertTrue((root / 'out' / f'{arch}.mtl4a').is_file(), 'valid archive pieces must survive a rejected constant')


if __name__ == '__main__': unittest.main()

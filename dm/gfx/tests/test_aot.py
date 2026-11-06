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


def render(chain, kind='render'):
    row = dict(version=1, chain=chain, **{'class': kind}, samples=1, a2c=False, raster=True, depth=0, stencil=0,
               colors=[[70, 15, False, 1, 0, 0, 1, 0, 0]] + [[0, 15, False, 1, 0, 0, 1, 0, 0]] * 7,
               fragment=['f_b', 'main0'])
    if kind == 'render': row.update(vertex=['v_b', 'main0'], topology=0, amp=1, attrs=[[0, 0, 0]] * 31, layouts=[[0, 1, 1]] * 31)
    else: row.update(mesh=['m_b', 'main0'], object=['t_b', 'main0'], mesh_threads=1, object_threads=1, payload=16, mesh_grid=0, mesh_multiple=False, object_multiple=False)
    return row


class Planning(unittest.TestCase):
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
                'l': 'struct V {float4 p [[position]]; uint layer [[render_target_array_index]];}; vertex V main0(uint i [[vertex_id]]) {return {float4(float(i),0,0,1),0};}',
                'c': 'kernel void main0(device uint *p [[buffer(0)]], uint i [[thread_position_in_grid]]) {p[i]=i;}',
                'm': 'struct V {float4 p [[position]];}; [[mesh]] void main0(metal::mesh<V,void,3,1,metal::topology::triangle> o) {o.set_vertex(0,{float4(0,0,0,1)}); o.set_vertex(1,{float4(1,0,0,1)}); o.set_vertex(2,{float4(0,1,0,1)}); o.set_index(0,0); o.set_index(1,1); o.set_index(2,2); o.set_primitive_count(1);}',
                't': '[[object]] void main0(metal::mesh_grid_properties g) {g.set_threadgroups_per_grid(uint3(1));}',
            }
            for key, src in shaders.items():
                metal = lib / (key + '.metal'); metal.write_text('#include <metal_stdlib>\nusing namespace metal;\n' + src)
                subprocess.run(['xcrun', 'metal', '-std=metal3.0', str(metal), '-o', str(lib / (key + '_b.metallib'))], check=True, capture_output=True)
                (lib / (key + '_b.json')).write_text(json.dumps(dict(chain=chain, stage={'c': 'cs', 'm': 'ms', 't': 'ts'}.get(key, key), entry='main0', **({'mesh_stage': {'threads': 1, 'payload': 16, 'task': True}} if key in ('m', 't') else {}))))
            seen = root / 'seen.jsonl'; seen.write_text('\n'.join(json.dumps(render(chain, k)) for k in ('render', 'mesh')) + '\n')
            pairs = root / 'pairs.tsv'; pairs.write_text('v\tf\nl\tf\n')
            shader_map = root / 'shader_map.tsv'; shader_map.write_text('pkg\t0\tmesh\tm\tprogram#var0\npkg\t0\ttask\tt\tprogram#var0\npkg\t0\tpixel\tf\tprogram#var0\n')
            # Probe device architecture without launching the host or a game.
            arch_src = root / 'arch.m'; arch_src.write_text('#import <Metal/Metal.h>\nint main(){@autoreleasepool{puts(MTLCreateSystemDefaultDevice().architecture.name.UTF8String);}}')
            subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-framework', 'Metal', '-framework', 'Foundation', str(arch_src), '-o', str(root / 'arch')], check=True, capture_output=True)
            arch = subprocess.check_output([str(root / 'arch')], text=True).strip()
            args = ['--platform', 'macos', '--gpu', arch, '--msl', str(lib), '--pairs', str(pairs), '--out', str(root / 'out'), '--work', str(root / 'work'), '--aot', '--shader-map', str(shader_map), '--seen', str(seen), '--batch-size', '8']
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
            # Feed real producer output back to the planner. Dedup and new state survive.
            rows, _ = pso_aot.plan(lib, chain, [learned], po.functions, pso_aot.HOST_DIR)
            self.assertTrue(any(r.get('colors', [[0]])[0][0] == 115 for r in rows))
            self.assertEqual(po.main(args + ['--seen', str(learned)]), 0)


if __name__ == '__main__': unittest.main()

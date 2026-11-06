"""Unwritten mesh varyings use the same defaults as the vertex path."""
import ast
import collections
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2] / 'gfx/tools'
sys.path.insert(0, str(TOOLS))
import dmsh_meshstage


class MeshPadding(unittest.TestCase):
    def test_missing_outputs_are_initialized_in_both_depth_entries(self):
        src = 'struct dm_vertex_t {\n float4 position [[position]];\n float4 a0 [[user(locn0)]];\n};\nstruct dm_prim_t { float4 p2 [[user(locn2)]]; };\n'
        src += 'void main0() { dm_vertex_t v; v.a0 = original; }\nvoid main0_z() { dm_vertex_t v; v.a0 = original; }'
        out, added = dmsh_meshstage.pad_locations(src, [0, 2, 4, 10, 11])
        self.assertEqual(added, [4, 10, 11])
        for n in added:
            self.assertEqual(out.count(f'v.dm_pad{n} = float4(0.0, 0.0, 0.0, 1.0);'), 2)
        self.assertEqual(out.count('v.a0 = original'), 2)
        self.assertNotIn('dm_pad2', out)
        self.assertEqual(dmsh_meshstage.pad_locations(out, [4, 10, 11]), (out, []))

    def test_source_pairs_are_gated_and_ambiguous_sources_are_not_guessed(self):
        tree = ast.parse((TOOLS / 'dmsh_build.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'load_pairs')
        ns = dict(os=os, collections=collections)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<load_pairs>', 'exec'), ns)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('shader_pairs.tsv', 'pso_pairs.tsv'): (root / name).write_text('')
            (root / 'shader_map.tsv').write_text('m.bin\t0\tmesh\tm\tsource\np.bin\t0\tpixel\tp\tsource\nm.bin\t1\tmesh\tx\tambiguous\np.bin\t1\tpixel\ty\tambiguous\np.bin\t2\tpixel\tz\tambiguous\n')
            class Game:
                def table(self, name): return root / name
            with mock.patch.dict(os.environ, DMSH_OOT_VISUAL='0'):
                self.assertEqual(dict(ns['load_pairs'](Game(), str(root / 'pkg'))), {})
            with mock.patch.dict(os.environ, DMSH_OOT_VISUAL='1'):
                self.assertEqual(dict(ns['load_pairs'](Game(), str(root / 'pkg'))), {'m': {'p'}})


if __name__ == '__main__': unittest.main()

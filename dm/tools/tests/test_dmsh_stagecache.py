"""Synthetic shader pipeline tests. No game files, translator binaries or Metal SDK."""
import ast
import collections
import concurrent.futures as cf
import copy
import json
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
from typing import Any

TOOLS = Path(__file__).resolve().parents[2] / 'gfx/tools'
sys.path.insert(0, str(TOOLS))
import dmsh_abi as abi  # noqa: E402
import dmsh_atomic  # noqa: E402
import dmsh_geometry  # noqa: E402
import dmsh_mtlcache  # noqa: E402
import dmsh_stagecache as cache  # noqa: E402
import dmsh_wide  # noqa: E402

BUILD = TOOLS / 'dmsh_build.py'


def build_functions():
    ns: dict[str, Any] = dict(__name__='dmsh_build', os=os, json=json, re=re, struct=struct,
              subprocess=subprocess, threading=threading, abi=abi, dmsh_atomic=dmsh_atomic, dmsh_geometry=dmsh_geometry,
              dmsh_wide=dmsh_wide, dmsh_mtlcache=dmsh_mtlcache, shutil=shutil)
    tree = ast.parse(BUILD.read_text())
    constants = {'HMMA_BODY', 'FIRST_STORE', 'FIRST_STORE_2D', 'TG_DECL', 'TG_BYTES',
                 'BORDER_HELPERS', 'TEX_BASE', 'SSBO', 'POOL_MIN', '_CAST', 'VP_BASE_INSTANCE', 'TF_SLOT'}
    nodes: list[ast.stmt] = [n for n in tree.body if isinstance(n, ast.FunctionDef) or
             (isinstance(n, ast.Assign) and any(getattr(x, 'id', '') in constants for t in n.targets for x in ast.walk(t)))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(BUILD), 'exec'), ns)
    return ns


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / 'work'; self.work.mkdir()
        self.out = self.root / 'out'; self.out.mkdir()
        self.cache = cache.Cache(self.root / 'stages', b'ABI 1')
        self.ns = build_functions()
        self.ns.update(STAGES=self.cache, XLATE_FP='translator 1', CROSS_FP='cross 1', XLATE='fake-xlate', SPIRV_CROSS='fake-cross',
                       XC=['--msl'], CHAIN='chain 1', out=str(self.out), w=str(self.work), TARGETS={'mac'}, IOSOUT=None,
                       loc={'shader': ('cs-synthetic', 0)}, pc_of={'shader': ''}, PAIRS={}, DUAL_WANT=set())
        self.code = self.work / 'shader.bin'; self.code.write_bytes(b'synthetic SASS')
        self.job: dict[str, Any] = dict(key='shader', stage='cs', code=str(self.code), attr={}, local=[1, 1, 1], c1='')
        self.calls = collections.Counter()
        self.spv = struct.pack('<5I', 0x07230203, 0x10000, 0, 1, 0)
        self.msl = '#include <metal_stdlib>\nusing namespace metal;\nkernel void main0() {}\n'
        self.tool_fails = False
        def run(argv, **kw):
            if argv[0] == 'fake-xlate':
                self.calls['translate'] += 1
                for j in json.loads(Path(argv[1]).read_text()):
                    if self.tool_fails: continue
                    (self.work / (j['key'] + '.spv')).write_bytes(self.spv)
                    (self.work / (j['key'] + '.res.json')).write_text(json.dumps(dict(key=j['key'], notes=[], sbufs=[])))
                    if 'geometry_topology' in j: (self.work / (j['key'] + '.reader.spv')).write_bytes(self.spv)
                return subprocess.CompletedProcess(argv, 1 if self.tool_fails else 0, '', '[RED] shader: failed' if self.tool_fails else '')
            self.assertEqual(argv[0], 'fake-cross')
            self.calls['cross'] += 1
            if '--output' in argv: Path(argv[argv.index('--output') + 1]).write_text(self.msl)
            return subprocess.CompletedProcess(argv, 1 if self.tool_fails else 0, self.msl, 'cross failed' if self.tool_fails else '')
        self.patch = mock.patch.object(subprocess, 'run', side_effect=run); self.patch.start(); self.addCleanup(self.patch.stop)
        def compile_metal(msl, air, lib):
            self.calls['metal'] += 1
            Path(lib).write_bytes(b'LIB:' + Path(msl).read_bytes())
        with mock.patch.object(dmsh_mtlcache, 'compiler_id', return_value='compiler 1'):
            self.ns['MTL'] = dmsh_mtlcache.Cache(str(self.root / 'metal'), {'mac': ('macosx', 'flags', compile_metal)}, str(self.work))

    def build(self):
        job = copy.deepcopy(self.job)
        r = self.ns['translate_jobs']([job], str(self.work / 'jobs.json'), str(self.work))
        if r.returncode: return r
        result = self.ns['finish']('shader', str(self.work), job, b'')
        self.assertEqual(result[0], 'ok', result)
        self.assertEqual((self.out / 'shader_b.metallib').read_bytes(), b'LIB:' + self.msl.encode())
        self.assertEqual(result[2]['chain'], self.ns['CHAIN'])
        return result

    def test_warm_hits_and_translator_edit_with_identical_spirv(self):
        self.build(); self.build()
        self.assertEqual(self.calls, dict(translate=1, cross=1, metal=1))
        self.ns.update(XLATE_FP='translator 2', CHAIN='chain 2')
        self.build()
        self.assertEqual(self.calls, dict(translate=2, cross=1, metal=1))
        self.assertEqual(json.loads((self.out / 'shader_b.json').read_text())['chain'], 'chain 2')

    def test_postpass_edit_that_changes_nothing_stops_at_output_content(self):
        self.build()
        before = self.cache.stats.copy()
        original = cache.function_code
        def edited(fn):
            return 'edited wide' if fn is dmsh_wide.wide_loads else original(fn)
        with mock.patch.object(cache, 'function_code', side_effect=edited): self.build()
        self.assertEqual(self.calls, dict(translate=1, cross=1, metal=1))
        self.assertEqual(self.cache.stats['dmsh_wide.wide_loads', 'miss'], 2)
        self.assertEqual(self.cache.stats['dmsh_build.border_emu', 'miss'], before['dmsh_build.border_emu', 'miss'])

    def test_cross_edit_and_changed_spirv_preserve_metal_if_msl_identical(self):
        self.build()
        self.ns['CROSS_FP'] = 'cross 2'; self.build()
        self.assertEqual(self.calls, dict(translate=1, cross=2, metal=1))
        self.code.write_bytes(b'new shader'); self.spv += struct.pack('<I', 1 << 16)
        self.build()
        self.assertEqual(self.calls, dict(translate=2, cross=3, metal=1))

    def test_changed_postpass_output_reruns_downstream(self):
        self.build()
        path = self.root / 'edited_border.py'
        path.write_text('def border(src): return src + "// changed\\n"\n')
        spec = importlib.util.spec_from_file_location('edited_border', path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.ns['border_emu'] = module.border
        self.msl += '// changed\n'
        self.build()
        self.assertEqual(self.cache.stats['dmsh_atomic.check_msl', 'miss'], 1)
        self.assertEqual(self.cache.stats['dmsh_build.first_store', 'miss'], 2)
        self.assertEqual(self.calls, dict(translate=1, cross=1, metal=2))

    def test_abi_edit_invalidates_all_intermediate_stages(self):
        self.build()
        self.ns['STAGES'] = cache.Cache(self.root / 'stages', b'ABI 2')
        self.build()
        self.assertEqual(self.calls, dict(translate=2, cross=2, metal=1))
        self.assertEqual(self.ns['STAGES'].stats['dmsh_wide.wide_loads', 'miss'], 1)

    def test_translation_flags_profile_answers_and_paths(self):
        self.build()
        other = self.work / 'other.bin'; other.write_bytes(self.code.read_bytes())
        self.job['code'] = str(other); self.build()
        self.assertEqual(self.calls['translate'], 1)
        self.job['attr'] = {'0': 'uint'}; self.build()
        self.job['debug'] = False; self.build()
        self.job['c1'] = '0001'; self.build()
        self.assertEqual(self.calls['translate'], 4)

    def test_failed_retranslation_does_not_publish_old_spirv(self):
        self.build(); self.job['attr'] = {'0': 'uint'}; self.tool_fails = True
        self.assertEqual(self.build().returncode, 1)
        self.assertFalse((self.work / 'shader.spv').exists())
        self.tool_fails = False; self.build()
        self.assertEqual(self.calls['translate'], 3)

    def test_geometry_translation_restores_reader_too(self):
        j = {**self.job, 'geometry_topology': 3}
        self.ns['translate_jobs']([j], str(self.work / 'jobs.json'), str(self.work))
        for suffix in ('.spv', '.reader.spv', '.res.json'): (self.work / ('shader' + suffix)).unlink()
        self.ns['translate_jobs']([j], str(self.work / 'jobs.json'), str(self.work))
        self.assertEqual((self.work / 'shader.reader.spv').read_bytes(), self.spv)
        self.assertEqual(self.calls['translate'], 1)

    def test_cross_failure_is_not_cached(self):
        spv = self.work / 'shader.spv'; spv.write_bytes(self.spv)
        self.tool_fails = True
        self.assertEqual(self.ns['cross_run'](str(spv), ['--msl']).returncode, 1)
        self.tool_fails = False
        self.assertEqual(self.ns['cross_run'](str(spv), ['--msl']).stdout, self.msl)
        self.assertEqual(self.calls['cross'], 2)

    def test_vertex_integer_retry_has_two_reusable_translation_entries(self):
        import dmsh_fetch
        self.ns.update(dmsh_fetch=dmsh_fetch, vin_finish=lambda k, s, r: r, pull_finish=lambda k, s, r: r)
        self.msl = """#include <metal_stdlib>
using namespace metal;
struct main0_in
{
    float4 m_0 [[attribute(0)]];
};
struct main0_out
{
    float4 gl_Position [[position]];
};
vertex main0_out main0(main0_in in [[stage_in]])
{
    main0_out out = {};
    int x = as_type<int>(in.m_0.x);
    out.gl_Position = float4(float(x));
    return out;
}
"""
        self.job['stage'] = 'vs'
        for _ in range(2):
            job = copy.deepcopy(self.job)
            self.ns['translate_jobs']([job], str(self.work / 'jobs.json'), str(self.work))
            result = self.ns['finish']('shader', str(self.work), job, b'')
            self.assertEqual(result[0], 'ok', result)
            self.assertEqual(job['attr'], {'0': 'uint'})
            self.assertIn(b'main0_z', (self.out / 'shader_b.metallib').read_bytes())
        self.assertEqual(self.calls, dict(translate=2, cross=1, metal=1))

    def test_pair_padding_keys_current_pixel_locations(self):
        self.ns['PAIRS'] = {'vertex': {'pixel'}}
        source = 'struct main0_out\n{\n};\nvertex main0_out main0() {main0_out out = {}; return out;}'
        pixel = self.out / 'pixel_b.metal'
        pixel.write_text('float4 x [[user(locn1)]];')
        first, pads = self.ns['vs_pad']('vertex', source)
        self.assertEqual(pads, [1]); self.assertIn('dm_pad1', first)
        pixel.write_text('float4 y [[user(locn2)]];')
        second, pads = self.ns['vs_pad']('vertex', source)
        self.assertEqual(pads, [2]); self.assertIn('dm_pad2', second)
        self.assertNotIn('dm_pad1', second)

    def test_disabled_cache_runs_original_pipeline(self):
        self.ns['STAGES'] = None
        self.build(); self.build()
        self.assertEqual(self.calls, dict(translate=2, cross=2, metal=1))


class Dependencies(unittest.TestCase):
    def setUp(self):
        cache.function_code.cache_clear(); cache.module_code.cache_clear()
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_local_import_added_or_changed_invalidates_parent_module(self):
        a, b = self.root / 'pass_a.py', self.root / 'helper.py'
        a.write_text('def transform(x): return x\n')
        initial = cache.module_code(str(a))
        b.write_text('VALUE = 1\n'); a.write_text('import helper\ndef transform(x): return x + helper.VALUE\n')
        cache.module_code.cache_clear(); imported = cache.module_code(str(a))
        self.assertNotEqual(initial, imported)
        b.write_text('VALUE = 2\n'); cache.module_code.cache_clear()
        self.assertNotEqual(imported, cache.module_code(str(a)))

    def test_wide_mesh_ampere_and_screen_helpers_are_covered(self):
        ns = build_functions()
        # Every actual cached pass must have a complete, computable fingerprint.
        tree = ast.parse(BUILD.read_text())
        import dmsh_fetch, dmsh_mesh, dmsh_meshstage, dmsh_pull, dmsh_side, dmsh_vin
        ns.update(dmsh_fetch=dmsh_fetch, dmsh_mesh=dmsh_mesh, dmsh_meshstage=dmsh_meshstage,
                  dmsh_pull=dmsh_pull, dmsh_side=dmsh_side, dmsh_vin=dmsh_vin)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'stage_pass':
                fn = eval(compile(ast.Expression(n.args[0]), str(BUILD), 'eval'), ns)
                self.assertEqual(len(cache.function_code(fn)), 64, fn.__name__)
        # No handwritten module allowlist can omit a new dmsh_wide dependency.
        self.assertNotEqual(cache.function_code(dmsh_wide.wide_loads), cache.function_code(dmsh_atomic.check_msl))

    def test_inline_helper_and_constant_changes_invalidate_only_dependents(self):
        ns = build_functions()
        original = cache.function_code(ns['pool_arrays'])
        precise = cache.function_code(ns['precise'])
        ns['POOL_MIN'] += 1; cache.function_code.cache_clear()
        self.assertNotEqual(original, cache.function_code(ns['pool_arrays']))
        self.assertEqual(precise, cache.function_code(ns['precise']))
        before = cache.function_code(ns['vs_layer'])
        ns['drop_point_size'] = ns['precise']; cache.function_code.cache_clear()
        self.assertNotEqual(before, cache.function_code(ns['vs_layer']))

    def test_unknown_import_fails_closed(self):
        p = self.root / 'pass_a.py'
        p.write_text('import untracked_shader_helper\ndef transform(x): return x\n')
        with self.assertRaisesRegex(ValueError, 'undeclared Python dependency'):
            cache.module_code(str(p))

    def test_dynamic_import_fails_closed(self):
        p = self.root / 'pass_a.py'
        p.write_text('import importlib\nhelper = importlib.import_module("helper")\n')
        with self.assertRaisesRegex(ValueError, 'dynamic Python dependency'):
            cache.module_code(str(p))

    def test_pass_flags_and_none_outputs_are_cached(self):
        c = cache.Cache(self.root, b'abi')
        ns = build_functions()
        self.assertEqual(c.call(ns['first_store'], 'kernel void main0() {}', None), ('kernel void main0() {}', []))
        self.assertEqual(c.call(ns['first_store'], 'kernel void main0() {}', [1, 1, 1]), ('kernel void main0() {}', []))
        self.assertEqual(c.stats['dmsh_build.first_store', 'miss'], 2)
        self.assertEqual(c.call(ns['first_store'], 'kernel void main0() {}', None), ('kernel void main0() {}', []))
        self.assertEqual(c.stats['dmsh_build.first_store', 'hit'], 1)
        self.assertIsNone(c.call(ns['fs_dual'], 'fragment void main0() {}'))
        self.assertIsNone(c.call(ns['fs_dual'], 'fragment void main0() {}'))
        self.assertEqual(c.stats['dmsh_build.fs_dual', 'hit'], 1)

    def test_corruption_and_uncommitted_entries_are_misses(self):
        c = cache.Cache(self.root, b'abi')
        c.put('key', (b'spirv', {'reflection': 1}))
        self.assertEqual(c.get('test', 'key'), (b'spirv', {'reflection': 1}))
        with c.db(): c.db().execute('UPDATE objects SET data=?', (b'corrupt',))
        c.local.objects.clear()
        self.assertIsNone(c.get('test', 'key'))
        c.put('key', ('repaired',)); self.assertEqual(c.get('test', 'key'), ('repaired',))
        c.db().execute("INSERT INTO entries VALUES ('uncommitted', 'missing')"); c.db().rollback()
        self.assertIsNone(c.get('test', 'uncommitted'))

    def test_concurrent_writers_and_noop_object_deduplication(self):
        c = cache.Cache(self.root, b'abi')
        def write(i):
            c.put(str(i), ('same MSL',)); return c.get('test', str(i))
        with cf.ThreadPoolExecutor(4) as ex: results = list(ex.map(write, range(40)))
        self.assertEqual(results, [('same MSL',)] * 40)
        self.assertEqual(c.db().execute('SELECT count(*) FROM objects').fetchone()[0], 1)


if __name__ == '__main__': unittest.main()

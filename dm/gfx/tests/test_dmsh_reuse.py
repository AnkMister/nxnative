"""Default-off constant word reuse and storage runs outside the old 16-byte grid."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import dmsh_cbuf  # noqa: E402
import dmsh_chain  # noqa: E402
import dmsh_wide  # noqa: E402


CBUF = '''#include <metal_stdlib>
using namespace metal;
struct _1 { float4 _m0[4096]; };
struct spvDescriptorSetBuffer0 {
    constant _1* fp_c1 [[id(0)]];
};
fragment float4 main0(constant spvDescriptorSetBuffer0& spvDescriptorSet0 [[buffer(0)]])
{
    float _1 = (*spvDescriptorSet0.fp_c1)._m0[3].x;
    float _2 = (*spvDescriptorSet0.fp_c1)._m0[3].x + (*spvDescriptorSet0.fp_c1)._m0[3].y;
    return float4(_1, _2, 0.0, 1.0);
}
'''
STORAGE = '''#include <metal_stdlib>
using namespace metal;
struct _1 { uint _m0[1]; };
struct spvDescriptorSetBuffer0 {
    const device _1* fp_s0 [[id(0)]];
};
fragment float4 main0(constant spvDescriptorSetBuffer0& spvDescriptorSet0 [[buffer(0)]], float4 pos [[position]])
{
    int _100 = int(pos.x) * 16;
    int _1 = _100 + 4;
    uint _2 = uint(int(uint(_1) >> uint(2)));
    uint _3 = (*spvDescriptorSet0.fp_s0)._m0[int(_2)];
    int _4 = _100 + 8;
    uint _5 = uint(int(uint(_4) >> uint(2)));
    uint _6 = (*spvDescriptorSet0.fp_s0)._m0[int(_5)];
    return float4(float(_3), float(_6), 0.0, 1.0);
}
'''


class Reuse(unittest.TestCase):
    def test_literal_constant_word(self):
        result = dmsh_cbuf.reuse_words(CBUF)
        self.assertIn('const float _dmcb0 = (*spvDescriptorSet0.fp_c1)._m0[3].x;', result)
        self.assertIn('float _1 = _dmcb0;', result)
        self.assertIn('float _2 = _dmcb0 + (*spvDescriptorSet0.fp_c1)._m0[3].y;', result)
        self.assertEqual(result.count('._m0[3].x'), 1)
        self.assertEqual(dmsh_cbuf.reuse_words(result), result)

    def test_cbuf_fallback(self):
        for source in (CBUF.replace('constant _1*', 'device _1*'), CBUF.replace('[3]', '[int(3)]'),
                       CBUF.replace('float4 _m0', 'uint4 _m0'), CBUF.replace('[3]', '[4096]')):
            with self.subTest(source=source): self.assertEqual(dmsh_cbuf.reuse_words(source), source)

    def test_cbuf_regions(self):
        for barrier in ('    if (_1 > 0.0) { }', '    threadgroup_barrier(mem_flags::mem_device);'):
            source = CBUF.replace('    float _2', barrier + '\n    float _2')
            self.assertEqual(dmsh_cbuf.reuse_words(source), source)

    def test_storage_between_grid_points(self):
        self.assertEqual(dmsh_wide.wide_loads(STORAGE), STORAGE)
        result = dmsh_wide.wide_loads(STORAGE, offset_runs=True)
        self.assertIn('packed_uint2 _dmr0 = uint(_2) <= 1073741822u ?', result)
        self.assertIn('*(const device packed_uint2*)&(*spvDescriptorSet0.fp_s0)._m0[int(_2)]', result)
        self.assertIn('packed_uint2((*spvDescriptorSet0.fp_s0)._m0[int((uint(_2) + 0u) & 0x3fffffffu)], (*spvDescriptorSet0.fp_s0)._m0[int((uint(_2) + 1u) & 0x3fffffffu)])', result)
        self.assertIn('uint _3 = _dmr0.x;', result)
        self.assertIn('uint _6 = _dmr0.y;', result)
        self.assertEqual(dmsh_wide.wide_loads(result, offset_runs=True), result)

    def test_storage_wrap_indices(self):
        # A scalar's uint byte address wraps before its word shift. The slow path
        # must select word zero after the last word, rather than reading past 4 GiB.
        for root in (0, 1, 0xfffffff4, 0xfffffff8, 0xfffffffc):
            for start in (0, 4, 8, 12):
                first = ((root + start) & 0xffffffff) >> 2
                for lane in range(4):
                    expected = ((root + start + lane * 4) & 0xffffffff) >> 2
                    self.assertEqual((first + lane) & 0x3fffffff, expected)

    def test_storage_barriers(self):
        for barrier in ('    _100 = 32;', '    _100++;', '    (*pointer) = 1u;', '    unknown(_100);', '    threadgroup_barrier(mem_flags::mem_device);',
                        '    (*spvDescriptorSet0.fp_s0)._m0[0] = 0;', '    if (_3 > 0u) { }'):
            source = STORAGE.replace('    int _4', barrier + '\n    int _4')
            self.assertEqual(dmsh_wide.wide_loads(source, offset_runs=True), source)
        self.assertEqual(dmsh_wide.wide_loads(STORAGE.replace('const device', 'device'), offset_runs=True), STORAGE.replace('const device', 'device'))
        commented = STORAGE.replace('    int _4', '    /* multiline\n    int _4')
        self.assertEqual(dmsh_wide.wide_loads(commented, offset_runs=True), commented)

    def test_default_off_and_version(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(dmsh_chain.storage_runs()); self.assertFalse(dmsh_chain.cbuf_reuse())
            baseline = dmsh_chain.version()
            for flag in ('DMSH_STORAGE_RUNS', 'DMSH_CBUF_REUSE'):
                with mock.patch.dict(os.environ, {flag: '1'}): self.assertNotEqual(dmsh_chain.version(), baseline)
                with mock.patch.dict(os.environ, {flag: '0'}): self.assertEqual(dmsh_chain.version(), baseline)
            with mock.patch.dict(os.environ, {'DMSH_RAW_LOAD_QUADS': '1', 'DMSH_CBUF_REUSE': '1', 'DMSH_STORAGE_RUNS': '1'}):
                self.assertTrue(dmsh_chain.raw_load_quads())
                self.assertTrue(dmsh_chain.cbuf_reuse())
                self.assertTrue(dmsh_chain.storage_runs())
                self.assertNotEqual(dmsh_chain.version(), baseline)

    @unittest.skipUnless(shutil.which('xcrun') and sys.platform == 'darwin', 'Metal compiler')
    def test_compiles(self):
        with tempfile.TemporaryDirectory() as d:
            for name, src in (('cb-before', CBUF), ('cb-after', dmsh_cbuf.reuse_words(CBUF)),
                              ('storage-before', STORAGE), ('storage-after', dmsh_wide.wide_loads(STORAGE, offset_runs=True))):
                path = Path(d) / (name + '.metal'); path.write_text(src)
                result = subprocess.run(['xcrun', '-sdk', 'macosx', 'metal', '-c', '-O1', '-fpreserve-invariance', str(path), '-o', str(path.with_suffix('.air'))], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__': unittest.main()

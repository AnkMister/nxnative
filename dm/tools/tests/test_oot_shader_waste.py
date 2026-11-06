"""Static census behavior. No game, compilers or source game files needed."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import oot_shader_waste as w

META = {'bindings': [{'kind':'gmem_map','msl_name':'cp_s0'},
                     {'kind':'sbuf','msl_name':'cp_s1'}]}
RAW = '''int _1(device T& cp_s0) {
 uint a = cp_s0._m0[0];
 return *(reinterpret_cast<device uint*>(ulong(a)));
}
'''


class Waste(unittest.TestCase):
    def test_calls_are_counted_per_access_and_per_loop(self):
        a = w.analyze(RAW + '''kernel void main0() {
 for (int i = 0; i < 8; i++) {
  int a = _1(cp_s0); int b = _1(cp_s0);
 }
}''', META)
        self.assertEqual(a['sites']['raw_loads'], 2)
        self.assertEqual(a['estimated']['raw_loads'], 16)
        self.assertEqual(a['estimated']['pool_table_loads'], 16)
        self.assertEqual(a['loops'][0]['trips'], 8)

    def test_unknown_trip_is_reported_and_has_sensitivity_score(self):
        a = w.analyze(RAW + '''kernel void main0() {
 while (n > 0) { int a = _1(cp_s0); }
}''', META)
        self.assertIsNone(a['loops'][0]['trips'])
        self.assertEqual(a['estimated']['raw_loads'], 4)
        self.assertEqual(a['unknown_once']['raw_loads'], 1)

    def test_nested_loops_and_zero_trip(self):
        a = w.analyze('''kernel void main0() {
 for (int i=0; i<2; i++) {
  for (int j=1; j<=3; j++) { float a = t.sample(s, uv); }
 }
 for (int k=0; k<0; k++) { float a = t.sample(s, uv); }
}''', META)
        self.assertEqual(a['max_loop_depth'], 2)
        self.assertEqual(a['sites']['texture_samples'], 2)
        self.assertEqual(a['estimated']['texture_samples'], 6)

    def test_alternative_entry_and_unused_helpers_do_not_inflate(self):
        a = w.analyze(RAW + '''[[mesh]] void main0() { _1(cp_s0); }
[[mesh]] void main0_z() { _1(cp_s0); _1(cp_s0); }
int unused() { return _1(cp_s0); }
''', META)
        self.assertEqual(a['sites']['raw_loads'], 1)
        self.assertNotIn('main0_z', a['reachable'])
        self.assertNotIn('unused', a['reachable'])

    def test_comments_and_storage_stores_are_not_loads(self):
        a = w.analyze('''kernel void main0() {
 // while (1) { t.sample(s, uv); }
 cp_s1._m0[0] = 7;
 uint x = cp_s1._m0[int(0)];
 uint y = (*spvDescriptorSet0.cp_s1)._m0[0];
 t.write(x, uv);
}''', META)
        self.assertEqual(a['sites']['storage_loads'], 2)
        self.assertEqual(a['sites'].get('texture_samples', 0), 0)
        self.assertEqual(a['loops'], [])

    def test_false_do_while_and_modified_loop_are_conservative(self):
        a = w.analyze('''kernel void main0() {
 do { t.read(uv); } while (false);
 for (int i=0; i<5; i++) { i = 4; t.read(uv); }
}''', META)
        self.assertEqual([x['trips'] for x in a['loops']], [1, None])
        self.assertEqual(a['estimated']['texture_reads'], 5)

    def test_atomic_condition_is_one_do_loop_and_has_side_effects(self):
        loops = w.loop_info('do { } while (atomic_compare_exchange(p, q, 1));')
        self.assertEqual(len(loops), 1)
        self.assertEqual(loops[0]['header'], 'atomic_compare_exchange(p, q, 1)')
        self.assertFalse(loops[0]['empty'])

    def test_lane_stride_bounds(self):
        loops = w.loop_info('for (uint i=dm_lid; i<2677u; i+=32u) p[i]=0;', lane_width=32)
        self.assertEqual(loops[0]['trip_range'], [83,84])
        loops = w.loop_info('for (uint i=dm_lid; i<96u; i+=32u) p[i]=0;', lane_width=32)
        self.assertEqual(loops[0]['trips'], 3)

    def test_border_helper_counts_conditional_extra_sample(self):
        source = """template<typename V, typename T> static inline V dm_bs(V r, T t) {
 if (border) r = t.sample(w, uv);
 return r;
}
kernel void main0() { float x = dm_bs(t.sample(w, uv), t); }
"""
        a = w.analyze(source, META)
        self.assertEqual(a['sites']['texture_samples'], 2)

    def test_packed_storage_load_counts_once_and_pointer_does_not(self):
        a = w.analyze("""kernel void main0() {
 packed_uint4 v = *(const device packed_uint4*)&(*spvDescriptorSet0.cp_s1)._m0[0];
 const device uint* ptr = &(*spvDescriptorSet0.cp_s1)._m0[4];
}""", META)
        self.assertEqual(a['sites']['storage_loads'], 1)

    def test_raw_store(self):
        a = w.analyze('''kernel void main0() {
 *(reinterpret_cast<device uint*>(ulong(1))) = 2;
}''', META)
        self.assertEqual(a['sites']['raw_stores'], 1)
        self.assertEqual(a['sites'].get('raw_loads', 0), 0)

    def test_sass_fields_are_guest_not_metal_registers(self):
        code = struct.pack('<QQ', 0x7981, 0) + struct.pack('<QQ', 0x7983, 0)
        ctl = bytearray(0x100)
        struct.pack_into('<II', ctl, 0, 0x98761234, 0xc9)
        struct.pack_into('<I', ctl, 0x38, len(code))
        struct.pack_into('<I', ctl, 0x4c, 64)
        stats, listing = w.sass_stats(bytes(0x38)+code+ctl, 'compute', ({0x981:'Ldg',0x983:'Ldl'},{}), True)
        self.assertEqual(stats['guest_registers'], 64)
        self.assertEqual(stats['guest_local_loads'], 1)
        self.assertEqual(stats['instructions'], 2)
        self.assertIn('Ldg', listing[0])

    def test_pipeline_references(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'bases.json'
            p.write_text(json.dumps({'pipeline_descriptors':{'render_pipeline_descriptors':[
                {'vertex_function_descriptor':'fnd:0123456789abcdef_bp.main0_z',
                 'fragment_function_descriptor':'fnd:fedcba9876543210_b.main0'}]}}))
            links, count = w.pipelines(p)
            self.assertEqual(links['0123456789abcdef'][0]['index'], 0)
            self.assertEqual(count, {'render_pipeline_descriptors':1})

    def test_read_only_build_guard(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'outside'):
                w.scan(Path(td),Path(td),Path(td)/'outputs')


if __name__ == '__main__': unittest.main()

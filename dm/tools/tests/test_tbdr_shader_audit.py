"""The audit never allow-lists a missing, pooled or dynamic reflection."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tbdr_shader_audit import audit


class ShaderAudit(unittest.TestCase):
    def test_readers_and_missing_reflection(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
            root = Path(d)
            (root / 'shader_map.tsv').write_text(
                'stage\tdm_ctl_sha16\n' + ''.join(f'pixel\t{i:016x}\n' for i in range(5)))
            (root / 'shader_facts.tsv').write_text('0000000000000000\t{"local":[1,1,1],"shared":0}\n')
            for i, bindings in enumerate([
                [{'kind': 'tex', 'reg': 0}],
                [{'kind': 'tex_pool', 'elem': 'texture2d<float>'}],
                [{'kind': 'tex', 'msl_name': 'fp_t_cb0_40000000', 'msl_type': 'array<texture2d<float>, 32>'}],
                [{'kind': 'new_unknown_reader'}],
            ]):
                (root / f'{i:016x}_b.json').write_text(json.dumps({'route': 'B', 'bindings': bindings}))
            r = audit(root, root)
            self.assertEqual(r['slot_resolvable_keys'], ['0000000000000000'])
            self.assertEqual(r['unresolved_keys'], ['0000000000000001', '0000000000000002', '0000000000000003'])
            self.assertEqual(r['missing_keys'], ['0000000000000004'])
            self.assertEqual(r['fact_fields'], {'local': 1, 'shared': 1})


if __name__ == '__main__':
    unittest.main()

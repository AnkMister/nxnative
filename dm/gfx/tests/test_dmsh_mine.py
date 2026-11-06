"""Mining counts use the primary entry and exclude generated output variants."""
import json
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import dmsh_mine as mine  # noqa: E402


class Mining(unittest.TestCase):
    def test_main_and_counts(self):
        src = '''fragment float4 main0() {
float _1 = (*spvDescriptorSet0.fp_c1)._m0[1].x;
float _2 = (*spvDescriptorSet0.fp_c1)._m0[1].x;
if (_1 > 0) { float _3 = (*spvDescriptorSet0.fp_c1)._m0[1].x; }
return float4(_2);
}
fragment uint4 main0_u() { return uint4(1); }
'''
        self.assertNotIn('main0_u', mine.main_body(src))
        self.assertEqual(mine.counts(src)['duplicate_cbuf'], 1)

    def test_published_folder_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); cache = root / 'cache'; index = cache / 'index'; index.mkdir(parents=True)
            output = cache / 'shader' / 'digest' / 'mac'; output.mkdir(parents=True)
            refl = {'dm_ctl': 'abc', 'stage': 'ps', 'chain': 'test'}
            (index / 'abc.json').write_text(json.dumps({'digest': 'digest'}))
            (output / 'abc_b.metal').write_text('fragment float4 main0() { return float4(0); }')
            (output / 'abc_b.json').write_text(json.dumps(refl))
            self.assertEqual(list(mine.folder_entries(cache)), [])  # incomplete publication
            (output / 'abc_b.metallib').write_bytes(b'compiled')
            mine.snapshot(cache, root / 'corpus', 1, None)
            manifest = json.loads((root / 'corpus/manifest.json').read_text())
            self.assertEqual(manifest['available'], {'ps': 1})
            self.assertEqual(manifest['shaders'][0]['id'], 'abc')
            self.assertEqual((root / 'corpus/abc.metal').read_text(), (output / 'abc_b.metal').read_text())

    def test_database_uses_current_index_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); db = root / 'cas.db'; reader = root / 'shader_cache.py'
            # The subclass must override setup, which a normal Store uses to write.
            reader.write_text("""class Store:
 def __init__(self, path): self.path = path; self._open()
 def _open(self): raise AssertionError('writable setup called')
 def names(self, prefix): return {r[0] for r in self.db.execute('SELECT name FROM entry WHERE name LIKE ?', (prefix + '%',))}
 def get(self, name): return self.db.execute('SELECT data FROM entry WHERE name=?', (name,)).fetchone()[0]
 def close(self): self.db.close()
""")
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE entry(name TEXT PRIMARY KEY, data BLOB)')
                entries = {'index/abc.json': json.dumps({'digest': 'current'}).encode()}
                for digest in ('old', 'current'):
                    base = f'shader/{digest}/mac/abc_b'
                    entries.update({base + '.metal': digest.encode(), base + '.metallib': b'compiled',
                                    base + '.json': json.dumps({'dm_ctl': 'abc', 'stage': 'cs', 'chain': 'test'}).encode()})
                conn.executemany('INSERT INTO entry VALUES(?, ?)', entries.items())
            before = db.read_bytes()
            rows = list(mine.db_entries(db, reader))
            self.assertEqual(len(rows), 1)
            self.assertIn('/current/', rows[0][0])
            self.assertEqual(rows[0][2](), b'current')
            self.assertEqual(db.read_bytes(), before)

    def test_mesh_body_counted_once(self):
        src = """void dm_stage_body() { float _1 = spvFAdd(1.0, 2.0); }
[[mesh]] void main0() { dm_stage_body(); }
[[mesh]] void main0_u() { dm_stage_body(); }
"""
        self.assertEqual(mine.main_body(src).count('spvFAdd'), 1)


if __name__ == '__main__': unittest.main()

"""Readable-tile cache misses compile on Mac independently of tensor opt-in."""
import ast
import collections
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import types
import unittest
from unittest import mock


class FetchBuild(unittest.TestCase):
    def test_mac_cache_miss_without_tensor(self):
        # dmsh_build's module starts a full build. Load just the production
        # coordinator and substitute its compiler/cache boundaries.
        source = Path(__file__).resolve().parents[1] / 'tools/dmsh_build.py'
        fn = next(n for n in ast.parse(source.read_text()).body
                  if isinstance(n, ast.FunctionDef) and n.name == 'fetch_finish')
        code = compile(ast.Module(body=[fn], type_ignores=[]), str(source), 'exec')
        for tensor in (None, '0', '1'):
            with self.subTest(tensor=tensor), tempfile.TemporaryDirectory() as directory:
                calls = []

                def compile_shader(msl, air, library):
                    calls.append(Path(msl).read_text())
                    Path(library).write_bytes(b'fixture library')

                scope = dict(
                    os=os, threading=threading, subprocess=subprocess,
                    stage_pass=lambda *a, **kw: ('fixture source', {'fixture': True}),
                    dmsh_fetch=types.SimpleNamespace(variant=None), BF_WANT=set(),
                    BF_STATS=collections.Counter(), out=directory, IOSOUT=None,
                    TARGETS=['mac'], bf_digest=lambda *a: 'digest',
                    CAS_LOCKS_GUARD=threading.Lock(), CAS_LOCKS={},
                    bf_cache_restore=lambda *a: False, mac_compile=compile_shader,
                    bf_cache_publish=lambda *a: None, write_refl=lambda *a: None)
                with mock.patch.dict(os.environ):
                    os.environ.pop('DMSH_HMMA_TENSOR', None)
                    if tensor is not None:
                        os.environ['DMSH_HMMA_TENSOR'] = tensor
                    exec(code, scope)
                    result = scope['fetch_finish']('fixture', 'source',
                                                   {'stage': 'ps', 'bindings': []})
                self.assertEqual(calls, ['fixture source'])
                self.assertEqual((Path(directory) / 'fixture_bf.metallib').read_bytes(),
                                 b'fixture library')
                self.assertTrue(result['fetch'])


if __name__ == '__main__':
    unittest.main()

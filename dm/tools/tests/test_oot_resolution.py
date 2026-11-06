"""The Ocarina resolution hooks stay on their audited build and instructions.
Set DM_OOT_ORIGINAL_MAIN to check the original NSO read-only, without rewriting it.
"""
import importlib.util
import os
from pathlib import Path
import struct
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'dm/tools'))
import nso

spec = importlib.util.spec_from_file_location('oot_patches', REPO / 'dm/games/0400486024DEC000/patches.py')
assert spec is not None and spec.loader is not None
patches = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patches)


class OotResolution(unittest.TestCase):
    def test_gates_are_build_bound_and_complete(self):
        self.assertEqual(set(patches.OBS), {'e0f3ccfaf50065ae4ea01eb5aeb13b1a'})
        self.assertEqual([(off, oid, word) for off, oid, word, _ in next(iter(patches.OBS.values()))], [
            (0x31ac7e0, 27, 'a9484ff4'), (0x31915ec, 28, 'a9474ff4'), (0xe83050, 29, '1e2202a0')])

    @unittest.skipUnless(os.environ.get('DM_OOT_ORIGINAL_MAIN'), 'original game NSO not provided')
    def test_original_module_sites(self):
        module = nso.read(os.environ['DM_OOT_ORIGINAL_MAIN'])
        self.assertEqual(module.build_id[:16].hex(), next(iter(patches.OBS)))
        for off, _, word, _ in patches.OBS[module.build_id[:16].hex()]:
            self.assertEqual(struct.unpack_from('<I', module.image, off)[0], int(word, 16))
        # Preceding instructions still own x20 at the two deserialization exits.
        self.assertEqual(module.image[0x31ac7dc:0x31ac7e0].hex(), 'e003152a')
        self.assertEqual(module.image[0x31915e8:0x31915ec].hex(), 'e0179f1a')
        self.assertEqual(module.image[0xe8304c:0xe83050].hex(), '605a0ebd')

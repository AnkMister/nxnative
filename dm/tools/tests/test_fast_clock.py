"""Opt-in counter lowering, including refusal, arbitrary destinations and the unchanged default."""
import ast
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / 'tests'))
import nso_asm
from test_nso_match import image

SOURCE = TOOLS / 'patch_nso.py'
TREE = ast.parse(SOURCE.read_text())
FUNCS = {'here', 'emit', 'emit_key_addr', 'emit_slot_addr', 'emit_gate_call', 'site_gate', 'site_clock'}


def lower(reg, fast=True):
    scope = dict(vars(nso_asm), struct=struct, patch=bytearray(), fix=[], gates=[], PATCH_BASE=0x10000,
                 KEY_PAGE_OFF=0x8000, KEY_INDEX={'KGATE': 3})
    exec(compile(ast.Module(body=[n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name in FUNCS], type_ignores=[]), str(SOURCE), 'exec'), scope)
    ins = next(Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(struct.pack('<I', 0xd53be020 | reg), 0x100))
    scope['site_clock' if fast else 'site_gate'](ins, 'cntpct', reg)
    return list(Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(bytes(scope['patch']), 0x10000)), scope['gates']


class FastClock(unittest.TestCase):
    def test_default_gate_bytes_and_metadata(self):
        ins, gates = lower(19, False)
        self.assertEqual([i.mnemonic for i in ins], ['stp', 'mrs', 'adrp', 'ldr', 'add', 'ldr', 'ldr', 'blr', 'ldp', 'b'])
        self.assertEqual(gates, [(ins[8].address, 'cntpct', 19, 0x100)])

    def test_fast_success_and_refusal_for_all_destinations(self):
        for reg in range(32):
            with self.subTest(reg=reg):
                ins, gates = lower(reg)
                if reg == 18:
                    self.assertEqual(len(ins), 10)
                    self.assertEqual(gates[0][1:3], ('clock_cntpct', 18))
                    continue
                call = next(i for i, p in enumerate(ins) if p.mnemonic == 'blr')
                self.assertEqual((ins[call - 1].mnemonic, ins[call - 1].op_str), ('add', 'x30, x30, #4, lsl #12'))
                result = ins[call + 1]
                self.assertEqual(result.mnemonic, 'str' if reg in (29, 30) else 'nop' if reg == 31 else 'mov')
                if reg < 29: self.assertEqual(result.op_str, f'x{reg}, x29')
                if reg in (29, 30): self.assertEqual(result.op_str, 'x29, [sp]' if reg == 29 else 'x29, [sp, #8]')
                self.assertEqual(ins[call + 3].op_str, '#0x104')
                refusal = next(p for p in ins if p.address == result.address + 12)
                self.assertEqual((refusal.mnemonic, refusal.op_str), ('ldp', 'x29, x30, [sp], #0x10'))
                self.assertEqual(gates[0][1:], ('clock_cntpct', reg, 0x100))
                self.assertEqual(ins[-2].address, gates[0][0])

    def test_driver_opt_in_and_frequency_scan(self):
        raw = image({0x100: [0xd53be033, 0xd53be054, 0xd53be015, 0xd5033fdf, 0xd65f03c0]})
        raw[0x1100:0x111c] = raw[0x20:0x3c]; struct.pack_into('<I', raw, 4, 0x1100)
        struct.pack_into('<ii', raw, 0x1110, 0x3000 - 0x1100, 0x3014 - 0x1100)
        raw[0x10:0x14] = b'NRO0'; struct.pack_into('<I', raw, 0x18, len(raw))
        struct.pack_into('<6I', raw, 0x20, 0, 0x1000, 0x1000, 0x2000, 0x3000, 0x1000); struct.pack_into('<I', raw, 0x38, 0)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'clock.nro'; src.write_bytes(raw)
            for flag in ('0', '1'):
                out = Path(tmp) / flag
                env = dict(os.environ, DM_GAME='0400486024DEC000', DM_REWRITE_J='1', DM_FAST_CLOCK=flag)
                run = subprocess.run([sys.executable, str(SOURCE), str(src), str(out), 'nro0'], env=env, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                gates = [l.split() for l in (out / 'nro0.gates.tsv').read_text().splitlines()]
                self.assertEqual([g[1] for g in gates], ['cntpct', 'cntvct'] if flag == '0' else ['clock_cntpct', 'clock_cntvct', 'clock_cntfrq'])
                self.assertEqual([int(g[2]) for g in gates], [19, 20] if flag == '0' else [19, 20, 21])
                patched = (out / 'nro0.patched.bin').read_bytes()
                self.assertEqual(struct.unpack_from('<I', patched, 0x10c)[0], 0xd5033fdf, 'existing ISB stays')
                self.assertEqual(struct.unpack_from('<I', patched, 0x108)[0] == 0xd53be015, flag == '0')


if __name__ == '__main__': unittest.main()

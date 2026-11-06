"""Execute Ocarina's emitted ARM64 cap and check its launcher capability."""
import importlib.util
import math
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'dm/tools'))
sys.path.insert(0, str(REPO / 'dm/games'))
import settings  # noqa: E402

spec = importlib.util.spec_from_file_location('oot_scale', REPO / 'dm/games/0400486024DEC000/patches.py')
assert spec is not None and spec.loader is not None
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)
try:
    unicorn = importlib.import_module('unicorn')
    arm = importlib.import_module('unicorn.arm64_const')
except ImportError:
    unicorn = arm = None


class RenderScale(unittest.TestCase):
    def test_registered_build_and_launcher_capability(self):
        self.assertEqual(list(profile.FRAME_STEP), ['e0f3ccfaf50065ae4ea01eb5aeb13b1a'])
        with tempfile.TemporaryDirectory() as tmp, patch.object(settings.nacp, 'languages', return_value=['en-US']):
            fixups = Path(tmp) / 'main.fixups.tsv'
            for supported in (False, True):
                fixups.write_text('# FPS_STATE_OFF\t0x10000\n' + ('# RENDER_SCALE\t1\n' if supported else ''))
                for platform in ('ios', 'mac'):
                    with patch.dict(settings.os.environ, {'SETTINGS_PLATFORM': platform}):
                        rows = settings.build('0400486024DEC000', tmp, 'unused')['settings']
                    scale = [row for row in rows if row['env'] == 'DM_RENDER_SCALE']
                    self.assertEqual(bool(scale), supported)
                    self.assertNotIn('DM_FPS_TARGET', [row['env'] for row in rows])
                    if scale:
                        self.assertEqual((scale[0]['min'], scale[0]['max'], scale[0]['default']), (0.5, 1.0, '1.0'))

    @unittest.skipIf(unicorn is None, 'optional ARM64 execution dependency: unicorn')
    def test_actual_stub_caps_the_store_and_preserves_registers(self):
        assert unicorn is not None and arm is not None
        base, area, state, obj, stack, site = 0x4000000, 0x10000, 0x20000, 0x30000, 0x40000, 0x31d3f48
        machine = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
        machine.mem_map(base, 0x3200000)
        cursor = area
        checked, patched = [], []

        def emit(word):
            nonlocal cursor
            machine.mem_write(base + cursor, struct.pack('<I', word))
            cursor += 4

        def put(offset, words, reason):
            patched.append((offset, reason))
            machine.mem_write(base + offset, struct.pack('<' + 'I' * len(words), *words))

        context = types.SimpleNamespace(here=lambda: cursor, emit=emit, site=lambda offset, old: checked.append((offset, old)), put=put, state=state)
        profile.render_scale(context)
        self.assertEqual(checked, [(site, '805e0ebd')])
        self.assertEqual([offset for offset, _ in patched], [site])
        self.assertEqual(context.render_scale, 1)
        self.assertLessEqual(cursor - area, 80)
        for ceiling in (-1.0, 0.0, 0.5, 0.75, 1.0, 2.0, float('inf'), float('nan')):
            machine.mem_write(base + state + 0x10, struct.pack('<f', ceiling))
            for original in (0.25, 0.5, 0.625, 0.875, 1.0):
                for flags in (0, 0x60000000, 0x90000000, 0xf0000000):
                    with self.subTest(ceiling=ceiling, original=original, flags=flags):
                        registers = {getattr(arm, f'UC_ARM64_REG_X{i}'): 0x12340000 + i for i in range(31)}
                        registers.update({getattr(arm, f'UC_ARM64_REG_Q{i}'): 0x123456789abcdef0fedcba9876543210 + i for i in range(32)})
                        registers.update({arm.UC_ARM64_REG_X20: base + obj, arm.UC_ARM64_REG_SP: base + stack, arm.UC_ARM64_REG_NZCV: flags})
                        original_bits = struct.unpack('<I', struct.pack('<f', original))[0]
                        registers[arm.UC_ARM64_REG_Q0] = (registers[arm.UC_ARM64_REG_Q0] & ~0xffffffff) | original_bits
                        for register, value in registers.items():
                            machine.reg_write(register, value)
                        machine.mem_write(base + obj + 0xe58, b'\xa5' * 12)
                        machine.emu_start(base + site, base + site + 4, count=64)
                        expected = original if not 0 < ceiling < 1 or math.isnan(ceiling) else min(original, ceiling)
                        stored = machine.mem_read(base + obj + 0xe58, 12)
                        self.assertEqual(bytes(stored), b'\xa5' * 4 + struct.pack('<f', expected) + b'\xa5' * 4)
                        for register, value in registers.items():
                            self.assertEqual(machine.reg_read(register), value, f'register {register}')

    @unittest.skipIf(unicorn is None, 'optional ARM64 execution dependency: unicorn')
    def test_frame_controller_stub_and_combined_hook(self):
        assert unicorn is not None and arm is not None
        base, area, state, obj, stack, site = 0x4000000, 0x10000, 0x20000, 0x30000, 0x40000, 0x3b4f074
        machine = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
        machine.mem_map(base, 0x3c00000)
        cursor, checked, patched = area, [], []
        def emit(word):
            nonlocal cursor
            machine.mem_write(base + cursor, struct.pack('<I', word))
            cursor += 4
        def put(offset, words, reason):
            patched.append(offset)
            machine.mem_write(base + offset, struct.pack('<' + 'I' * len(words), *words))
        ctx = types.SimpleNamespace(here=lambda: cursor, emit=emit, site=lambda offset, old: checked.append((offset, old)), put=put, state=state)
        profile.apply(ctx)
        self.assertEqual(patched, [0x31d3f48, site])
        self.assertEqual(checked[-1], (site, 'e00314aa'))
        self.assertEqual(ctx.render_scale, 1)
        for target in (0, 30, 60):
            for step in (0, 1, 2, 3):
                with self.subTest(target=target, step=step):
                    machine.mem_write(base + state, struct.pack('<f', target))
                    machine.mem_write(base + state + 0x20, struct.pack('<I', step))
                    machine.mem_write(base + state + 0x30, struct.pack('<Q', 41))
                    machine.mem_write(base + obj, b'\xa5' * 0x80)
                    machine.mem_write(base + obj + 0x48, struct.pack('<I', 7))
                    machine.mem_write(base + obj + 0x58, struct.pack('<I', 8))
                    regs = {getattr(arm, f'UC_ARM64_REG_X{i}'): 0x12340000 + i for i in range(31)}
                    regs.update({arm.UC_ARM64_REG_X20: base + obj, arm.UC_ARM64_REG_SP: base + stack, arm.UC_ARM64_REG_NZCV: 0x90000000})
                    for reg, value in regs.items(): machine.reg_write(reg, value)
                    machine.emu_start(base + site, base + site + 4, count=64)
                    active = bool(target and step)
                    self.assertEqual(struct.unpack('<I', machine.mem_read(base + obj + 0x48, 4))[0], step if active else 7)
                    self.assertEqual(struct.unpack('<I', machine.mem_read(base + obj + 0x58, 4))[0], 60 // step if active else 8)
                    self.assertEqual(struct.unpack('<Q', machine.mem_read(base + state + 0x30, 8))[0], 41 + step if active else 41)
                    self.assertEqual(bytes(machine.mem_read(base + obj + 0x4c, 12)), b'\xa5' * 12)
                    for reg, value in regs.items():
                        self.assertEqual(machine.reg_read(reg), base + obj if reg == arm.UC_ARM64_REG_X0 else value)


if __name__ == '__main__':
    unittest.main()

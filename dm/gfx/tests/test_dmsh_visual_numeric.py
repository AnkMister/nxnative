"""Execute emitted F2IP and RED on Metal against independent scalar numeric models."""
import math, os, re, struct, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_dmsh_ampere_mem as fixtures
from test_dmsh_ampere_mem import Translated, inst, mov, sts, EXIT
TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0,str(TOOLS))


def bits(f): return struct.unpack('<I', struct.pack('<f', f))[0]
def fp(b): return struct.unpack('<f', struct.pack('<I', b))[0]
def ftz(b): return b & 0x80000000 if b & 0x7fffffff < 0x00800000 else b


def byte(f, mode):
    if math.isnan(f): return 0
    if f <= 0: return 0
    if f >= 255: return 255
    return (round, math.floor, math.ceil, math.trunc)[mode](f)


@unittest.skipUnless(os.environ.get('DMSH_TEST_GPU') == '1', 'set DMSH_TEST_GPU=1 for Metal execution')
class Numeric(Translated):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, DMSH_OOT_VISUAL="1"))
        self.work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.runner = self.work / 'numeric'
        subprocess.run(['clang', '-O1', '-fobjc-arc', str(Path(__file__).with_name('t_visual_numeric.m')), '-framework', 'Foundation', '-framework', 'Metal', '-o', str(self.runner)], check=True, capture_output=True)

    def execute(self, source, initial, threads=1):
        src = self.work / 'k.metal'; lib = self.work / 'k.metallib'; init = self.work / 'initial.bin'
        src.write_text(source); init.write_bytes(struct.pack('<' + 'I' * len(initial), *initial))
        subprocess.run(['xcrun', '-sdk', 'macosx', 'metal', '-O1', '-fpreserve-invariance', '-fbracket-depth=1024', str(src), '-o', str(lib)], check=True, capture_output=True)
        r = subprocess.run([str(self.runner), str(lib), str(init), str(threads)], check=True, capture_output=True)
        return list(struct.unpack('<' + 'I' * len(initial), r.stdout))

    def test_f2ip_numeric_reference_all_rounding_modes(self):
        values = [-math.inf, -1, -0.0, 0.49, 0.5, 1.5, 2.5, 3.5, 127.5, 254.5, 254.9, 255, 256, math.inf, math.nan, fp(1)]
        code = b''; expected = []
        for mode in range(4):
            for i,a in enumerate(values):
                b = values[-i-1]
                code += mov(4,bits(a)) + mov(5,bits(b)) + inst(0x000fe200000004ff | mode << 14, 0x0000000504067243) + sts(len(expected)*4,6)
                expected.append(byte(fp(bits(a)),mode)<<8 | byte(fp(bits(b)),mode))
        source = self.translate(code+inst(*EXIT),shared=1024)
        shared = re.search(r'threadgroup spvUnsafeArray<uint, \d+> (\w+);',source)[1]
        source = re.sub(r'kernel void main0\((.*?)\)\n\{', lambda m:'kernel void main0('+m[1]+(', ' if m[1].strip() else '')+'device uint* result [[buffer(30)]])\n{',source,flags=re.S)
        end = source.rfind('}')
        source = source[:end]+f'for (uint i=0;i<{len(expected)};i++) result[i]={shared}[i];\n'+source[end:]
        self.assertEqual(self.execute(source,[0]*len(expected)),expected)

    def test_global_cas_exact_bits_and_old_value(self):
        # ATOMG.E.CAS: B is expected, C is replacement; D receives the old bits.
        # IMAD.MOV reads the mapped storage address out of compute c0[0x40:48].
        cases = [(0, 0, 0xffffffff), (0xffffffff, 0xffffffff, 0),
                 (0x80000000, 0x80000000, 0x7fc01234),
                 (0x7fc01234, 0x7fc01234, 0x80000000),
                 (0x7fc01234, 0x7fc05678, 1), (42, 41, 99)]
        for old, expected, replacement in cases:
            for dest in (4, 6):  # including destination aliasing the address
                with self.subTest(old=hex(old), expected=hex(expected), dest=dest):
                    code = inst(0x000fe200078e00ff, 0x00001000ff047624)
                    code += inst(0x000fe200078e00ff, 0x00001100ff057624)
                    code += mov(8, expected) + mov(9, replacement)
                    code += inst(fixtures.ctrl() | 0x1ee109, 0x00000008040073a9 | dest << 16)
                    code += sts(0, dest) + inst(*EXIT)
                    source = self.translate(code, nvn2_cs=[3, 1, 0, 0x50, 0], shared=4)
                    shared_match = re.search(r'threadgroup spvUnsafeArray<uint, \d+> (\w+);', source)
                    assert shared_match is not None
                    shared = shared_match[1]
                    source = re.sub(r'kernel void main0\((.*?)\)\n\{',
                                    lambda m: 'kernel void main0(' + m[1] + ', device uint* result [[buffer(30)]])\n{', source, flags=re.S)
                    end = source.rfind('}')
                    source = source[:end] + f'result[1]={shared}[0];\n' + source[end:]
                    self.assertEqual(self.execute(source, [old, 0]),
                                     [replacement if old == expected else old, old])

    def test_float16_limit_preserves_nan_and_finite_values(self):
        import dmsh_limit16
        values = [math.inf, -math.inf, math.nan, 70000.0, -70000.0, 1.5, -0.0]
        stores = ''.join(f'result[{i}]=as_type<uint>(dm_limit16(as_type<float>({bits(v)}u)));' for i,v in enumerate(values))
        source = '#include <metal_stdlib>\nusing namespace metal;\n' + dmsh_limit16.HELPER + 'kernel void main0(device uint* result [[buffer(30)]]) {' + stores + '}'
        result = self.execute(source,[0]*len(values))
        self.assertEqual(result[:2],[bits(65504.0),bits(-65504.0)])
        self.assertTrue(math.isnan(fp(result[2])))
        self.assertEqual(result[3:],[bits(65504.0),bits(-65504.0),bits(1.5),bits(-0.0)])

    def test_global_float_reduction_ftz_and_contention(self):
        cases = [(bits(1),bits(1.5),1), (1,0x80000001,1), (0x80000001,0x80000001,1),
                 (0x00800001,0x80800000,1), (0x80800001,0x00800000,1),
                 (bits(1),bits(2**-24),1), (bits(math.inf),bits(1),1), (bits(math.nan),bits(1),1), (bits(math.inf),bits(-math.inf),1), (bits(0),bits(1.5),128)]
        for old,value,threads in cases:
            with self.subTest(old=hex(old),value=hex(value),threads=threads):
                code=mov(5,value)+inst(*fixtures.RedF32.ULDC)+inst(*fixtures.RedF32.RED)+inst(*EXIT)
                source=self.translate(code,nvn2_cs=[3,1,0,0x50,0])
                expected=old
                for _ in range(threads): expected=ftz(bits(fp(ftz(expected))+fp(ftz(value))))
                result = self.execute(source,[old],threads)
                if math.isnan(fp(expected)): self.assertTrue(math.isnan(fp(result[0])))
                else: self.assertEqual(result,[expected])


if __name__ == '__main__': unittest.main()

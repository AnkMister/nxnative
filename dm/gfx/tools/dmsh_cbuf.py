"""Experimental literal constant-buffer word reuse; default off in dmsh_build.py.

Only float4 arrays in constant address space qualify. Repeated reads of one literal
component in a straight-line region take a local const float. There is no widening,
no address speculation, and no change to floating-point operations or precision.
Metal may already eliminate these reads; source counts alone are not a speedup.
"""
import re
import dmsh_wide


_MEMBER = re.compile(r'^\s*constant (\w+)\* ([a-z]p_c\d+) \[\[id\(\d+\)\]\];', re.M)
_ARRAY = re.compile(r'struct (\w+)\s*\{\s*float4 _m0\[(\d+)\];\s*\};')
_WORD = re.compile(r'\(\*spvDescriptorSet0\.([a-z]p_c\d+)\)\._m0\[(\d+)\]\.([xyzw])\b')


def reuse_words(msl):
    """Leave unknown layouts, dynamic indices and unsafe regions unchanged."""
    if '_dmcb' in msl or '/*' in msl: return msl
    arrays = {typ: int(size) for typ, size in _ARRAY.findall(msl)}
    buffers = {name: arrays[typ] for typ, name in _MEMBER.findall(msl) if typ in arrays}
    if not buffers: return msl
    lines = msl.split('\n'); groups = {}; block = 0
    for i, line in enumerate(lines):
        if '{' in line or '}' in line or dmsh_wide._WRITE.search(line): block += 1; continue
        if '//' in line or '"' in line or line.lstrip().startswith('#'): block += 1; continue
        for m in _WORD.finditer(line):
            if m[1] in buffers and int(m[2]) < buffers[m[1]]:
                groups.setdefault((block, m[0]), []).append((i, m))
    edits = {}; count = 0
    for (_, word), uses in groups.items():
        if len(uses) < 2: continue
        name = f'_dmcb{count}'; count += 1
        for n, (i, match) in enumerate(uses):
            edits.setdefault(i, []).append((match.start(), match.end(), name, f'const float {name} = {word};' if n == 0 else None))
    for i, changes in edits.items():
        line = lines[i]; before = []
        for start, end, name, declaration in sorted(changes, reverse=True):
            line = line[:start] + name + line[end:]
            if declaration: before.append(declaration)
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        lines[i] = ''.join(indent + decl + '\n' for decl in reversed(before)) + line
    return '\n'.join(lines)

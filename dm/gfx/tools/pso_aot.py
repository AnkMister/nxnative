"""Opt-in exact descriptor planning. pso_seen uses numeric Metal enums; metal-tt
uses their SDK names. Libraries and identities contain no machine paths."""
import collections
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import romfs


HOST_DIR = None
FUNCTIONS = ('vertex', 'fragment', 'compute', 'mesh', 'object')


def library_path(root, name):
    if not isinstance(name, str) or '/' in name or '\\' in name or '..' in name:
        raise ValueError(f'invalid library identity: {name!r}')
    if name.startswith('host:'):
        if HOST_DIR is None: raise ValueError('host libraries have not been prepared')
        return Path(HOST_DIR) / (name[5:] + '.metallib')
    return romfs.Path(root) / (name + '.metallib')


def libraries(rows):
    return {v[0] for row in rows for k, v in row.items() if k in FUNCTIONS}


def enums(platform):
    sdk = subprocess.check_output(['xcrun', '-sdk', 'macosx' if platform == 'macos' else 'iphoneos', '--show-sdk-path'], text=True).strip()
    headers = Path(sdk) / 'System/Library/Frameworks/Metal.framework/Headers'
    text = '\n'.join(p.read_text() for p in headers.glob('*.h'))
    result = {}
    for prefix in ('MTLPixelFormat', 'MTLBlendFactor', 'MTLBlendOperation', 'MTLVertexFormat', 'MTLVertexStepFunction', 'MTLPrimitiveTopologyClass'):
        result[prefix] = {int(n, 0): name for name, n in re.findall(prefix + r'(\w+)\s*(?:API_\w+\([^;=]*?\)\s*)?=\s*(0x[\da-fA-F]+|\d+)\b', text)}
    return result


def configuration(row, fd, enum):
    """Translate the portable census into the documented metal4-pipelines-script."""
    kind = row['class']
    out = {k + '_function_descriptor': fd(*row[k]) for k in FUNCTIONS if k in row}
    if kind == 'compute': return 'compute_pipeline_descriptors', out
    def en(prefix, value):
        if value == -1: return 'Unspecialized'
        try: return enum['MTL' + prefix][value]
        except KeyError as e: raise ValueError(f'unknown {prefix} value {value}') from e
    out.update(raster_sample_count=row['samples'], rasterization_enabled=bool(row['raster']), alpha_to_coverage_state='Enabled' if row['a2c'] else 'Disabled')
    colors = []
    for c in row['colors']:
        if c[0] == -1:
            colors.append(dict.fromkeys(('pixel_format', 'write_mask', 'blending_state', 'source_rgb_blend_factor', 'destination_rgb_blend_factor', 'rgb_blend_operation',
                                         'source_alpha_blend_factor', 'destination_alpha_blend_factor', 'alpha_blend_operation'), 'Unspecialized'))
        else:
            colors.append(dict(zip(('pixel_format', 'write_mask', 'blending_state', 'source_rgb_blend_factor', 'destination_rgb_blend_factor', 'rgb_blend_operation',
                                    'source_alpha_blend_factor', 'destination_alpha_blend_factor', 'alpha_blend_operation'),
                                   (en('PixelFormat', c[0]), ' '.join(n for b, n in ((8, 'Red'), (4, 'Green'), (2, 'Blue'), (1, 'Alpha')) if c[1] & b) or 'None',
                                    'Enabled' if c[2] else 'Disabled', en('BlendFactor', c[3]), en('BlendFactor', c[4]), en('BlendOperation', c[5]),
                                    en('BlendFactor', c[6]), en('BlendFactor', c[7]), en('BlendOperation', c[8])))))
    out['color_attachments'] = colors
    if kind == 'mesh':
        for key, field in (('mesh_threads', 'max_total_threads_per_mesh_threadgroup'), ('object_threads', 'max_total_threads_per_object_threadgroup'),
                           ('payload', 'payload_memory_length'), ('mesh_grid', 'max_total_threadgroups_per_mesh_grid'),
                           ('mesh_multiple', 'mesh_threadgroup_size_is_multiple_of_thread_execution_width'), ('object_multiple', 'object_threadgroup_size_is_multiple_of_thread_execution_width')):
            out[field] = row[key]
        return 'mesh_render_pipeline_descriptors', out
    out['input_primitive_topology'] = en('PrimitiveTopologyClass', row['topology'])
    out['max_vertex_amplification_count'] = row['amp']
    if row['attrs']:
        out['vertex_descriptor'] = {
            'attributes': [dict(format=en('VertexFormat', f), offset=o, buffer_index=b) for f, o, b in row['attrs']],
            'layouts': [dict(stride=s, step_function=en('VertexStepFunction', f), step_rate=r) for s, f, r in row['layouts']]}
    return 'render_pipeline_descriptors', out


def validate(row, chain):
    if row.get('version') != 1 or row.get('chain') != chain or row.get('class') not in ('compute', 'render', 'mesh'):
        raise ValueError('unsupported descriptor version, chain or class')
    needed = {'compute': 'compute', 'render': 'vertex', 'mesh': 'mesh'}[row['class']]
    if needed not in row: raise ValueError('missing pipeline function')
    for k in FUNCTIONS:
        if k in row:
            ref = row[k]
            if not isinstance(ref, list) or len(ref) != 2 or not all(isinstance(s, str) and s for s in ref): raise ValueError('invalid function identity')
            if any(x in ref[0] for x in ('/', '\\', '..')): raise ValueError('library identity contains a path')
    if row['class'] != 'compute':
        if len(row['colors']) != 8 or any(len(c) != 9 for c in row['colors']): raise ValueError('invalid color state')
        if row['class'] == 'render' and (len(row['attrs']) != len(row['layouts']) or len(row['attrs']) > 31): raise ValueError('invalid vertex layout')
    return row


def plan(root, chain, seen, functions, host_dir, shader_map=None, zero=False):
    """Every successful compute; explicit program-source mesh combinations; learned exact states.
    Do not guess a cross-product of unrelated task/mesh/fragment functions."""
    global HOST_DIR
    HOST_DIR = host_dir
    root = romfs.Path(root); rows = []; gaps = collections.Counter(); reflections = {}
    def add(row): rows.append(dict(version=1, chain=chain, **row))
    for path in sorted(root.glob('*_b.json')):
        j = json.loads(path.read_text()); key = path.name[:-7]
        if j.get('chain') != chain: continue
        reflections[key] = j
        if j.get('stage') != 'cs': continue
        entry = j.get('entry', 'main0'); lib = key + '_b'
        try: fn = functions(root / (lib + '.metallib'))
        except (OSError, ValueError): gaps['compute library'] += 1; continue
        if entry not in fn or fn[entry]: gaps['compute constants/entry'] += 1; continue
        add({'class': 'compute', 'compute': [lib, entry]})
    if host_dir:
        for path in sorted(Path(host_dir).glob('*.metallib')):
            # TYPE tags identify kernel entries; the adjacent source is the build input.
            src = path.with_suffix('.metal')
            for name in re.findall(r'kernel\s+void\s+(\w+)\s*\(', src.read_text()):
                add({'class': 'compute', 'compute': ['host:' + path.stem, name]})
    # shader_map records the first source of each key. Only a source with one
    # unambiguous mesh, fragment, and (if required) task is evidence of a combination.
    groups = collections.defaultdict(lambda: collections.defaultdict(set))
    if shader_map and Path(shader_map).is_file():
        for line in Path(shader_map).read_text().splitlines():
            c = line.split('\t')
            if len(c) >= 5 and c[2] in ('mesh', 'task', 'pixel'): groups[c[4]][c[2]].add(c[3])
    covered_mesh = set()
    for stages in groups.values():
        if len(stages['mesh']) != 1 or len(stages['pixel']) != 1 or len(stages['task']) > 1: continue
        mk, fk = next(iter(stages['mesh'])), next(iter(stages['pixel']))
        mj, fj = reflections.get(mk), reflections.get(fk)
        if not mj or not fj: continue
        task = next(iter(stages['task']), None); tj = reflections.get(task) if task else None
        info = mj.get('mesh_stage', {})
        if info.get('task', True) and not tj: continue
        refs = {'mesh': [mk + '_b', mj.get('entry_z') if zero and mj.get('entry_z') else mj.get('entry', 'main0')], 'fragment': [fk + '_b', fj.get('entry', 'main0')]}
        if task and tj: refs['object'] = [task + '_b', tj.get('entry', 'main0')]
        try:
            if any(functions(root / (lib + '.metallib')).get(entry, True) for lib, entry in refs.values()): continue
        except (OSError, ValueError): continue
        ti = tj.get('mesh_stage', {}) if tj else {}
        add(dict({'class': 'mesh', 'base': True, 'samples': 1, 'a2c': False, 'raster': True, 'colors': [[-1] * 9 for _ in range(8)],
                  'mesh_threads': info.get('threads', 0), 'object_threads': ti.get('threads', 0), 'payload': (ti.get('payload', 0) + 15) & ~15,
                  'mesh_grid': 0, 'mesh_multiple': False, 'object_multiple': False}, **refs))
        covered_mesh.add(mk)
    gaps['mesh keys without source combination'] = sum(j.get('stage') == 'ms' and k not in covered_mesh for k, j in reflections.items())
    for path in seen:
        for n, line in enumerate(Path(path).read_text().splitlines(), 1):
            if not line.strip(): continue
            try:
                row = validate(json.loads(line), chain)
                for k in FUNCTIONS:
                    if k not in row: continue
                    lib, entry = row[k]
                    fn = functions(library_path(root, lib))
                    if entry not in fn or fn[entry]: raise ValueError('function missing or has constants')
                rows.append(row)
            except (ValueError, KeyError, TypeError, OSError) as e:
                raise ValueError(f'{Path(path).name}:{n}: invalid/stale pso_seen: {e}') from e
    rows = list({json.dumps(r, sort_keys=True, separators=(',', ':')): r for r in rows}.values())
    return rows, dict(gaps)


def prepare_helpers(work, platform):
    """Small built-in shaders only, same sources and compiler flags as the host."""
    repo = Path(__file__).resolve().parents[3]
    match = re.search(r'MACOS_MIN\s*:?=\s*([\d.]+)', (repo / 'dm/mac/min_os.mk').read_text())
    if not match: raise ValueError('missing host deployment target')
    minimum = '26.0' if platform == 'ios' else match.group(1)
    sdk = 'macosx' if platform == 'macos' else 'iphoneos'
    version = subprocess.check_output(['xcrun', '-sdk', sdk, 'metal', '--version'], text=True).strip()
    dst = Path(work).resolve() / 'host-libs'; dst.mkdir(exist_ok=True)
    stamp = dst / 'compiler.txt'; identity = f'{sdk} {minimum} {version}\n'
    same = stamp.is_file() and stamp.read_text() == identity
    for src in sorted((repo / 'dm/gfx/msl').glob('*.metal')):
        out = dst / (src.stem + '.metallib'); copy = out.with_suffix('.metal')
        if same and copy.is_file() and copy.read_bytes() == src.read_bytes() and out.is_file(): continue
        subprocess.run(['xcrun', '-sdk', sdk, 'metal', f'-m{sdk if platform == "macos" else "ios"}-version-min={minimum}', '-o', str(out), '../gfx/msl/' + src.name], cwd=repo / 'dm/host', check=True)
        copy.write_bytes(src.read_bytes())
    stamp.write_text(identity)
    return dst


def base_rows(bases, chain):
    """The existing render bases are also loaded before gameplay, never specialized
    by this inventory. Exact final states are separate learned descriptors."""
    return [dict(version=1, chain=chain, **{'class': 'render'}, base=True,
                 vertex=[b[0], b[1]], fragment=[b[2], b[3]], samples=1, a2c=False, raster=True,
                 colors=[[-1] * 9 for _ in range(8)], topology=3 if len(b) == 5 else 0, amp=1, attrs=[], layouts=[])
            for b in bases if isinstance(b, tuple)]

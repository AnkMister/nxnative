#!/usr/bin/env python3
# The pipeline archive made offline: the base of every shader pair, as the host's pipeline prebuild makes it on the device (pre_desc / pre_pair in dm/gfx/nvn/nvn_mtl.m), compiled on the Mac
# by metal-tt into one Metal 4 pipeline archive per GPU architecture, so an iPhone takes the bases from the app bundle instead of compiling them on its first start.
# The host matches libraries by content, so the archive serves the libraries the app ships (msl/b-<chain>); measurements are in dm/games/01007EF00011E000/README.md.
# Per pair (vertex key, pixel key) of the profile's shader_pairs.tsv and pso_pairs.tsv, read in that order with repeated lines dropped, as the host reads them:
#   · the vertex shader's pulling library <key>_bp (a vertex shader without stage inputs: its own <key>_b), entry `entry`, or `entry_z` for the near = 0 depth mode, from its reflection
#     <key>_b.json; the pixel shader's <key>_b, entry `entry` (main0); no vertex descriptor, one sample, every colour attachment unspecialized
#   · left out as the host leaves them out (to the draws): a reflection of another chain version or none, a vertex shader with stage inputs and no pulling library, a vertex library that
#     writes the layer (render_target_array_index), a pixel shader that reads the primitive ID (its reflection's raster.primitive_id: the host builds its pipelines whole, since
#     through a base every primitive reads 0), a missing library or entry point
#   · without --aot, a pair whose functions declare function constants is left to the device (rest_pairs.tsv): the host specializes such functions with an empty set of values, and metal-tt makes
#     no specialized function from a library (applegpu-nt: "cannot find private metadata"), nor the function unspecialized ("cannot lower module with unresolved function constants")
# --aot with --seen/--user captures exact final states and typed constants. Constant descriptors use the matching local Mac --host compiler/serializer instead of metal-tt.
# Output folder (what the app bundles as pso/, the host's DM_PSO_BUNDLE):
#   <arch>.mtl4a     first archive per GPU architecture; additional parts are <arch>.<n>.mtl4a (n >= 1)
#   prebuilt.tsv     what the archives cover, in the host's stamp format (pso_prebuild): chain version, depth mode, the pair lists' size and SHA-256. The host skips its prebuild when
#                    it matches and a probe of a few bases finds them in the archive
#   rest_pairs.tsv   the pairs the device still builds (only when there are any)
#   archive.tsv      what was built: architectures, OS minimum, toolchain, bases and part sizes (the host checks that every listed part is present)
# Each archive is made again only when its compiler inputs change (key.<arch> in the work folder): the complete pipeline configuration without library locations,
# the referenced libraries' bytes, architecture, platform, minimum OS and metal-tt version. Chain/profile stamps are validated and refreshed independently.
# More bases than --batch-size are compiled in bounded groups (batches.<arch>/<index>/ in the work folder, each cached by its own inputs) and merged with metal-pack: one metal-tt on
# Super Mario Odyssey's 32,864 bases runs an 8 GB Mac out of paging space (docs/reference/shaders.md, Bounded groups for the offline pipeline compiler). Large outputs are split below PACK_LIMIT; every part ships in the bundle.
# DM_PSO_J: independent cached batch workers; DM_METAL_PACK_THREADS: merge threads (both default 1).
# Usage: pso_offline.py --msl <b-<chain> folder> --out <folder> --work <folder> [--game <id>] [--pairs <shader_pairs.tsv> [--pairs <pso_pairs.tsv>]] [--gpu g18p[,g17p]]
#          [--depth gl|zero] [--platform ios|macos] [--os-min 27.0] [--script-only] [--batch-size N]
#   --game: the profile (DM_GAMES_DIR as for game.py) whose shader_pairs.tsv and pso_pairs.tsv are the pairs, and whose depth_mode key the depth mode, unless --pairs / --depth say;
#   --gpu: architectures, with or without the applegpu_ prefix (default g18p); --depth: the game's NVN depth mode (gl = near -w, NVN's default; zero = near 0, which the game sets
#   with nvnDeviceSetDepthMode: the host knows it only at run time, so the profile says it; a wrong one costs the device its own prebuild, as without the archive);
#   --os-min: the archives' system (default: for iOS the SDK's major version, e.g. 27.0; for macOS the major version this Mac runs, since the Mac app is built for the Mac that builds it).
#   A device opens only an archive of its own major version (macOS 27.2 refused archives made for 26.0 and 26.6 and opened those for 27.0 and 27.2), and builds the bases itself
#   otherwise: the SDK's version on a Mac whose system is older than its Xcode's SDK (macOS 26.6 with Xcode 27.1) left that Mac without them (GitHub issue #673)
import concurrent.futures as cf
import argparse, filecmp, hashlib, json, os, shutil, struct, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import romfs, shader_lib   # the libraries may be one file (shader_lib.py), read in place; metal-tt alone needs files of its own (real_libraries)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pso_aot
AOT_ENUMS = {}
AOT_HOST = None
AOT_SHADER_MAP = None
AOT_ZERO = False

LAYER = b'render_target_array_index'
PACK_LIMIT = 7 * (1 << 29)   # 3.5 GiB: leave headroom below a GPU Mach-O slice's 4 GiB offsets
BATCH = 1000   # bases per metal-tt run: Odyssey's largest compiler lifetime footprint at this size was 2.065 GiB on an 8 GB M2
COLOUR = ('pixel_format', 'write_mask', 'blending_state', 'alpha_blend_operation', 'rgb_blend_operation', 'destination_alpha_blend_factor', 'destination_rgb_blend_factor',
          'source_alpha_blend_factor', 'source_rgb_blend_factor')


def arch_name(a):   # 'g18p' → 'applegpu_g18p'
    a = a.strip()
    return a if a.startswith('applegpu_') else f'applegpu_{a}'


def pair_text(paths):
    """The pair lists as the host reads them: their bytes one after the other (shader_pairs.tsv, then pso_pairs.tsv when it exists)"""
    return b''.join(Path(p).read_bytes() for p in paths if p and Path(p).is_file())


def read_pairs(text):
    """(vertex key, pixel key) per line, in order, without empty lines, comments and repeated lines (pso_prebuild's reading)"""
    seen, out = set(), []
    for line in text.decode('utf-8').split('\n'):
        if not line or line.startswith('#') or line in seen: continue
        seen.add(line); c = line.split('\t')
        if len(c) >= 2: out.append((c[0], c[1]))
    return out


def stamp(chain, zero, text):
    """The host's prebuild stamp (pso_prebuild in nvn_mtl.m): chain version, depth mode, and the pair lists' length in bytes and SHA-256 (first 16 hex digits)"""
    return f'chain\t{chain}\ndepth\t{"near=0" if zero else "near=-w"}\npairs\t{len(text)}\t{hashlib.sha256(text).hexdigest()[:16]}\n'


def functions(path):
    """{entry name: declares function constants} of a .metallib, from its header: the function list (NAME tags) and each function's public metadata (a CNST tag lists its constants).
    Raises ValueError on a file it cannot read"""
    with romfs.open(path, 'rb') as f: b = f.read(1 << 20)
    if b[:4] != b'MTLB' or len(b) < 0x58: raise ValueError(f'{path}: not a Metal library')
    fo, _, po, ps = struct.unpack_from('<QQQQ', b, 0x18)
    def tags(p, end):
        t = {}
        while p + 4 <= end:
            tag = b[p:p + 4]; p += 4
            if tag == b'ENDT': return t
            n = struct.unpack_from('<H', b, p)[0]; p += 2; t[tag] = b[p:p + n]; p += n
        raise ValueError(f'{path}: unterminated tag list')
    try:
        count = struct.unpack_from('<I', b, fo)[0]; p = fo + 4; names = []
        for _ in range(count):   # each entry: its size (counting the size field), then tags
            size = struct.unpack_from('<I', b, p)[0]; names.append(tags(p + 4, p + size)[b'NAME'].rstrip(b'\0').decode()); p += size
        # metal -c + metallib excludes the size word; direct metal -o includes
        # it on current Xcode. Validate the complete section in either format.
        for includes_size in (False, True):
            consts, p = [], po
            try:
                for _ in range(count):
                    size = struct.unpack_from('<I', b, p)[0]; end = p + size + (0 if includes_size else 4)
                    if end > po + ps or end <= p + 4: raise ValueError('metadata bounds')
                    consts.append(b'CNST' in tags(p + 4, end)); p = end
                if p == po + ps: break
            except (struct.error, ValueError): pass
        else: raise ValueError(f'{path}: public metadata does not match the function list')
    except (struct.error, KeyError) as e: raise ValueError(f'{path}: unreadable function list ({e})') from e
    return dict(zip(names, consts))


def plan(lib_dir, chain, pairs, zero, aot=False):
    """The bases the archive holds: [(vertex library, vertex entry, pixel library, pixel entry)], the pairs left to the device (function constants), and counts of the pairs left out"""
    lib_dir = romfs.Path(lib_dir); js, fns, layer = {}, {}, {}
    def refl(key):
        if key not in js:
            try: js[key] = json.loads((lib_dir / f'{key}_b.json').read_bytes())
            except (OSError, ValueError): js[key] = None
        return js[key]
    def fn(lib):
        if lib not in fns:
            try: fns[lib] = functions(lib_dir / f'{lib}.metallib')
            except (OSError, ValueError): fns[lib] = None
        return fns[lib]
    def writes_layer(lib):
        if lib not in layer: layer[lib] = LAYER in (lib_dir / f'{lib}.metallib').read_bytes()
        return layer[lib]
    bases, rest, seen, left = [], [], set(), dict.fromkeys(('reflection', 'stage inputs', 'library', 'layer', 'primitive ID', 'entry'), 0)
    for vk, fk in pairs:
        vj, fj = refl(vk), refl(fk)
        if not vj or not fj or vj.get('chain') != chain or fj.get('chain') != chain or vj.get('mesh_stage'): left['reflection'] += 1; continue
        ventry = vj['entry_z'] if zero and vj.get('entry_z') else vj.get('entry'); fentry = fj.get('entry') or 'main0'
        pull = isinstance(vj.get('pull'), dict)
        if not pull and vj.get('vertex_inputs'): left['stage inputs'] += 1; continue
        if (fj.get('raster') or {}).get('primitive_id'): left['primitive ID'] += 1; continue
        vl, fl = vk + ('_bp' if pull else '_b'), fk + '_b'
        vf, ff = fn(vl), fn(fl)
        if vf is None or ff is None: left['library'] += 1; continue
        layered = writes_layer(vl)
        if layered and not aot: left['layer'] += 1; continue
        if ventry not in vf or fentry not in ff: left['entry'] += 1; continue
        if vf[ventry] or ff[fentry]: rest.append((vk, fk)); continue
        b = (vl, ventry, fl, fentry) + (('layer',) if layered else ())
        if b not in seen: seen.add(b); bases.append(b)
    return bases, rest, left


def compute_keys(paths):
    """The compute shaders of the shader maps (column 3 'compute', column 4 the key), in order, each once"""
    seen, out = set(), []
    for p in paths:
        if not p or not Path(p).is_file(): continue
        for line in Path(p).read_text(encoding='utf-8', errors='replace').split('\n'):
            c = line.split('\t')
            if line.startswith('#') or len(c) < 4 or c[2] != 'compute' or c[3] in seen: continue
            seen.add(c[3]); out.append(c[3])
    return out


def plan_compute(lib_dir, chain, keys):
    """The compute pipelines the archive holds: [(library, entry)], one per compute shader whose library the host would dispatch (a reflection of this chain, the entry in the
    library, no function constants), and counts of the shaders left out. A compute pipeline has no base: the dispatch takes it whole from the archive (nvn_mtl.m cps_make), where
    Metal otherwise compiles it at the shader's first dispatch, on the submit thread"""
    lib_dir = romfs.Path(lib_dir); kernels, left = [], dict.fromkeys(('reflection', 'library', 'entry', 'function constants'), 0)
    for key in keys:
        try: j = json.loads((lib_dir / f'{key}_b.json').read_bytes())
        except (OSError, ValueError): j = None
        if not j or j.get('chain') != chain or j.get('stage') != 'cs': left['reflection'] += 1; continue
        lib, entry = key + '_b', j.get('entry') or 'main0'
        try: fns = functions(lib_dir / f'{lib}.metallib')
        except (OSError, ValueError): left['library'] += 1; continue
        if entry not in fns: left['entry'] += 1; continue
        if fns[entry]: left['function constants'] += 1; continue
        kernels.append((lib, entry))
    return kernels, left


def script(lib_dir, bases):
    """A Metal 4 pipelines script (metal4-pipelines-script(5), the .mtl4-json format metal-tt reads) with one render pipeline descriptor per base"""
    libs, fns, specs, pipes, kernels = {}, {}, {}, [], []
    def fd(lib, entry, constants=None):
        if lib not in libs: libs[lib] = {'label': lib, 'path': str(pso_aot.library_path(lib_dir, lib).resolve())}
        label = f'{lib}.{entry}'
        if label not in fns: fns[label] = {'label': label, 'library': f'lib:{lib}', 'name': entry}
        if constants is None: return f'fnd:{label}'
        specialized = label + '.' + hashlib.sha256(json.dumps(constants, separators=(',', ':')).encode()).hexdigest()[:16]
        specs[specialized] = {'label': specialized, 'function_descriptor': f'fnd:{label}', 'constant_values': [
            {'id_type': 'FunctionConstantIndex', 'id': {'data': index}, 'value_type': 'ConstantBool' if typ == 'bool' else 'ConstantInt', 'value': {'data': int(value)}} for index, typ, value in constants]}
        return f'fnd:{specialized}'
    extra = {}
    for row in bases:
        if isinstance(row, dict):
            name, desc = pso_aot.configuration(row, fd, AOT_ENUMS)
            extra.setdefault(name, []).append(desc); continue
        if len(row) == 2:
            kernels.append({'compute_function_descriptor': fd(*row)}); continue
        vl, ve, fl, fe = row[:4]
        pipes.append({'vertex_function_descriptor': fd(vl, ve), 'fragment_function_descriptor': fd(fl, fe),
                      'color_attachments': [dict.fromkeys(COLOUR, 'Unspecialized') for _ in range(8)],
                      **({'input_primitive_topology': 'Triangle'} if len(row) == 5 else {})})
    pipes.extend(extra.pop('render_pipeline_descriptors', []))
    if kernels: extra.setdefault('compute_pipeline_descriptors', []).extend(kernels)
    return {'libraries': list(libs.values()), 'function_descriptors': dict({'library_function_descriptors': list(fns.values())},
            **({'specialized_function_descriptors': list(specs.values())} if specs else {})),
            'pipeline_descriptors': dict(extra, render_pipeline_descriptors=pipes)}


def write_script(path, configuration):
    """Stream the script to disk beside the previous one (<name>.partial, written again by the next run if this one is killed), which it replaces only when the two differ: an unchanged file keeps its time"""
    part = path.with_name(path.name + '.partial')
    try:
        with part.open('w', encoding='utf-8', newline='\n') as out: json.dump(configuration, out, indent=1)
        if not path.is_file() or not filecmp.cmp(path, part, shallow=False): os.replace(part, path)
    finally: part.unlink(missing_ok=True)


def library_digest(lib_dir, bases):
    """The bytes metal-tt consumes: a profile/chain stamp does not change when the same shaders are rebuilt by another Metal compiler."""
    h = hashlib.sha256()
    names = {lib for row in bases if not isinstance(row, dict) for lib in ((row[0],) if len(row) == 2 else (row[0], row[2]))} | pso_aot.libraries([row for row in bases if isinstance(row, dict)])
    for name in sorted(names):
        h.update(name.encode() + b'\0')
        lib = hashlib.sha256()
        with romfs.open(pso_aot.library_path(lib_dir, name), 'rb') as f:
            while chunk := f.read(1 << 20): lib.update(chunk)
        h.update(lib.digest())
    return h.hexdigest()


def space_needed(bases):   # what metal-tt is let start with, an estimate: its temporary files (TMPDIR, one .airp per base) and the archive (about 41 KB per base at 15,767 bases); Cruis'n Blast's 33,858 bases failed with 366 MB free
    return max(2 << 30, bases * (96 << 10))


def clear_temporaries(work):   # what a failed or killed metal-tt leaves in its TMPDIR (the work folder): translate-*, *.airp, multiple-functions-input-*.metallib
    for f in [*work.glob('translate-*'), *work.glob('*.airp'), *work.glob('multiple-functions-input-*.metallib')]:
        shutil.rmtree(f) if f.is_dir() else f.unlink(missing_ok=True)


def archive_key(configuration, libraries, arch, platform, osmin, toolchain):
    """Identity of metal-tt's inputs, independent of chain labels and library locations.

    The generated configuration includes all entry points and pipeline settings; the
    library digest covers every referenced file's name and bytes. Only absolute
    library paths are replaced: moving identical inputs cannot change the GPU code.
    Version this format if a future input is not represented here. Legacy keys miss
    once; runtime stamps are rewritten even when the compiled archive is reused.
    """
    config = dict(configuration, libraries=[dict(lib, path=lib['label'] + '.metallib') for lib in configuration['libraries']])
    inputs = {'format': 1, 'configuration': config, 'libraries': libraries,
              'arch': arch, 'platform': platform, 'os_min': osmin, 'toolchain': toolchain}
    digest = hashlib.sha256()
    for chunk in json.JSONEncoder(sort_keys=True, separators=(',', ':')).iterencode(inputs):
        digest.update(chunk.encode())
    return digest.hexdigest()


def sdk(platform):
    return 'iphoneos' if platform == 'ios' else 'macosx'


def tool_version(platform):
    r = subprocess.run(['xcrun', '-sdk', sdk(platform), 'metal-tt', '-version'], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'[RED] pso_offline: metal-tt is not available ({(r.stderr or r.stdout).strip()}); install the Metal toolchain: xcodebuild -downloadComponent MetalToolchain')
    return r.stdout.strip().splitlines()[0]


def os_min_default(platform):
    cmd = ['sw_vers', '-productVersion'] if platform == 'macos' else ['xcrun', '-sdk', sdk(platform), '--show-sdk-version']
    v = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    return v.split('.')[0] + '.0'


def archive_os_min(platform, explicit, native):
    if not native: return explicit or os_min_default(platform)
    # MTL4's on-device serializer stamps the running OS major/minor and has no
    # deployment-target option. All metal-tt pieces must use that exact triple.
    runtime = '.'.join(subprocess.check_output(['sw_vers', '-productVersion'], text=True).strip().split('.')[:2])
    if explicit and explicit != runtime:
        raise ValueError(f'native function-constant archives require --os-min {runtime} on this Mac (got {explicit})')
    return runtime


class DescriptorRefused(SystemExit):
    """Metal rejected a linked descriptor, rather than a storage/tool failure."""


def compile_archive(js, part, work, arch, platform, osmin, count):
    """One compiler invocation, with its temporaries on the work volume. Never publish a failed output."""
    part.unlink(missing_ok=True)
    clear_temporaries(work)
    need, free = space_needed(count), shutil.disk_usage(work).free
    if free < need: sys.exit(f'[RED] pso_offline: {free / 2**30:.1f} GB free on the volume of {work}, metal-tt needs about {need / 2**30:.0f} GB for {count} bases: free some space and run again')
    cmd = ['xcrun', '-sdk', sdk(platform), 'metal-tt', '-arch', arch, f'-{platform}-version-min', osmin, str(js), '-o', str(part)]
    log_path = work / f'metal-tt.{arch}.log'
    with log_path.open('w') as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, TMPDIR=str(work)))
    if r.returncode or not part.is_file() or not part.stat().st_size:
        free = shutil.disk_usage(work).free
        clear_temporaries(work); part.unlink(missing_ok=True)
        full = f' ({free / 2**30:.1f} GB free on the volume of {work} when it failed: likely out of disk space)' if free < 1 << 30 else ''
        if not full and 'cannot emit pipeline' in log_path.read_text():
            raise DescriptorRefused(log_path.read_text()[-2000:])
        sys.exit(f'[RED] pso_offline: metal-tt failed for {arch} (exit {r.returncode}){full}: {log_path.read_text()[-2000:]}')


def real_libraries(lib_dir, bases, work):
    """Where metal-tt finds the bases' libraries: it takes file paths, so the libraries of one file get a temporary folder of what this compile reads, which clear_real_libraries removes after it.
    An archive whose key still holds compiles nothing and gets none"""
    if os.path.isdir(lib_dir): return lib_dir
    real = Path(work) / 'libraries'; shutil.rmtree(real, ignore_errors=True); real.mkdir(parents=True)
    names = {lib for row in bases if not isinstance(row, dict) for lib in ((row[0],) if len(row) == 2 else (row[0], row[2]))}
    names |= pso_aot.libraries([row for row in bases if isinstance(row, dict)])
    for name in sorted(n for n in names if not n.startswith('host:')):
        with romfs.open(os.path.join(lib_dir, f'{name}.metallib'), 'rb') as f, open(real / f'{name}.metallib', 'wb') as o: shutil.copyfileobj(f, o)
    return real


def clear_real_libraries(work): shutil.rmtree(Path(work) / 'libraries', ignore_errors=True)


def compile_batch(lib_dir, bases, work, arch, platform, osmin, toolchain):
    """Cache one bounded group by its actual libraries and descriptors; also used for an isolated pilot."""
    work.mkdir(parents=True, exist_ok=True)
    configuration = script(lib_dir, bases)
    js = work / 'bases.mtl4-json'; write_script(js, configuration)
    key = archive_key(configuration, library_digest(lib_dir, bases), arch, platform, osmin, toolchain)
    native = any(pso_aot.has_constants(row) for row in bases)
    if native:
        if platform != 'macos' or not AOT_HOST or not AOT_SHADER_MAP:
            raise ValueError('function-constant archives require the local Mac --host and --shader-map (or --game)')
        key = hashlib.sha256((key + hashlib.sha256(Path(AOT_HOST).read_bytes()).hexdigest()).encode()).hexdigest()
    del configuration
    dst, kf = work / f'{arch}.mtl4a', work / f'key.{arch}'
    if dst.is_file() and dst.stat().st_size and kf.is_file() and kf.read_text().strip() == key: return dst, True
    refused = work / f'refused.{arch}.json'
    if refused.is_file():
        saved = json.loads(refused.read_text())
        if saved['key'] == key: raise DescriptorRefused(saved['error'])
    kf.unlink(missing_ok=True)
    part = work / f'{arch}.mtl4a.partial'
    if native:
        # metal-tt has refused specialized library functions on this toolchain
        # (private metadata/unresolved constants). Capture the exact MTL4 API
        # descriptor at build time on its target Mac instead. No game is loaded.
        rows = [row for b in bases for row in ([b] if isinstance(b, dict) else pso_aot.base_rows([b], shader_lib.name_of(lib_dir)[2:]))]
        source = work / 'exact.json'; source.write_text(json.dumps(rows, sort_keys=True) + '\n')
        env = pso_aot.tool_env(lib_dir, AOT_SHADER_MAP, 'compile', source.resolve(), part.resolve(), AOT_ZERO, arch)
        log = work / f'native-compile.{arch}.log'
        part.unlink(missing_ok=True)
        with log.open('w') as f: r = subprocess.run([str(Path(AOT_HOST).resolve())], env=env, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode == 2:
            audit = Path(str(part) + '.refused.json')
            raise DescriptorRefused(audit.read_text() if audit.is_file() else log.read_text()[-2000:])
        if r.returncode or not part.is_file():
            raise RuntimeError(f'exact native archive failed (no states dropped): {log}')
        os.replace(part, dst); kf.write_text(key + '\n'); return dst, False
    write_script(js, script(real_libraries(lib_dir, bases, work), bases))
    try:
        compile_archive(js, part, work, arch, platform, osmin, len(bases))
    except DescriptorRefused as error:
        tmp = refused.with_suffix('.partial')
        tmp.write_text(json.dumps({'key': key, 'error': str(error)}))
        os.replace(tmp, refused)
        raise
    finally:
        clear_real_libraries(work)
    refused.unlink(missing_ok=True)
    os.replace(part, dst); kf.write_text(key + '\n')
    return dst, False


def compile_aot_batch(lib_dir, bases, work, arch, platform, osmin, toolchain):
    """Bisect only actual descriptor refusals; keep every successful child cached."""
    try:
        piece, reused = compile_batch(lib_dir, bases, work, arch, platform, osmin, toolchain)
        return [piece], []
    except DescriptorRefused as error:
        if len(bases) == 1:
            print(f'[RED] AOT descriptor refused: {json.dumps(bases[0], sort_keys=True)}: {error}', flush=True)
            return [], [{'descriptor': bases[0], 'error': str(error)}]
        middle = len(bases) // 2
        pieces, rejected = [], []
        for name, group in (('left', bases[:middle]), ('right', bases[middle:])):
            ready, bad = compile_aot_batch(lib_dir, group, work / name, arch, platform, osmin, toolchain)
            pieces.extend(ready); rejected.extend(bad)
        return pieces, rejected


def compile_batches(lib_dir, bases, work, part, arch, platform, osmin, toolchain, batch_size, aot=False, rejected=None):
    """Limit compiler input size, then combine every completed group into the size-bounded archives.

    This bounds input count, not memory: a single pipeline can still exceed Apple's compiler resources.
    On M2, merged archives passed archive-only lookups of two synthetic pipelines and all 32,864 Odyssey bases.
    Other workloads and compiler versions can have different resource use.
    """
    total = (len(bases) + batch_size - 1) // batch_size
    for old in (work / f'batches.{arch}').glob('[0-9]*'):   # the groups of a longer list than this one
        if int(old.name) > total: shutil.rmtree(old)
    workers = int(os.environ.get('DM_PSO_J', '1'))
    pack_threads = int(os.environ.get('DM_METAL_PACK_THREADS', '1'))
    if workers < 1 or pack_threads < 1: raise ValueError('archive worker counts must be positive')
    def build_group(item):
        index, start = item
        group = bases[start:start + batch_size]
        print(f'pso_offline: {arch}: batch {index}/{total}: {len(group)} bases, compiling or checking cache', flush=True)
        folder = work / f'batches.{arch}' / f'{index:05d}'
        if aot:
            ready, bad = compile_aot_batch(lib_dir, group, folder, arch, platform, osmin, toolchain)
            print(f'pso_offline: {arch}: batch {index}/{total}: ready, {len(bad)} refused descriptors', flush=True)
            return ready, bad
        piece, reused = compile_batch(lib_dir, group, folder, arch, platform, osmin, toolchain)
        print(f'pso_offline: {arch}: batch {index}/{total}: ready ({"reused" if reused else "compiled"})', flush=True)
        return [piece], []
    groups = enumerate(range(0, len(bases), batch_size), 1)
    if workers == 1:
        results = list(map(build_group, groups))
    else:
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(build_group, groups))
    pieces = [piece for ready, bad in results for piece in ready]
    if rejected is not None: rejected.extend(item for ready, bad in results for item in bad)
    if not pieces: raise SystemExit('[RED] pso_offline: every descriptor was refused')
    packed, size = [[]], 0
    for piece in pieces:
        n = piece.stat().st_size
        if n > PACK_LIMIT: raise SystemExit(f'[RED] pso_offline: single batch exceeds archive size limit: {piece}')
        if packed[-1] and size + n > PACK_LIMIT:
            packed.append([]); size = 0
        packed[-1].append(piece); size += n
    need, free = max(2 << 30, sum(p.stat().st_size for p in pieces)), shutil.disk_usage(work).free
    if free < need: sys.exit(f'[RED] pso_offline: {free / 2**30:.1f} GB free before merging; need at least {need / 2**30:.1f} GB')
    outputs = [part if i == 0 else part.with_name(f'{arch}.{i}.mtl4a.partial') for i in range(len(packed))]
    try:
        for i, (group, output) in enumerate(zip(packed, outputs)):
            output.unlink(missing_ok=True)
            print(f'pso_offline: {arch}: merging {len(group)} pieces into part {i + 1}/{len(packed)}', flush=True)
            cmd = ['xcrun', '-sdk', sdk(platform), 'metal-pack', '-nthreads', str(pack_threads), *map(str, group), '-o', str(output)]
            log_path = work / f'metal-pack.{arch}.{i}.log'
            with log_path.open('w') as log:
                r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, TMPDIR=str(work)))
            if r.returncode or not output.is_file() or not 0 < output.stat().st_size <= PACK_LIMIT:
                sys.exit(f'[RED] pso_offline: metal-pack failed or exceeded size limit for {arch} part {i} (exit {r.returncode}): {log_path.read_text()[-2000:]}')
    except BaseException:
        for output in outputs: output.unlink(missing_ok=True)
        raise
    return outputs


def main(argv=None):
    ap = argparse.ArgumentParser(description='Build the pipeline archive of a game\'s shader pairs offline (metal-tt)')
    ap.add_argument('--msl', required=True, help='the shader libraries, b-<chain version> (with their reflection <key>_b.json)')
    ap.add_argument('--game', help='the game profile: its pair lists and depth_mode key')
    ap.add_argument('--pairs', action='append', help='shader_pairs.tsv, then pso_pairs.tsv (missing files are skipped; default: the profile\'s)')
    ap.add_argument('--compute', action='append', help='shader_map.tsv: every compute shader in it gets its pipeline in the archive (default: the profile\'s map with --game; none without)')
    ap.add_argument('--out', required=True, help='the folder the app bundles (archives and stamp)')
    ap.add_argument('--work', required=True, help='the script, keys and logs')
    ap.add_argument('--gpu', default='g18p', help='GPU architectures, comma-separated (default g18p)')
    ap.add_argument('--depth', choices=('gl', 'zero'), help='the game\'s NVN depth mode (default: the profile\'s depth_mode, else gl: near = -w)')
    ap.add_argument('--platform', choices=('ios', 'macos'), default='ios')
    ap.add_argument('--os-min', help='minimum OS of the archives (default: iOS, the SDK\'s major version; macOS, this Mac\'s)')
    ap.add_argument('--script-only', action='store_true', help='write the script and the stamp, run no metal-tt')
    ap.add_argument('--batch-size', type=int, default=BATCH, help=f'compile groups of at most N bases and merge with metal-pack, when there are more (default {BATCH}; 0: one compiler invocation)')
    ap.add_argument('--aot', action='store_true', default=os.getenv('DM_AOT') == '1', help='expanded compute/mesh/layer/helper coverage and exact learned descriptors (opt-in)')
    ap.add_argument('--seen', action='append', default=[], help='per-game pso_seen.jsonl, repeatable; stale entries fail visibly')
    ap.add_argument('--user', action='append', default=[], help='legacy pso_user.tsv, decoded by this build\'s --host before archive planning')
    ap.add_argument('--host', help='matching source-built Mac dmhost; import and exact constant archive tool modes never load a game')
    ap.add_argument('--rebase-seen', action='store_true', help='explicitly carry observed final state to this chain after function/library validation')
    ap.add_argument('--shader-map', help='program-source evidence for native mesh combinations (default: profile shader_map.tsv)')
    a = ap.parse_args(argv)
    if (a.seen or a.user or a.rebase_seen) and not a.aot: ap.error('--seen/--user/--rebase-seen require --aot')
    if a.batch_size < 0: ap.error('--batch-size must be zero or positive')
    if a.game:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'games')); import game
        g = game.load(a.game)
        a.pairs = a.pairs or [str(g.table('shader_pairs.tsv')), str(g.table('pso_pairs.tsv'))]
        a.compute = a.compute or [str(g.table('shader_map.tsv'))]
        a.depth = a.depth or g.get('depth_mode', 'gl')
        a.shader_map = a.shader_map or str(g.table('shader_map.tsv'))
        if a.depth not in ('gl', 'zero'): sys.exit(f'[RED] pso_offline: {g.id}: depth_mode must be gl or zero: {a.depth}')
    if not a.pairs: sys.exit('[RED] pso_offline: no pair lists (--pairs or --game)')
    a.depth = a.depth or 'gl'
    lib_dir, out, work = shader_lib.view(a.msl), Path(a.out), Path(a.work)
    chain = shader_lib.name_of(lib_dir)[2:] if shader_lib.name_of(lib_dir).startswith('b-') else sys.exit(f'[RED] pso_offline: {lib_dir} is not a b-<chain version> folder')
    archs = sorted({arch_name(x) for x in a.gpu.split(',') if x.strip()})
    if not archs: sys.exit('[RED] pso_offline: no GPU architecture (--gpu)')
    text = pair_text(a.pairs)
    if not text: sys.exit(f'[RED] pso_offline: no pair list ({", ".join(a.pairs)})')
    zero = a.depth == 'zero'
    t0 = time.time()
    pairs = read_pairs(text)
    bases, rest, left = plan(lib_dir, chain, pairs, zero, aot=a.aot)
    kernels, cleft = plan_compute(lib_dir, chain, compute_keys(a.compute or []))
    nrender = len(bases); bases = bases + kernels   # one list for the script, the digest and the batches: a kernel is a 2-tuple, a base a 4-tuple
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    if a.aot:
        global AOT_ENUMS, AOT_HOST, AOT_SHADER_MAP, AOT_ZERO
        AOT_ENUMS = pso_aot.enums(a.platform)
        AOT_HOST, AOT_SHADER_MAP, AOT_ZERO = a.host, a.shader_map, zero
        host_dir = pso_aot.prepare_helpers(work, a.platform)
        learned = a.seen or ([os.environ['DM_PSO_SEEN']] if os.environ.get('DM_PSO_SEEN') else [])
        imported = pso_aot.import_user(a.host, lib_dir, a.shader_map, a.user, work, zero) if a.user else []
        rows, gaps = pso_aot.plan(lib_dir, chain, [*learned, *imported], functions, host_dir, a.shader_map, zero, a.rebase_seen)
        refused_imports = [{**row, 'source': n} for n, path in enumerate(imported) for row in json.loads(Path(str(path) + '.refused.json').read_text())]
        (out / 'aot-import-refused.json').write_text(json.dumps(refused_imports, indent=2) + '\n')
        gaps['stale native rows'] = sum(r['stale'] for r in refused_imports)
        gaps['unreplayable native rows'] = sum(not r['stale'] for r in refused_imports)
        if os.environ.get('DM_AOT_STRICT') == '1' and gaps['unreplayable native rows']:
            raise SystemExit('[RED] strict AOT: native states could not be replayed; see aot-import-refused.json (no app should be packed)')
        if a.user:
            profile = Path(a.shader_map).with_name('pso_manifest.tsv') if a.shader_map else None
            (out / 'pso_manifest.tsv').write_text(pso_aot.manifest(profile, [str(path) + '.manifest.tsv' for path in imported]))
        else: (out / 'pso_manifest.tsv').unlink(missing_ok=True)
        inventory = pso_aot.base_rows(bases, chain) + rows
        bases.extend(rows)
        (out / 'aot.json').write_text(json.dumps(inventory, sort_keys=True, separators=(',', ':')) + '\n')
        classes = {k: sum(r['class'] == k for r in rows) for k in ('compute', 'mesh', 'render')}
        report = {'format': 1, 'chain': chain, 'classes': classes, 'gaps': dict(gaps, **left), 'constant_pairs': len(rest),
                  'layer_bases': sum(isinstance(b, tuple) and len(b) == 5 for b in bases),
                  'unknown': ['unobserved final render/mesh state', 'unobserved function-constant variants', 'diagnostic source', 'helper render state until learned'],
                  'seen_files': len(learned), 'user_files': len(a.user), 'rebased_seen': a.rebase_seen,
                  'constant_descriptors': sum(pso_aot.has_constants(row) for row in rows),
                  'render_bases': len(inventory) - len(rows), 'exact_learned_render': sum(r['class'] == 'render' and not r.get('base') for r in rows),
                  'complete': False, 'archive_verified': False}
        (out / 'aot-preflight.json').write_text(json.dumps(report, indent=2) + '\n')
    else:
        for name in ('aot.json', 'aot-preflight.json', 'aot-import-refused.json', 'pso_manifest.tsv'): (out / name).unlink(missing_ok=True)
    js = work / 'bases.mtl4-json'   # metal-tt takes the format from the extension: .mtl4-json is Metal 4's (.mtlp-json is the Metal 3 format)
    configuration = script(lib_dir, bases)
    write_script(js, configuration)
    st = stamp(chain, zero, text)
    print(f'pso_offline: {len(pairs)} pairs: {nrender} bases, {len(rest)} left to the device (function constants), left out as the host leaves them: '
          + ', '.join(f'{k} {v}' for k, v in left.items()) + f'; {len(kernels)} compute pipelines, left out: ' + ', '.join(f'{k} {v}' for k, v in cleft.items()) + f' ({time.time() - t0:.1f} s)')
    if a.script_only: (out / 'prebuilt.tsv').write_text(st); return 0
    if pairs and not bases and not rest: sys.exit('[RED] pso_offline: no base to build')   # pairs, but the host would leave out every one: wrong or missing libraries
    if not pairs: print('pso_offline: no pairs (only a header): nothing to build, no archive')   # a profile whose split found no pair (GitHub issue #338)
    if not bases: archs = []   # no pair, or every eligible pair needs device specialization; clear old archives and still write the stamp and the remainder list
    native = any(pso_aot.has_constants(row) for row in bases)
    osmin = archive_os_min(a.platform, a.os_min, native); tv = tool_version(a.platform) if bases else 'not used (function constants only)'
    libraries = library_digest(lib_dir, bases)
    keys = {arch: archive_key(configuration, libraries, arch, a.platform, osmin, tv) for arch in archs}
    if any(pso_aot.has_constants(row) for row in bases):
        if not a.host or not a.shader_map or a.platform != 'macos': raise ValueError('captured function constants require --platform macos --host --shader-map (or --game)')
        compiler = hashlib.sha256(Path(a.host).read_bytes()).hexdigest()
        keys = {arch: hashlib.sha256((key + compiler).encode()).hexdigest() for arch, key in keys.items()}
    del configuration   # the compiler reads the script from disk
    rejected_archs = {}
    for arch, key in keys.items():
        dst, kf = out / f'{arch}.mtl4a', work / f'key.{arch}'
        rejected_file = out / f'aot-refused.{arch}.json'
        manifest = work / f'parts.{arch}.json'
        saved = json.loads(manifest.read_text()) if manifest.is_file() else {}
        complete = saved.get('limit') == PACK_LIMIT and bool(saved.get('parts')) and all((out / name).is_file() and (out / name).stat().st_size == size for name, size in saved['parts'].items())
        if complete and dst.is_file() and kf.is_file() and kf.read_text().strip() == key:
            rejected_archs[arch] = json.loads(rejected_file.read_text()) if rejected_file.is_file() else []
            for old in out.glob(f'{arch}*.mtl4a'):   # this branch publishes one archive per architecture, so leftover split parts are obsolete
                if old.stem.split('.')[0] == arch and old != dst: old.unlink()
            print(f'pso_offline: {arch}: reused ({dst.stat().st_size / 2**20:.0f} MB)'); continue
        kf.unlink(missing_ok=True)
        (out / 'prebuilt.tsv').unlink(missing_ok=True)
        for old in out.glob(f'{arch}*.mtl4a'):
            if old.stem.split('.')[0] == arch: old.unlink()
        part = work / f'{arch}.mtl4a.partial'; part.unlink(missing_ok=True)
        t1 = time.time(); print(f'pso_offline: {arch}: metal-tt, {len(bases)} bases (minutes) ...', flush=True)
        refused_rows = []
        if a.aot or a.batch_size and len(bases) > a.batch_size:
            parts = compile_batches(lib_dir, bases, work, part, arch, a.platform, osmin, tv, a.batch_size or len(bases), a.aot, refused_rows)
        else:
            write_script(js, script(real_libraries(lib_dir, bases, work), bases))
            compile_archive(js, part, work, arch, a.platform, osmin, len(bases))
            clear_real_libraries(work)
            parts = [part]
        published = {}
        for piece in parts:
            target = out / piece.name.removesuffix('.partial')
            os.replace(piece, target)
            published[target.name] = target.stat().st_size
        manifest.write_text(json.dumps({'limit': PACK_LIMIT, 'parts': published}) + '\n')
        rejected_tmp = rejected_file.with_suffix('.partial')
        rejected_tmp.write_text(json.dumps(refused_rows, indent=2) + '\n')
        os.replace(rejected_tmp, rejected_file)
        kf.write_text(key + '\n')
        rejected_archs[arch] = refused_rows
        print(f'pso_offline: {arch}: {dst.stat().st_size / 2**20:.0f} MB in {time.time() - t1:.0f} s')
    if a.aot:
        def identity(row): return json.dumps(row, sort_keys=True, separators=(',', ':'))
        rejected_rows = []
        for refused in rejected_archs.values():
            for item in refused:
                row = item['descriptor']
                rejected_rows.extend([row] if isinstance(row, dict) else pso_aot.base_rows([tuple(row)], chain))
        denied = {identity(row) for row in rejected_rows}
        kept = [row for row in inventory if identity(row) not in denied]
        (out / 'aot.json').write_text(json.dumps(kept, sort_keys=True, separators=(',', ':')) + '\n')
        report['refused_descriptors'] = rejected_archs
        report['gaps']['compiler-refused descriptors'] = len(denied)
        report['classes'] = {k: sum(row['class'] == k and not (k == 'render' and row.get('base')) for row in kept) for k in ('compute', 'mesh', 'render')}
        report['layer_bases'] = sum(row['class'] == 'render' and row.get('base', False) and row.get('topology') == 3 for row in kept)
        report['render_bases'] = sum(row['class'] == 'render' and row.get('base', False) for row in kept)
        (out / 'aot-preflight.json').write_text(json.dumps(report, indent=2) + '\n')
        if os.environ.get('DM_AOT_STRICT') == '1' and any(not row.get('base') and identity(row) in denied for row in rows):
            raise SystemExit('[RED] strict AOT: an exact descriptor was refused; see aot-preflight.json (no app should be packed)')
    for f in out.glob('*.mtl4a'):   # architectures no longer asked for
        if f.stem.split('.')[0] not in archs: f.unlink()
    (out / 'prebuilt.tsv').write_text(st)
    rp = out / 'rest_pairs.tsv'
    if rest: rp.write_text(''.join(f'{v}\t{f}\n' for v, f in rest))
    else: rp.unlink(missing_ok=True)
    (out / 'archive.tsv').write_text(f'# the pipeline archive made offline (dm/gfx/tools/pso_offline.py); the host reads prebuilt.tsv for coverage and checks the parts listed here\narch\t{" ".join(archs)}\n'
                                     f'platform\t{a.platform}\t{osmin}\ntoolchain\t{tv}\nbases\t{nrender - (len(denied) if a.aot else 0)}\ncompute\t{len(kernels)}\nrest\t{len(rest)}\n')
    with (out / 'archive.tsv').open('a') as metadata:
        for f in sorted(out.glob('*.mtl4a')): metadata.write(f'part\t{f.name}\t{f.stat().st_size}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

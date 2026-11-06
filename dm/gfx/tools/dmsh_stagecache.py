"""Optional intermediate shader cache. Final chain/ABI validation stays in dmsh_build.

One SQLite database holds dependency keys and compressed, content-addressed outputs.
No-op passes share their output object. Transactions publish complete entries only.
"""
import ast
import base64
import collections
import copy
import functools
import hashlib
import inspect
import json
from pathlib import Path
import re
import sqlite3
import shutil
import symtable
import sys
import textwrap
import threading
import types
import zlib
from typing import Any, Callable, ParamSpec, TypeVar

import dmsh_chain

P = ParamSpec('P')
T = TypeVar('T')
FORMAT = 'dmsh-stages-1'
DATA = {'dmsh_abi': ('../nvn/dmsh_abi.h',), 'dmsh_pull': ('dmsh_pull.metal',)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    if isinstance(value, bytes): return {'bytes': base64.b64encode(value).decode('ascii')}
    if isinstance(value, tuple): return {'tuple': [encode(v) for v in value]}
    if isinstance(value, dict): return {'dict': [[encode(k), encode(v)] for k, v in value.items()]}
    if isinstance(value, list): return [encode(v) for v in value]
    return value


def decode(value):
    if isinstance(value, list): return [decode(v) for v in value]
    if isinstance(value, dict):
        if 'bytes' in value: return base64.b64decode(value['bytes'], validate=True)
        if 'tuple' in value: return tuple(decode(v) for v in value['tuple'])
        return {decode(k): decode(v) for k, v in value['dict']}
    return value


def dump(value):
    return json.dumps(encode(value), separators=(',', ':'), ensure_ascii=True).encode()


@functools.lru_cache(64)
def text_sha(text):
    return sha(text.encode())


def input_key(value):
    # Hash large sources once across no-op passes rather than JSON-escaping them
    # in every dependency key. Preserve argument types and dictionary ordering.
    if isinstance(value, str): return ('str', text_sha(value))
    if isinstance(value, bytes): return ('bytes', sha(value))
    if isinstance(value, dict): return ('dict', [(input_key(k), input_key(v)) for k, v in value.items()])
    if isinstance(value, tuple): return ('tuple', [input_key(v) for v in value])
    if isinstance(value, list): return ('list', [input_key(v) for v in value])
    return value


@functools.lru_cache(None)
def module_code(path):
    """Hash every local Python import recursively, including imports inside functions."""
    seen, pieces = set(), []
    def visit(p):
        p = Path(p).resolve()
        if p in seen: return
        seen.add(p)
        source = p.read_text()
        pieces.append((p.name, dmsh_chain.code_form(source)))
        for data in DATA.get(p.stem, ()):
            q = p.parent / data
            pieces.append((data, q.read_bytes()))
        for n in ast.walk(ast.parse(source)):
            if isinstance(n, ast.Call) and (getattr(n.func, 'id', '') == '__import__' or getattr(n.func, 'attr', '') == 'import_module'):
                raise ValueError(f'dynamic Python dependency in {p.name}')
            imports = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ''] if isinstance(n, ast.ImportFrom) else []
            for name in imports:
                q = p.parent / (name.replace('.', '/') + '.py')
                if q.is_file(): visit(q)
                elif name.split('.')[0] not in sys.stdlib_module_names:
                    raise ValueError(f'undeclared Python dependency {name} in {p.name}')
    visit(path)
    return sha(dump(pieces))


@functools.lru_cache(None)
def function_code(fn):
    """Inline passes hash their function, referenced helpers, constants and local modules.

    Unsupported global state fails closed. File/environment inputs belong in arguments;
    only pure transforms may use Cache.call.
    """
    if fn.__closure__: raise ValueError(f'uncacheable closure {fn.__name__}')
    seen, pieces = set(), []
    def visit(f):
        if f in seen: return
        if f.__closure__: raise ValueError(f'uncacheable closure {f.__name__}')
        seen.add(f)
        source = textwrap.dedent(inspect.getsource(f))
        pieces.append((f.__name__, dmsh_chain.code_form(source)))
        def globals_in(table):
            return {s.get_name() for s in table.get_symbols() if s.is_global() and s.is_referenced()} | set().union(*(globals_in(c) for c in table.get_children()))
        names = globals_in(symtable.symtable(source, '<pass>', 'exec'))
        for name in sorted(names):
            if name not in f.__globals__: continue  # builtins
            v = f.__globals__[name]
            if inspect.isfunction(v): visit(v)
            elif isinstance(v, types.ModuleType):
                p = getattr(v, '__file__', None)
                if p and Path(p).parent == Path(dmsh_chain.__file__).parent:
                    pieces.append((name, module_code(p)))
                elif v.__name__.split('.')[0] not in sys.stdlib_module_names:
                    raise ValueError(f'uncacheable module {v.__name__}')
            elif isinstance(v, re.Pattern): pieces.append((name, v.pattern, v.flags))
            elif isinstance(v, (str, int, float, bool, bytes, tuple, list, dict, type(None))): pieces.append((name, v))
            else: raise ValueError(f'uncacheable global {name} in {f.__name__}')
    # A module pass includes its whole module and transitive imports. Inline build
    # functions use the smaller symbol closure so unrelated passes remain reusable.
    if Path(inspect.getfile(fn)).name != 'dmsh_build.py':
        return module_code(inspect.getfile(fn))
    visit(fn)
    return sha(dump(pieces))


def tool_code(executable, directory=False):
    p = Path(shutil.which(executable) or executable).resolve()
    files = sorted(q for q in p.parent.rglob('*') if q.is_file()) if directory else [p]
    return sha(dump([(str(q.relative_to(p.parent)), sha(q.read_bytes())) for q in files]))


class Cache:
    def __init__(self, root, abi):
        root = Path(root); root.mkdir(parents=True, exist_ok=True)
        self.path = root / ('v1-' + sha(abi) + '.sqlite3')
        self.local = threading.local()
        self.stats, self.lock = collections.Counter(), threading.Lock()
        db = self.db()
        db.executescript('CREATE TABLE IF NOT EXISTS objects (digest TEXT PRIMARY KEY, data BLOB NOT NULL);'
                         'CREATE TABLE IF NOT EXISTS entries (key TEXT PRIMARY KEY, digest TEXT NOT NULL);')

    def db(self):
        if not hasattr(self.local, 'db'):
            db = sqlite3.connect(self.path, timeout=60)
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA synchronous=NORMAL')
            self.local.db = db
            self.local.objects = collections.OrderedDict()
        return self.local.db

    def key(self, stage, dependency, inputs):
        return sha(dump((FORMAT, sys.version, stage, dependency, input_key(inputs))))

    def get(self, stage, key) -> Any:
        db = self.db()
        row = db.execute('SELECT digest FROM entries WHERE key=?', (key,)).fetchone()
        value = None
        if row:
            digest = row[0]
            if digest in self.local.objects:
                value = self.local.objects[digest]
                self.local.objects.move_to_end(digest)
            else:
                blob = db.execute('SELECT data FROM objects WHERE digest=?', (digest,)).fetchone()
                if blob:
                    try:
                        data = zlib.decompress(blob[0])
                        if sha(data) == digest:
                            value = decode(json.loads(data))
                            self.remember(digest, value)
                    except (ValueError, KeyError, TypeError, zlib.error): pass
        with self.lock: self.stats[stage, 'hit' if value is not None else 'miss'] += 1
        return copy.deepcopy(value)

    def remember(self, digest, value):
        self.local.objects[digest] = copy.deepcopy(value)
        if len(self.local.objects) > 32: self.local.objects.popitem(last=False)

    def put(self, key, value):
        data = dump(value); digest = sha(data)
        db = self.db()
        with db:
            if digest not in self.local.objects:
                db.execute('INSERT INTO objects VALUES (?, ?) ON CONFLICT(digest) DO UPDATE SET data=excluded.data', (digest, zlib.compress(data)))
            db.execute('INSERT OR REPLACE INTO entries VALUES (?, ?)', (key, digest))
        self.remember(digest, value)

    def call(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        stage = fn.__module__ + '.' + fn.__name__
        key = self.key(stage, function_code(fn), (args, kwargs))
        found = self.get(stage, key)
        if found is not None: return found[0]
        result = fn(*args, **kwargs)
        self.put(key, (result,))
        return result

    def translation_key(self, job, translator):
        return self.key('translate', translator, ({k: v for k, v in job.items() if k != 'code'}, Path(job['code']).read_bytes()))

    def translation(self, job, work, translator, publish=False):
        key = self.translation_key(job, translator)
        suffixes = ['.spv', '.res.json'] + (['.reader.spv'] if 'geometry_topology' in job else [])
        paths = [Path(work) / (job['key'] + s) for s in suffixes]
        if publish:
            if all(p.is_file() for p in paths): self.put(key, tuple(p.read_bytes() for p in paths))
            return False
        found = self.get('translate', key)
        if found is None: return False
        for p, data in zip(paths, found): p.write_bytes(data)
        return True

    def cross(self, spv, flags, converter, run):
        key = self.key('cross', converter, (Path(spv).read_bytes(), flags))
        found = self.get('cross', key)
        if found is not None: return found[0]
        result = run()
        if result.returncode: return result
        self.put(key, (result.stdout,))
        return result.stdout

    def summary(self):
        return 'stage cache: ' + '; '.join(f'{s} {self.stats[s, "hit"]} hit, {self.stats[s, "miss"]} miss' for s in sorted({s for s, _ in self.stats}))

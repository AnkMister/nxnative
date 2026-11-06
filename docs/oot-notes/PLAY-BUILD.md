# Ocarina community play build

`oot-play-1444` follows the latest upstream Ocarina implementation, including
`b1d7c707`, `6121fd75` and the movie decoder worker in `75c1a8cf`, through `d928699b`. It also includes opt-in #1456, #1459 and #1461.
The profile tables and overlapping shader fixes come from upstream. The
community additions retain serial-held ownership, guarded upload caches,
optional BC targets, pool placement/retirement, GPU safety, pipeline learning
and optional HDR. See [FLAGS](FLAGS.md) for the selected defaults.

Upstream reports a locked 60 fps in Kokiri Forest at 1536x864 internal
resolution on its tested Mac. That is not a measurement of this fork or an M4
Max. Its pool-read marks, depth-reader classification, segment submission and
mapped archives are retained. No frame-step patch is needed. Use
`DM_FPS_TARGET=0`, `DM_PRESENT_LINK=2`, `DM_PRESENT_HZ=60`,
`DM_PRESENT_INTERVAL=game` and `DM_FOCUS_KEEP=1`. A 120 Hz screen repeats each
60 fps frame twice; it does not force 4K internal rendering or 120 game fps.

## Build

Use the locally rebuilt translator and its matching lock/header. Never use a
PR-shipped DLL. The full shader map must be built: `--no-seen-shaders`.
The ready script is kept beside the output, outside this repository:

```sh
"$HOME/Documents/Crypt/Gaming-rea/_work/games/oot-play-1444/run-build.sh"
```

It uses the existing uv Python, `J=16`, `MAKEFLAGS=-j16`, the registered game
profile, a `.noindex` work directory, and the output app under that same
`oot-play-1444` folder. Its full command is:

```sh
J=16 MAKEFLAGS=-j16 python scripts/build_ipa_from_nsp.py "$NSP" \
  --platform mac-app --progress lines --no-seen-shaders --no-heap-check \
  --work-dir "$RUN_ROOT/0400486024DEC000_build.noindex" \
  --out "$RUN_ROOT/The Legend of Zelda - Ocarina of Time.app" \
  --env-file "$RUN_ROOT/env.txt"
```

The script defines `NSP`, `RUN_ROOT`, tool paths and the complete build
environment. It refuses to start while dmhost is running. The integration task starts it only after the integrated checks pass.

The prebuild consumes the deduplicated native census from session2-0120,
session1 and the live save directory, copied after the game exited. The saved
union has 12,176 rows: 9,572 shader loads, 2,198 render states, 341 compute
pipelines and 65 mesh states. Four JSON descriptors are also included. Snapshot
hashes and source paths are recorded beside the script in `pipeline-inputs`.
An external derived profile adds the one observed readable-tile request
(`1e38b4a840f89d93`) without changing upstream source tables. Its shader input
stamp is `01f3dfa63e7c`; the default chain remains `64e85bd187b5`.
Offline AOT is enabled for packing; runtime AOT remains disabled. Accepted
native rows also seed startup preparation. Refused states are audited and are
not proof of complete archive coverage.

## Play and A/B

The output folder contains `env.txt`, `env-A.txt` and `env-B.txt`. A/B files
differ only in `DM_NVN_BCRT`: A is `0`, B is `1`. BCRT is new lossy BC1/BC4
decode/render/re-encode work, absent from the pinned PR1444 source. Keep it off
for the reference build. Its GPU fixture does not establish game image parity.
Compare the Deku Tree pool at the same save and camera, including reflected
posts, black regions, terrain texture detail and frame pacing.

Runtime uses `DM_AOT=0`, `DM_AOT_STRICT=0`, `DM_PSO_LEARN=1`,
`DM_NVN_SERIAL_HELD=1`, `DM_NVN_P1444_STUTTER=1`, `DM_SAFE_GPU=1`
and `DM_GPU_LOST_STOP=1` and `DM_PSO_WORKERS=1`. Native mesh prediction preserves every draw. A cold
pipeline can still wait when its exact worker result is not ready.

Pool placement, destructive guest texture release, alias retirement, copy-state
experiments and HDR remain off for this reference. Keep the game upscaler,
full render scale, SDR and stock internal resolution. Apple10 tensor options
stay off on the M4 Max's Apple9 GPU.

The UI merge shader `9b310b3349825e9a` explicitly samples a 2D array in SASS.
Upstream identifies the 3D binding warning as an inactive branch. No forced 3D
fact is added. The upstream exposure CAS and gather-offset fixes replace the
earlier visual hypotheses.

No game launch or visual acceptance is performed by this integration task.

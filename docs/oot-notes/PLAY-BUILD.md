# Recommended Ocarina play build

The reviewed visual and stable replacements are integrated. The Float16/integer
selector, watchdog snapshot and auxiliary residency races are repaired.
`DM_SAFE_GPU=1` is restored in the recommended play environment.

**Offline pipeline coverage is still an acceptance gate.** oot-aot is integrated
with expanded archives, startup prewarm, exact descriptor learning and counters.
No variant is a finished play package until the no-runtime-compilation rule is
verified. Branch selection follows the integrated checks recorded below.

This recipe enables correctness and stability. Performance experiments stay off.
It describes the parent's later build; this integration did not run a game, full
shader build or shader-map extraction. Do not modify the protected baseline
checkout or `${OOT_READONLY_GAME_ROOT}/`.

## Split, rewrite and shader-build environment

**No runtime shader compilation. Everything is ahead of time; lazy shaders
stay off.** Build the entire shader map, with `SEEN_SHADERS=False` /
`--no-seen-shaders`; do not enable any future lazy-shader option.

Use an independent writable game build/output root on the NSP drive. Use this
branch's bundled translator and matching tool lock, not a PR-shipped binary.
Set these consistently for shader splitting, module rewriting and shader building:

```sh
export GAME=0400486024DEC000 DM_GAME=0400486024DEC000
export DMSH_OOT_VISUAL=1
export DM_AOT=1 DM_AOT_STRICT=1
export DMSH_WIDE_GROUP=0 DMSH_RAW_LOAD_QUADS=0 DMSH_CBUF_REUSE=0 DMSH_STORAGE_RUNS=0
export DMSH_STAGECACHE=0 DMSH_STAGECACHE_WARM=0
export DM_NVN_BORDER_SPLIT=0
export DM_OOT_RENDER_RES=off DM_OOT_BRENT=0
export DM_FAST_CLOCK=0 DM_REWRITE_J=4 J=4
export DMSH_TARGETS=mac XLATE_DEBUG=1 XLATE_REDUCED=1
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="${OOT_PYTHON_BIN}:$HOME/.dotnet:$PATH"
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
unset IOSOUT XLATE SPIRV_CROSS DMSH_CAS DMSH_PREFILL WORK DM_GAMES_DIR
```

**The next app build must re-rewrite main with the merged Ocarina profile.**
It adds three build-bound observation hooks for DM_OOT_RENDER_RES. A host-only
rebuild cannot install them, even if the option is later enabled at runtime.
Leave the resolution override off for this recipe. DM_FAST_CLOCK separately
remains off at rewrite time.

Re-split the independent shader inputs with `DMSH_OOT_VISUAL=1`. The entry-wise
NDSR reader recovers SMAA-weights key `d17eefaff4f0bc23`; confirm it enters the
new shader map. Existing profile maps were not rewritten by this integration.
Regenerate `dmsh_chain.h` using `python dm/gfx/tools/dmsh_chain.py --header`
under this environment, build that profile's matching Mac shader libraries, then
build the host with `make -C dm/host -j4 GAME=0400486024DEC000 dmhost`.

The committed header describes source defaults, where visual translation is off.
The recommended enabled build has its own chain hash. Never combine that header
or host with libraries built using another option set. The common translator
binary includes gated visual paths; its lock is shared by both configurations.

## Runtime environment

Use these entries in the independent play build's environment. They are proposed
settings; the integration does not write the user's Application Support env.txt.

```ini
DM_SAFE_GPU=1
DM_AOT=1
DM_AOT_STRICT=1
DM_OOT_RENDER_RES=off
DM_OOT_BRENT=0
DM_NVN_POOL_SKIP_RETIRED=0
DM_NVN_VISUAL=1
DM_NVN_MESH_INDIRECT=1
DM_PRESENT_COLORSPACE=srgb
DM_QUALITY=off
DM_ANISO=0
DM_TRILINEAR=0
DM_SHARPEN=0
DM_PRESENT_UPSCALE=off
DM_PRESENT_UPSCALE_OUT=1
DM_UPSCALER=game
DM_OPMODE=1
DM_FPS_TARGET=0
DM_RENDER_SCALE=1
DM_PRESENT_ABSOLUTE=0
DM_NVN_FEEDBACK_MEMO=0
DM_NVN_TEX_DEDUPE=0
DM_NVN_UPLOAD_TRIM=0
DM_NVN_BORDER_SPLIT=0
DM_ECO_COPY_WAIT=0
DM_ECO_COMPILE_THREADS=0
DM_ECO_SAME_FRAME=0
DM_ECO_HIDDEN=off
DM_NVN_TBDR=0
DM_NVN_XV=0
DM_NVN_UNWRITTEN_DC=0
DM_NVN_ATTPROF=0
DM_NVN_GMEM_ALL=0
DM_NVN_NANSCAN=0
DM_NVN_VQA=0
DM_METAL_HUD=0
```

Leave `DM_TEST_GPU_HANG`, `DM_NVN_RES_LIMIT_MB`, `DM_DETCLOCK`, `DM_QOS_MAP`
and diagnostic environment variables unset. Keep audio enabled. Leave source-compiling `DM_NVN_HILITE`, `DM_NVN_MAGSCAN`
and `DM_NVN_TEXDUMP` diagnostics unset. Prepare complete offline libraries and
pipeline archives before play. This task did not prove that every runtime driver
pipeline-specialization request is served without compilation; the parent must
verify that strict gate before release. Keep memory dedupe and border splitting off for the correctness play build.
Hidden pause is repaired by oot-idle-fix, but stays off here as an experiment.

The safety net defaults on for this Ocarina Mac profile and caps GPU memory at
70% of recommendedMaxWorkingSetSize. Its source fixes remain active. It cannot
guarantee survival of a kernel/driver failure.

`DM_NVN_MESH_INDIRECT=1` enables a correctness candidate whose NVN2 record layout
is still provisional. The first eight records are logged after completion. The
parent must check those records and missing geometry against console/reference
images. `DM_QUALITY=max` is a separate optional image-enhancement experiment;
it is left off here so the game's filtering and reconstruction remain selected.
Crop and all quality configurations pass Metal validation as synthetic tests;
that does not prove game pictures, GPU safety or display colour acceptance.

## AOT acceptance

Set `DM_AOT=1` for both the packer and runtime. Keep `DM_AOT_STRICT=1`
during acceptance and play. Packing consumes the standard per-game
`pso_seen.jsonl`, or `DM_PSO_SEEN`; direct planning uses `--aot --seen <census>`.
Read the packed preflight report and require zero startup archive misses and
zero cumulative gameplay compiler entries on every required route. First present
starts gameplay accounting, including title and loading screens. Strict mode
reports a miss but still compiles it synchronously so native meshes stay visible.
Any gameplay compiler event fails the user's rule. Repack learned descriptors
and repeat acceptance; static preflight always reports incomplete coverage.
Function constants, unobserved final states and diagnostic source remain gaps.
No game or full offline build ran here, so no finished play package is claimed.

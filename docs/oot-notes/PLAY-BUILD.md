# Ocarina community play build

Use branch `oot-play`. It combines `oot-1439`, upstream `c83c48f2`,
`oot-play-fixes`, local and cloud Brent round two ports, and optional HDR.
The [integration list](NEXT-MERGES.md) records the selected inputs.

Visual correctness comes first. Gameplay and zero compiler entries during play
remain unproven. Unit and native fixtures do not establish either result.
`DM_AOT_STRICT=1` reports misses and still compiles to preserve visible geometry.
Lazy shaders stay off. Build the entire map and pipeline archives.

The default chain is `e16dbb187984`. With `DMSH_OOT_VISUAL=1`, the play
chain is `4323760be52f`, different from the existing package at `992d6981956f`.
Adopting `oot-play` requires a full shader and archive rebuild, then a matching
host. A host rebuild alone will reject the old library stamp.

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
export DM_BUILD_NOINDEX=1
export DMSH_HMMA_TENSOR=0
export DM_PSO_PREPARE_THREADS=4
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
new shader map. The three recovered NDSR keys are already in the committed profile.
Regenerate `dmsh_chain.h` using `python dm/gfx/tools/dmsh_chain.py --header`
under this environment, build that profile's matching Mac shader libraries, then
build the host with `make -C dm/host -j4 GAME=0400486024DEC000 dmhost`.

The committed header describes source defaults, where visual translation is off.
The enabled play build has its own chain hash. Never combine that header
or host with libraries built using another option set. The common translator
binary includes gated visual paths; its lock is shared by both configurations.

## Runtime environment

Use these entries in the independent play build's environment. They are proposed
settings; the integration does not write the user's Application Support env.txt.

```ini
DM_SAFE_GPU=1
DM_GUEST_FILE=0
DM_AOT=1
DM_AOT_STRICT=1
DM_PSO_PREPARE_THREADS=4
DM_OOT_RENDER_RES=off
DM_OOT_BRENT=0
DM_NVN_POOL_SKIP_RETIRED=0
DM_NVN_VISUAL=1
DM_NVN_MESH_INDIRECT=0
DM_NVN_SERIAL_HELD=1
DM_NVN_GMEM_COMMIT=1
DM_SDK22_SERVICES=1
DM_GPU_LOST_STOP=1
DM_NVN_IDLE_RETIRE=0
DM_NVN_RETIRE_CHUNKS=0
DM_NVN_POOL_TABLE_REUSE=0
DM_NVN_GW_INTERVALS=0
DM_AV1_PARALLEL=0
DM_CV_LATE=0
DM_NVN_HMMA_TENSOR=0
DM_NVN_FB_DSELF=0
DM_HDR=0
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

`DM_NVN_MESH_INDIRECT` stays off. Static analysis proves that this SDK consumes
two words, but the field order and the game's producer remain unverified.
Enabling it is a separate diagnostic run. The converter refuses counts above
its cap and first-task overflow. The host waits for the converted snapshot and
checks every record before submitting the mesh draw, logging the first eight
raw records. The waits cost performance. Missing indirect geometry remains an
open visual limitation while the flag is off. See [record evidence](mesh-indirect-layout.md).
`DM_QUALITY=max` is a separate optional image-enhancement experiment;
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

## Optional HDR and resolution

HDR stays off by default. To try it, set `DM_HDR=1` before launch on a Mac
with an HDR display. The host reports HDR only while that display supports it.
`DM_HDR_PAPER_WHITE` defaults to 203 nits and `DM_HDR_PEAK` to 1000 nits.
The game must produce HDR output. Display colours, monitor changes and archive
coverage still need gameplay validation. HDR alone changes the host, not the game
shader chain. See [HDR evidence](../../dm/games/0400486024DEC000/README.md#hdr-output).

Keep `DM_OOT_RENDER_RES=off`. The optional `observe` mode records the game's
resolution calls. Numeric modes require the matching rewritten main module and
separate image validation. See [resolution controls](oot-res.md).

Keep the remaining Brent performance experiments off. Parallel AV1 decoding and the movie
clock need cutscene checks. `DM_CV_LATE=1` may skip overdue movie pictures.
Tensor HMMA requires a different shader build and Apple10 hardware. The M4 Max
uses the existing matrix path. No NDVE bilinear replacement is included.

## Reviewed play defaults

Review 4a accepts `DM_NVN_SERIAL_HELD=1` for the play configuration because
its counts preserve texture-view ancestor protection. Keep its debug check off.
The repository's unset default remains off for comparison runs.

The user's final play decision enables `DM_SDK22_SERVICES=1`,
`DM_NVN_GMEM_COMMIT=1` and `DM_GPU_LOST_STOP=1`, with `DM_SAFE_GPU=1`.
Use `DM_BUILD_NOINDEX=1` for the next fresh build. No gameplay acceptance is
claimed for the chosen settings. The source defaults remain off for comparisons.

Keep `DM_NVN_FB_DSELF=0`, `DM_NVN_IDLE_RETIRE=0`, `DM_NVN_RETIRE_CHUNKS=0`,
`DM_NVN_POOL_TABLE_REUSE=0` and `DM_NVN_GW_INTERVALS=0` for later comparisons.
Keep both movie experiments, retired-pool skipping and both tensor flags off.
The three recovered NDSR entries are included through the corrected full split.
Mip omission and the NDVE bilinear replacement are excluded.

The AOT inventory includes exact SDR/P3 and HDR present descriptors, including
RGBA16Float's linear and sharpened functions and RGB10A2's PQ targets.
Startup prewarm consumes that same inventory. MetalFX scaler creation is counted
as compiler work, including a refused creation. Keep present MetalFX off for play.
Archive misses, resize transitions and unobserved game states still need route
acceptance. Neither the inventory nor strict logging proves zero play compiles.

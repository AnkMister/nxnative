# Ocarina community play build

Use branch `oot-play-1444`. It adds the reviewed PR #1444 source ports to final
`oot-play` at `e8c3bc22`, which includes the earlier fixes, Brent ports and optional HDR.
The [integration list](NEXT-MERGES.md) records the selected inputs.

Visual correctness comes first. Gameplay and zero compiler entries during play
remain unproven. Unit and native fixtures do not establish either result.
Play defaults to `DM_AOT=0` and `DM_AOT_STRICT=0`. A live hotfix with that
setting and counted serial holds was reported much smoother. The earlier
`aot_lookup(compile=1)` compiled whole exact misses synchronously before the
hybrid stand-in could run. The new archive-only lookup fix remains unverified.
Use `DM_PSO_LEARN=1` to capture descriptors without enabling that AOT path.
`DM_NVN_MESH_PREDICT=1` queues native task/mesh pipelines on workers and adds
them to bounded command look-ahead. Every draw is preserved. A first use can
still wait for an unfinished worker; this is not a zero-stutter guarantee.
Lazy shaders stay off. Build the entire map and pipeline archives.

The committed `dm/gfx/nvn/dmsh_chain.h` describes source defaults. Building
with `DMSH_OOT_VISUAL=1` produces a different play chain. Regenerate the header
under the chosen build environment, then rebuild every shader, the pipeline
archives and the matching host. Replacing only the host rejects the old stamp.

## Native 60 fps and the 120 Hz screen

PR #1444 reports native ~60 fps after rendering, shader and memory fixes.
It adds no Ocarina `FRAME_STEP` patch, `fps_target` or `fps_max` key.
`DM_FPS_TARGET=60` cannot unlock this game because no frame-step or engine
limiter hook is registered. Keep `DM_FPS_TARGET=0` and the game's interval.

For the user's 4K 120 Hz display, use `DM_PRESENT_LINK=2`,
`DM_PRESENT_HZ=60` and `DM_PRESENT_INTERVAL=game`. The host can show each game
frame for two display ticks. Keep `DM_OPMODE=1`, `DM_RENDER_SCALE=1` and
`DM_UPSCALER=game` for initial visual acceptance. These settings neither force
4K internal rendering nor prove sustained 60 fps on M4 Max. Both Apple10 tensor
options stay off on its Apple9 GPU. HDR and 1440p internal rendering remain
separate options below.

The actual pair-table additions let the shader build pad missing mesh outputs
for genuine BNSH variations. AOT's independent interface check still excludes
incompatible inferred pairs. There are no additional shader content keys to
append; both bases contain the same 42,854 keys and all NDSR additions.

## Split, rewrite and shader-build environment

**Build the entire shader map ahead of time. Lazy shaders stay off.** Use
`SEEN_SHADERS=False` / `--no-seen-shaders`. Zero compiler entries during play
remain an acceptance requirement that this branch has not proved.

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
export DM_OOT_RENDER_RES=off DM_OOT_BRENT=1
export DM_FAST_CLOCK=0 DM_REWRITE_J=4 J=4
export DMSH_TARGETS=mac XLATE_DEBUG=1 XLATE_REDUCED=1
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="${OOT_PYTHON_BIN}:$HOME/.dotnet:$PATH"
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
export DM_PSO_USER="$OOT_SHARED_CONTEXT/oot-saves/session1-0024/pso_user.tsv"
export DM_PSO_SEEN="$OOT_SHARED_CONTEXT/playtest-1/live/pso_seen.jsonl"
export DM_AOT_REBASE_SEEN=1
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
build the host with `nice -n 19 make -C dm/host -j2 GAME=0400486024DEC000 dmhost`.

After explicit `RESUME`, the exact full Mac app command is below. Run from
this branch's checkout. First set `OOT_SHARED_CONTEXT` to
`$HOME/Documents/Crypt/Gaming-rea/_work/nxnative` and `OOT_PYTHON_BIN` to
`$HOME/Documents/Crypt/Gaming-rea/nxnative/.venv/bin`, then apply the build
exports above. The prepared runtime env file contains the runtime block below.
Do not source it into the build shell: the packer needs AOT enabled while play
keeps it disabled.

```sh
nice -n 19 python dm/gfx/tools/dmsh_chain.py --header
nice -n 19 python scripts/build_ipa_from_nsp.py \
  "$HOME/Documents/Crypt/Gaming-rea/_work/games/oot/The Legend of Zelda Ocarina of Time.nup" \
  --platform mac-app --progress lines --no-seen-shaders --no-heap-check \
  --work-dir "$HOME/Documents/Crypt/Gaming-rea/_work/games/oot-play-1444/0400486024DEC000_build" \
  --out "$HOME/Documents/Crypt/Gaming-rea/_work/games/oot-play-1444/The Legend of Zelda - Ocarina of Time.app" \
  --env-file "$OOT_SHARED_CONTEXT/pr1444-evidence/next-play.env"
```

The archive step imports the 7,387-row session TSV using the rebuilt host's
descriptor-only tool mode and consumes the JSON census too. Exact descriptors
include blend/format/sample/layout state and captured function constants.
Known TSV rows also become the bundled startup prepare list, so they are warmed
with runtime AOT disabled. Neither tool mode loads a game. Captured constants
use the local Mac's Metal 4 compiler and serializer at build time because
`metal-tt` has refused these specialized library functions. Compiler refusals
and missing inputs stop the strict archive build. This command has not run.

The committed header describes source defaults, where the new visual translation paths are off.
The enabled play build has its own chain hash. Never combine that header
or host with libraries built using another option set. The common translator
binary includes gated visual paths; its lock is shared by both configurations.

## Runtime environment

Use these entries in the independent play build's environment. They are proposed
settings; the integration does not write the user's Application Support env.txt.

```ini
DM_SAFE_GPU=1
DM_GUEST_FILE=0
DM_AOT=0
DM_AOT_STRICT=0
DM_PSO_LEARN=1
DM_NVN_MESH_PREDICT=1
DM_PSO_PREPARE_THREADS=4
DM_OOT_RENDER_RES=off
DM_OOT_BRENT=1
DM_NVN_POOL_SKIP_RETIRED=0
DM_NVN_VISUAL=1
DM_NVN_P1444_TEX=1
DM_NVN_P1444_STUTTER=1
DM_NVN_BCRT=1
DM_FOCUS_KEEP=1
DM_PRESENT_LINK=2
DM_PRESENT_HZ=60
DM_PRESENT_INTERVAL=game
DM_NVN_MESH_INDIRECT=1
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

The user selected `DM_NVN_MESH_INDIRECT=1` based on PR #1444's long gameplay
report. The source default remains off. Static guest analysis proves that the
SDK consumes two words; field order and the game's producer remain unverified.
The converter refuses excessive counts and first-task overflow. The host waits
for the converted snapshot and checks every record before submitting its mesh
draw, logging the first eight raw records. These waits can cause stalls and
remain part of the accepted diagnostic protection. Neither a synthetic fixture
nor upstream gameplay establishes the exact record ABI on this fork.
See [record evidence](mesh-indirect-layout.md).

`DM_QUALITY=max` is a separate optional image-enhancement experiment;
it is left off here so the game's filtering and reconstruction remain selected.
Crop and all quality configurations pass Metal validation as synthetic tests;
that does not prove game pictures, GPU safety or display colour acceptance.

## AOT acceptance

Use `DM_AOT=1 DM_AOT_STRICT=1` for the offline packer and controlled AOT
fixtures. Keep the play defaults at `DM_AOT=0 DM_AOT_STRICT=0` until the new
miss path passes validation. Packing consumes `pso_seen.jsonl` and
`pso_user.tsv`, or explicit `DM_PSO_SEEN` and `DM_PSO_USER`. Direct planning
uses `--aot --seen <jsonl> --user <tsv> --host <matching-dmhost>`.
Read the packed preflight report and require zero startup archive misses and
zero cumulative gameplay compiler entries on every required route. First present
starts gameplay accounting, including title and loading screens. Strict mode
reports compiler entries; it does not prohibit the existing fallback paths.
Any gameplay compiler event fails the user's rule. Repack learned descriptors
and repeat acceptance; static preflight always reports incomplete coverage.
Unobserved final states, unobserved constant values and diagnostic source remain gaps.
No game or full offline build ran here, so no finished play package is claimed.

Native TSV imports isolate stale and unsupported rows in `aot-import-refused.json`.
Only accepted native rows join the startup manifest. Strict packing refuses
unsupported current states. Exact compiler refusals are bisected so non-strict
builds retain successful archive pieces. Constants are checked against the
function's declared indices, types and required values. The source-built host
must match the planned chain and local GPU architecture.

With runtime `DM_AOT=0`, exact mesh/helper archives are not queried by the
expanded AOT path. The bundled native manifest still prepares known states.
Controlled `DM_AOT=1` acceptance is required to prove direct exact hits after
the synchronous lookup repair. An archived open-color base still needs color
specialization; only an exact final descriptor avoids that request.

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

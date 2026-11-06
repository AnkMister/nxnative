# Ocarina play controls

`oot-play` is the community build branch. The [play recipe](PLAY-BUILD.md)
sets `DM_AOT=1`, `DM_AOT_STRICT=1` and `DM_SAFE_GPU=1`. Keep
`DM_NVN_MESH_INDIRECT=0`, `DM_HDR=0` and `DM_OOT_RENDER_RES=off`.
Gameplay image parity and zero compiler entries during play remain unproven.
Source defaults and recommended recipe settings are separate.

## Brent round two and HDR

| Control | Source default | Play setting and limit |
| --- | --- | --- |
| `DM_NVN_SERIAL_HELD` | Off | Counted lookup retains texture-view ancestors. ON in the play recipe after review 4a; debug checking stays off. |
| `DM_NVN_GMEM_COMMIT` | Off | Refreshes raw pool table words before commit. ON by user decision; raw-map growth, segment and geometry acceptance remains open. |
| `DM_NVN_FB_DSELF` | Off | Ignores a pool shader's depth-write bit when classifying feedback. OFF pending water, depth, decal and stencil image checks. |
| `DM_HDR` | Off | Keep off. `1` opts in on an HDR display. Display colours and archive coverage need validation. |
| `DM_HDR_PAPER_WHITE`, `DM_HDR_PEAK` | 203, 1000 nits | Optional HDR calibration. Both are inactive in the SDR recipe. |
| `DMSH_HMMA_TENSOR`, `DM_NVN_HMMA_TENSOR` | Off | Keep off. Build and runtime must both opt in. Apple10 only; M4 Max uses the matrix path. |
| `DM_SDK22_SERVICES` | Off | ON by user decision; gameplay checks for the five SDK hooks remain open. |
| `DM_GPU_LOST_STOP` | Off | ON by user decision; alert and window acceptance remain open. Safe GPU stays on. |
| `DM_NVN_RETIRE_CHUNKS`, `DM_NVN_POOL_TABLE_REUSE` | Off | Keep off pending buffer lifetime and image checks. |
| `DM_NVN_GW_INTERVALS`, `DM_NVN_IDLE_RETIRE` | Off | Keep off pending write tracking, focus and resume checks. |
| `DM_AV1_PARALLEL`, `DM_CV_LATE` | Off | Keep off. The clock can omit overdue movie pictures. No NDVE bilinear replacement is included. |
| `DM_BUILD_NOINDEX` | Off | ON for the next fresh build; excludes temporary and shader folders from Spotlight. |
| `DM_PSO_J`, `DM_METAL_PACK_THREADS` | 1 | Optional offline build concurrency. Changing them does not change shader semantics. |

The play recipe enables no quality reduction. All source experiments remain
available for separate comparisons. The existing inventory follows.

The tables cover controls added, changed or used for experiments by `oot-stack`,
`oot-cpu`, `oot-mem`, `oot-1203`, `oot-idle`, `oot-upscale`, `oot-bench` and
`oot-msl`, `oot-tbdr`, `oot-stagecache`, `oot-vqa`, `oot-quality`,
`oot-clock`, `oot-stable` and `oot-visual`. Defaults describe an unset environment on the Ocarina profile.
Expected gains are hypotheses or upstream reports, not measured gameplay results
on this integrated branch. Check pictures before accepting any efficiency gain.
The complete repository inventory remains [env_switches.tsv](../env_switches.tsv).

## Accepted replacements and remaining gates

Review-1 replacements are integrated: oot-stack-fix, oot-idle-fix, oot-mem-fix
and oot-1203-fix replace their parents. Memory dedupe, upload trim and border
splitting remain default-off. Hidden pause now preserves queued audio and remains
opt-in; actual hide/resume and dialogue acceptance is still open. Review-2 visual and stable replacements are also integrated. Their regression
fixtures still need to pass in this combined stack.
The growing-pool correctness change remains unconditional; the numeric readable-
tile memo is now opt-in, preserving the original string-key lookup when off.

## Feature switches

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DM_NVN_FEEDBACK_MEMO=1` | Off | Function lookup/cache changes need image checks; seeded off-path regression passes | Numeric readable-tile function memo; no integrated game gain measured | oot-stack-fix, #1161 |
| `DMSH_RAW_LOAD_QUADS=1` (shader build) | Off; only exact `1` enables | Raw address lookup or interval errors can corrupt pixels; compare scalar/quad outputs and latency | Shares four adjacent raw reads' lookup; upstream reports about 2 ms GPU with increased present latency | oot-stack, #1405 |
| `DM_PRESENT_ABSOLUTE=1` | Off | Cadence, scanout latency and game speed need on-screen checks | May prevent cumulative relative-present delay; unmeasured | oot-stack |
| `DM_ECO_COPY_WAIT=1` | Off; Mac only | Low image risk; scheduling, deadlock and late-frame risk | Stops consumer spinning when uniform-copy worker is delayed | oot-cpu |
| `DM_ECO_COMPILE_THREADS=1..64` | Unset/0 disables; invalid values disable | Longer preparation or first-use hitches; does not change shaders | Less competing compile work per pool; no warm steady-state saving promised | oot-cpu |
| `DM_NVN_TEX_DEDUPE=1` | Off; Mac only | Experimental page faults and restore I/O; texture reads and loading require visual checks | Releases cold guest copies; upstream reports about 1.9 GB, not reproduced here | oot-mem-fix, #1386 |
| `DM_NVN_TEX_DEDUPE_AGE_MS` | 2000 ms; inert without dedupe | Short ages increase release/restore churn | Trades retained bytes against I/O | oot-mem-fix |
| `DM_NVN_TEX_DEDUPE_MB` | 32 MiB per submission; inert without dedupe | Large budgets can stall submission | Bounds synchronous backup/release work | oot-mem-fix |
| `DM_NVN_TEX_DEDUPE_DIR` | `TMPDIR`; dedupe refuses absent/unwritable storage | Restore timeout now fails closed; permanent failure stops before GPU/kernel access. Disk I/O and release races remain visual/latency risks | Unlinked disk backup enables release; does not shrink Metal textures | oot-mem-fix |
| `DM_NVN_UPLOAD_TRIM=1` | Off; Mac only | Later uploads reallocate and can hitch | Zero to 192 MiB of retained staging after 120 unused submissions | oot-mem-fix |
| `DM_NVN_BORDER_SPLIT=1` | Off at build and runtime; only exact `1` enables | Sampler changes must select/invalidate the correct `_b`/`_bn` PSO; check custom borders | Removes correction code from eligible ordinary pixel shaders | oot-1203-fix |
| `DM_ECO_SAME_FRAME=1` | Off; only exact `1` enables | Wrong sameness proof could leave stale scanout; synthetic tests cover conservative refusals | Avoids display-only GPU work for repeated proven GPU-only images; never skips guest submissions | oot-idle |
| `DM_ECO_HIDDEN=pause` | Off | Audio/clock mismatch repaired by oot-idle-fix; real window/dialogue acceptance open | Preserves queued PCM while guest clock and graphics pause | oot-idle, oot-idle-fix |
| `DM_ECO_HIDDEN=slow` | Off | Hidden progression may slow; verify resume | Caps each NVN acquire/vsync caller at 8 Hz | oot-idle |
| `DM_UPSCALER=game` / `metalfx` | `game` | Spatial substitution changes reconstruction and sharpness; check motion, edges and colours | Replaces eligible standard NDSR compute work; no Ocarina GPU result | oot-upscale, existing control |
| `DM_OPMODE=0` / `1` | `1`, docked | Handheld intentionally lowers image resolution; not visual equivalence | At equal palette level, 43.75% fewer scene/final pixels; not a whole-frame saving | oot-upscale, existing control |
| `DMSH_CBUF_REUSE=1` (shader build) | Off; only exact `1` enables | Constant reuse changes register lifetime/scheduling; check images and occupancy | One sampled compute AIR decreased; sampled pixel AIR did not; no frame result | oot-msl |
| `DMSH_STORAGE_RUNS=1` (shader build) | Off; only exact `1` enables | Wrap fallback and four-byte alignment need GPU checks; can add branches/loads | Shares addresses in off-grid read-only storage runs; may regress GPU cost | oot-msl |

The raw-load, storage-run and constant-reuse switches compose in `dmsh_chain.options()`.
Their tools enter `FILES` and `CODE_FP`. Each combination requires its own
regenerated header, matching shader libraries and rebuilt host. Runtime switches
cannot enable a build pass. No full shader build was run for this integration.
The border split build flag now enters the chain/complete-shader key. The pure
`border_plain` pass has its own intermediate key. Default `_b`/`_bx` compile
inputs retain correction; opt-in `_bn` assets are disposable and fail back to `_b`.

## Inherited controls used by the experiments

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DM_NVN_UB_COPY_THREAD` | On; `0` bypasses worker | Scheduling/pacing only | Negative control for copy waits | oot-cpu |
| `DM_PSO_PREPARE_THREADS` | Active CPU count | Preparation/stutter | Existing pool size, still bounded by eco ceiling | oot-cpu |
| `DM_PSO_PREBUILD_THREADS` | Performance cores minus one for standalone tool | Preparation/stutter | Existing tool size, still bounded by eco ceiling | oot-cpu |
| `DM_QOS_MAP` | Off | Scheduling and audio/pacing need checks | Opt-in guest-priority QoS map | oot-cpu |
| `DM_QOS_EDGES` | `44,59`; inert without QoS map | Scheduling only | `-1,59` caps ordinary valid guest priorities at USER_INITIATED | oot-cpu |
| `DM_RT` | On | Acquire/present scheduling can change | `0` removes acquire thread's Mach time-constraint policy | oot-cpu |
| `DM_NVN_FAST_WAKE` | On | Fence wake semantics | Already present; `0` is a comparison control | oot-cpu |
| `DM_PRESENT_FIFO` | On | Frame selection and latency | Already present; `0` chooses newest queued frame | oot-cpu |
| `DM_GUEST_FILE=1` | Off | Compatibility guard disables dedupe; file backing is included only in oot-hyper-main | Avoids combining file-backed guest memory with dedupe | oot-mem-fix |
| `DM_NVN_DIRTYCHECK` | Off | Diagnostic hash/read overhead | Verifies uploads; not an efficiency switch | oot-mem-fix |
| `DM_FOCUS_KEEP` | Off | Affects game focus response | Harness uses `1`; explicit eco hidden policy takes precedence | oot-cpu, oot-idle, oot-bench |
| `DM_PRESENT_LINK` | `1` | Cadence/latency | Stack's direct-present A/B uses `0` | oot-stack |
| `DM_PRESENT_HZ` | 60 | Pacing; `0` is uncapped | Synthetic tests use `0`; not an efficiency recommendation | oot-idle |
| `DM_FPS` | Follows game's present interval | Cadence/game speed | Existing low-level 30/60 present pin used in stack recipe | oot-stack |
| `DM_FPS_TARGET` | Profile `0`, game's own limit | Host frame-step support is game-dependent | Harness forces `30`; observed cap/game speed still need validation | oot-cpu, oot-idle, oot-bench |
| `DM_FPS_HOLD` | Existing hold policy | Game speed on frame-step titles | No Ocarina frame-step rewrite; no gain established | oot-upscale |
| `DM_RENDER_SCALE` | 1.0 | No effect on Ocarina here | No Ocarina render-scale rewrite; 0.75/0.67/0.5 are negative controls | oot-upscale |
| `DM_DYNAMIC_RESOLUTION` | Existing build-gated NieR policy | No effect on Ocarina here | Does not control Ocarina's own dynamic resolution | oot-upscale |
| `DM_NVN_GPU_TS` | Profile default, whole submission | Can alter the game's dynamic-resolution feedback | Optional `segment` comparison; keep equal between arms | oot-upscale |
| `DM_PSO_PREBUILD` | On | Compilation/prewarm changes hitches | Harness forces `0` for controlled measurement | oot-cpu, oot-bench |
| `DM_DETCLOCK` | Off | Changes guest time and randomness | Replay diagnostic; keep unset for energy measurement | oot-idle |
| `DM_WINDOW`, `DM_WINDOW_TOP` | Existing frontend policy; top off | Window occlusion/focus affects progression | Harness forces both `1` to retain visible rendering | oot-cpu, oot-idle, oot-bench |
| `DM_AUDIO` | On | Harness intentionally mutes audio | Harness forces `0`; does not prove normal-audio energy | oot-cpu, oot-bench |
| `DM_METAL_HUD` | Off | HUD and measurement overhead | Harness forces `0`; idle counters also recognise its presence | oot-idle, oot-bench |
| `DM_NVN_LOG` | Off | Diagnostic overhead | Eco counters; no saving | oot-idle |
| `DM_NVN_WAITS` | Off | Diagnostic overhead | Copy-wait attribution; no saving | oot-cpu |
| `DM_THRCPU` | Unset | Sampler overhead | Per-thread CPU attribution; interval defaults to 10 s | oot-cpu |
| `DM_NVN_GPUPROF` | Off | Profiling overhead | Per-pass GPU attribution; no saving | oot-upscale, oot-msl |
| `DM_NVN_TSV`, `DM_NVN_TSV_CALLS` | TSV off; call rows on when enabled | Logging overhead | Harness sets a per-run TSV and calls `0` | oot-stack, oot-idle, oot-bench |
| `DM_KEYS`, `DM_CTL` | Unset | Scripted input changes route | Harness supplies one route and isolated control file | oot-bench |

## Paths and build/test inputs

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `GAME`, `DM_GAME` | Required, no default | Wrong profile means wrong constants/assets | Set `0400486024DEC000` for make/tools respectively | All |
| `DM_ROOT`, `DM_ROMFS`, `DM_MSL_DIR`, `DM_FONT_DIR`, `DM_NVN_SHMAP` | Existing package/tool-derived paths | Mismatched game/shader inputs corrupt results | Harness resolves read-only assets and isolates writable root | oot-stack, oot-cpu, oot-idle, oot-bench |
| `DM_SAVE`, `DM_TEMP` | Existing frontend root-derived paths | Different saves invalidate comparisons | Harness makes fresh per-run directories from one immutable save seed | oot-stack, oot-cpu, oot-idle, oot-bench |
| `DM_PSO_ARCHIVE`, `DM_PSO_USER`, `DM_PSO_BUNDLE` | Existing frontend/profile defaults | Stale/wrong archive or warm-state mismatch | Harness isolates writable archive/user files; bundle remains input | oot-cpu, oot-idle, oot-bench |
| `DM_AOC_DIR` | Package-derived when present | Changes mounted game content | Harness preserves package AOC input | oot-bench |
| `XLATE`, `SPIRV_CROSS` | Bundled executables | Translator/tool mismatch changes shaders | Keep stack's source-built translator matching the lock | oot-stack, oot-msl |
| `XLATE_DEBUG`, `XLATE_REDUCED` | `1`, `1` | Changes translation and chain | Inherited chain controls; do not change between comparison arms | oot-stack |
| `DMSH_TARGETS`, `IOSOUT` | Existing build default; IOSOUT unset here | Platform libraries must match host | Parent Mac-only recipe sets targets `mac`; this task builds no game shaders | oot-1203, oot-msl |
| `J`, make `-j` | Tool/make default | Resource contention distorts measurements | Explicit ceiling of four jobs in this integration | oot-stack, oot-msl |
| `DMSH_TEST_XLATE` | Bundled translator for native fixture target; Python fixture tests opt in | Test-only | Runs trusted translator on synthetic shaders | oot-stack |
| `DMSH_TEST_METAL`, `DMSH_TEST_GPU`, `DM_TEST_BORDER` | Off/unset | Test-only | Enable synthetic compiler/GPU/border checks | oot-stack, oot-1203 |
| `TMPDIR` | OS default; explicitly overridden in all integration commands | Wrong path violates workspace storage rules | Use `${OOT_SHARED_CONTEXT}/setup/scratch` | All |
| `DOTNET_ROOT`, `PATH` | Shell settings | Wrong .NET architecture/runtime prevents translation | Stack rebuild uses `~/.dotnet`; Python uses supplied uv venv | oot-stack |
| `DOTNET_PROCESSOR_COUNT`, `DOTNET_CLI_TELEMETRY_OPTOUT`, `DOTNET_SKIP_FIRST_TIME_EXPERIENCE`, `NUGET_PACKAGES` | Rebuild recipe uses `4`, `1`, `1`, isolated audited cache | Build provenance only | Cooled exact-version feed; restore uses only the audited local feed in this integration | oot-stack |
| `DM_GAME_UPSCALER_KEYS`, `DM_GAME_UPSCALER_N` (generated macros) | 22 standard NDSR compute keys | VR/NDVE must remain excluded | Existing profile derivation; not user-settable env switches | oot-upscale |
| `DMSH_CHAIN`, `DMSH_GMEM_MAP_ENTRIES`, `DMSH_GMEM_MAP_ENTRY` (compiled ABI) | Generated chain; 4096 minimum entries; 32 bytes per entry | Host/translator ABI mismatch can hang GPU | Growing power-of-two table through 2^20 preserves existing low-entry hints | oot-stack |

No branch adds a user-facing C compiler optimization flag. #1360's growing
pool table and #1161's original readable-tile lookup are inherited source
paths from `oot-stack`. The fixed #1203 library splitting and memory experiments are integrated, default-off. Idle submission accounting also
runs with experiments off. No feature default was changed during integration; the incoming safety branch already defaults DM_SAFE_GPU on for Ocarina Mac.
`DM_NVN_CUT_FIRST` and `DM_NVN_HANGLOG` appear in historical notes but are removed
names, not supported controls. Shell recipe path variables such as `AB`, `SOURCE`,
`PUBLISH` and `OOT_BENCH_ROUTE` are placeholders, not build feature switches.

## Integrated TBDR, build-cache, VQA and quality controls

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DM_NVN_TBDR=1` | Off | **HIGH**. A wrong dontCare store shows as black or garbage regions | Conservative store/load elision and pass continuation; no measured game saving | oot-tbdr, #1340/#1367 |
| `DM_NVN_XV=1` | Off; requires TBDR | **HIGH**. History cannot prove future readers; black or garbage regions are possible | Experimental cross-submission store prediction | oot-tbdr |
| `DM_NVN_ATTPROF=1` | Off | **HIGH** for the measured TBDR experiment; telemetry does not establish sound stores | Nominal per-subresource bytes and split causes, not physical DRAM traffic | oot-tbdr |
| `DM_NVN_UB_DEFER` | On, including TBDR | **HIGH**. Wrong reordering can corrupt regions | Preserve inline uniform deferral across passes | oot-tbdr, #1367 |
| `DM_NVN_UNWRITTEN_DC` | On independently of TBDR; `0` disables optional savings | **HIGH**. Wrong dontCare store shows as black or garbage regions | Avoids unchanged attachment stores; mandatory image-write preservation remains | oot-tbdr |
| `DM_NVN_DEFER`, `DM_NVN_DEFER_AB`, `DM_NVN_RT_RANGE`, `DM_NVN_ZSKIP` | Defer on under TBDR; AB off; RT range off; ZSKIP on under TBDR | **HIGH**. Wrong merge/reader proof can leave black or garbage regions | Existing TBDR comparison controls; no new default enables TBDR | oot-tbdr |
| `DM_NVN_UBD_MEMO` | On; `0` scans | **HIGH** for uniform visibility if memo is wrong | Existing deferred-update lookup memo; no new default | oot-tbdr |
| `DM_XV_FILE` | Existing validity-ledger path | **HIGH**. A recorded past violation cannot prove a future store safe | Persists disabled prediction keys; leave XV off | oot-tbdr |
| `DMSH_STAGECACHE=1` | Off; exact `1` enables | Wrong dependency keys can silently restore stale shader outputs | Reuses raw translation, SPIRV-Cross and pure MSL results; whole-build gain unmeasured | oot-stagecache |
| `DMSH_STAGECACHE_WARM=1` | Off; inert without stagecache | Same key risk; extra build/cache work | Bypasses complete hits once to seed intermediates | oot-stagecache |
| `DMSH_CAS`, `DMSH_PREFILL`, `WORK`, `DM_GAMES_DIR` | CAS under output; optional prefill; WORK/TMPDIR temp; repository profiles | Never write to protected baseline caches/profiles | Reuse an independent writable cache and derived profile | oot-stagecache, existing build inputs |
| `DM_PRESENT_COLORSPACE=srgb` | Legacy nil/untagged output when unset | **recommended default for the user**. Correct sRGB tagging fixes untagged, un-colour-matched output that looks oversaturated on P3 displays | Colour correctness; no speedup | oot-vqa |
| `DM_PRESENT_COLORSPACE=auto` / `p3` | Opt-in | Auto means SDR sRGB; p3 converts primaries before tagging; compare display appearance | Explicit SDR colour contract; no HDR inference | oot-vqa |
| `DM_NVN_NANSCAN=1` | Off | Diagnostics add GPU/readback overhead and may change timing | Names first stored floating-point attachment with nonfinite pixels; does not repair pixels | oot-vqa |
| `DM_NVN_NANSCAN_EVERY` | 1 presented-frame index | Diagnostic sampling can miss transient faults | Reduces scanner overhead when explicitly sampling | oot-vqa |
| `DM_NVN_VQA=1` | Off | Logging overhead | Skipped pipeline/source format/HDR-query evidence and compile timing | oot-vqa |
| `DM_NVN_SHOT_OUT` | Source-sized existing screenshot policy | Offscreen scaling differs from actual scanout | Fixed output-size diagnostic stills; not an efficiency control | oot-vqa, existing control |
| `DM_QUALITY=max` | Off | Changes filtering, reconstruction and sharpening; game/console acceptance open | Quality candidate; adds GPU work | oot-quality |
| `DM_ANISO` | Game sampler; max preset floor 16 | Sampling changes; shadow/reduction/nearest samplers stay protected | Sharper oblique texture detail; extra sampling cost | oot-quality |
| `DM_TRILINEAR` | Game sampler; max preset 1 | Alters eligible mip transitions | Smoother mip transitions; extra filtering cost | oot-quality |
| `DM_PRESENT_UPSCALE` | Off; max preset metalfx | Spatial reconstruction changes picture | Optional MetalFX presentation; independent of the game's NDSR replacement | oot-quality, existing control |
| `DM_PRESENT_UPSCALE_OUT` | 1; max preset 1.5; range 1 to 4 | Supersampled reconstruction/downsampling; does not resize guest scene targets | Presentation quality with more GPU work and memory | oot-quality |
| `DM_SHARPEN` | 0; max preset 0.2; range 0 to 1 | Contrast/detail changes; compare edges and motion | Clamped sharpening keeps footprint filtering and P3 conversion | oot-quality |

TBDR is host-only and adds no shader-chain module or build option. Its telemetry
is default-off. The stage cache passes `storage_runs` explicitly as a pure-pass
argument, caches raw quads with ABI/table parameters, and invokes constant reuse
only when enabled. Debug/reduced flags and profile answers enter translation jobs.
Source-built translator distribution plus translation sources enter translation
keys. The complete-shader key covers orchestration, ABI and platform convention;
each intermediate pass fingerprints its function/module dependencies. The coverage
test checks every `dmsh_chain.FILES` file against those actual key paths.

The Metal 4 spatial scaler output barrier is set for its next consumer. Presentation
uses fragment stages; the game-upscaler route uses all stages. The installed SDK
omits its setter, so the compatibility path guards the runtime ivar and refuses
unknown implementations. Crop, colour and all quality cases run with validation.

## Correctness, safety and clock controls

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DMSH_OOT_VISUAL=1` (split and shader build) | Off in source; **ON for the user's build (correctness)**; oot-visual-fix merged | Mixed integer/Float16 attachment defect repaired; correctness ports change numeric lowering, atomics, handles and Float16 outputs; game/console picture acceptance remains open | Restores missing effects/foliage and supported shader translations; no frame gain claimed | oot-visual |
| `DM_NVN_VISUAL=1` | Off; ON in recommended play build | Changes image aliases, texture write ranges, mesh prewarm and output-limit PSOs; gameplay still needs checking | Host half of visual correctness ports | oot-visual |
| `DM_NVN_MESH_INDIRECT=1` | Off, including play recipe | HIGH: field order remains unverified; bounded conversion and a GPU wait before every converted batch | Diagnostic only; logs first eight raw records and refuses overflow before mesh submission | oot-visual |
| `DM_SAFE_GPU` | **On for Ocarina Mac**, off elsewhere; oot-stable-fix merged | Watchdog and auxiliary residency races repaired; stops the process on GPU errors, stalled feedback or memory pressure; cannot guarantee driver recovery | GPU memory capped at 70% of recommendedMaxWorkingSetSize, conservative system wired-memory cap, no submission after refusal | oot-stable |
| `DM_NVN_RES_LIMIT_MB` | Existing working-set guard; safe mode enforces its stricter cap | Lower limit can stop early; higher values or `0` cannot bypass safe mode | Optional lower cap for prevention; no FPS gain | oot-stable, #1391 |
| `DM_NVN_GMEM_ALL=1` | Off | Exposes all raw pools and increases residency pressure; leave off | Diagnostic comparison against address-mark filtering | oot-stable, #1394 |
| `DM_TEST_GPU_HANG` | Off | Fault injection stops safe-mode process; never set for play | Synthetic callback/diagnostic test only, no real GPU hang required | oot-stable, #1382 |
| `DM_FAST_CLOCK=1` (module rewrite) | Off; exact `1` enables | Counter frequency/epoch, pause, capture and fallback semantics need gameplay acceptance | Branch microbenchmark 22.6 to 8.8 ns per read, 45 SDK sites; not integrated gameplay gain | oot-clock |
| `SEEN_SHADERS`, `--seen-shaders` | Off; require `False` / `--no-seen-shaders` for play | Partial maps omit geometry/effects; not acceptable for the user | No runtime shader compilation: full offline shader corpus required; lazy shaders stay off | Existing packer, user play-build rule |
| `DM_HDR=1` | Off, including play | HDR display and colours need gameplay validation | Optional guest HDR output | oot-hdr, #1176 |
| `DM_CLOCK_STATS=1` | Off | Diagnostic overhead; forces full clock gate and disables fast entry | Counts physical, virtual and frequency reads per thread; no speedup | oot-clock |
| `DM_REWRITE_J` | Existing rewrite worker policy | Build resource use only | Set `4` at most for a re-rewrite; no visual gain | oot-clock, existing build input |

`DM_FAST_CLOCK` needs a module re-rewrite and host rebuild, with modest rewrite
work (the branch brief estimates about 30 seconds; this integration did not
measure it). It needs no shader rebuild. A runtime-only setting cannot patch
already rewritten modules.

Stable #1394 address marking retains the growing table and low-entry hints used
by raw-load quads. Scalar and optimized four-word shaders are compared on the GPU
against the actual host table with 5,001 marked ranges. The stable deferred-release
partition is unconditional, preserving its safety fix even with visual ports off.
The recommended choices and build/runtime boundary are in [PLAY-BUILD.md](PLAY-BUILD.md).

The play build requires full ahead-of-time shaders. Lazy shaders and partial
seen-only builds stay off; source-compiling diagnostics stay unset. See the
release blockers in [PLAY-BUILD.md](PLAY-BUILD.md).

## Additional source harvest and internal resolution

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DM_OOT_RENDER_RES=1440` / `2160` | Off; exact values only | HIGH: engine hooks change scene/final dimensions and disable dynamic reduction; NDSR 1:1, effects, UI, allocation capacity and images unverified | More internal detail with higher GPU/memory cost; no gameplay result | oot-res, 51c75925 |
| `DM_OOT_ORIGINAL_MAIN` | Unset | Test-only read-only original-NSO input | Audits original hook instructions; no runtime gain | oot-res |
| `DM_OOT_BRENT=1` | Off | Alias/heap layout is gated only on oot-hyper; audio-lock discovery and resource cleanup need acceptance; packaging checks may refuse bad inputs | SDK lock correctness, completed-log reclamation and build reuse; no measured frame gain | oot-brent |
| `DM_NVN_POOL_SKIP_RETIRED=1` | Off | HIGH: a finalized handle can legally read surviving storage; can omit visible textures | Avoids remaking retired textures; game savings unmeasured | oot-brent, #1393 |
| `DM_ALIAS_SIZE` | Existing profile/host policy; Brent opt-in on oot-hyper reserves at least 64 GB | Guest address layout and pointer truncation; reserves address space, not RAM | Explicit override preserved; upstream-main variant uses upstream alias implementation | oot-brent, upstream main |

The resolution feature needs main re-rewritten with the merged profile and a
rebuilt host; no shader rebuild is required solely for its three engine hooks.
On the upstream-main basis, VOTEU's uniform destination and guarded-handle
resolution stay unconditional. Only local additions are controlled by the visual
flag. Review 3 checks those fixes against an independently source-built upstream
reference and checks enabled output against 64a163ba.

DMSH_OOT_VISUAL also enables Brent's LDSM ordering and validated splitter changes.
The new tensor translator source enters FILES and translation-stage fingerprints.

## Final foliage and offline pipeline coverage

| Flag or environment variable | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DMSH_WIDE_GROUP=1` | Off; OFF for play | HIGH until image parity; boundary fallbacks are tested | About 70% fewer static pool lookups in selected foliage meshes; GPU gain unmeasured | oot-foliage |
| `DM_AOT=1` | Off; ON for play packer and runtime | Coverage gaps can still compile synchronously; fixtures preserve mesh draws on misses | Expanded archives and startup prewarm reduce first-use pipeline work | oot-aot |
| `DM_AOT_STRICT=1` | Off; ON for play acceptance | Logs gaps; does not prevent compilation | Conservative evidence of compiler API entries | oot-aot |
| Compile counters | Always on | Low, diagnostic accounting | Separates startup/gameplay compiler and archive API entries | oot-aot |
| `DM_AOT_LOG_SECONDS` | 5 seconds | None | Summary interval without a timer thread | oot-aot |
| `DM_PSO_SEEN` | Per-game `pso_seen.jsonl` beside `pso_user.tsv` | None; stale chain entries are rejected | Learn exact descriptors and consume them on repack | oot-aot |
| `pso_offline.py --aot`, repeatable `--seen` | Off / no explicit census | Unknown final states remain gaps | Offline compute, layer, mesh, helper and learned exact states | oot-aot |
| `DM_TEST_AOT` | Unset | Test only | Native archive round-trip fixture path | oot-aot |

Stage keys include grouping's `readonly` argument and module bytes. Raw-load
quads, storage runs, constant reuse, border splitting and visual translation keep
their distinct inputs. TBDR host-only controls do not change the shader chain.

## Additional upstream-main controls

| Flag or environment variable | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DM_GUEST_FILE_CHUNK` | 1 GiB, minimum 64 MiB | File-backed guest-memory compatibility; OFF for play via DM_GUEST_FILE=0 | Bounds periodic file-flush work | origin/main, oot-hyper-main only |
| `DM_GUEST_FILE_DIR` | Process temporary directory | None when file backing is off; use an owned persistent scratch root when testing | Select backing-file storage | origin/main, oot-hyper-main only |
| `DM_GUEST_FILE_MIN_FREE` | 5 GiB; Mac also keeps 8 GiB reserve | Stops the process when free-space guard trips | Avoids exhausting backing storage | origin/main, oot-hyper-main only |

On oot-hyper-main, the upstream 64 GB alias reservation and provisional heap
alias accounting are unconditional upstream fixes. DM_OOT_BRENT no longer gates
or duplicates them. The per-renderer PCM-block repair is also unconditional.

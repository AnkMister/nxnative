# Ocarina integrated controls

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
opt-in; actual hide/resume and dialogue acceptance is still open. Review 2 blocks
shipping the visual set and default-on safety watchdog until their fix branches.
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
| `DM_GUEST_FILE=1` | Off | Compatibility guard disables dedupe; backing implementation itself is not included | Avoids combining file-backed guest memory with dedupe | oot-mem-fix |
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
| `TMPDIR` | OS default; explicitly overridden in all integration commands | Wrong path violates workspace storage rules | Use `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch` | All |
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
| `DMSH_OOT_VISUAL=1` (split and shader build) | Off in source; **ON for the user's build (correctness)** after oot-visual-fix | Known mixed integer/Float16 attachment corruption pending fix; correctness ports change numeric lowering, atomics, handles and Float16 outputs; game/console picture acceptance remains open | Restores missing effects/foliage and supported shader translations; no frame gain claimed | oot-visual |
| `DM_NVN_VISUAL=1` | Off; ON in recommended play build | Changes image aliases, texture write ranges, mesh prewarm and output-limit PSOs; gameplay still needs checking | Host half of visual correctness ports | oot-visual |
| `DM_NVN_MESH_INDIRECT=1` | Off; separately enabled in recommended play build | HIGH: provisional NVN2 `{count, first}` record layout; logs first eight records for acceptance | Enables otherwise missing indirect mesh draws; console layout remains unverified | oot-visual |
| `DM_SAFE_GPU` | **On for Ocarina Mac**, off elsewhere; **do not ship watchdog default-on until oot-stable-fix** | Known watchdog false-stop and auxiliary residency cleanup races (review 2); stops the process on GPU errors, stalled feedback or memory pressure; cannot guarantee driver recovery | GPU memory capped at 70% of recommendedMaxWorkingSetSize, conservative system wired-memory cap, no submission after refusal | oot-stable |
| `DM_NVN_RES_LIMIT_MB` | Existing working-set guard; safe mode enforces its stricter cap | Lower limit can stop early; higher values or `0` cannot bypass safe mode | Optional lower cap for prevention; no FPS gain | oot-stable, #1391 |
| `DM_NVN_GMEM_ALL=1` | Off | Exposes all raw pools and increases residency pressure; leave off | Diagnostic comparison against address-mark filtering | oot-stable, #1394 |
| `DM_TEST_GPU_HANG` | Off | Fault injection stops safe-mode process; never set for play | Synthetic callback/diagnostic test only, no real GPU hang required | oot-stable, #1382 |
| `DM_FAST_CLOCK=1` (module rewrite) | Off; exact `1` enables | Counter frequency/epoch, pause, capture and fallback semantics need gameplay acceptance | Branch microbenchmark 22.6 to 8.8 ns per read, 45 SDK sites; not integrated gameplay gain | oot-clock |
| `SEEN_SHADERS`, `--seen-shaders` | Off; require `False` / `--no-seen-shaders` for play | Partial maps omit geometry/effects; not acceptable for the user | No runtime shader compilation: full offline shader corpus required; lazy shaders stay off | Existing packer, user play-build rule |
| `DM_PRESENT_EDR` | Unavailable; proposed only | No proven guest HDR contract | Future-only note, not an exposed flag | oot-vqa |
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

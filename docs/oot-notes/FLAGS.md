# Ocarina integrated controls

The tables cover controls added, changed or used for experiments by `oot-stack`,
`oot-cpu`, `oot-mem`, `oot-1203`, `oot-idle`, `oot-upscale`, `oot-bench` and
`oot-msl`, `oot-tbdr`, `oot-stagecache`, `oot-vqa` and `oot-quality`. Defaults describe an unset environment on the Ocarina profile.
Expected gains are hypotheses or upstream reports, not measured gameplay results
on this integrated branch. Check pictures before accepting any efficiency gain.
The complete repository inventory remains [env_switches.tsv](../env_switches.tsv).

## Review exclusions

The independent review blocks `oot-mem` and `oot-1203`. Their merge commits were
reverted with `git revert -m 1`; the historical rows below describe unavailable
controls, not runnable experiments. `DM_ECO_HIDDEN=pause` is **do not use: audio/clock
mismatch, fix pending**. `oot-mem-fix`, `oot-1203-fix` and `oot-idle-fix` remain pending.
The original growing-pool correction and readable-tile memo from oot-stack remain
unconditional prerequisites. Flag-off is therefore not an unchanged oot-base.

## Feature switches

| Env var or build flag | Default | Visual risk | Expected gain | Source branch |
| --- | --- | --- | --- | --- |
| `DMSH_RAW_LOAD_QUADS=1` (shader build) | Off; only exact `1` enables | Raw address lookup or interval errors can corrupt pixels; compare scalar/quad outputs and latency | Shares four adjacent raw reads' lookup; upstream reports about 2 ms GPU with increased present latency | oot-stack, #1405 |
| `DM_PRESENT_ABSOLUTE=1` | Off | Cadence, scanout latency and game speed need on-screen checks | May prevent cumulative relative-present delay; unmeasured | oot-stack |
| `DM_ECO_COPY_WAIT=1` | Off; Mac only | Low image risk; scheduling, deadlock and late-frame risk | Stops consumer spinning when uniform-copy worker is delayed | oot-cpu |
| `DM_ECO_COMPILE_THREADS=1..64` | Unset/0 disables; invalid values disable | Longer preparation or first-use hitches; does not change shaders | Less competing compile work per pool; no warm steady-state saving promised | oot-cpu |
| `DM_NVN_TEX_DEDUPE=1` | Unavailable; Mac only | Experimental page faults and restore I/O; texture reads and loading require visual checks | Releases cold guest copies; upstream reports about 1.9 GB, not reproduced here | oot-mem, #1386 |
| `DM_NVN_TEX_DEDUPE_AGE_MS` | Unavailable; historical 2000 ms; inert without dedupe | Short ages increase release/restore churn | Trades retained bytes against I/O | oot-mem |
| `DM_NVN_TEX_DEDUPE_MB` | Unavailable; historical 32 MiB per submission; inert without dedupe | Large budgets can stall submission | Bounds synchronous backup/release work | oot-mem |
| `DM_NVN_TEX_DEDUPE_DIR` | Unavailable; historical `TMPDIR`; dedupe refuses absent/unwritable storage | Blocked: failed BUSY restores could return before bytes were safe for GPU residency | Unlinked disk backup enables release; does not shrink Metal textures | oot-mem |
| `DM_NVN_UPLOAD_TRIM=1` | Unavailable; Mac only | Later uploads reallocate and can hitch | Zero to 192 MiB of retained staging after 120 unused submissions | oot-mem |
| `DM_NVN_BORDER_SPLIT=1` | Unavailable; only exact `1` enables | Sampler changes must select/invalidate the correct `_b`/`_bb` PSO; check custom borders | Removes correction code from eligible ordinary pixel shaders | oot-1203 |
| `DM_ECO_SAME_FRAME=1` | Off; only exact `1` enables | Wrong sameness proof could leave stale scanout; synthetic tests cover conservative refusals | Avoids display-only GPU work for repeated proven GPU-only images; never skips guest submissions | oot-idle |
| `DM_ECO_HIDDEN=pause` | Off | **do not use: audio/clock mismatch, fix pending** | Blocked until queued audio and guest clocks pause together | oot-idle |
| `DM_ECO_HIDDEN=slow` | Off | Hidden progression may slow; verify resume | Caps each NVN acquire/vsync caller at 8 Hz | oot-idle |
| `DM_UPSCALER=game` / `metalfx` | `game` | Spatial substitution changes reconstruction and sharpness; check motion, edges and colours | Replaces eligible standard NDSR compute work; no Ocarina GPU result | oot-upscale, existing control |
| `DM_OPMODE=0` / `1` | `1`, docked | Handheld intentionally lowers image resolution; not visual equivalence | At equal palette level, 43.75% fewer scene/final pixels; not a whole-frame saving | oot-upscale, existing control |
| `DMSH_CBUF_REUSE=1` (shader build) | Off; only exact `1` enables | Constant reuse changes register lifetime/scheduling; check images and occupancy | One sampled compute AIR decreased; sampled pixel AIR did not; no frame result | oot-msl |
| `DMSH_STORAGE_RUNS=1` (shader build) | Off; only exact `1` enables | Wrap fallback and four-byte alignment need GPU checks; can add branches/loads | Shares addresses in off-grid read-only storage runs; may regress GPU cost | oot-msl |

All three `DMSH_*` experiment switches compose in `dmsh_chain.options()`.
Their tools enter `FILES` and `CODE_FP`. Each combination requires its own
regenerated header, matching shader libraries and rebuilt host. Runtime switches
cannot enable a build pass. No full shader build was run for this integration.
The blocked border split is absent from active stage keys and library routing.

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
| `DM_GUEST_FILE` | Unavailable after revert | Historical compatibility guard only | No file-backed guest implementation is included | oot-mem |
| `DM_NVN_DIRTYCHECK` | Off | Diagnostic hash/read overhead | Verifies uploads; not an efficiency switch | oot-mem |
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
| `DOTNET_PROCESSOR_COUNT`, `DOTNET_CLI_TELEMETRY_OPTOUT`, `DOTNET_SKIP_FIRST_TIME_EXPERIENCE`, `NUGET_PACKAGES` | Rebuild recipe uses `4`, `1`, `1`, isolated audited cache | Build provenance only | Cooled exact-version feed; no restore/install needed in this integration | oot-stack |
| `DM_GAME_UPSCALER_KEYS`, `DM_GAME_UPSCALER_N` (generated macros) | 22 standard NDSR compute keys | VR/NDVE must remain excluded | Existing profile derivation; not user-settable env switches | oot-upscale |
| `DMSH_CHAIN`, `DMSH_GMEM_MAP_ENTRIES`, `DMSH_GMEM_MAP_ENTRY` (compiled ABI) | Generated chain; 4096 minimum entries; 32 bytes per entry | Host/translator ABI mismatch can hang GPU | Growing power-of-two table through 2^20 preserves existing low-entry hints | oot-stack |

No branch adds a user-facing C compiler optimization flag. #1360's growing
pool table and #1161's readable-tile function lookup are unconditional source
fixes inherited from `oot-stack`. The #1203 library splitting and memory experiments have been reverted. Idle submission accounting also
runs with experiments off. No feature default was changed during integration.
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

# Final AOT and foliage integration

Merged oot-aot a876c45a and oot-foliage eb699305 after their reviewed ancestors.
Existing commits were preserved; these late additions supersede earlier checks.
Archived every incoming implementation note separately. Kept colorspace and
quality presentation, the MetalFX barrier fix and all reviewed GPU safety work.
Added AOT accounting to the merged sharpening and NaN-scan compiler paths.

Kept raw_load_quads, border splitting, constant reuse and storage-run inputs.
Grouping is default-off and passes readonly explicitly through the stage cache.
The complete FILES coverage regression remains in the tools suite.

The final source snapshot uses the original 57 cooled packages from the audited
private feed. Four asset manifests match exactly. One final publish after both
late merges uses PathMap=/_/nxnative; the inherited universal launcher stays.
The optional PDB is omitted to avoid its absolute SourceLink paths. No third-party
translator was executed. Earlier integration publications were superseded when
the requested source scope grew. Full evidence remains outside Git.

DM_AOT=1 is in both packer and runtime recipes; strict mode is diagnostic and
cannot establish complete offline coverage. No gameplay compiles are allowed.
Lazy shaders stay off. Final tests and branch selection are recorded separately.

Merge review found that Brent's synchronous visual mesh builder bypassed AOT;
it now uses aot_mesh. Its depth-only fragment is a compiled host library rather
than runtime source. Exact AOT keys conservatively retain depth/stencil formats from the legacy
descriptor. Metal 4 has no depth/stencil format setters, so those fields are
not sent to its compiler descriptors. The native fixture checks key separation
and valid replay through the actual Metal 4 API.

## Upstream-main variant

Base is origin/main resolved at creation: eab0aaac, including a334797d's PCM
blocks and the upstream 64 GB alias/heap accounting fixes. The gated Brent copy
of alias/heap layout is removed here. Upstream packed shader-library loading and
single-file compile storage remain intact. AOT planning, digesting and bounded
compiler extraction now support packed shader inputs and host helpers together.
A regression compares real packed bytes, descriptor rows and cache digests.

The merged translator's C# and build inputs are byte-identical to oot-hyper;
only the vendor README differs. Both use the same final audited source-built
bundle, with no additional restore/publication and no third-party artifacts.
Each branch regenerates its own chain header. Main source fingerprints are
recorded separately. Existing commits and all feature merge history are kept.

The full main graphics suite exposed the miner's folder-reader dependency on the
older cache API. Its explicit read-only folder adapter now supplies STORE.names
without opening or migrating a cache database. The existing incomplete/current
publication regression covers the repair. Python graphics is rerun after it.

Final verification is green for both branches. oot-hyper-main is the recommended
basis for the next complete play build, with DM_AOT=1 in both packer and runtime.
All experiments remain default-off except inherited/profile defaults; the play
recipe explicitly enables reviewed correctness/stability and srgb. Complete
pipeline coverage and image/gameplay acceptance remain parent gates. No game,
full shader build, push or PR ran. Final results and cleanup are in docs/oot-notes.

## Review 3 fixes

Created oot-review3 from oot-hyper-main 64a163ba. Restored upstream VOTEU and
guarded-handle corrections unconditionally, leaving only local additions gated.
Moved their behavioral tests out of the visual-only gate.

Static inspection found the guest indirect call and decoded the SDK procedure
table and command-segment writer. The driver consumes two words, but neither
the indirect macro nor the game buffer's producer establishes their order yet.
Kept the experimental converter's layout explicitly provisional. Removed its
flag from the play recipe. Added GPU rejection above the existing cap and on
first-plus-count overflow, followed by a host snapshot check before mesh draw
submission. Raw logging covers the first eight records. These diagnostic waits
cost performance only when the existing experimental flag is enabled.

Strict AOT retains report-only fallback. Documented a separate reject-mode
design without changing its runtime implementation. Translator source rebuild,
shader comparisons, tests and host-build evidence are recorded in the external
review-astra-3-fixes report. No game, full shader build or protected build writes
are authorized. No push or PR is authorized.

The final candidate translator was published once. A separate upstream source
reference was built to compare default outputs without running shipped upstream
binaries. Eight targeted fixtures match upstream default and prior enabled
output. All 38 sampled game shaders match prior enabled SPIR-V/reflection.
Broader default equality is not claimed because this branch retains earlier
raw-memory translation changes. Tests and builds finished before the CPU-priority
instruction are recorded as such. Remaining native checks were lowered to nice
19, and all subsequent heavy commands use nice 19. The play log is read-only.

Final verification passes: tools 1,368 tests, graphics Python 417 tests,
Metal/GPU translator 295 tests, native graphics make run with 128 native targets,
the final mesh cap/overflow fixture and host build. Document/chain checks pass.
clang-tidy remains unavailable. No generated roots were removed because T3
processes retain working directories in this checkout. The eight .NET bin/obj
roots, host outputs, native fixtures and private evidence are inventoried and
retained for review. No protected game root was written.

## PR 1439 port

Branched oot-1439 from oot-review3 b3e29584 and fetched upstream PR #1439
45996122. Ported its held-object count into all four serial-table writer paths,
beside the base lineage's generation updates. tex_put keeps its active-ghost
routing and same-object release guard. The upgrade still replaces slots in place.
The pool-retired, AOT and stable paths have no additional serial-table writers.

The stable branch's serial_holds also follows texture-view parents. Counts now
include those ancestors, so the faster lookup preserves that protection.
DM_NVN_SERIAL_HELD=1 enables the lookup; the default keeps the original walk.
DM_NVN_SERIAL_HELD_CHECK=1 enables a count-versus-walk diagnostic unless NDEBUG
is defined. It aborts on a queried count mismatch and defaults off.

Tests cover live/ghost ownership, serial replacement, shared names, texture-view
parents, upgrades at the growth threshold and deliberate diagnostic corruption.
The upgrade fixture now uses serial_put for its synthetic names so it follows
the same ownership rules as production. No shader or chain inputs were changed.
Game execution, regression game runs, pushes and PR creation are excluded.
All heavy commands use nice 19 and at most four combined build jobs.

Verification passed: t_alias_takeover has 53 checks in each of default, fast and
checked-fast modes; deliberate count corruption aborts as expected. Nine affected
targets passed in default and checked-fast modes: upgrade_alias, pool_retired,
tex_dedupe, deferred_release, srgb_alias, image_alias, copy_alias, res_guard and
defer_chain. Host build passed. Documentation and chain checks passed all 28 tests.
clang-tidy could not run because the tool is absent; no packages were installed.
The first expanded takeover fixture also covered an intentionally unheld texture;
its synthetic cost case now uses a separate pool key so it checks only its own
held entries. No production fix was needed for that fixture failure.

Retained generated host gen/, dmhost and ten native test binaries for the parent's
integration review. No generated storage was removed. No protected build, game,
shader-chain input or translator output was changed. Independent review and game
visual/performance acceptance remain parent gates.

# Ocarina play build implementation notes

Basis: `oot-hyper-main` (`64a163ba`). Work branch: `oot-play-fixes`.
Follow `docs/oot-notes/PLAY-BUILD.md`; preserve the baseline as read-only.
Build into a separate output root; APFS-clone extraction only. No shader cache reuse.
Use the existing Python and .NET; install nothing. No game launch or env installation.
Play flags produce chain `992d6981956f`; bundled tools pass the lock check.
Four shader workers and four rewrite workers follow the recipe. Disable heap/region
launch probes explicitly. Build/runtime environment and evidence remain external.

User requested full build speed: J=16 and make -j16. The offline planner now
accepts opt-in DM_PSO_J and DM_METAL_PACK_THREADS (both default 1), enabling
independent cached archive batches and the final merge to use 16 workers.
No shader semantics or runtime settings change.
## Brent round 2, #1430, 5cb7d718

Keep depth-writing pool draws in a pass with DM_NVN_FB_DSELF=1. Preserve attachment profiling and the original default.

## Brent round 2, #1427, f684c7eb

Refresh raw table words with DM_NVN_GMEM_COMMIT=1. Use ba07d353 bitmap-log adaptation and retain local exposure filtering and hint ABI.

## Brent round 2, #1393 follow-up, 0eeccf00

Preserve live shared textures under the existing default-off DM_NVN_POOL_SKIP_RETIRED policy.

## Brent round 2, #1334, 76cfd109

Gate tensor output with DMSH_HMMA_TENSOR=1 and Apple10 runtime selection with DM_NVN_HMMA_TENSOR=1. Apple9 keeps the existing simdgroup_matrix path. Include cd5f3040 ABI-literal cleanup. Chain header follows the single source publish.

## Brent round 2, poolstat/texstat, 01cce669

Add explicit DM_CTL poolstat and texstat diagnostics. Preserve local texture storage fields and safety policy. No automatic diagnostic dump or quality change.

## Brent round 2, #1388/#1353 table refresh, 62e966b8

Restore three NDSR keys and facts from the corrected split. The splitter algorithm remains behind DMSH_OOT_VISUAL=1. No profile switch is enabled. Re-split prepared inputs before using the changed numeric shader indices; rebuild shaders and the AOT archive.

## Brent round 2 verification and handoff

The six source ports start at oot-hyper-main 64a163ba. oot-review3 had the same
head at comparison. Fetched origin/main is c83c48f2. The external comparison
report accounts for all 56 commits, including 34 non-merge source commits.
Cloud branches were fetched for integration notes only, never merged. Their
rewritten bases require selective cherry-picks and duplicate-port checks.

One source translator publish used 57 live-audited NuGet versions, all older
than seven days. Restore used an isolated audited feed, disabled parallel
restore and NuGet audit, no runtime ID, and two build jobs. The four translator
asset manifests match the exact allowlist. Publish used no restore, a portable
PathMap and no PDB. No third-party translator was copied or executed. C# sources
are unchanged from the base; the optional HMMA lowering is a Python MSL pass.
The locally built project DLLs, lock and default chain header are committed.
Default chain b21db59c74dc becomes 0a1b16ea927d with DMSH_OOT_VISUAL=1 and
219d47bbcf7e with the additional DMSH_HMMA_TENSOR=1. Other build flags also alter
these stamps, so final integration must regenerate its own matching header.

Final verification: tools discovery ran 1,368 cases with 24 skips; graphics
Python ran 419 cases with four skips, including translator/Metal/GPU checks.
The complete native graphics run passed all 129 executable targets and its
Python pull/budget checks. The raw-word fixture passed 17 checks, including the
default-off gate. Retired shared descriptors passed 13 checks. Both render modes
passed the depth-reader fixture. Six HMMA tests passed, including both numeric
GPU kernels against the CPU reference. The final host build and 39 final
docs/environment/chain/ABI tests passed. No baseline was weakened. Initial
fixture/ABI failures and their corrected final runs remain in the evidence logs.
All heavy steps used nice 19; make and publish used at most two jobs per command.

No game, full shader build, regression gameplay run, iOS operation, push or PR
ran. The M4 Max keeps its old HMMA helper, proven source-identical, regardless
of tensor flags because it is Apple9. Native fixture success does not establish
gameplay visual parity, FPS, power or Apple10 AOT coverage. Parent review and
integrated game acceptance remain open. The new NDSR table indices require a
fresh split, shader build and archive; the four host-only ports can instead be
picked separately for a quick rebuild with the old matching shader chain.

Private NuGet packages were cleared through dotnet's cache command after an
open-file check. The generated private feed and publish copies were removed.
Audit scripts, dates, configs, logs and the external report remain. Checkout
host/gen, native fixtures, dotnet bin/obj and Python caches remain because the
harness keeps cwd inside this checkout. Unknown paths and other agents' artifacts
were preserved. No active play build or baseline file was changed.

## oot-play integration

Merged upstream c83c48f2 and oot-play-fixes. Generated translator DLLs, lock
and header conflict in the Brent merge and are deferred to the final source
publish after all source integrations. Neither binary side is selected.
# Ocarina host/runtime harvest

Scope: glass-oot-brent2-movie.md. Baseline a14fb78c. Source brent-oot-combined-new 89a0ff52.

NDVE #1331 (b6367705, 76c20edb, 943b0bea) skipped: bilinear replacement discards the game reconstruction, conflicting with visual-quality priority. No shader chain or stable GPU changes touched.

AV1 d234d4f6 port: DM_AV1_PARALLEL=1 enables delayed decoding; default retains synchronous behavior. Serialize submission/reset using decode lock before buffer lock, avoiding the source patch's unlock-before-decode-lock window. Mac runtime verification remains open.

AV1 3b588ca6 port: DM_CV_LATE=1 opts into skipping overdue pictures; no pixel resampling. Default retains all pictures. Temporal completeness is traded for synchronization only when opted in.

AV1 7ee81e91 port: guest movie clock, pause/focus rebase and host-stall catch-up, still behind default-off DM_CV_LATE. Existing focus providers reused; only declarations added. No stable GPU path changed. Linux cannot validate Apple decode/Metal behavior.

Verification: final Linux tools discovery ran 1098 tests, with 16 failures, 205 errors and 94 skips (missing Python packages/tools, Python 3.10 versus required 3.12 and Mac-only utilities; not a green suite). Focused docs/env checks passed all 12 tests. GCC strict syntax check passed hle_codec_video.c with a generated Ocarina header, and the AV1 public header passed. Extracted actual clock code and the existing clock assertions passed ASan/UBSan with absent/0/1 flag values. Full Apple decoder integration remains unverified. regress.py impact cannot import libproc.dylib on Linux. Cross-family review unavailable because Claude provider is unauthenticated; no substitute review claimed.
## Brent round 2: misc1

Scoped to #1320, #1355, #1377 and #1379. Neither integrated base a14fb78c nor upstream c83c48f2 has these implementations. Ported #1320 (46975a20) behind DM_NVN_GW_INTERVALS=1, retaining the baseline threshold and range capacity by default. Skipped #1377 (d234d4f6): software AV1 throughput on older Macs, whereas M4 normally uses VideoToolbox; no demonstrated benefit for this target. Skipped #1379 (7ee81e91 plus 3b588ca6): deliberately discards movie pictures, contrary to the quality-first instruction. No existing stable GPU, presentation or shader behavior was replaced.

Ported #1355 (2e1f4953) behind DM_BUILD_NOINDEX=1. All temporary-folder consumers share the selected name. Unlike the source, existing tmp/ is not deleted when opting in; preserve interrupted work. Did not port the later shader-folder migration ea680b3e (separate scope). Both flags require the exact value 1. NSP chain tests: 18 passed. Extracted production C ledger compiled with ASan/UBSan and passed both modes. Full tools discovery: 1099 tests, 16 failures, 205 errors, 94 skips (missing dependencies, Python 3.10.12 vs required 3.12+, documentation checks outside this change; not green). Installed nothing. Claude Opus cold review was attempted but OAuth expired; no independent verdict. Mac validation remains required.
## Brent round 2 host/runtime harvest

The assigned audit compares a14fb78c (oot-hyper-main), c83c48f2 (origin/main),
and Brent 89a0ff52. No dependency installs or third-party binaries are used.

Ported upstream correctness commit 2202d610 (issue #949), with fixture correction
51ea3df8. A layer crop selects texels; layer shape controls display proportions.
It is already in origin/main, so no experiment flag is added. Metal build and
t_present_crop / t_present_alloc need a Mac. Linux checks follow below.

PR #1418 is skipped because omitted texture mips reduce image quality. PR #1436
is 01cce669 (poolstat/texstat), confirmed through gh pr view, and is skipped
because the task explicitly assigns those diagnostics to the Mac agent.
Our existing PR #1391 guard and DM_SAFE_GPU remain in place.

Ported temporary-folder exclusion from PR #1355, source 2e1f4953, behind
DM_BUILD_NOINDEX=1 (default off). All capture/heap-check scratch paths follow
TMP too; the source commit left these under tmp/. Old tmp/ is preserved.

Ported PR #1438 from ea680b3e behind the same DM_BUILD_NOINDEX=1 switch.
Shader data is renamed only on opt in; an existing destination and symlinks are
preserved. Reader tools accept both names. Resolved mac_pso against our AOT
seen-descriptor support, keeping both changes. New tests cover folder migration
and compatibility. Keep the flag consistent to avoid separate shader caches.

Spotlight checks passed on installed Python 3.14 without installs: 51 tests
cover chain/migration, work-dir, benchmark and bug-report paths. mac-app tests
need BSD cp -cRX; regress tests import libproc.dylib at module load on Linux.
Review fixed the formatted shader-capture scratch path and made benchmark /
regress prefer the selected folder when both shader layouts exist.

Ported PR #1392 from 8cf26912, gated by DM_NVN_IDLE_RETIRE=1. The existing
#1391 guard, safe GPU caps, linear deferred partition and #1393 retired-ID
policy remain intact. Pending additions count before commit. Small and large
pool buffers can retire without an unsubmitted future fence. DM_CTL focus
is an explicitly invoked diagnostic, as in the source.

Independent Codex review found two source-port concurrency risks. The final
port reserves a persistent retirement fence under g_mu at submission begin,
rather than reading g_cb beside g_fence. A single async worker performs idle
draining, so a stuck residency lock cannot block the watchdog timer. Review
also found old large-pool chunks needed the same fence; that path and a test
fixture are included. Claude review could not run because its provider is
not authenticated. Metal tests remain unrun on Linux.
## Optional Mac HDR port

Created oot-hdr from oot-hyper-main at 64a163ba. Ported the Mac changes from
PR #1176 fetched at a360806f. Omitted unrelated game validation and the iOS
frontend. The launcher HDR setting is offered only on Mac Switch 2 builds.
DM_HDR remains off by default. The fetched head now defaults to a PQ layer;
DM_HDR_LAYER=float retains its extended-linear BT.2020 path.

Static v131072 inspection establishes the game's output path. Main calls the
HDR status query and paper white. The SDK interprets format 1 as HDR. Main and
UI scene configs enable HDR. An agl output shader contains the BT.709-to-BT.2020
matrix and all PQ constants. The game's note records addresses and shader key.

Kept the existing SDR source tagging, quality filtering, sharpening, AOT helper
hooks, crop and absolute present cadence. The quality and HDR constants occupy
separate float4s. PQ bypasses the SDR-configured MetalFX scaler; scaled SDR is
converted only in the final present. Combined checks compare HDR white against
the same scaled SDR output because MetalFX can shift saturated SDR by one code.
2202d610 is absent from the base, so no crop redesign was included.

Native checks cover HDR on Metal 3 and Metal 4, unset and zero defaults, quality
plus P3, ColorSync comparison, quality variants, crops, snapshots, allocators,
rescue and eco-present. Settings and documentation tests pass. The host builds.
No game, regression harness, shader translation, installation, push or PR ran.
Only the embedded host present shader was rebuilt. Existing game libraries stay
valid, but HDR-specific AOT archive coverage and display acceptance remain open.
The parent task owns independent review. External evidence and hdr.md are kept
in the shared task workspace. All heavy commands ran at nice 19.

## oot-play review integration

Integrated the requested local branches and unique cloud source ports. Upstream
c83c48f2 supplies the crop and cube-array correctness fixes. The cloud contributes
only its four retained features. Misc2 supplies complete capture/noindex paths
and asynchronous idle retirement. Movie ports remain opt-in; their lifetime lock
was adapted to this lineage's always-serialized decoder API. No mip omission or
NDVE bilinear replacement is included.

Review 4b fixes remove the accidental tensor gate from readable-tile compilation,
restore HID diagnostic stubs and adapt the retirement fixture to marked pools and
gmem_map. A cache-miss regression covers tensor absent, zero and one. Review 4a's
HDR fix derives the MetalFX format from the raw view; a direct-encoder test checks
both HDR targets and the scaler compiler counter. Exact present descriptors enter
the AOT inventory and startup prewarm. Inferred mesh pairs require proven matching
MSL outputs and fragment inputs. Mesh layout and strict AOT remain open gates.

The translator was published once from the integrated source after auditing 57
NuGet publication dates. Restore used only that feed; all four assets manifests
match the allowlist. Publish omits PDBs and maps source paths to /_/nxnative.
SPIRV-Cross was built locally from its pinned source, with at most two jobs.
Generated DLL conflicts, lock and header are rebuilt, never selected from a side.
Default and play chain labels and source fingerprints were refreshed.

The user selected SDK22, raw-commit, GPU-lost and serial-held in the play recipe,
with safe GPU, AOT and strict reporting. Fresh builds use noindex. Every other
new performance or visual experiment stays off. No game, full shader build,
Application Support update, baseline write, push or PR ran. Final verification
and storage results follow in the handoff. Current fixture checks are in progress.

User clarified that incompatible AOT-inferred pairs must be dropped, never padded.
Reverted the mesh-output padding commit before rebuilding; chain is again
992d6981956f. AOT offline compilation now bisects descriptor refusals, caches
successes/refusals, filters the packed prewarm inventory, and records the exact
refusals. Non-AOT and infrastructure failures remain fatal. All 42 archive tests
pass. Run at J=16, 16 archive workers, 16 merge threads, make -j16.

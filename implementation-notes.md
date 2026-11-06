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

Final Linux verification: 62 focused Python/doc tests passed. Broad tool tests
ran 110 files: 77 passed and 33 failed on the recorded environment/toolchain
issues; test_xlate_anycpu was excluded. test_spirv_cross_pin should also have
been excluded: its attempted bundled executable was rejected by Linux before
execution. No packages were installed or translator binaries touched. C syntax
checks passed for hle_hid.c, hle_vi.c and t_hid.c with existing portability
warnings. Env-switch check has only the existing six stale doc mentions.

The report and per-file outcomes are in docs/oot-notes/oot-brent2-misc2.md and
oot-brent2-misc2-tests.json, with the requested report mirrored under
~/code/nxnative-research/reports/. Mac verification remains open for all
runtime source changes. Push target is ankmister/oot-brent2-misc2.

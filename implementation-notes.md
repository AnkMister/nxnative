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

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

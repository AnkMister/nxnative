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

The first complete shader pass produced 42,853 successes / one known false BAHS
translation candidate. Archive batch 38 exposed three real foliage mesh links
missing fragment varyings. Applied the existing NVN vertex default-output rule
to source-paired native meshes, gated by DMSH_OOT_VISUAL. Real offline compilation
of all three formerly failing pipelines passes; 28 padding/cache tests pass.
Rebuild the matching chain and host; unchanged Metal source binaries remain
cached by compiler and source content, and completed archive batches are cached.

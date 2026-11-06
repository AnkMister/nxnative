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

## PR 1444 stutter lane

Base: oot-hyper-main 64a163ba. Upload and packaged-alias changes are opt-in
with DM_NVN_P1444_STUTTER=1. Retained the texture-only pool fallback and the
cold-page dedupe experiment's transient buffers. Cached sources are held through
upload completion and invalidated by overlapping pool removal. Sparse packaged
uploads gather pages after staging allocation and use the existing GPU encoder.
The upstream sparse GPU branch is later in pkg_upload_, after the older
non-sparse branch. The port shares its existing encoder loop and gathers after
staging allocation, avoiding the upstream source-retirement race on a flush.

Ported the unbounded packaged alias map, overlap invalidation, persistent hits
and finalized-descriptor reuse. NvPkg fields, deallocation and texture recycling
remain the texture lane's ownership. Its alias-drop ordering must survive merge.

Mesh/object function notes hold portable identities rather than legacy Metal 4
function descriptors. Ordinary vertex-only planning excludes mesh reflections.
Typed mesh AOT descriptors, inference, archive lookup, learning and compiler
accounting remain. Invalid mesh/stripped base specialization is guarded here as
a new repair because the fetched source does not contain the described guard.
Every fallback still routes through a compiler-accounted helper.

Ported descriptor refusal isolation and parallel archive builds from 71b8bec4
without reverting packed-library readers or extraction. The final oot-play base
already contains that repair; merge should retain its version. Added the loader
fixture presentation stubs. No game, translator, shader-chain rebuild, install,
push or PR ran. The lead owns final integrated verification and cold review.

Intentionally omitted upstream reversions of romfs/shader_lib, the loss of the
texture_only source fallback, raw-pool filtering, AOT wrappers/counters, and the
existing visual mesh path. Other lanes own texture upgrades, NvPkg recycling,
terrain/attachment policy, shaders, services and profile keys. Unrelated changes
to segmented-submit defaults, readback/absorb policy, retry depth and prefetch
compilation were not imported. Validation and storage details are in the external
p1444-stutter handoff.

Verification before the user pause: 43 offline PSO tests passed. The pool fixture
passed with the stutter gate off (102 checks) and on (712 checks). The sparse
fixture passed off (4,252 checks) and on (4,259 checks). The loader fixtures and
the final host build passed. Native AOT, PSO archive and remaining upload test
execution is pending. The user stopped the final gfx build and forbids all
builds, tests, compiles and restores until an explicit RESUME. Preserve its
processes and generated outputs for that continuation. No cleanup was run.

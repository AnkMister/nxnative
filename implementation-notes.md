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

## PR #1444 texture lane (static-ready, verification paused)

Branch `p1444-tex` starts at `64a163ba`. Source inputs are upstream `a15c0415`
and `e03bdc8f`, local `oot-review3` (`b3e29584`), and local `oot-1439`
(`575f834e`). No third-party binary, game, shader-chain build, push or PR ran.

`DM_NVN_P1444_TEX=1` enables the ported texture behavior. It unwraps texture
parents, replaces placement-heap textures in their actual heap, updates serial
and ghost entries in place, preserves #1439 ancestor counts, and records each
affected serial with `ser_note`. It recreates a sampling view only for compatible
sRGB/linear storage. Image preparation persists IMAGE intent and upgrades integer
image views before opening a pass. Attachment resolution suppresses first-use
CPU snapshots. Alias eviction records serial notes, protects every view ancestor,
keeps upstream's 512-submission idle interval, and marks evicted retired descriptor
views gone. Retired packaged IDs skip unbound pool walks while #1393's explicit
pool skip and submission-local view lifetime remain intact. VIRTUAL pools skip
flush tracking; NULL pool/buffer queries are guarded. Readback retains our tighter
16-buffer/16-MiB cap with upstream's eviction policy.

`DM_NVN_DISPATCH_CLAMP=1` enables upstream's GPU dispatch-dimension clamp; the
texture gate also enables it unless explicitly overridden with 0. Missing clamp
pipelines and misaligned arguments refuse the dispatch. #1439 counting stays
behind `DM_NVN_SERIAL_HELD=1`, with `DM_NVN_SERIAL_HELD_CHECK=1` for a debug walk.

The indirect mesh path already existed locally. The lane carries over review3's
GPU snapshot, count cap, overflow rejection and refusal path under the existing
default-off `DM_NVN_MESH_INDIRECT=1`. The upstream kernel also interprets its two
words as count then first. Its reported 274,851-frame gameplay session supports
that interpretation for this title, but neither the commit nor PR supplies a
producer disassembly proving the ABI. The interpretation remains provisional.

The dynamic #1360 GMEM table and its per-submission commit words remain intact.
The upstream fixed GMEM_RUN cache would regress that design. The pool test now
also checks all 521 contiguous 64-KiB pools. #1390's exact GPU-written ranges
remain intact, including for 260/68 terrain tiles, rather than adding size
exceptions that could ignore a GPU write over a tile. #1394 residency, #1420,
DM_SAFE_GPU and the existing AOT/visual/foliage paths are preserved. The local
lookahead suite already contains every upstream case plus stronger conditional,
depth and compute-reader cases, so it is retained. `nvn_dirty` has no e03 changes
to port; this lane does not add unused copy-absorption helpers from a15.

NEW work, absent from e03: `DM_NVN_BCRT=1` redirects plain BC1/BC4 colour targets
to uncompressed full-resolution shadows and GPU-encodes their selected mip and
slice back after the pass. Static evidence was `rt_view_fmt` refusing a plain BC
format, `attach` clearing its attachment, and `rp_begin_ex_` refusing a pass with
no usable target. The existing block-sized integer-view path stays intact. The
new path supports BC1 including sRGB and BC4 UNORM, preserves Load/Clear, and
refuses layered draws. It is lossy compression with simple endpoint fitting,
not a proven match for the game's compressor. The new GPU test checks encoded
mips with an independent CPU decoder, GPU sampling, and unchanged neighboring
mips/slices. Gameplay and visual acceptance remain unverified.

Ownership stays separate from the stutter lane's `pkg_upload`, `up_big_src`,
`g_pkg_alias`, `tex_mtl_` alias lookup/insertion and `mtl_tex_release` retention.
`mtl_alias_drop_pool` overlaps only at cleanup: retain the stutter lane's package
cache cleanup and this lane's serial notes and descriptor-before-CPU cleanup.
The lead owns flag/build docs and final integrated verification on pinned
`oot-play` commit `e8c3bc222b06413347d533fca7e060a69943c57a`.

Validation is pending. A nice-19, two-job focused test build first exposed a
duplicate alias_sweep and a missing forward declaration. Both were corrected in
source. The replacement build was SIGSTOPped by the user before completion.
No test executable ran; the attempted test runner exited because the first
binary did not yet exist. No host build ran. The user forbids builds, tests,
compiles, restores and process resumes until explicit RESUME. Only static
inspection and `git diff --check` ran after that pause. Stopped outputs predate
later source edits and are not final-build evidence.

Storage cleanup removed nothing. Generated host headers under `dm/host/gen`,
test outputs, and task scratch/log files are retained because the paused build
still owns them and verification is pending. No install or dependency update ran.

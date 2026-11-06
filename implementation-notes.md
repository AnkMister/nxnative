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

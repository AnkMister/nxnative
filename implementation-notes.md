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

## PR #1444 services and profile port

The p1444-svc lane starts at oot-hyper-main 64a163ba. The lead integrates onto
the separately pinned oot-play base e8c3bc222b06413347d533fca7e060a69943c57a.
Only local commits are authorized. Existing experiments and notes are retained.

Compared 634305a6 with the existing #1345 audio port. The offset-discovery code
is equivalent; keep the existing DM_OOT_BRENT=1 gate. The audio virtual-device
and prepo AsyncContext implementations already match #1444, so no second forced
registration or another implementation was added.

Ported the remaining finite eventfd wait policy behind DM_SDK22_SERVICES=1.
The original 23 eventfd checks stay and four checks cover the opt-in timeout,
wakeup, counter and negative-timeout slice. Added the Ounce vibration query
with #1434's false result, consistent with advertised Switch 1 actuators.
Reused oot-brent2-cloud's loader gate and lookup checks byte for byte. Other
#1434 hooks remain on that separate lane. The lead owns independent review.

The user explicitly approved the Ocarina game.tsv changes as defaults. No
DM_OOT_PROFILE_1444 flag was added. Existing render_cond and safe_gpu stay on;
the new memory/upload/timestamp values and old values for rollback are in the
game note. The inherited e9d71e27 and eab0aaac implementations were not copied
or changed. The registered v0 row and resolution-only patches.py remain;
upstream's v131072/1.1.1 versus prose 1.2.0 discrepancy is flagged.

The game note and frame-rate reference explain the native 60 fps cadence.
DM_FPS_TARGET cannot unlock this main. The 4K 120 Hz display recipe uses
DM_PRESENT_LINK=2, DM_PRESENT_HZ=60 and DM_PRESENT_INTERVAL=game, with
DM_FPS_TARGET=0. The M4 Max's 1440p override and SDR/HDR limits are explicit.
Neither 60 fps at the new resolution nor native HDR is claimed locally.

Verification runs at nice -n 19 with at most two native make jobs per command.
The first host-test attempts exposed the inherited nvn_eco_wait link omission
in SDK-including tests. Link the real nvn_eco.c into language, shared-font,
NFC and system-event tests; no runtime stub was added. Docs, profile tests,
host tests and the host build have separate logs in the external work folder.
Final results and exact generated storage cleanup are in p1444-svc.md there.
No game, regression gameplay, full shader build or third-party binary ran.

Before the user's compute pause, the host build completed with 57 warnings,
the focused eventfd test passed 27 checks, HID passed 157 checks, symbol lookup
passed, 42 profile/survey/env tests passed and 11 documentation tests passed.
The full host run remains incomplete and SIGSTOPped by user request. Its make
PID is 73048 and its memory-test PIDs are 3152 and 3587, all in group 73048.
No build, test, compile, restore or SIGCONT is permitted until the user sends
RESUME. Preserve the generated host, gen directory and test build directory
while those processes remain pending. The lead owns integrated verification.

The pstack feature checklist is adapted to this assigned implementation lane.
Direct source comparison supplies the subsystem investigation; a new design
exercise and nested delegation are unnecessary for the fixed port. Blocking
work was baseline and overlap comparison. There is one local write owner and
no shared checkout edits. Host-only checks establish the port's local gate;
the lead owns merged graphics, shaders, display and gameplay acceptance. PR
creation is skipped because the task permits local commits only.

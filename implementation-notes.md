# Integrated Ocarina branch

The branch `oot-hyper` starts at oot-stack 8284776d. Stability then visual ports
are the first two feature merges. CPU, idle, upscale, bench, MSL, TBDR, stage
cache, VQA, quality and clock follow as separate merge commits. The reviewed
stack/idle replacements follow; fixed memory and border implementations come
after those original feature merges and remain default-off. Resolution hooks
follow quality ancestry. Final visual/stable repairs precede Brent; the waste
scanner joins the bench tooling. Every incoming branch has an archived log in
[docs/oot-notes](docs/oot-notes/README.md).

The initially merged blocked memory/border revisions were reverted in the
recovery history. The ordered integration used their reviewed replacements.
Original branches and past commit identities were left intact. New commits use
AnkMister after the user's identity correction. Local work only: no push or PR.

## Source and artifact integration

All code was combined from source. Stable resource classification, address-mark
filtering, growing pool tables, retained-map write-log completion, deferred
release and safe-GPU gates remain. Brent retired-ID skipping and completed-log
cleanup are optional. Restore-before-residency and kernel copy preparation come
from mem-fix. The two staging trim policies keep distinct functions and defaults.
The profile-driven safety default is validated and remains on for Ocarina Mac.

Review 2's Float16/integer selector defect, watchdog snapshot race and auxiliary
residency ownership race are repaired. The last committed save is kept on an
emergency stop; an in-progress save can be lost. No save transaction is forced.
CPU race and synthetic Metal checks do not establish genuine driver recovery.

The Metal 4 spatial scaler's output stages are Fragment for presentation and
All for the game-upscaler route. This SDK exposes its getter/ivar without a
setter, so the guarded KVC compatibility path sets that known state and refuses
unknown implementations. Crop and every quality configuration use validation.
Sharpening keeps footprint filtering and P3 conversion. The colour fixture's
uniform layout matches the present shader.

Shader keys cover raw_load_quads, storage_runs, cbuf_reuse, oot_visual and the
fixed border_split option. All chain FILES, including the additional tensor
translator source, enter actual stage or complete-shader fingerprints. The
translation key includes the distribution, merged sources and visual flag.
The pure border pass is cached; the correcting _b/_bx path stays intact, while
optional _bn compilation/load failure retains correction. Shared ABI constants
are used for border metadata without changing its schema.

## Translator provenance

The initial stack/visual source rebuild was superseded when the user added the
Brent tensor source. The final oot-hyper translator has one restore/publish from
the fully combined C# source snapshot (tree 6f5a321b321890271c66d72623279be8baa352b9).
No C# source changed afterward. The inherited universal launcher is retained.
No incoming fork/upstream managed binary was run as the final translator.

The official NuGet publication audit covers 57 exact versions, each older than
seven days. Restore uses only a private cleared-source local feed; all four
project.assets.json package sets match its allowlist exactly. Publish uses
--no-restore, --self-contained false and at most four jobs. The final lock is
regenerated from the locally built bundle. [Package dates and SHA256s](docs/oot-notes/nuget-audit.json)
and [source/distribution SHA256s](docs/oot-notes/translator-fingerprints.json)
are committed. The launcher's embedded digest alone is not full source proof.

## Build choices and remaining work

[FLAGS](docs/oot-notes/FLAGS.md) lists defaults, risk, gain and origin.
[PLAY-BUILD](docs/oot-notes/PLAY-BUILD.md) enables correctness and stability,
uses srgb and keeps experiments off. **The next app build must re-rewrite main
with the merged Ocarina profile.** A host-only build cannot install the three
resolution observation hooks. Their runtime option remains off.

No runtime shader compilation is allowed for play; everything is ahead of time
and lazy shaders stay off. Complete offline pipeline coverage/counters remain
the forthcoming oot-aot gate. oot-foliage is also pending; neither was awaited.
The parent owns full shader/map rebuilding, gameplay/display acceptance and an
independent review. This task runs no game, full shader build or regress.py.

A second branch will start from origin/main resolved when created. It will use
upstream's 64 GB alias layout instead of the DM_OOT_BRENT copy, preserve the
PCM-block fix and packed library loading, rebuild generated translator artifacts
and repeat verification. The passing variant will be named in PLAY-BUILD.

## Verification and storage

Final results are appended after integrated checks finish. Evidence is retained
in the external task workspace under `oot-hyper/`; source paths here are relative.
One implementation agent owns all integrated verification. Task compiler jobs
are capped at four across concurrent commands. The external storage manifest
records generated translator source/feed/cache/publish roots and worktree build
outputs. Known task roots are cleaned only after ownership, tracked-file and
open-file checks pass. Source, Git, evidence, protected inputs, unknown paths
and other agents' artifacts are preserved.

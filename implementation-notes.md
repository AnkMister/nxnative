# Ocarina Mac memory implementation

Scope: task B, branch `oot-mem`, based on `ee9b7765` (PR #1299).
The running baseline checkout and its game work folder were not accessed.
No game builds, shader-chain builds, regress runs, installs, pushes or PR writes.
All Python commands use the supplied uv venv. Compiles use at most two jobs.
Scratch outputs are outside this checkout and TMPDIR is explicitly set.

## Plan and decisions

1. Read AGENTS.md, the memory reference and development loop, and inspect live Git state.
2. Isolate PR #1386's top commit, `562c1f4098d513b08c0011ebac98318ce97d2dd3`.
   Its parent `f3ac5ea` is a large local integration, not part of this port.
3. Inspect `1110473c` (#1198) and `865cc35f` (#1315).
4. Port cold texture backup/release, then reduce retained upload staging.
5. Run Python and relevant graphics tests, and commit the changes separately.

The pstack performance workflow is adapted to this implementation subtask.
Baseline and post-change game traces, regress and PR creation are deferred by
explicit task constraints. No subagents were started. Implementation stays
serial because both changes share the NVN upload and residency code.
The Sequence Work into Verifiable Units principle drove separate tests and
commits for dedupe and staging retention.

## Change 1: cold guest texture copies

Flag: `DM_NVN_TEX_DEDUPE=1`, default off and Mac-only.
Requires `DM_NVN_TEX_DEDUPE_DIR` or `TMPDIR` to name a writable folder.
Use the supplied scratch folder, never /tmp. The backup is unlinked immediately.
Companion settings are `DM_NVN_TEX_DEDUPE_AGE_MS` (2000 by default) and
`DM_NVN_TEX_DEDUPE_MB` (32 by default). Off when `DM_GUEST_FILE=1`.

Estimate: up to the whole host pages of cold, tracked uploaded textures whose
pools are not resident. PR #1386 reports about 1.9 GB for Ocarina on its own
integration. That is an upstream measurement, not a result on this branch or
on this M4 Max. Metal texture allocations are unchanged.

The port contains only the core release/restore code and its tests, without
upstream's texture-breakdown census or stacked mip-skipping changes.
The uploaded private texture stays intact. Cold guest pages have a disk backup,
become inaccessible, and are released with MADV_FREE_REUSABLE. A later CPU
access or GPU residency restores them first.

Deviations and fixes relative to the WIP:

- Release and restore use a host-only Mach alias of the same VM object. Guest
  pages stay inaccessible throughout. This removes the WIP's writable release
  window and its visible partial-restore window without replacing the backing
  object that existing no-copy Metal buffers address.
- The residency mutex covers the release check and release itself. The WIP
  could mark pages BUSY, then wait for this mutex while pool_res held it and
  waited for those pages.
- Restore waits for BUSY pages even when the released-page count is still zero.
  The released-page count is published before GONE becomes visible.
- A failed restore exits with code 88 instead of resuming with invalid bytes.
- The file must be unlinked successfully; path truncation is rejected. There
  is no fallback to /tmp. Dedupe is disabled on iOS.
- The per-submission budget also splits a single large texture candidate.

Dependencies: the base has the dirty tracker, GPU upload batching and no-copy
pool buffers. No other stacked PR was imported. To reproduce the upstream
savings, integrate task A's #1405 texture-only transient uploads and raw-memory
pool filtering. On oot-base, gmem_map makes all pools resident, which correctly
prevents dedupe but can eliminate its savings. When resolving that integration,
keep nvn_dirty_restore before every pool residency addition and before creating
no-copy buffers, including large-pool chunks and transient upload sources.
#1389 changes dirty tracking nearby; preserve its tracking semantics too.

Risk: experimental fault handling, synchronous backup I/O on submission and
restoration latency. A kernel system call reading PROT_NONE guest storage may
return EFAULT rather than fault through the CPU handler. This WIP limitation
remains open; test texture reads and loading carefully. Disk use can reach the
high-water mark of backed pages. VM aliases of guest storage outside the dirty
tracker are not a validated access path. Do not infer a shipping verdict from
unit tests.

## Survey of other memory

- #1198 (`1110473c`) shares sparse placement tiles by physical memory and format.
  The GPU-written contents and physical-pool lifetime govern retention. This
  is already in oot-base; no duplicate tile cache or game-specific rule added.
- #1315 (`865cc35f`) maps guest memory into files. It reduces charged footprint
  without reducing physical bytes while resident, and adds file writes and
  periodic flush stalls. It is not a new Mac efficiency win and was not ported.
- Upload overflow is already bounded to 128 MiB per batch and retired on upload
  completion. Reimplementing this would duplicate existing work.
- Each upload slot retains a primary and overflow private staging buffer,
  at most 64 MiB, across three slots. This is the second selected target.
- Shader libraries already use mmap and dispatch_data with a destructor that
  unmaps the image. No second malloc copy is evident in the host loader.
- Pipeline archives on external drives can be copied internally by Metal.
  The existing reference documents about 1.1 GB in Kirby. The URL-only Metal
  archive API owns that choice. Evicting archives requires a separate pipeline
  lookup/reopen design and could introduce recompilation or loading stalls.
- Private textures support GPU compression. Switching them all to shared on
  unified memory is not proof of savings and can lose compression. No blanket
  storage-mode change was made.

## Validation and parent measurement

Pending final test results below. Tests cannot establish gameplay, peak game
footprint, frame pacing, bandwidth, CPU overhead or visual equivalence.

Parent: wait for the existing baseline run to finish. Build a separate Mac
candidate after integration; do not overwrite the baseline executable. Run the
same save, route, resolution, 30 fps cap and shader inputs with all flags off,
then each flag alone, then both. Keep the other heavy workloads comparable.
Use regress.py's `peak MB` column for peak footprint. Also capture steady
phys_footprint, RSS, compressed memory, Metal allocated bytes, disk writes,
page-ins, CPU, GPU duration and frame percentiles. The dedupe memory line gives
currently released MiB, file high-water MiB, restored pages and failures.
Check house-to-forest travel, repeated scene transitions, texture reads,
loading, movie playback and return visits. Screenshot the same frames.
A lower footprint with equal or larger RSS alone is not proof of lower memory
pressure. Check that savings hold with the game's 30 fps cap and that backup
I/O does not create extra loading hitches or compete with the user's work.

Dedupe verification before its commit:

- `t_dirty_dedupe`, `t_dirty_race`, `t_dirty_retire_race`, `t_dirty_slots` pass.
- The 64 MiB dedupe test measured 65.13 MiB before and 1.09 MiB after release.
  Every byte was then restored from disk and checked. This is a synthetic
  kernel-accounting check, not Ocarina memory or RSS evidence.
- `t_nvn` passes 234 checks with the flag off and 234 with it on.
- `t_tex_dedupe` passes 7 checks with Metal API validation. A previously created
  no-copy Metal buffer reads every restored byte after pool residency; resident
  pools reject release.
- Full Python discovery is running. No host source was changed.
- Independent review is left to the parent. This subtask starts no delegates.

## Change 2: release idle upload staging

Flag: `DM_NVN_UPLOAD_TRIM=1`, default off and Mac-only.
A slot used within the last 120 rendering submissions keeps its reusable
buffers. An older slot drops both only after its GPU completion flag clears.
The residency set is committed and its allocation demand history is reset.
No extra thread, timer or wakeup is added.

Estimate: zero to 192 MiB of steady memory, from two buffers of at most 32 MiB
in each of three slots. Loading peaks may be unchanged because the buffers are
still needed then. The Metal test measured destruction of 64 MiB in one slot.
That is a synthetic resource-lifetime result, not an Ocarina measurement.

Risk: a later upload must allocate again. Intermittent texture streaming can
trade steady memory for allocation work or a loading hitch. Slots used every
few submissions never trim, so movie playback keeps its existing reuse.

Tests: `t_upload_trim` passes with trim off (11 checks) and on (13 checks),
with Metal validation. It holds GPU work behind a gate beyond the idle age,
checks the age boundary, copied bytes, actual buffer destruction and another
upload after trim. The initial lifetime assertion failed until the trim path
committed its residency removals; that correction is included.

Parent measurement: compare off versus on with dedupe held off, then with
dedupe on. Capture the same steady forest scene after 120 idle submissions,
then load another scene and return. The `upload staging: trimmed` line reports
cumulative bytes, not live savings. Compare Metal allocation, footprint,
loading peaks and hitches. Do not subtract cumulative trimmed bytes from RSS.

## Integrated verification

- `make -C dm/gfx/tests GAME=0400486024DEC000 check_t_upload_trim` passes
  11 checks with trim off and 13 with trim on, under Metal validation.
- `check_t_tex_dedupe` passes 7 checks under Metal validation, including forcing
  file restoration before the existing no-copy buffer is read by the GPU.
- `check_t_upload_slots` passes 305 checks with trim off. The same binary passes
  305 checks with `DM_NVN_UPLOAD_TRIM=1`; recurring batches still reuse staging.
- Rebuilt `t_nvn` passes 234 checks with both flags off and 234 with both on.
- The first full Python discovery ran 1,217 tests with 23 skipped and one
  failure. The new compatibility read of DM_GUEST_FILE needed a documentation
  row. That row is now in the dedupe commit, and the table was regenerated.
- No host source changed, so the host Makefile suite was not required.
- No chain tool changed, so no chain version or shader rebuild was needed.
- Game regress, peak MB, screenshot comparison and independent review are
  deliberately unverified. The baseline remains untouched.

Final Python discovery passes: **1,217 tests, 23 skipped, zero failures**.
The env-table checker also passes. It still prints the pre-existing notice
about DM_NVN_CUT_FIRST being mentioned in docs but not read by code; the notice
is not a failing check. The first Python failure is resolved.

Final deliverables are two local behaviour commits on `oot-mem`. Both flags
are off by default, and either commit can be reverted separately after the
parent resolves any nearby integration edits. No push or PR was made.
Scratch probes and compiled test executables were removed after verification.

## Independent review fixes (supersedes the open kernel-read risk above)

Branch: oot-mem-fix. Findings 2 and 3 are fixed together because they share
restoration and the kernel-read boundary.

nvn_dirty_restore returns success. BUSY timeout disables further dedupe.
Every GPU/no-copy consumer uses nvn_dirty_require, including pool_res, pool
creation, large chunks, transient uploads and the raw pool-map loop. This helper
gives an in-flight restore a second bounded wait; if still incomplete it stops
the host before residency/submission. This is a failure policy, not a claim that
stalled disk I/O can safely produce pixels. Release failures retain guest bytes.

Kernel sources use dm_guest_read_prepare. Under the slot mutex it excludes
all overlapping tracked ranges until retirement, then waits out releases already
admitted. File writes and their overloads converge on h_fs_WriteFile. Socket
Send/SendTo/Recv/Read/Write paths in hle_net.c are offline stubs or in-process
eventfd counters; no guest socket buffer reaches a host syscall. Existing file
read destinations use dm_guest_write_prepare. Oodle pipe writes, JIT/probe dumps,
NVN shader/uniform/vertex/index dumps and Vulkan shader captures are covered too.
Frame capture copies an uncompressed source to host storage before fwrite.
Other read/write paths use host-owned buffers (loader, SDK16, save sync, Oodle
input). GL shader capture stores a host-owned source copy. No network capability
was added. Future kernel consumers must use the preparation hook or a bounce.

Regression evidence: the pre-fix dirty implementation (only signature-adapted
for the new test API) fails seven assertions: real file writes return EFAULT,
re-release remains possible, and BUSY incorrectly authorizes access. The fixed
test passes every assertion, including an actual pread held beyond BUSY_WAIT_MS.
The fs test separately enforces preparation before pwrite.

Upload trim already occupied commit 8830915b but its diff needed dedupe context.
Tag oot-upload-trim-only names a separate standalone commit directly on oot-base,
with just trim, its tests and docs. This can ship without dedupe. The original
branches and their history remain intact.

Validation: host build passed; dirty dedupe/race/retirement/slot tests passed;
Metal tex dedupe 7 checks, trim off/on 11/13, upload slots 305 in each mode,
NVN 234 in each mode; fs 138 checks. Full tools discovery 1217 tests passed,
23 skipped. Gfx/iOS discovery and final counts are in review-fixes.md.
No game, regress.py or full shader build was run. Timeout failure can terminate
the host; kernel-visible pools retain their guest copies, reducing savings.
Front-ends: no new flag. Dedupe and upload trim remain default off.

The final concurrency extension additionally blocks a residency consumer at
nvn_dirty_require while the backup pread is held, proves it cannot proceed,
then lets it proceed only after restoration. A concurrent release worker races
64 real file writes and cannot reclaim the kernel-visible pool. Both pass.

File read destinations also use the permanent dedupe exclusion before their
existing write-preparation hook. This prevents re-release during kernel
copy-out. Their existing write-tracking EFAULT re-preparation remains in place.
The fs regression and host build pass after this boundary addition.

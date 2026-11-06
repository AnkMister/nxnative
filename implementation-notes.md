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

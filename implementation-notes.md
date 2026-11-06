# Task C: Mac CPU and scheduling

Base: `ee9b7765`. Branch: `oot-cpu`. No game runs, shader builds, installs,
baseline changes, pushes or GitHub comments are authorized for this lane.
The running baseline and its game work folder are untouched.

## Plan and log

The ponytail, pstack and plain-writing skills guide this lane. Model the Domain
keeps scheduling controls local to their owning subsystem. Sequence Work into
Verifiable Units keeps each control in a separate tested commit. Prove It Works
requires gameplay A/B evidence before claiming energy savings.

Pstack checklist:

1. Keep pstack mode active until the lane is complete.
2. Skim the principles index and open leaves when applicable. Done.
3. Capture a baseline trace on the matching surface. Skipped because the parent
   owns the running baseline and explicitly forbids touching it.
4. The how skill to ground hypotheses. Source audit below substitutes for
   delegation because this task is already the implementation sub-agent.
5. Plan the fix from the trace. Source-ranked candidates are experiments until
   the parent measures gameplay. Implement and test locally without delegates.
6. Parse and compare the artifacts (JSON to sqlite, diff). Pending local tests;
   gameplay measurements remain with the parent.
7. Cite the measurement in the PR. Not applicable; no PR is authorized.
8. Run Opening a PR. Skipped; the user explicitly forbids PRs and pushes.

Throughput checkpoint: inspect the clean checkout and related changes first.
This lane owns only CPU scheduling, copy waits, telemetry and their tests.
Other lanes own memory and upstream integration. No shared baseline writes.
One worker is required by the implementation sub-agent instruction.

## Related changes

- PR #158: `fast_wake`, `post_early` and the GPU event wait are already present.
  `DM_NVN_FAST_WAKE=0` restores feedback-handler wakeup.
- PR #31: FIFO is already present in the display-link callback.
  `DM_PRESENT_FIFO=0` restores newest-frame selection.
- PR #1001: even-interval tracking and immediate return to 60 Hz for odd
  intervals are already present in `hle_nvn.c`.
- `72d00571` is not on this base. It changes the standalone prebuild tool to
  Metal's concurrent compile count. It leaves prepare and background pools
  unchanged. This lane will not duplicate that integration.

## Ranked findings

Savings below are hypotheses from source, not gameplay measurements.

| Rank | Location | Issue | Expected saving at 30 fps | Risk / choice |
|---|---|---|---|---|
| 1 | `dm/gfx/nvn/nvn_rec.h:ubc_wait` | Uniform-copy consumers spin with ARM yield until the worker finishes; no blocking slow path. | Stops a consumer burning a core when the copy worker is delayed by competing work. Little gain when every copy finishes immediately. | Use a completion condition variable behind `DM_ECO_COPY_WAIT`; preserve acquire/release publication. |
| 2 | `dm/gfx/nvn/nvn_mtl.m:prepare_workers`, `pso_prebuild_bg`, `pp_bg_queue` | Prepare uses all active CPUs, background prebuild half the P cores, and hybrid builds another pool. | Reduces simultaneous compile work and contention, mainly at startup and new scenes. No steady-state gain after compilation ends. | Cap each pool behind `DM_ECO_COMPILE_THREADS`; it is not a process-wide Metal limit. |
| 3 | `dm/host/hle_thread.c:prio_qos` | Default guest threads all request USER_INTERACTIVE. Existing `DM_QOS_MAP=1` still gives the main-priority band that class. | May reduce scheduling competition with other apps and CPU energy. No reduction in useful instructions is promised. | Reuse `DM_QOS_MAP=1 DM_QOS_EDGES=-1,59` for a USER_INITIATED ceiling. Audio/vsync helpers keep explicit QoS. |
| 4 | `nvn_rec.h:ubc_thread`, `rec_thread` | Copy worker briefly polls 2,000 atomic loads; encode worker already sleeps on an empty queue. | Small, bounded burst cost. | Leave the brief producer poll intact; change the unbounded consumer wait first. |
| 5 | `hle_thread.c:block`, arbiter and condition waits; `nvn_mtl.m` fences/uploads/present | These already sleep on condition variables or Metal shared events. Repeated guest yields and short polls already back off. | No evidence for another general wait rewrite. | Preserve timeout and wake semantics. |
| 6 | `hle_sdk16.c` vsync; `hle_audio.c` silent sink; display link | Vsync is 60 Hz, silent audio 5 ms; these drive guest-visible clocks or audio release. Display link already follows a sustained even interval at 30 Hz. | Coalescing could remove wakeups but risks pacing/audio errors. | Do not change without a gameplay trace. |
| 7 | `hle_hid.c`, cheats, diagnostics and frontend timers | Input scripts poll at 5 ms, control-file loop at 100 ms; diagnostics and recording are opt-in. Home-hold timer is transient. | Usually absent in normal play. | Leave opt-in/transient paths alone. |
| 8 | `nvn_mtl.m`, `nvn_rec.h` per-frame objects | Render descriptors and record blocks exist; record blocks are recycled. | Unknown without allocation sampling. | Leave to the memory lane; avoid speculative pooling. |

Compile workers terminate their blocks once work runs out. They do not stay hot
after startup. Utility QoS is already used for archives, background prebuilds
and hybrid pipeline builds. Speculative predictions use USER_INITIATED because
the upcoming draw may need them; leave their admission policy intact.

## Measurement

Existing `DM_THRCPU=<absolute-path>,10` records per-thread CPU. Existing `[nvn]
power up to frame` lines report CPU percentage, interrupt and package-idle
wakeups, CPU energy and GPU time every 300 frames. A 30 fps run reports roughly
every ten seconds. CPU percent uses one core as 100%.

Exact new flags, test results and parent A/B commands will be appended below.

### Copy waits

Implemented `DM_ECO_COPY_WAIT=1` (Mac only, default off). Consumers sleep on a
completion condition separate from the work condition. The producer retains its
brief burst poll. Release/acquire ordering and the existing wait ledger remain.
The default path still spins as before. Tests queue 128 real copy rounds with
two additional consumers, and exercise spurious wakes and completed waits.

### Compile pool ceiling

Implemented `DM_ECO_COMPILE_THREADS=1..64` (Mac only; unset or zero is off).
It caps prepare workers, prebuild workers (including the standalone tool),
hybrid background queues and speculative admission. It never enlarges a pool.
Synchronous draws and Metal's private compiler scheduling are outside the cap.
Pools are independent, so `=2` does not mean two process-wide compile tasks.
Existing prepare/prebuild overrides are also subject to the ceiling. QoS is
unchanged; startup prepare remains USER_INITIATED, background work UTILITY.
No attempt was made to lower QoS dynamically inside a compile already running
when the first frame appears. That would not reliably lower Metal service QoS.

### Reused controls and deviations

Only the first two candidates require code changes. The existing
`DM_QOS_MAP=1 DM_QOS_EDGES=-1,59` already maps valid guest priorities 0..59 to
USER_INITIATED and 60..63 to UTILITY. It preserves the existing priority donation
path and helper-specific audio/vsync QoS. No duplicate guest-QoS flag was added.
The acquire/render thread also has a separate time-constraint policy by
default. QoS alone does not remove that policy. Test existing `DM_RT=0` as a
separate experiment if the render thread still competes with other apps.

No new telemetry thread or timer was added. Existing process-wide power lines
already cover the requested CPU, idle wakeups and energy, and `DM_THRCPU` covers
per-thread attribution. This avoids adding wakeups just to measure them. The
power line needs frame progress and counts process CPU energy, not whole-system
power or Metal compiler service energy. The thread sampler omits threads that
exit between samples; use the process power line for the total.

Local checks so far: both copy-wait modes passed 128 rounds each; compile caps
unset/0/1/2/4 and four invalid inputs passed. The docs suite passed 11 tests.
Full integrated checks and build are recorded below after they finish.

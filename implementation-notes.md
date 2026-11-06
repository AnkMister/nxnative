# Task C: Mac CPU and scheduling

Base: `ee9b7765`. Branch: `oot-cpu`. This lane made no game runs, game shader
builds, installs, baseline changes, pushes or GitHub comments.
The running baseline and its game work folder are untouched.

## Plan and log

The ponytail, pstack and plain-writing skills guide this lane. Model the Domain
keeps scheduling controls local to their owning subsystem. Sequence Work into
Verifiable Units keeps each control in a separate tested commit. Prove It Works
requires gameplay A/B evidence before claiming energy savings.

Pstack checklist:

1. Keep pstack mode active until the lane is complete. Done.
2. Skim the principles index and open leaves when applicable. Done.
3. Capture a baseline trace on the matching surface. Skipped because the parent
   owns the running baseline and explicitly forbids touching it.
4. The how skill to ground hypotheses. Source audit below substitutes for
   delegation because this task is already the implementation sub-agent.
5. Plan the fix from the trace. Source-ranked candidates are experiments until
   the parent measures gameplay. Implement and test locally without delegates.
6. Parse and compare the artifacts (JSON to sqlite, diff). Local tests passed;
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

The new flags, test results and parent A/B commands follow below.

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

Local checks: both copy-wait modes passed 128 rounds each; compile caps
unset/0/1/2/4 and four invalid inputs passed. The docs suite passed 11 tests.
The integrated checks and build are recorded below.

## Integrated validation

The following completed on the Mac with the required Python venv on PATH and
`TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch`.
No dependency was installed. Builds used at most six total make jobs across
simultaneous commands, with `-j2` on each command.

- `make -C dm/host -j2 GAME=0400486024DEC000 dmhost` passed. Output is this
  checkout's `dm/host/dmhost`, a 4.8 MiB ARM64 Mach-O executable. The host's
  embedded utility shaders were built as required by make. No game shader chain
  or game build ran, and no chain version changed.
- `make -C dm/gfx/tests -j2 GAME=0400486024DEC000 check_t_ubc_wait check_t_eco_compile`
  passed. Copy tests pass at `DM_ECO_COPY_WAIT=0/1`, with 128 copy rounds per
  mode and two concurrent consumers. The enabled mode proves both consumers
  enter condition waits, re-wait after a spurious wake, and finish on broadcast.
  Compile-policy tests pass with the cap unset, `0`, `1`, `2`, `4`, `invalid`,
  `2junk`, `-1` and `65`. They check prepare workers, actual utility queue
  rotation, speculative admission and unthrottled demanded admission.
- Graphics executables built with `make -C dm/gfx/tests -j2 GAME=0400486024DEC000
  t_nvn t_pso_pending t_ubp_running`. With `MTL_DEBUG_LAYER=1`, `t_nvn` passed
  234 checks per copy-wait mode, and `t_ubp_running` passed 8 checks per mode.
  `DM_ECO_COMPILE_THREADS=2 ./t_pso_pending` passed 52 checks.
- Host executables built with `make -C dm/host/tests -j2 GAME=0400486024DEC000
  build/t_condvar build/t_condvar_old build/t_pollwait build/t_preempt
  build/t_notify_sched`. All six invocations passed, both with defaults and
  with `DM_QOS_MAP=1 DM_QOS_EDGES=-1,59` (12 runs). The six invocations are
  `t_condvar`, its expected-failure `t_condvar_old` negative control,
  `t_pollwait`, `t_preempt`, `t_preempt --all-peers` and `t_notify_sched`.
- `python -m unittest discover -s dm/tools/tests -p test_docs.py` passed 11
  tests; `test_env_switches.py` passed 1. The environment-table generator
  reports the already-documented removed switch `DM_NVN_CUT_FIRST` as a notice.
- `git diff --check` passed. The compiler emits Metal type, ARC and deprecation
  warnings in existing NVN code; the build exits successfully.

No `regress.py`, game launch, iOS build, shader-chain build or broad GPU suite
ran. This is build and synthetic behavior evidence, not gameplay acceptance.
The task's update `v131072`, pacing, picture, audio and other-game regressions
remain unverified. Parent integration review remains separate from this lane.

## Parent gameplay A/B procedure

Use the same built executable for all arms. Keep the running protected baseline
and its game work folder untouched. Use a separate parent-owned run workspace,
save seed and cache seed. The examples below are instructions only; this lane
did not execute them. Set the variables to those isolated assets first:

```sh
export HOST=/Users/ankur/.t3/worktrees/nxnative-oot/t3-7ace80f6/dm/host/dmhost
# CPU_AB: a new workspace outside both protected baseline directories.
# PATCHED: the isolated rewritten v131072 modules.
# SAVE_SEED: a copy of the same Kokiri Forest checkpoint for every arm.
# ARCHIVE_SEED: an isolated, identically warmed pipeline archive seed.
# Export the normal DM_ROOT, DM_ROMFS, DM_MSL_DIR, DM_NVN_SHMAP and DM_FONT_DIR
# for the parent's isolated assets. Do not point writable caches at the baseline.
: "${CPU_AB:?}" "${PATCHED:?}" "${SAVE_SEED:?}" "${ARCHIVE_SEED:?}"

run_cpu_ab() {
    local label="$1"
    shift
    mkdir -p "$CPU_AB/$label/save" "$CPU_AB/$label/temp" "$CPU_AB/$label/archive"
    cp -R "$SAVE_SEED/." "$CPU_AB/$label/save/"
    cp -R "$ARCHIVE_SEED/." "$CPU_AB/$label/archive/"
    env -u DM_ECO_COPY_WAIT -u DM_ECO_COMPILE_THREADS \
        -u DM_QOS_MAP -u DM_QOS_EDGES -u DM_RT \
        DM_FPS_TARGET=30 DM_WINDOW=1 DM_AUDIO=1 DM_FOCUS_KEEP=1 \
        DM_NVN_WAITS=1 DM_NVN_UB_COPY_THREAD=1 \
        DM_THRCPU="$CPU_AB/$label/threads.tsv,10" \
        DM_SAVE="$CPU_AB/$label/save" DM_TEMP="$CPU_AB/$label/temp" \
        DM_PSO_ARCHIVE="$CPU_AB/$label/archive" \
        DM_PSO_USER="$CPU_AB/$label/pso_user.tsv" \
        "$@" "$HOST" "$PATCHED" > "$CPU_AB/$label/log.txt" 2>&1
}

run_cpu_ab control
run_cpu_ab copy DM_ECO_COPY_WAIT=1
run_cpu_ab compile DM_ECO_COMPILE_THREADS=2
run_cpu_ab qos DM_QOS_MAP=1 DM_QOS_EDGES=-1,59
run_cpu_ab combined DM_ECO_COPY_WAIT=1 DM_ECO_COMPILE_THREADS=2 \
    DM_QOS_MAP=1 DM_QOS_EDGES=-1,59
# Optional separate experiment; keep all other settings at control values.
run_cpu_ab rt DM_RT=0
```

Stop each arm normally before starting the next. Start every arm from the same
checkpoint, use the same input route and camera, window size, focus state and
audio. Keep the other apps' workload comparable. Preserve identical diagnostic
flags between arms. Reverse the arm order on another pass to expose system
cache/thermal drift. The script intentionally refuses to use an unset workspace;
give repeat passes new labels so logs and seed copies are not mixed.

For copy waits, compare warm gameplay after preparation and after the first
300-frame measurement baseline. Read `[nvn] power up to frame` for CPU %, CPU
mJ/frame, interrupt wakeups/s and platform-idle wakeups/s. `DM_THRCPU` identifies
the consumers whose CPU falls. `[waits]` records uniform-copy wait wall time;
longer blocked wall time alone is not proof of more CPU work. Verify the same
30 fps and on-screen p95/p99, responsive controls, correct picture and audio.

For compile caps, compare startup and a repeatable new-scene traversal separately
from warm play. Use identical archive seeds for each cold comparison and repeat
in reversed order because Metal's system cache is shared. A fully warm archive
may do no compilation, so no benefit from the cap is expected there. Check the
logged worker counts, preparation completion and first-use stutter. `=1` is a
stronger optional cap; `=2` allows at most two workers per affected pool, not
two workers across the process. The CPU/power counters exclude compiler-service
processes, so they cannot establish total compile energy savings.

Accept a flag only if gameplay stays at 30 fps with equivalent pacing and audio
and CPU/energy or competition with other apps improves. Disable by unsetting
that flag or setting it to `0`. The two behavior commits can also be reverted
separately. No fps uplift or measured energy reduction is claimed by this lane.

Final cleanup removed the lane's scratch logs and generated test binaries and
debug bundles. The built Mac host, its debug bundle and its small generated
build inputs remain for parent use. Only tracked source, tests and documentation
are committed. Nothing was pushed.

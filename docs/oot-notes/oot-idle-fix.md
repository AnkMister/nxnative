# Ocarina idle efficiency implementation

Branch: `oot-idle`, based on `ee9b7765` (`oot-base`).

## Status and scope

This is a conservative partial implementation of the requested idle optimisation.
It does **not** make a title screen that continues drawing nearly free. It skips
only the host's scan-out GPU command buffer when a game presents the same GPU-only
texture without an intervening submission. Guest draw/compute submissions are
always executed. Their identical-frame detector remains open.

All behaviour is opt-in. `DM_ECO_SAME_FRAME=1` enables repeat scan-out detection
and demand-driven display-link suspension. `DM_ECO_HIDDEN=pause` or `slow` enables
the window policy. Unset, `0`, and unknown hidden modes keep the old policy.

No game, NSP packer, full shader build, or regression harness was run. The running
baseline checkout and its game folder were read only. Nothing was installed,
pushed, signed or committed. The task's implementation-subagent role was kept;
there was no nested delegation or independent review. The parent should review
this diff before integration.

## Existing behaviour

`front_mac.m` normally sends focus 2 when its window stops being key, unless
`DM_FOCUS_KEEP=1` or the software keyboard is open. Regaining key sends focus 1.
Minimizing sends focus 3, suspends audio, and closes/drains the graphics gate.
Restoring reopens graphics/audio. Occlusion only logged visibility before this
change. A game's response to focus 2 varies; a notification alone is not a host
clock freeze. The existing background freeze implementation is in `hle_os.c`.

## Soundness of the implemented detector

The proof concerns scan-out only. No guest command, fence, event, counter, copy,
or uniform update is omitted. There is no command hash or probabilistic equality.
`nvn_eco_image` compares every scan-out input exactly.

A repeated scan-out is accepted only when all of the following hold:

* The source is the same NVN initialization serial and Metal resource identity.
* It is a private Metal texture without buffer or IOSurface backing, in a
  CPU_NO_ACCESS, non-virtual NVN pool. Sparse textures and textures resolved from
  guest storage are refused. CPU textures deliberately do not use dirty-page
  tracking to establish sameness; an incomplete observation cannot prove it.
* No NVN submission has begun or ended between the two presents. An atomic epoch
  advances at submission begin and commit; an odd epoch refuses an in-progress
  submission. The enqueue epoch must also match at display encoding.
* Source ownership is native NVN. External producers and snapshot presents are
  refused. There is no retained guest descriptor or command-memory dependency.
* Crop, origin, destination size/format and the window surface generation match.
  Resizing and visibility/activation changes invalidate the proof.
* The preceding display GPU work completed and its drawable was acknowledged as
  actually displayed. Unacknowledged, failed, missing or unknown frames cannot
  seed a skip. The integration test injects this physical-display acknowledgement
  because its layers are offscreen; it does not prove physical-window behaviour.

Core Animation retains the previously displayed image. Metal drawables are
single-use; the implementation therefore leaves that image up instead of trying
to present a consumed drawable again. The logical present still completes its
swapchain ticket and records a display timestamp. The game keeps its existing
acquire pacing. No guest rendering work is claimed as avoided.

## Deliberately refused cases and remaining work

Ordinary draws/dispatches, including visually static menus, advance the work epoch
and always render. A hash of their commands and CPU inputs would miss reads from
GPU-written attachments, storage/image atomics, indirect arguments, blending with
previous attachments, transform feedback, queries, and persistent queue state.
Shader reflection plus the current selective texture dirty tracker does not prove
that complete read/write closure. A future full-frame detector needs that closure,
side-effect preservation and resource-version tracking for every GPU writer.

The display link pauses on an empty present queue when no caller is waiting for
its ticks. Enqueue and explicit acquire/vsync clock demand wake it under the same
queue mutex. It uses no idle timer or polling watchdog. Active clock demand keeps
ticks running. If a game creates a vi vsync helper that keeps requesting ticks
while no frames are submitted, that helper remains active while visible. Audio,
input, networking and game timer threads are also outside this change. A claim
that the **whole process** sleeps fully on a visible pause menu is unverified and
not guaranteed. Suspending those clocks based only on absent presents can deadlock
a game that needs a tick to submit its next frame.

`pause` is stronger and independent of whether the game honors focus loss. It
freezes the guest clock with reason 3, blocks guest counter reads, closes/drains
graphics and suspends audio. The vi helper and acquire wait on a condition, without
periodic eco wakeups. Queued presents are discarded before draining to release
acquire tickets when the OS has already stopped the display link. Resume removes
only freeze reason 3, preserving keyboard/background freeze reasons.

`slow` keeps focus 1 so games that stop on focus loss can keep drawing. Each acquire
thread and vi helper is limited to 8 Hz with an interruptible monotonic condition
wait. The display link is detached and the normal blocking presentation worker
handles drawables while hidden. The OS may deliver hidden drawables slower than
8 Hz. There is no promise of an 8 Hz minimum, nor a process-wide cap across multiple
independent windows/acquire threads. Non-NVN backends do not use this acquire cap.

Both hidden modes use app active state, key-window state, NSWindow occlusionState
and minimization. A visible software keyboard is exempt from key-window loss.
Explicit `DM_ECO_HIDDEN` takes precedence over `DM_FOCUS_KEEP` and over the old
minimize policy. Input release/resume handling remains in the window observers.

## Counters

Every 300 considered scan-outs, `DM_NVN_LOG=1` or an existing `DM_METAL_HUD` setting
prints `[eco] considered ..., skipped ..., display GPU command buffers avoided
...; guest submissions avoided 0`. Counts are cumulative. Each skip avoids one
display command buffer, including its bilinear or MetalFX scan-out work. This is
an operation count, not an estimate of saved GPU milliseconds or energy. Logical
skips are not mixed with the presentation queue's dropped-frame counter.

## Validation log

* Initial host compile found a stale `present_now` forward declaration. It was
  updated alongside the new enqueue-time proof arguments.
* Mac host build passed with `make -C dm/host -j2 GAME=0400486024DEC000 dmhost`.
* `t_eco` passed under ASan/UBSan. It covers first/repeat/unknown inputs, every byte
  of the scan-out key, odd work epochs, zero identity, mode parsing and all 32
  combinations of visibility inputs.
* `t_eco_wait` passed in separate off, pause and slow processes. It checks blocking,
  foreground wakeup and the 125 ms slow interval. The pause and slow cases
  also passed a separate ThreadSanitizer build.
* `t_eco_present` passed 23 checks with real Metal queues/offscreen drawables.
  It exercises the production display encoder, refuses CPU/shared/external and
  in-progress work, tests submission/surface invalidation and checks idle-link
  suspension versus outstanding tick demand.
* `t_eco_clock` passed against the real guest clock. Hidden pause blocks guest
  reads while host drains proceed; background/keyboard reasons compose and
  resume preserves clock continuity.
* The embedded rusage reader compiled with `-Werror` and read its own process
  successfully. That validates the recipe, not game energy savings.
* Existing graphics suspend test passed 15 checks. Existing display allocator test
  passed 13 checks. Existing display-link rescue test passed 80 checks.
* Game pictures, real AppKit visibility transitions, Ocarina skip rates, energy,
  wakeups and the five-game regression gate remain unmeasured. Per task rules,
  do not run the game or `regress.py` from this implementation session.

Re-run the focused checks with the provided Python venv on PATH and the approved
scratch TMPDIR. The Makefile builds no more than the requested targets:

```sh
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
export PATH=${OOT_PYTHON_BIN}:$PATH
make -C dm/gfx/tests GAME=0400486024DEC000 check_t_eco check_t_eco_wait check_t_eco_present check_t_gfx_suspend check_t_present_alloc check_t_present_rescue
make -C dm/host/tests GAME=0400486024DEC000 eco-clock
make -C dm/host -j2 GAME=0400486024DEC000 dmhost
```

## Exact A/B recipe for the operator

Run only after the operator stops the existing baseline and reserves the Mac for
measurement. Use the same candidate binary for A and B; A has the flags unset.
Keep scene/save, archive, shaders, resolution, 30 fps target, audio, HUD, power
state and all other switches identical. Do not use `DM_DETCLOCK`, capture or shader
compilation in an energy sample. Alternate A/B/B/A with at least three valid
samples per case. Compare elapsed-normalized counter deltas, and retain each raw
sample. A zero or unavailable energy counter is not evidence of zero energy.

Set up a separate APFS clone so runtime writes cannot touch the live baseline:

```sh
export REPO=.
export BUILD=${OOT_READONLY_GAME_ROOT}/0400486024DEC000_build
export EXP=${OOT_SHARED_CONTEXT}/idle-ab
mkdir -p "$EXP"
# Run once. cp -c makes an APFS clone; do not substitute symlinks for mutable caches.
cp -cR "$BUILD" "$EXP/assets"
```

Build the measurement reader outside the repo. It reads two snapshots from the
same live PID. It rejects a PID change/counter reset, records actual elapsed time,
and reports raw billed-energy units without inventing a joule conversion:

```sh
cat > "$EXP/rusage.c" <<'C'
#include <libproc.h>
#include <sys/resource.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static double mono(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    int pid = atoi(argv[1]), secs = atoi(argv[2]);
    if (pid <= 0 || secs <= 0) return 2;
    struct rusage_info_v4 a = {0}, b = {0};
    if (proc_pid_rusage(pid, RUSAGE_INFO_V4, (rusage_info_t *)&a)) { perror("snapshot A"); return 1; }
    double t = mono(); struct timespec left = {secs, 0};
    while (nanosleep(&left, &left)) if (errno != EINTR) return 1;
    if (proc_pid_rusage(pid, RUSAGE_INFO_V4, (rusage_info_t *)&b)) { perror("snapshot B"); return 1; }
    double elapsed = mono() - t;
    if (a.ri_proc_start_abstime != b.ri_proc_start_abstime ||
        b.ri_billed_energy < a.ri_billed_energy || b.ri_pkg_idle_wkups < a.ri_pkg_idle_wkups) return 1;
    printf("{\"pid\":%d,\"seconds\":%.6f,\"energy_a\":%llu,\"energy_b\":%llu,\"energy_delta\":%llu,\"energy_per_second\":%.6f,\"wakeups_a\":%llu,\"wakeups_b\":%llu,\"wakeups_delta\":%llu,\"wakeups_per_second\":%.6f}\n",
      pid, elapsed, a.ri_billed_energy, b.ri_billed_energy, b.ri_billed_energy-a.ri_billed_energy,
      (b.ri_billed_energy-a.ri_billed_energy)/elapsed, a.ri_pkg_idle_wkups, b.ri_pkg_idle_wkups,
      b.ri_pkg_idle_wkups-a.ri_pkg_idle_wkups, (b.ri_pkg_idle_wkups-a.ri_pkg_idle_wkups)/elapsed);
}
C
clang -O2 -Wall -Wextra -Werror "$EXP/rusage.c" -o "$EXP/rusage"
```

Launch each variant in a fresh output directory. The following is A; for B add
`DM_ECO_SAME_FRAME=1`, `DM_ECO_HIDDEN=pause`, or `DM_ECO_HIDDEN=slow` to the env
command, one feature at a time, then test the combined configuration. For repeat
runs choose a new OUT. To resume a fixed gameplay save, copy the same immutable
seed save into OUT/save before launching every variant. Never copy a save back to
the baseline during this experiment.

```sh
export OUT="$EXP/title-A-1"
mkdir -p "$OUT/save" "$OUT/temp"
cd "$OUT"
env -u DM_ECO_SAME_FRAME -u DM_ECO_HIDDEN -u DM_DETCLOCK \
 DM_ROOT="$EXP/assets" DM_ROMFS="$EXP/assets/extract/v131072/RomFS.img" \
 DM_SAVE="$OUT/save" DM_TEMP="$OUT/temp" \
 DM_MSL_DIR="$EXP/assets/shader/cache" DM_FONT_DIR="$EXP/assets/font" \
 DM_NVN_SHMAP="$EXP/assets/profile/0400486024DEC000/shader_map.tsv" \
 DM_WINDOW=1 DM_FPS_TARGET=30 DM_FOCUS_KEEP=1 DM_NVN_LOG=1 \
 DM_NVN_TSV="$OUT/frames.tsv" DM_NVN_TSV_CALLS=0 \
 "$REPO/dm/host/dmhost" "$EXP/assets/patched_v131072" > "$OUT/log.txt" 2>&1 &
export GAME_PID=$!
# First reach and settle the target scene. Then run the reader from this same shell.
"$EXP/rusage" "$GAME_PID" 60 > "$OUT/rusage.json"
```

This build stores RomFS in `extract/v131072/RomFS.img`, verified read only. Use the baseline launch's existing
DM_PSO_BUNDLE/DM_PSO_ARCHIVE settings if present, pointing at the cloned asset
paths. Before sampling, require compilation/upload activity to have settled and
check the host still runs at its own 30 fps cap. Keep the HUD setting identical
in A and B. `DM_NVN_LOG=1` is the counter switch and avoids adding a Metal HUD.

For each sample retain the launch environment, scene/save identity, raw rusage
JSON, log and frames.tsv. Record first/last eco counts around the sample (counts
are emitted at 300-present boundaries), actual presentation rate and GPU work.
After measuring, inspect matching pictures outside the energy window.

| Case | Procedure and acceptance |
| --- | --- |
| Title idle | Leave the title untouched in both runs. Animated titles must render. A title that submits every frame will have zero skips with this implementation. Compare raw energy/wakeup rates and screenshots; do not claim a rendering win from a lower frame rate. |
| Pause menu | Reach the same gameplay save, press Return (+) and stop input. A game that stops presenting should stop the display link after its empty callback unless a tick consumer remains. If it keeps drawing, expect zero skips. Sample energy and wakeups despite absent frame/HUD reports. Check resume and input immediately after the sample. |
| Gameplay | Replay the same short route from the same seed save. Expect approximately zero skips (every new submission invalidates the proof), equivalent frame rate and equivalent pictures. |
| Covered window | Cover the whole window with another app; repeat by switching apps while the game stays visible. With pause, verify the `[eco]` transition, absent new frames, reduced counter rates and a continuous clock on restore. With slow, verify acquire/present progression at no more than 8 Hz for the single-window case, then immediate normal pacing on focus/visibility return. |
| Minimized/hidden app | Repeat with minimize and Cmd-H. Check pause and slow separately, then restore the window. A real OS drawable stall may lower slow mode below 8 Hz. Keep the window in the target state throughout both rusage snapshots. |

A successful full-frame follow-up must additionally show nonzero guest rendering
work avoided in title/pause cases that continue submitting. The current log
explicitly reports guest submissions avoided 0, so it cannot satisfy that gate.

## Review finding 4: preserve audio during hidden clock pause

`oot-idle-fix` adds dm_audio_pause, distinct from background mute. Pause sets a
callback guard, halts the AudioUnit and joins the silent sink without releasing
pending buffers. Starts, watchdog retries, mute transitions and media resets
cannot start a consumer while paused. Queue order and the partly played buffer
position remain intact. Resume starts only outputs still in STATE_STARTED,
respecting background mute. The Mac pauses audio before freezing the clock and
unfreezes the clock before restarting consumption. Off and slow retain their
existing policy.

Regression t_audio queues partially played dialogue, starts while hidden,
waits through silent-sink periods and injects a late device callback. It checks
silence, unchanged PCM position, queue/release cursors and notification count,
then verifies queued dialogue releases on resume. Mute transitions while paused
are covered. Mapping this call to the old dm_audio_suspend reproduces failure;
the new policy passes. Existing audio lifecycle, SPSC, stream, stats, mocked
device and eco-clock tests pass. Host build and focused idle/presentation tests
pass. Logs and exact counts are in review-fixes.md.

No game, physical AppKit hide/resume, full shader build or regress run. Speaker
latency and full audio-renderer/game acceptance remain unverified.
Front-ends: Mac DM_ECO_HIDDEN=pause now preserves audio; no new flag.

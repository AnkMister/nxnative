# Oot-clock implementation notes

## Scope and decisions

Branch `oot-clock` starts at `oot-base`, `ee9b7765`. The supplied agent context and the complete `glass-reports/g3-rewriter-cost.md` were read before implementation. The baseline checkout and Ocarina build were inspected read-only. No game, regression route, shader rebuild, device operation, dependency installation, push or PR was run.

The measured v131072 module identities, site counts and destinations are recorded once in the [game note](../../dm/games/0400486024DEC000/README.md#counter-read-census-v131072). The shared mechanism, flags and clock semantics are in the [rewriter reference](../../docs/reference/rewriter.md#counter-reads-save-a-full-simd-context).

The clock rate follows the existing SDK spec detection. Ocarina is Ounce and uses 31.25 MHz, rather than the task's suggested 19.2 MHz. Switch 1 retains its existing multiply-by-12, divide-by-625 conversion. Both rates keep the existing Mach-to-nanosecond truncation and multiplication wrap behavior.

The implementation uses a guarded integer-only assembly entry on the existing per-thread gate stack. It reads the Darwin commpage counter type and brackets its counter read with the Mach offset reads. It follows the selected speculative, architectural non-speculative or Apple non-speculative counter mechanism. An unsupported type falls back. The mapped commpage type on the test Mac was 3. Actual machine sleep/wake is not tested. The private commpage layout is an explicit platform dependency of this opt-in experiment.

A generation counter guards freeze and lag updates. Frozen, background, deterministic and statistics modes use the full gate. The first read also falls back to initialize the state. All ordinary counter destinations work; x18 uses the full gate and its guest TSD slot. x29 and x30 fallback results update the guest's saved pair. Distinct `clock_*` gate kinds make older hosts stop during loading rather than interpret the new entry ABI.

The default rewrite keeps the original lowering. CNTFRQ emulation is added only for the opt-in rewrite; the supplied update has no frequency-read sites. The NSP rewrite cache includes `DM_FAST_CLOCK`, so a flag change invalidates a cached rewrite. No shader-chain files changed.

TLS specialization was deferred. It would add serialized per-site instruction fixups, loader validation and executable-memory changes. It is independent of the clock entry and should have its own measurement and review. x18 access classification and SVC GetSystemTick specialization are outside this change.

## Cost per successful read

Static counts below describe the Mac's type-3 counter path, Ounce scaling and the destinations present in the supplied update. They count an executed paired load/store as one instruction. C instructions and C stack spills are excluded.

| Component | Existing gate | Fast entry |
|---|---:|---:|
| Original branch and rewrite block | 11 instructions | 13 instructions |
| Thread stub | 4 instructions | 4 instructions |
| Host assembly entry | 91 or 94 instructions | 50 instructions |
| Wrapper total | 106 or 109 instructions | 67 instructions |
| Wrapper stack traffic | 1,632 bytes | 168 bytes |
| SIMD traffic within that total | 1,024 bytes | 0 bytes |
| Reserved host register frame | 800 bytes | 64 bytes |

The two existing-entry counts depend on which non-nested-stack range check exits first. A successful fast read saves 39 or 42 wrapper instructions and 1,464 bytes of local stack traffic, plus the uncounted C dispatch, lookup and clock-call work. Stack traffic includes the unchanged 16-byte guest pair, its reloads and the host frame; it does not mean DRAM traffic. The fast entry preserves flags by using instructions that do not change them and uses no SIMD instructions.

The emitted block grows from 40 to 92 bytes because it retains an ordinary fallback block. That adds 52 bytes per site. The host adds one 16 KiB thread-stub table. A rejected fast read incurs the small attempted entry before paying the existing full-gate cost.

## Microbenchmark and estimated CPU saving

`make -C dm/host/tests GAME=0400486024DEC000 clock` runs the actual assembly entries and real clock/gate dispatch. The microbenchmark alternates five trials per side, 200,000 reads per trial, using thread CPU time and a volatile result. The wrapper enters the real thread stub directly; it omits the generated TSD/key lookup on both sides. The legacy side is the candidate host's full gate, including the new default-disabled statistics/preparation check. It is not a separately built original host.

Recorded samples in ns/read:

| Rate and entry | Samples | Median | Range |
|---|---|---:|---|
| Switch 1, gate | 25.031, 24.790, 24.555, 24.196, 24.312 | 24.555 | 24.196 to 25.031 |
| Switch 1, fast | 11.318, 11.016, 11.827, 11.523, 11.887 | 11.523 | 11.016 to 11.887 |
| Ounce, gate | 23.276, 22.686, 22.610, 22.135, 22.194 | 22.610 | 22.135 to 23.276 |
| Ounce, fast | 8.249, 9.162, 8.050, 8.835, 8.997 | 8.835 | 8.050 to 9.162 |

Measured result on that run is 13.775 ns less CPU work per Ounce entry, about 61%. The limiter is the per-read assembly, clock conversion and legacy C dispatch. All correctness checks passed. The Mac was busy, with a load average of 90 on 16 logical cores before the build/test work. Another heavy compile overlapped parts of verification. Alternating sides and thread CPU time reduce scheduler-wait bias, but do not remove core migration, cache contention or frequency changes. Treat this as a local microbenchmark, not a game or energy result.

Estimated saving is dynamic reads per second multiplied by roughly 14 ns, subject to the microbenchmark limits. Hypothetical examples are 100,000 reads/s saving about 1.4 ms of CPU/s, or 1,000,000 reads/s saving about 14 ms of CPU/s, respectively 0.14% and 1.4% of one core. At 30 fps, 10,000 reads/frame would save roughly 0.14 ms/frame. No dynamic Ocarina rate has been collected, so its total CPU and energy savings are unknown. GPU work and wakeups have not been measured.

## A/B recipe

Use a separate writable A/B directory on the game's drive. Keep both supplied baseline directories read-only. `AB` below must name that new directory, never `oot/0400486024DEC000_build` or its existing patched output. The source modules are read-only inputs.

```sh
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
PY=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python
SRC=/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build/extract/v131072/ExeFS
: "${AB:?Set AB to a separate writable A/B directory on the game drive}"
for variant in A B; do
  flag=0
  if [ "$variant" = B ]; then flag=1; fi
  mkdir -p "$AB/$variant"
  for module in main subsdk0 sdk; do
    DM_GAME=0400486024DEC000 DM_FAST_CLOCK="$flag" DM_REWRITE_J=4 \
      "$PY" dm/tools/patch_nso.py "$SRC/$module" "$AB/$variant" "$module" \
      > "$AB/$variant/rewrite_$module.log" 2>&1 || exit 1
  done
done
make -C dm/host -j4 GAME=0400486024DEC000 dmhost
```

`DM_FAST_CLOCK` is a rewrite-time option. The modules must be re-rewritten for each side; the task's rough budget was about 30 seconds, not measured here. No shader rebuild is required. Setting the flag only in the app's runtime environment cannot change already rewritten modules.

Use the rebuilt host for both A and B, with the existing launcher or benchmark environment unchanged except for the patched-module directory. Keep the 30 fps cap, save, scene, shader libraries, audio and foreground/background state identical. Before timing, run each side with `DM_CLOCK_STATS=1` to estimate dynamic read rates from per-thread log deltas. Statistics force the full gate and perturb timing. Unset that variable for A/B timing.

Alternate A/B runs and compare CPU active time/frame, energy/frame, frame consistency and audio. Include background/foreground, freeze/resume and deterministic stepping. Check actual machine sleep/wake before promoting the flag. The final pictures and game timing must remain correct. Test Ocarina, another Ounce title such as Donkey Kong Bananza, a Switch 1 title such as Super Mario Bros. Wonder, Streets of Rage 4 for the gate-stack requirement, and Tears of the Kingdom for frame-clock interactions. No game regression route was run under the supplied no-game/no-regress boundary.

## Execution and validation log

1. Verified the clean worktree at `ee9b7765` and created `oot-clock`. Read the handoff and full research report. Counted original instruction words and checked the existing rewrite logs and metadata. Recorded the measured game facts in its note.
2. Traced the rewriter, thread stubs, gate frame, gate dispatch, clock freeze/deterministic state and rewrite cache. Applied Sequence Work into Verifiable Units by checking the first lowering and host entry before expanding destination and lifecycle checks.
3. Added the opt-in entry, guarded clock snapshot, legacy fallback, frequency emulation and per-thread statistics. Added full-rewriter synthetic tests and host execution tests. Added environment documentation and regenerated the symptom index. Applied plain-writing to the notes and type-discipline to the atomic assembly layout assertion.
4. Applied Explain the Number by limiting the measured result to the direct-entry microbenchmark, recording samples and ranges, and leaving the game's dynamic hit rate and end-to-end saving unknown.
5. Host clock tests cover both selected frequencies, first-read fallback, monotonicity, scaling, frozen exact values, nested reasons, lag continuity, background blocking and host-work bypass, deterministic stepping, all SIMD registers, caller GPRs and NZCV/FPSR/FPCR. The dispatch test covers every destination for all three counter kinds. The symbol-index test also passes.
6. The first full Python suite ran 1,220 tests with 23 skips and one failure because the new flags were missing from the environment table. Added their descriptions. The subsequent 15 targeted tests, including the full-rewriter synthetic test, environment registry and documentation checks, passed. Final full-suite and host-build results are recorded below.
7. Python lint reports three findings in untouched tests, two `NSP_FOLDER` attributes in `test_nsp_mac.py` and a float/int mismatch in `test_tree_tar.py`. No finding names a changed file. The baseline retains 389 findings; do not change that file for this task. C compile-database generation passes with 236 sources. C tidy cannot run because clang-tidy is absent; no tool was installed.
8. Independent review remains for the parent task. As the requested implementation sub-agent, no nested reviewer or implementation agent was started. Changes are committed locally only.

Final results: the complete Python tool suite passes, 1,220 tests with 23 skips. The final host clock target passes in five configurations, including both clock rates, deterministic stepping at both rates and statistics mode. The symbol-index target passes. The final Mac host build exits 0. `git diff --check` passes. Python lint and C tidy retain the limits recorded above. Gameplay, energy and machine sleep/wake proof remain open.

Artifacts for the orchestration task are under `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-clock/`, including the site-count JSON, rewrite test logs, host build logs, lint logs and benchmark samples. The durable measurements and limits are included above; game binaries are not committed.

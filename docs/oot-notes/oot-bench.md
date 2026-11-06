# Task E: Ocarina A/B harness

## Implementation log

- Created branch `oot-bench` from `ee9b7765`. No commits or pushes.
- Read AGENTS.md, the regression sections of docs/development.md, scripts/regress.py, scripts/bench.py, Ocarina's note, Mac packaging/launcher paths, and the installed SDK's rusage_info_v6 layout.
- Added scripts/oot_ab.py and dm/tools/tests/test_oot_ab.py. Stdlib/ctypes only; installed nothing.
- Inputs: A/B Mac build folders, optional separate dmhost paths, or .app bundles. Optional literal DM_NAME=VALUE env files; shell commands are never evaluated. .app runs its bundled dmhost directly, avoiding the launcher and its Library save/log writes.
- Reuses regress.read_route and bench.frames/pct. The small watchdog follows regress.run_watched's deadline/progress model rather than calling it: that function also checks free space, can clean Metal caches, waits for idle, and takes a shared measurement lock. Those side effects conflict with the protected running baseline and the requested measurement alongside other work. No regress.py changes.
- Ocarina has no smoke.tsv. Default route: DM_KEYS=f2600:A,f2950:A; wall deadline 180 seconds; frame reach 2951 by 115 seconds; measured window [120,178). Override with --route (regress smoke TSV), --seconds, --window START,LENGTH and --save. Shots and prebuild in a supplied smoke route are deliberately unused because capture/prebuild disturbs efficiency measurement.
- Each run gets a fresh copy of ONE save source, empty temp and writable pipeline archive, isolated DM_ROOT and control/timing files. Existing PSO bundles are read-only inputs. Inherited DM_* settings are cleared. Forces DM_FPS_TARGET=30, audio/HUD off, window visible/focus kept, logging calls off. Run metrics reject observed mean or median above 31.5 fps. Slower runs remain visible: inspect fps and frame p99 before accepting any efficiency gain.
- Runs A1 B1 A2 B2 ... N times per build. Raw counters and sampling timestamps, per-run results/logs/frame TSV, plan.json, results.json and results.md remain in --out. --out must be new and outside both builds. Dry-run writes nothing, starts nothing and permits incomplete builds.
- V6 captures ri_pkg_idle_wkups, ri_interrupt_wkups, ri_billed_energy, ri_phys_footprint and ri_lifetime_max_phys_footprint (all raw in samples). CPU/wakeup/energy differences use window endpoints at the first poll at or after each boundary (roughly 100 ms skew, exact counter_window retained). Peak footprint is the process lifetime high-water mark, including boot; ending footprint is at the measurement endpoint.
- Fake-process testing exposed Mach absolute CPU ticks on this Apple Silicon Mac. Verified a 0.1501-second Python process-clock burn against libproc: raw / 1e9 was 0.00360, and mach_timebase_info conversion (125/3) gave 0.15007 seconds. Added conversion and a process-clock agreement test. Never label billed_energy as joules: opaque kernel billing units, possibly zero if unavailable; it is not whole-machine power.
- Table cells show run median and [min,max]. Delta is B minus A. Significant means absolute delta strictly greater than the larger within-side range, with at least two complete measurements per side and no failed/missing run for that metric. This is a spread heuristic, not a statistical confidence test. GPU p50 comes from existing @gpu_ms rows; missing GPU samples show unavailable.
- Read build-baseline.log, which had reached [5/7], then inspected the baseline build root layout ONCE read-only. Present: tools/, patched_v131072/, extract/, profile/, shader/, logs/, tmp/. Build still incomplete then; no run/save was present. Did not modify either protected baseline location or launch any game.

## Validation

15 tests pass with the specified Python and TMPDIR. Tests cover ABI size/offsets, self and fake-host V6 readings, invalid PID, CPU clock conversion, counter deltas/reset rejection, frame/GPU summaries, spread significance, literal env parsing, .app resolution, watchdog hang/reach/early-exit, cap rejection and dry-run with launch forbidden.

```sh
TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch \
/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python \
-m unittest discover -s dm/tools/tests -p test_oot_ab.py -v
```

No game regressions were run: the explicit task forbids game launches. No shader/host/runtime changes. Real cap application, route/save equivalence, window visibility and game speed need the parent's Mac run. No independent agent review: this task explicitly makes this process the implementation sub-agent and forbids nested agents unless requested.

## Parent handoff: exact commands

Run from this checkout. The candidate host path below is the normal dm/host/Makefile output in this checkout; the parent must first build the integrated efficiency changes there. A uses the finished baseline's tools/dmhost. Both use exactly the baseline's v131072 game assets. If the integrated host lives in another worktree, change only --b-host.

First choose an immutable starting save. The build had no run/save at inspection, so the following explicit empty seed reproduces the new-game route without using the running baseline's save. Run this setup only after the current baseline play session is finished. A recorded/test save is preferable if that route requires it: replace --save with that immutable folder for both sides.

```sh
mkdir -p /Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-input/save
```

Exact dry-run (validated here; incomplete inputs are allowed):

```sh
TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch \
/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python \
scripts/oot_ab.py \
--a /Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build/ \
--b /Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build/ \
--b-host /Users/ankur/.t3/worktrees/nxnative-oot/t3-f55bd7db/dm/host/dmhost \
--save /Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-input/save \
--runs 3 \
--out /Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-integrated-01 \
--dry-run
```

Actual A/B: run the same command with the final --dry-run removed, after baseline packing is complete and the parent is ready to run the game. To compare feature flags, append --a-env and/or --b-env with the parent-created literal DM_* env-file paths; cap, measurement and writable storage settings always override those files. For an A/A noise calibration, remove --b-host as well and choose another fresh --out directory. For a genuinely separate candidate package, replace --b with its build folder or .app.

The benchmark intentionally does not assert that identical scripted input reached identical gameplay. Check logs and the scene once before trusting the default [120,178) window. On a cap unsupported by the game/host, results fail rather than reporting a maximum-fps comparison. Keep the Mac display unobscured; no caffeinate process is launched, so avoid system sleep during the parent's run.

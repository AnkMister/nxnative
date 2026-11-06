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
TMPDIR=$HOME/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch \
$HOME/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python \
-m unittest discover -s dm/tools/tests -p test_oot_ab.py -v
```

No game regressions were run: the explicit task forbids game launches. No shader/host/runtime changes. Real cap application, route/save equivalence, window visibility and game speed need the parent's Mac run. No independent agent review: this task explicitly makes this process the implementation sub-agent and forbids nested agents unless requested.

## Parent handoff: exact commands

Run from this checkout. The candidate host path below is the normal dm/host/Makefile output in this checkout; the parent must first build the integrated efficiency changes there. A uses the finished baseline's tools/dmhost. Both use exactly the baseline's v131072 game assets. If the integrated host lives in another worktree, change only --b-host.

First choose an immutable starting save. The build had no run/save at inspection, so the following explicit empty seed reproduces the new-game route without using the running baseline's save. Run this setup only after the current baseline play session is finished. A recorded/test save is preferable if that route requires it: replace --save with that immutable folder for both sides.

```sh
mkdir -p $HOME/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-input/save
```

Exact dry-run (validated here; incomplete inputs are allowed):

```sh
TMPDIR=$HOME/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch \
$HOME/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python \
scripts/oot_ab.py \
--a $HOME/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build/ \
--b $HOME/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build/ \
--b-host $HOME/.t3/worktrees/nxnative-oot/t3-f55bd7db/dm/host/dmhost \
--save $HOME/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-input/save \
--runs 3 \
--out $HOME/Documents/Crypt/Gaming-rea/_work/nxnative/oot-ab-integrated-01 \
--dry-run
```

Actual A/B: run the same command with the final --dry-run removed, after baseline packing is complete and the parent is ready to run the game. To compare feature flags, append --a-env and/or --b-env with the parent-created literal DM_* env-file paths; cap, measurement and writable storage settings always override those files. For an A/A noise calibration, remove --b-host as well and choose another fresh --out directory. For a genuinely separate candidate package, replace --b with its build folder or .app.

The benchmark intentionally does not assert that identical scripted input reached identical gameplay. Check logs and the scene once before trusting the default [120,178) window. On a cap unsupported by the game/host, results fail rather than reporting a maximum-fps comparison. Keep the Mac display unobscured; no caffeinate process is launched, so avoid system sleep during the parent's run.

## Ocarina shader waste investigation

- Branch `oot-waste` starts at `oot-bench` (`d7696c63`). The initial checkout was clean. The baseline build and its source checkout were inspected read-only. No installs, game run, shader build, host build, push or GitHub action occurred.
- Applied pstack's perf-issue playbook and ponytail. Build the Lever drove the repeatable full census. Explain the Number kept static scores and conditional savings separate from GPU measurements. Runtime traces, an independent review delegate and opening a PR were skipped under the explicit sub-agent and no-run/no-push instructions. Parent review remains open.
- Inspected all 42,851 package records. The finished source census has 42,823 translated shaders and lists every one of the 28 failed candidates. The ordered MSL digest and compact results are in `docs/analysis/oot-shader-waste-summary.json`. Full evidence stays in the assigned analysis folder's `waste/census/` directory. The report is committed at `docs/analysis/oot-shader-waste.md` and copied to the requested external `shader-waste.md`.
- The top five are foliage mesh variants with 971, 971, 940, 930 and 506 potential raw word accesses. The tool expands generated helper calls and loop costs, excludes alternate entry points, counts conditional border samples and packed storage reads, and reports known per-lane loop bounds. The SASS register counts describe NVIDIA, not Apple. Apple spills, actual execution frequency and frame gains remain unmeasured.
- Recovered 6,582 declared BAHS program names with existing read-only container readers. An independent extraction matched the scanner's recovery exactly. The two Metal failures are auto-exposure aggregation programs exceeding bracket nesting 256. One apparent unsupported instruction is a suspicious BAHS descriptor inside another record; documented as open in the shader reference and symptom index.
- The no-stutter requirement preserves build-time compilation for proposed fixes. No shader or host optimization was implemented. Safe pooling needs predicate, range, wrap and alias proofs and overlaps the other implementation lane. No per-shader override is justified. The report gives conditional local lookup savings and pixel/semantic checks, without a frame-time claim.
- Found online pipeline creation in the existing host. The completed offline archive has 30,515 ordinary render bases from 33,190 pairs and omits 2,675 layer-writing pairs. It has no compute or native mesh descriptors. The compute prewarm list has 11 movie keys. Mesh misses build asynchronously while omitting their draws. Exact runtime miss frequency is unknown. Existing encoder timings are not per-shader timings, and the old PASSGPU path does not attach its counters on this Metal 4 path.
- Verification: the scanner completed on the entire real build with three analysis workers and one coordinator. All 25 selected tests pass (14 scanner tests and 11 documentation tests). Direct Ruff and Pyright on the two new Python files pass. Full repository lint is not green: 415 findings against 389 baseline entries, with 26 ratchet additions. These are in unchanged files relative to `oot-bench`: 21 in `scripts/oot_ab.py`, two in `test_oot_ab.py`, two in `test_nsp_mac.py`, and one in `test_tree_tar.py`. No lint baseline was changed. No five-game or image regression was run under the explicit task limits.
- Storage: two interrupted output roots, `waste/census-1/` (37 MiB) and `waste/census-final/` (15 MiB), were removed after their task processes ended and lsof showed no open file or working directory there. Each contained only this task's untracked `shaders.jsonl`; neither was in a Git checkout. Retained the completed census, partial SASS, report generators, pass-name/coverage evidence, logs and final report for parent review. No dependencies or build roots were generated in this checkout.
- The later user instruction sets commit identity to AnkMister and prohibits absolute user paths in committed files. Portable paths are used in the new artifacts. Existing machine paths in this inherited log were changed to `$HOME` without changing their commands' purpose.

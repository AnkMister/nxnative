# Ocarina oot-latest build preparation

This is an implementation handoff for title `0400486024DEC000`, Switch 2 update v131072, on an M4 Max Mac. Correct visuals take priority over stability, pipeline stalls, and efficiency, in that order. The branch is prepared for a full build. The full shader libraries and game app have not been built in this task, and gameplay is not accepted by these source and synthetic checks.

The checkout is `/Users/ankur/Documents/Crypt/Gaming-rea/nxnative`, on `oot-latest`. It started clean on main. The existing checkout was reused; no child worktrees or delegates were needed because the PRs overlap the same renderer and shader-builder files. The protected play app, play worktree, caches, saved sessions and `oot-next2` were not changed. No push or PR was made.

Latest fetched upstream is `46404e8940fa420afa0c34e79d85c2be268c514f`. It is an ancestor of the final branch. The original stack `87564a6bc5c137ad51da9d02cec7069e28f5e99f` is also an ancestor. Local source was reapplied through an explicit merge onto current main, with equivalent implementations resolved in favor of upstream. This preserves original commit provenance instead of rewriting other branches.

## PR decisions

HAVE means the final implementation comes from upstream main or an existing equivalent. The snapshot includes every explicitly requested PR and the newer PRs #1526, #1527, #1530 and #1531 found during this run. PR metadata and source diffs are retained under `oot-latest-audit/prs`; no PR executable payload was run.

| PR | Decision | Author | Reason |
| --- | --- | --- | --- |
| [#1465](https://github.com/seedds/nxnative/pull/1465) | HAVE | rohitkug | Upstream 9c2fb0c9 streams finished libraries through cas.db into the shader image. Keep its bounded batches and progress file. |
| [#1466](https://github.com/seedds/nxnative/pull/1466) | TAKE | Xipzer | Signal guest wakes after releasing the scheduler lock; keep pending wake references until signaling completes. |
| [#1467](https://github.com/seedds/nxnative/pull/1467) | TAKE | Xipzer | Cache Metal texture class checks. Make the cache thread-local to avoid racing its class and answer arrays. |
| [#1468](https://github.com/seedds/nxnative/pull/1468) | TAKE | Xipzer | Keep pass splitting available, but change its default from 256 draws to 0. The play configuration explicitly disables it. |
| [#1469](https://github.com/seedds/nxnative/pull/1469) | TAKE | Xipzer | Avoid attachment lookups when fragment bindings name none of the pass attachments. |
| [#1470](https://github.com/seedds/nxnative/pull/1470) | TAKE | Xipzer | Reject uniform-update lookups outside the recorded update span before scanning pages. |
| [#1472](https://github.com/seedds/nxnative/pull/1472) | TAKE | Xipzer | Reuse argument tables for uniform-only changes; retain the full-path comparison switch. |
| [#1473](https://github.com/seedds/nxnative/pull/1473) | TAKE | Xipzer | Avoid ARC return traffic where the owning registry keeps textures and encoders alive. Preserve local texture ownership checks. |
| [#1475](https://github.com/seedds/nxnative/pull/1475) | TAKE | smile-alive | Preserve the caller PATH before GUI fallback directories. |
| [#1476](https://github.com/seedds/nxnative/pull/1476) | TAKE | rohitkug | Honor WORK for compiler scratch. Upstream already supplies bounded batches and eager per-shader cleanup, so keep those implementations. |
| [#1478](https://github.com/seedds/nxnative/pull/1478) | HAVE | v0lumehi | The stack already fixes the texture-pool-marker expectation in 4d9b5b45. |
| [#1479](https://github.com/seedds/nxnative/pull/1479) | SKIP | ilyakarevcop | Explicitly excluded. Fast Fusion changes and its translator payload are outside this Ocarina Mac build. |
| [#1480](https://github.com/seedds/nxnative/pull/1480) | HAVE | akshay4 | Upstream 04df08d4 already corrects BAHS control lengths and the affected profile tables. |
| [#1481](https://github.com/seedds/nxnative/pull/1481) | TAKE | akshay4 | Printed controller face-button labels are available and enabled in this build env. |
| [#1482](https://github.com/seedds/nxnative/pull/1482) | TAKE | akshay4 | Adapt the residency-set measurement to the retained DM_SAFE_GPU guard. Do not replace the wired-memory reserve, watchdog or fault-stop handling with the older bundled guard. |
| [#1483](https://github.com/seedds/nxnative/pull/1483) | SKIP | aksmith-git | Control-path expansion and texture-dump filtering are diagnostics, with no demonstrated improvement to this play build. |
| [#1484](https://github.com/seedds/nxnative/pull/1484) | TAKE | aksmith-git | Key shader code without making its guest pools resident to the GPU. |
| [#1485](https://github.com/seedds/nxnative/pull/1485) | SKIP | thehobbit85 | Explicitly excluded iOS TV/settings UI. |
| [#1486](https://github.com/seedds/nxnative/pull/1486) | SKIP | aksmith-git | Its first-out-of-memory stop is iOS-only. The Mac keeps DM_SAFE_GPU and GPU-lost stops. |
| [#1487](https://github.com/seedds/nxnative/pull/1487) | TAKE | thehobbit85 | Preserve shared-memory store arguments and atomic side effects in optimized translator output. Source only; rebuilt locally. |
| [#1488](https://github.com/seedds/nxnative/pull/1488) | TAKE | aksmith-git | Union its prewarm list with #1493. Retain every distinct row including task/mesh states. |
| [#1489](https://github.com/seedds/nxnative/pull/1489) | TAKE | PucaVaz | Patch pool tables using changed-ID notes instead of rebuilding all entries. Integrate with the retained view/ancestor lifetime rules. |
| [#1490](https://github.com/seedds/nxnative/pull/1490) | TAKE | Xipzer | Mac mouse camera and its settings plumbing. Mouse capture remains a click action, with Escape releasing it. |
| [#1491](https://github.com/seedds/nxnative/pull/1491) | SKIP | aksmith-git | The staging shrink is gated to iOS; it does not improve this Mac build. |
| [#1492](https://github.com/seedds/nxnative/pull/1492) | TAKE | aksmith-git | Return released guest-file blocks and account for dirty pages in the disk-space guard. Preserve dm_guest_in_files. |
| [#1493](https://github.com/seedds/nxnative/pull/1493) | TAKE | itsyunusacar | Add distinct first-start states to #1488 rather than replacing its mesh and other scene coverage. |
| [#1494](https://github.com/seedds/nxnative/pull/1494) | SKIP | CatPawPrint | Explicitly excluded Pokemon Friends account flow. |
| [#1495](https://github.com/seedds/nxnative/pull/1495) | SKIP | CatPawPrint | Explicitly excluded Pokemon Friends add-on mount flow. |
| [#1496](https://github.com/seedds/nxnative/pull/1496) | SKIP | TheGoldfish11 | Explicitly excluded Tetris 99 time-service flow. |
| [#1497](https://github.com/seedds/nxnative/pull/1497) | TAKE | givethesourceplox | Build-ID-gated v131072 render-scale ceiling. Default 1.0 preserves the original scale store. |
| [#1498](https://github.com/seedds/nxnative/pull/1498) | TAKE | akshay4 | Optional residency-based preallocation budget. Leave DM_POOL_BUDGET_MB unset. |
| [#1500](https://github.com/seedds/nxnative/pull/1500) | SKIP | mmkzer0 | Vulkan attachment semantics do not affect Ocarina, which uses NVN. |
| [#1502](https://github.com/seedds/nxnative/pull/1502) | HAVE | hlstwizard | Ported first, then upstream merged it as 48d0b372 during this run. The final branch contains that upstream commit and keeps its implementation. |
| [#1503](https://github.com/seedds/nxnative/pull/1503) | TAKE | Romen-Adama-Dev | Use atomic AND/OR for independent subword stage-memory stores. Preserve #1487 side effects; source-built translator only. |
| [#1508](https://github.com/seedds/nxnative/pull/1508) | SKIP | Atomsk-debug | Explicitly excluded language-selection plumbing; no required Ocarina English-play fix. |
| [#1515](https://github.com/seedds/nxnative/pull/1515) | TAKE | Atomsk-debug | Use the compare whose flags actually guard the jump-table dispatch. This applies to the next rewrite, including Ocarina. |
| [#1520](https://github.com/seedds/nxnative/pull/1520) | TAKE | melocalex | Cold compiler launch/PCH improvements and readable-tile compilation. Preserve exact function-constant metadata and the ordinary HMMA default. |
| [#1521](https://github.com/seedds/nxnative/pull/1521) | SKIP | 3ig | The demonstrated defect is Unity copying programs in Ori. No Ocarina copy defect is established; this also changes key-record lifetime to process lifetime. |
| [#1522](https://github.com/seedds/nxnative/pull/1522) | TAKE | Romen-Adama-Dev | Include all eligible compute shaders in offline archives and load compute pipelines from those archives. Preserve exact AOT inventory and every split bundle part. |
| [#1524](https://github.com/seedds/nxnative/pull/1524) | SKIP | kishan-dhankecha | Explicitly excluded. It includes a Mac icon override as well as iOS plumbing, but changes no Ocarina picture, stability or pipeline behavior. |
| [#1526](https://github.com/seedds/nxnative/pull/1526) | HAVE | lunks | Ported, then upstream 8764cdfc supplied the equivalent frame-queued stub. Keep upstream plus the local guest-file fixture hook. |
| [#1527](https://github.com/seedds/nxnative/pull/1527) | HAVE | lunks | Ported first, then upstream merged it as 46404e89. Keep the upstream closed microphone-stream responses and our added null-stream regression checks. |
| [#1530](https://github.com/seedds/nxnative/pull/1530) | SKIP | aksmith-git | Substitutes flat normal maps and a neighbouring baked texture for damaged RomFS files. This can reduce reload work, but it changes visual content, the Ganon replacement is untested, and damage in our copy is not established. Correct visuals take priority. |
| [#1531](https://github.com/seedds/nxnative/pull/1531) | TAKE | Atomsk-debug | Use the registered display version when a NUP-derived build lacks control data. Package control data still wins; unknown builds remain unknown. |

## Local implementations dropped or replaced

| Local implementation | Final choice |
| --- | --- |
| #1464 MSL range rewriting | Keep upstream `0f510fd5` translator last-entry caching and its mesh-variable handling. Remove the redundant `raw_ranges` call from the shader build; leave its isolated transform/test available. |
| Opt-in copy-stride capture | Keep upstream `cac783a1`, which always records strides as command-buffer state. Remove `DM_NVN_COPY_STATE` from the play env. |
| Community `3604b403` ATOMG.CAS decoder | Keep upstream `04df08d4` decoder, opcode identity and address handling, including its global INC/DEC support. |
| Community `168290c6` indirect mesh recorder | Keep upstream `6d928fd1` implementation, including its Metal GPU-address signature. |
| Community bracket-depth patch | Keep upstream's general 1024-depth compiler convention. |
| Older HMMA uniformity implementation | Keep upstream `bd9f422d` loop/back-edge analysis. Retain local opt-in gating and the reserved temporary accumulator slot. |
| Harvest `d1f25de6` single-archive cleanup adaptation | Restore the complete `42658776` split archive implementation and reapply `0907c1e2`. Reuse now preserves every manifest-listed part and removes only obsolete parts. |
| #1465 streaming patch | Keep upstream `9c2fb0c9` bounded-batch/cache-image implementation. |
| #1476 cleanup loops | Keep upstream per-shader/batch cleanup; port only the missing caller WORK handling. |
| Local ports of #1502, #1526 and #1527 | Main advanced during the task. Merge `48d0b372`, `8764cdfc` and `46404e89` and keep the equivalent upstream implementations. Retain our added null-stream tests. |

The held-object implementation retains its parent-view accounting and opt-in switch. Replacing it with an earlier direct-object-only count could permit evicting a live view's parent. Other local safety hooks, texture ownership repairs, HDR support, draw-preserving workers, mesh padding and point topology remain in the source.

## Conflicts and resolutions

The complete initial merge conflict diff is `oot-latest-audit/stack-conflicts.diff`; file-level choices are in `stack-resolutions.json`. Per-port application logs are `port-N.log`.

| Area | Resolution |
| --- | --- |
| Initial game note and reference entries | Keep current upstream findings and local historical findings. Regenerate the symptom index. |
| Initial shader chain header, lock and DLL conflicts | Treat generated values as pending, never choose a PR translator to run. Rebuild the combined source, write the lock, then generate the final header. |
| Initial `hle_nvn.c` copy paths | Keep unconditional upstream stride snapshots and local destination-range tracking. |
| Initial `nvn_rec.h` | Keep upstream indirect mesh replay. |
| Initial renderer ownership/count helpers | Keep one local ancestor-aware count table and all its writers. Preserve upstream pool-finalization ordering and linear-texture deswizzle restrictions. |
| Initial archive specialization | Keep upstream specialization-descriptor ownership and the local mesh guard/worker behavior. |
| Initial CPU-texture tests | Keep both upstream finalization-race coverage and local packaged-holder/range coverage. |
| Initial mesh tests | Keep upstream private-variable preservation and local point-topology coverage. |
| Initial translator conflicts | Keep upstream CAS and HMMA loop analysis; retain the ordinary default HMMA ABI and temporary-slot isolation. |
| #1467 | Preserve the local RED key bound and GPU-owned texture classification. Make the class cache thread-local. |
| #1468 | Keep both the raw-pool commit hook and pass-split declarations. Set pass splitting off by default in code and env. |
| #1473 | Apply unretained returns around the existing ownership, pool-heap and release code. Preserve all local return branches. |
| #1476 | Reject its older global translation/finish loops; use current upstream batching and cleanup. |
| #1482 | Its three-commit diff bundles an older guard. Drop that attempted replacement and port only residency accounting into `nvn_safe_gpu.inc`, with a no-copy-alias regression check. |
| #1489 | Keep local pool-release bookkeeping and lifetime protection. Shared holder re-uploads must leave notes for every live or finalized serial naming the holder; a generic generation bump defeats incremental tables. Alias deletions that affect no live serial leave a serial-zero note. Adapt the upstream test to assert the retained live-parent protection, while still comparing patched tables to full tables. |
| #1490 | Keep both `front_screen.h` and the new mouse header as host dependencies. |
| #1492 | Preserve `dm_guest_in_files` and add the file chunk/dirty-page accounting. Keep both game-note findings. |
| #1493 | Union and deduplicate the two manifests. No first-start or mesh state is discarded. |
| #1497 | Keep all existing reference sections and add the build-checked render-scale stub. |
| #1498 | Apply residency accounting to the local factored `pool_room`, keeping its budget and smallest-first walk behavior. |
| #1502 | Keep the local segment counter and the new bound-target preservation hook. Upstream later supplied the same source. |
| #1503 | Keep both shader findings. Adjust #1487's optimizer regression to verify the new AND/OR write helper survives, rather than requiring the removed CAS loop. |
| #1520 | Use `main0_f` for readable-tile fragments while retaining exact constant metadata. Keep upstream raw lookup caching. Restore the ordinary HMMA helper body after an early test caught the chain helper in the legacy slot. Adapt AST test loaders and the progress-file fixture to current APIs. |
| #1522 | Support plain compute tuples alongside render tuples and exact descriptor dictionaries. Keep constant specialization, AOT learning, shader-image extraction and split parts. All bundled parts count as bundled during archive compaction. The expanded AOT planner already enumerates compute shaders, so do not insert its plain map kernels a second time. |
| #1526 and latest-main merges | Keep upstream frame-history stub plus the local guest-file fixture hook. For #1527 the only conflict was our corrected apostrophe against a shell-escaped apostrophe in the upstream source comment; keep the readable comment. |
| #1531 | Clean source port. Regenerate the symptom index. The registered display version applies to this NUP-derived build; package control data still wins. |
| Final safety check | Background sleep coalescing made fifty 2 ms sleeps exceed the intended 100 ms residency-lock wait. Use an elapsed-time deadline. The test retains its 500 ms upper bound and passes at background priority. |
| Loader fixtures | Both main and the stack added `mtl_present_screen`. Remove the duplicate local definitions from `t_nro.c` and `t_symbols.c`; keep the upstream definitions. |
| Final held-serial test | Its reference and debug modes scan the full table by design. Run their correctness checks, and measure the normal counted mode separately under Metal validation. Remove a duplicate Makefile target. |
| Split archive restore | Preserve compute counts in archive metadata and manifest-listed parts during reuse. |

## Play defaults and build controls

The new folder is `/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot-latest/`. `run-build.sh` delegates to the committed `scripts/build-oot-latest.sh`. It has not been executed. The committed env source is `docs/oot-notes/oot-latest-env.txt`; helper sources are in `docs/oot-notes/oot-latest-inputs/`.

Runtime AOT and strict runtime AOT remain off. `DM_SAFE_GPU=1`, `DM_GPU_LOST_STOP=1` and `DM_NVN_SERIAL_HELD=1` remain on. BCRT, pool heaps, guest texture release, alias retirement, HMMA tensor replacement, dispatch overlap, pass splitting, HDR and MetalFX replacement remain off. `DM_RENDER_SCALE=1` preserves the game-selected scale. `DM_POOL_BUDGET_MB` stays unset.

`DM_PSO_MTL4=1` makes the archive path explicit. Mouse camera and printed pad labels are enabled with `DM_MOUSE=1` and `DM_PAD_LABELS=1`. The mouse is captured by clicking the picture; Escape releases it.

Build-only AOT stays on and strict, with both saved pipeline censuses and the live census frozen only after dmhost exits. The build-derived profile copies current source tables and adds only census-proven readable-tile wants. It includes the new combined seed list. Compiler scratch and game outputs are isolated under the new build root. The script refuses less than 64 GiB free, uses four workers and runs through `taskpolicy -b nice -n 19`. It checks the source-built translator lock and chain tests before starting the app build.

## Translator and chain

The translator and universal launcher were rebuilt from this branch's source. None of the binary diffs from #1487, #1503 or other PRs were copied into the build. The 57 existing offline NuGet packages were checked against saved publication dates and SHA256 hashes before restore; all exceeded the seven-day cooldown. No online dependency upgrade or install was performed.

The final chain is `c9efd1ed86f3`, with HMMA chain reuse off. `tool_lock.py --update-lock` records the locally produced assemblies and installed compilers. The header is generated from the final source and lock. Initial preliminary headers and failed test attempts are retained as failed evidence, not counted as final passes.

The full new Mac shader-library rebuild is deferred to the prepared full-build script, per the instruction not to run that build. It must produce matching libraries, `inputs.tsv`, `c1_full.tsv` and `cb_extent.tsv`, then a matching host. Existing play libraries cannot be used with this chain. There is no iOS target or device installation in this task.

## Verification and limits

Logs live in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-latest-audit/`.

| Check | Final result | Evidence |
| --- | --- | --- |
| Integrated source-built translator | Offline restore and publish passed; 57 cached packages passed date/hash checks; all restored asset packages matched the audited set | `translator-restore.log`, `translator-build.log`, `translator-assets-audit.json` |
| Translator lock and script syntax | `tool_lock.py --check-tools`, `zsh -n` for both build scripts, and `git diff --check` passed | `verification.json` |
| Python checks in 24 modules | 459 selected: 458 passed across the base suite and the enabled-translator recheck; 1 optional Unicorn check skipped | `python-tests-clean.log`: 459, 74 skips; `translator-tests-clean.log`: all 73 translator checks passed with the source-built executable |
| Real offline pipelines | 48 passed, with the real Metal AOT fixture enabled. Covers render/mesh/constants, split/reused parts, duplicate-free compute planning and compute archive hits with runtime `DM_AOT=0` | `pipeline-tests-final.log` |
| Native renderer checks | 31 targets passed after the alias and safe-GPU corrections. The pool-note test passes 81 checks; patched tables equal full tables | `native-results-verified.json`, original per-target logs, `alias-recheck-final.log`, `safe-gpu-check-final.log` |
| Held serials | Reference mode 27 checks, debug-comparison mode 27, normal counted mode 28. Normal mode took 0.092 ms in the synthetic 1,000-entry/20,002-serial takeover, under Metal validation | `alias-recheck-final.log` |
| Host memory and scheduler | Guest-file/dirty-page, map-limit, 16 KiB page, real dirty tracking, notification delivery and screen tests passed | `host-tests.log` |
| Loader and stop handoff | NRO lifecycle, symbol indexes and blocked-cleanup exit passed | `loader-stop-tests-final.log` |
| Audio and pad labels | Closed microphone-stream assertions, real/silent output lifetime, suspend/resume, device recovery and Apple pad checks passed on final recheck | `audio-tests-recheck.log`, `pad-tests-final.log` |
| Host | `make -j4 -C dm/host GAME=0400486024DEC000 dmhost` passed with the final renderer and safety changes; 62 existing compiler warnings remain | `host-build-final.log`, `built-artifacts.json` |

The base Python run deliberately left the translator environment unset; its 73 conditional tests were then rerun explicitly against the source-built translator and all passed. The only remaining unexecuted check is optional ARM64 emulation of the actual render-scale stub because Unicorn is not installed. The profile/stub source checks pass. No dependency was installed to make the skip disappear.

Earlier failures are preserved. These include the HMMA helper merge, old fixture APIs, missing compute function metadata in the test fixture, incremental holder invalidation, and the background-safe lock wait; each was corrected and rechecked. One real-audio recovery attempt at background priority under concurrent verification load failed to observe callbacks. The same unchanged audio code passed an earlier background run and the final ordinary-priority real-device check. This scheduling-sensitive failure remains in `audio-tests-final.log`; music quality and playing a song in the game are unverified.

The seed union has 9,846 distinct rows: 8,376 shader rows, 1,267 render states, 145 compute states and 58 task/mesh states. Every referenced key exists in the current 42,849-key shader map. All merged shader-pair keys exist too.

The regression harness was invoked for the one local title and exited 2 before building or launching anything because REGRESS_ROOT and REGRESS_GAMES are not configured. Only Ocarina assets are local. The other relevant coverage would be Mario Kart World for mesh/storage, Tears of the Kingdom for CPU textures, Breath of the Wild for attachment/lifetime behavior, and Star Fox for compute/image behavior. No five-game regression or gameplay acceptance is claimed.

Pipeline archives reduce compile misses only for covered descriptors. The seed lists and saved sessions do not prove coverage of every unseen scene, mesh state, attachment format or function-constant combination. Runtime AOT stays off as requested, so uncovered pipelines may still compile in play. A complete cold-build and representative cold-cache playthrough are required before claiming zero stutter or visual parity. Synthetic Metal results and a host compile do not prove either.

PR #1530 is intentionally absent. Flat normal maps and a neighbouring baked texture are content substitutions, and its Ganon replacement has no in-game check. This branch does not hide missing or damaged textures behind that unverified visual tradeoff. If our dump has the reported damage, its reload cost remains open until the assets are verified or replaced with correct copies.

The safety guard still cannot guarantee that a kernel call already stuck inside the driver will return. The residency-size correction can observe growth one commit later; the lower local memory cap and independent wired-memory reserve remain. Risky scheduling and memory-release features are not enabled to hide this limit.

The implementation sub-agent does not supply independent review of its own ports. The parent should review the combined source, especially descriptor inventory, residency accounting and shared-holder invalidation, before starting the full build.

## Storage

No worktree was added, no game app was built, and no existing cache or saved session was removed. Exact generated roots are listed in `oot-latest-audit/generated-roots.json`. Compiler outputs in the maintained checkout are retained. Test logs, source-built translator output, PR diffs, source-resolution evidence and build inputs remain available for review. Temporary test fixtures clean up through their own test lifetimes. The task scratch contents were removed after confirming no open files or process working directories and no Git repository or tracked files: 16,384 bytes, with an exact manifest in `scratch-cleanup.json`. The empty scratch directory remains for reruns. There was no use of /tmp or /private/tmp for task storage.

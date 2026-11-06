# Brent round 2 host and runtime harvest

The branch ports four source units for the Ocarina Mac integration. Texture
quality reduction is excluded. The runtime experiment and build layout changes
are default off. No game, full shader build, regression gameplay run, or Mac
host build ran on Linux. No packages were installed.

## Compared revisions

- Integrated base `oot-hyper-main`: `a14fb78c`.
- Upstream snapshot `origin/main`: `c83c48f2`.
- Brent source branch: `89a0ff52`, inspected from `a54b2092` onward.
- Destination: `ankmister`, branch `oot-brent2-misc2`.

The task file authorizes this push and the AnkMister commit identity, overriding
the shared context's no-push rule and AGENTS.md's seedds identity.

## Verdicts and value for Ocarina on a Mac

Value is inferred from the source and its reported observations, not measured
on this branch. Present means semantic presence, rather than only ancestry.

| Rank | Item and source | Integrated base | Upstream snapshot | Verdict and reason |
|---|---|---|---|---|
| 1, high | PR #1392, `8cf26912`, merge `f4955191` | Missing; existing guard and retired-ID policy cover different mechanisms | Missing | Port behind `DM_NVN_IDLE_RETIRE=1`. Out-of-focus pool churn can otherwise retain buffers until a submission that never arrives. Source reports about 770 MB/s retained. |
| 2, high for builds | PR #1438, `ea680b3e` | Missing | Missing | Port shader Spotlight exclusion behind `DM_BUILD_NOINDEX=1`. Large shader trees need not be indexed. No shader content or image quality changes. |
| 3, medium for builds | PR #1355, `2e1f4953` | Missing | Missing | Port temporary-folder exclusion under the same build flag. Fix all capture helpers to use the selected folder too. |
| 4, low direct OoT value, useful general correctness | Present crop/layer shape, `2202d610` (issue #949) | Missing | Already merged as a correctness fix | Port without a flag under the task's upstream-correctness exception. Crop selects texels; layer dimensions control display proportions. OoT benefit is unmeasured; Galaxy 2's anamorphic crop is the documented case. |
| 5, test correction | Present fixture, `51ea3df8` | Missing | Missing | Port with the crop fix. Square fixtures declare a square layer. No runtime change. |
| 6, useful diagnostics, assigned elsewhere | PR #1436, `01cce669`, merge `8ed8a820` | Missing | Missing | Skip because the task explicitly assigns poolstat/texstat to the Mac agent. Live PR metadata confirms #1436 is these diagnostics, not the older memory guard. |
| Excluded for quality | PR #1418, `4b13851d`, `1269a71f`, merge `78ab71dc` | Missing | Missing | Skip. Omitting up to three compressed texture mip levels reduces image detail. No OoT saving has been verified here. Its prerequisite and incidental unrelated hunks are not imported. |

PR records were read through `gh pr view` for #1392, #1436 and #1438.
Sources: [#1392](https://github.com/seedds/nxnative/pull/1392),
[#1418](https://github.com/seedds/nxnative/pull/1418),
[#1436](https://github.com/seedds/nxnative/pull/1436),
[#1438](https://github.com/seedds/nxnative/pull/1438),
[#1355](https://github.com/seedds/nxnative/pull/1355).

## Commits

| Commit | Source and final behavior | Mac verification |
|---|---|---|
| `a9fb6b01` | `2202d610` plus `51ea3df8`. Shared presentation uses layer shape, including frontend shape reports, both encoders, MetalFX and captures. | Host build, t_present_crop and t_present_alloc; Galaxy 2 anamorphic scene, BotW taller screen, ordinary OoT present. |
| `50cd958a` | PR #1355, `2e1f4953`. `DM_BUILD_NOINDEX=1` selects tmp.noindex. Capture/heap/region helpers follow TMP. Old tmp data is preserved rather than deleted. | Check temporary files and Spotlight exclusion during an authorized build. |
| `41f2ce4d` | PR #1438, `ea680b3e`. Same flag selects shader.noindex and renames an existing shader folder. Existing destinations and symlinks are preserved. Reader tools support both layouts; bench/regress follow the flag when both exist. | Reuse an existing cache without retranslating; verify packer paths and Spotlight exclusion. |
| `7890ca61` | PR #1392, `8cf26912`/`f4955191`. Opt-in pending residency accounting, idle retirement and asynchronous drain; explicit DM_CTL focus diagnostic. | Host build; t_res_guard ordinary and stuck-lock modes; t_hid; OoT focus loss/resume with memory tracking and safety mode enabled. |

The source was ported without translator binaries. No chain tool changed, so
no chain version or shader library rebuild is required by these source changes.

## Differences from Brent and preserved integration

Our PR #1391 memory guard and `DM_SAFE_GPU` remain. Safe mode keeps its 70%
working-set cap, submission checks, error stop, and wired-memory checks.
The existing linear deferred partition and submission-aware retired-ID policy
remain. No replacement versions of #1382, #1409, #1408 or #1420 were imported.
The crop port preserves the integrated shader/host paths. The Spotlight port
keeps our AOT seen-descriptor handling in mac_pso.

The new idle behavior needs two corrections beyond the source port. First,
submission begin reserves a retirement fence under the pool lock. Deletion
uses that reservation under the same lock. Commit does not clear it, so a
concurrent deletion cannot combine an old fence with a newly closed submission.
Current chunks and superseded large-pool chunks use the same fence.

Second, the watchdog schedules at most one idle drain worker. A worker blocked
on a driver-held residency lock cannot block later watchdog ticks. Tests cover
pending additions, default-off retention, idle release, an open submission,
fence reservation across commit, old large-pool chunks, and pending retirement
while the residency lock is held. These Metal tests are written but unrun here.

New controls:

- `DM_NVN_IDLE_RETIRE=1` enables the runtime port. Default off. Leave
  `DM_SAFE_GPU` at the integration default for gameplay checks.
- `DM_BUILD_NOINDEX=1` enables both folder exclusions. Default off. Keep it
  consistent for build and benchmark/regression commands. Changing it does not
  delete caches, but can create separate shader trees. If both exist, readers
  follow this setting.

## Linux verification

The installed Python 3.14.2 interpreter was used directly. System Python 3.10
cannot run the build-planning tests because the script requires Python 3.12+.
No environment or dependency was installed.

Final focused command, with TMPDIR under the project work folder:

```sh
~/.local/share/uv/python/cpython-3.14.2-linux-aarch64-gnu/bin/python3 -m unittest \
  dm.tools.tests.test_docs dm.tools.tests.test_nsp_chain \
  dm.tools.tests.test_nsp_work_dir dm.tools.tests.test_bench \
  dm.tools.tests.test_bug_report
```

Result: **62 tests passed**. The checks cover migration, preserved times and
keys, existing destinations, symlinks, default-off names, reader selection and
document links/indexes. `docs_symptoms.py` regenerated 924 symptoms.
`py_compile` passed for the four changed scripts. `git diff --check` passed.

The broader tools run attempted 110 test files separately: **77 passed, 33
failed**. One further test, test_xlate_anycpu.py, was excluded because it reads
the forbidden translator directory. Per-file outcomes are committed in
[oot-brent2-misc2-tests.json](oot-brent2-misc2-tests.json). Full output is in
`~/Documents/Crypt/Projects/_work/nxnative/oot-brent2-misc2/tool-tests/`.

Failures include missing capstone/lz4, missing clang/dotnet/xattr/lipo, the
macOS-only libproc.dylib import in regress.py, BSD cp flags in Mac packaging,
an inode-reuse assertion in test_nsp_mac, a toolchain expectation in
 test_own_compilers, and an older git merge-tree interface. These results are
not a green suite. No baseline rerun was used to claim every failure preexists.
The changed-path tests that can run independently are green.

The broad test selection also attempted bundled SPIRV-Cross through
 test_spirv_cross_pin. Linux rejected it with Exec format error before any
binary code ran. This test should have been excluded in advance. No translator
binary was run, copied or inspected, and no foreign binary executed.

`cc -std=gnu11 -fsyntax-only` passed for hle_hid.c, hle_vi.c and t_hid.c using a
generated OoT game_profile.h outside the repo. Warnings concern the existing
BSD mergesort declaration and platform uint64_t printf spelling. Objective-C
Metal and loader compilation remain unchecked without Apple's SDK and clang.

`env_switches.py --check` recognizes both new controls but fails on six existing
stale documentation mentions: DM_NVN_CUT_FIRST, DM_NVN_HANGLOG, DM_NVN_VC_WAYS,
DM_PRESENT_EDR, DM_RESCALE and DM_UPSCALE. Those unrelated controls were left
untouched. Full lint-c/lint-python could not be certified in this environment.

Independent Codex review found the retirement/watchdog and path issues described
above. A separate static recheck accepted the concurrency fixes and identified
the old large-chunk path, which was then fixed with matching test coverage.
Claude review was unavailable because the provider is not authenticated.

## Remaining Mac acceptance

None of the runtime changes is certified for gameplay by this Linux run.
Build the host with GAME=0400486024DEC000, then run the Metal tests named in the
commit table. Check both values of the runtime opt-in with safety mode enabled,
including repeated focus loss, streaming and resume. Record allocation, memory,
GPU errors and screenshots; do not infer savings from the source's numbers.

When Mac gameplay testing is authorized, the five-game regression set should
cover OoT (`0400486024DEC000`, streaming and focus), Galaxy 2
(`0100FD8022DAA000`, Vulkan anamorphic crop), Link's Awakening
(`01006BB00C6F0000`, NVN crop), Breath of the Wild (`01007EF00011E000`, taller
screen), and Metroid Dread (`010093801237C000`, deferred-release churn).
These are proposed coverage targets, not games available or tested on Linux.

The branch publication command is:

```sh
git push ankmister HEAD:refs/heads/oot-brent2-misc2
```

No PR is created and no changes are merged into oot-hyper-main by this task.

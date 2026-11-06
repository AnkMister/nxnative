# Ocarina upstream stack implementation notes

## Outcome

Integration stopped before the first merge, as required by the task's explicit
rule: "If a PR needs a different dmsh_xlate_bin, stop and report."
PR #1360 needs different bundled translator binaries. No implementation or
merge commits were made. This branch contains only this report on top of
`ee9b7765d579c46e45a7297493565e098f3bda33`.

The worktree was clean at entry. It initially used branch `t3/81a0db5d`, which
the outer environment renamed to `t3/oot-pr-stack` during inspection without
changing HEAD. I created the requested local branch `oot-stack` from that HEAD.
Only `pull/1360/head` was fetched, into local ref `pr-1360`. No push, PR,
GitHub comment, package installation, translator rebuild, game build, shader
build, regression run, or device work occurred. Neither protected baseline
directory was accessed. No scratch outputs were created.

## PR status

All four PRs were OPEN and MERGEABLE according to `gh pr view` during this run.
That is GitHub's status against upstream main, not proof of compatibility with
this Ocarina stack.

| PR | Inspected head | Stack status | Tests run | Risk or remaining work |
| --- | --- | --- | --- | --- |
| [#1360](https://github.com/seedds/nxnative/pull/1360) | `eaa7a1daed0eca9427941889462f683234235c44` | Blocked before merge by the translator stop rule. No conflicts attempted. | None. Source, binary diff, lock and PR description inspected. | Requires the shipped updated translator and matching host/shaders. Keeping the old translator would retain its fixed search bound. |
| [#1405](https://github.com/seedds/nxnative/pull/1405) | `3fe33bc3997aaba9ef15b0497b5e80c1895edabe` | Not merged because #1360 blocks the ordered stack. No conflicts attempted. | None. PR description inspected. | Its documented fixed-table matcher needs verification against #1360's actual emitted helper. Present latency remains open. |
| [#1161](https://github.com/seedds/nxnative/pull/1161) | `b21178a2b22366e86595012e3195640257a54ad4` | Not merged because #1360 blocks the ordered stack. No conflicts attempted. | None. PR description inspected. | Numeric lookup cache needs integrated feedback tests. |
| [#1389](https://github.com/seedds/nxnative/pull/1389) | `c4204db67f30d697c4255f34aa63929d29aae420` | Not selected under the "only if it is general" condition, based on its PR description. No conflicts attempted. | None. PR description inspected. | The author explicitly limits default enablement to Bananza through its profile key because game speed in VRR mode needs validation. Ocarina at its 30 fps cap has no demonstrated benefit here. |

## Translator blocker evidence

Commands used include:

```sh
gh pr view 1360 --repo seedds/nxnative --json body,files,headRefOid,mergeable,state
git fetch --no-tags origin pull/1360/head:refs/heads/pr-1360
git diff pr-1360^ pr-1360 -- dm/gfx/tools/dmsh_chain.lock
git diff --stat pr-1360^ pr-1360 -- dm/gfx/tools/dmsh_xlate_bin
```

The PR's own commit replaces these five artifacts:

```text
dm/gfx/tools/dmsh_xlate_bin/Ryujinx.Common.dll
dm/gfx/tools/dmsh_xlate_bin/Ryujinx.Graphics.Shader.dll
dm/gfx/tools/dmsh_xlate_bin/Spv.Generator.dll
dm/gfx/tools/dmsh_xlate_bin/dmsh_xlate.dll
dm/gfx/tools/dmsh_xlate_bin/dmsh_xlate.pdb
```

The lock records these differences from the requested Ocarina base:

| Artifact | Ocarina base fingerprint | #1360 fingerprint |
| --- | --- | --- |
| `dmsh_xlate.dll` | `ec44dceaa4da2fa9` | `2d35a6c4e55455a1` |
| `Ryujinx.Graphics.Shader.dll` | `50581a78af87cf53` | `10beb9e8d40f86fe` |
| `Ryujinx.Common.dll` | `243e1e08993eabb3` | `51756311ad91ef33` |

In #1360's `GlobalToStorage.cs`, `GmemMapCountWord = 4` replaces the fixed
`GmemMapLog2 = 12`. The generated search initializes `step` from table word 4
shifted right by one, then halves it until zero. This is a translator change,
not just a larger host allocation. The PR description also states that its
translator was rebuilt and all game shaders must be rebuilt.

The actual MSL helper was not emitted or inspected. The shipped binary update
was not accepted under the task's stop rule. No conclusion is claimed about
the #1405 matcher from a generated MSL test, and no safety adaptation was made.

## Latency investigation

I read #1405's PR text. It reports approximately 1.80 to 1.98 ms lower
whole-frame GPU medians, alongside approximately 39 to 61 ms higher median
enqueue-to-display latency at the direct-present 30 fps target. These are
upstream measurements, not results on this M4 Max or this checkout.

Host present-path inspection and any proposed env-gated fix remain unstarted
because the explicit stop condition was reached first. A display-link tick
selection cause is still a hypothesis. No host env flag was added.

## Verification and A/B handoff

No tests were run because integration stopped before any source or chain
change. In particular, the tools discovery suite, `test_dmsh_wide.py`, graphics
tests and `test_nsp_chain.py` are unrun. No chain header was edited or generated.
The requested done criteria are not met.

To resume, the parent must first resolve whether accepting #1360's already
shipped binary update is allowed under the translator stop rule. No local
`dotnet publish` is needed to obtain those shipped files, but they are still a
different `dmsh_xlate_bin` from the Ocarina base. Merging #1360 as supplied also
pulls its upstream-main ancestry; conflicts with Ocarina's raw-memory changes
have not been assessed.

The following are the exact relevant settings documented by the task and
#1405 for a future Mac-only A/B build. They have not been exercised on this
branch and do not make this report an integrated candidate:

```sh
export PATH="$HOME/.dotnet:$PATH"
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
export DM_GAME=0400486024DEC000
export GAME=0400486024DEC000
unset IOSOUT

# Scalar arm. Use this environment consistently for header, shaders and host.
unset DMSH_RAW_LOAD_QUADS

# Quad arm. Use this instead, consistently for header, shaders and host.
export DMSH_RAW_LOAD_QUADS=1
```

Use `/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python` for every
Python command. After an authorized integration, regenerate the header with
that Python and `dm/gfx/tools/dmsh_chain.py --header`; never resolve its
conflicts by hand. Each arm needs separate shader outputs and a matching host.
Limit build parallelism to `-j6` or fewer. Keep the game's own 30 fps cap and
existing pacing settings unchanged for the first comparison. No VRR flag is
required or recommended by this report. Parent build commands and output
locations remain to be selected after the running baseline finishes.

## Deviation from the plan

The required translator dependency was present in the first PR. I followed the
explicit stop rule rather than partially merge it, mix its host with the old
translator, skip ahead in the ordered stack, or add untested pacing changes.
The only local commit records this blocker.

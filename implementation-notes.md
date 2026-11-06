# Ocarina integrated branch

The branch is `oot-hyper`, based on oot-stack `8284776d`. Branch snapshots are
preserved in [docs/oot-notes](docs/oot-notes/FLAGS.md). Local commits only; no push,
PR, game run, regress.py, full shader build or protected baseline/game writes.

## Merge order and exclusions

Separate merge commits bring in oot-stable, oot-visual, oot-cpu, oot-idle,
oot-upscale, oot-bench, oot-msl, oot-tbdr, oot-stagecache, oot-vqa, oot-quality
and oot-clock, in that order. The final history places stability immediately
after oot-stack and visual correctness immediately after stability.

The initial growing integration merged oot-mem and oot-1203, then reverted both
merge commits using `git revert -m 1` after the stop-change review. That history
is retained as `oot-hyper-before-early-safety`. The final ordered history omits
both blocked merges entirely; the original correcting border path remains.
No source branch was rewritten. The temporary ordered branch is retained locally.

## Combined translator rebuild

Exactly one restore/publish was performed after merging all translator C# sources.
Source snapshot: `64fd458c`, including the stack's GlobalToStorage changes and all
visual source ports. The original native launcher was retained. No upstream PR
binary was executed as the integrated translator.

The cooled-NuGet procedure audited the exact 57 dependency versions from the
bundle dependency manifest against official NuGet registration publication dates.
Every package was older than seven days. Only these packages entered a private
local feed; restore used a cleared-source NuGet.Config with this feed alone.
All four project.assets.json files were checked against the audited allowlist;
their package union matches it exactly. Publish used --no-restore,
--self-contained false and at most four jobs. The original universal launcher
remains unchanged. No unaudited runtime pack was restored.

[NuGet dates, source URLs and package SHA256s](docs/oot-notes/nuget-audit.json)
and [full source/distribution SHA256s](docs/oot-notes/translator-fingerprints.json)
are committed. The latter covers source beyond the launcher's limited embedded
digest. The lock was updated from the rebuilt tools and checked. Default chain
and recommended visual-enabled chain are recorded in the final verification.

## Integration resolutions

- Keep raw_load_quads, cbuf_reuse, storage_runs and oot_visual chain options.
  Include all changed C# modules, constant-reuse, stage-cache and limit16 tools
  in FILES and the applicable builder/key paths. Blocked #1203 modules stay absent.
- Stage translation keys hash the merged translator distribution, translation
  source and DMSH_OOT_VISUAL value. Pure raw-quad and storage passes key their
  actual arguments; constant reuse is selected only when enabled. The cache
  implementation and chain source invalidate old intermediate-key semantics.
  A test covers every chain FILES entry through actual key fingerprint paths.
- Preserve #1394 address marking, dynamic count-driven tables and low-entry hints.
  A translated four-word load is run both scalar and optimized through the real
  host table. The optimized fixture composes raw quads, storage-run and constant
  reuse passes. GPU output comparisons include ranges above entry 4095.
- Preserve the stable branch's unconditional deferred-release partition despite
  the visual branch's optional version. Preserve both branches' CPU texture tests.
- Set Metal 4 spatial MetalFX output barrier stages to Fragment for presentation,
  All for the game-upscaler consumer. This SDK/runtime exposes a getter and ivar
  but no setter. The guarded KVC compatibility path sets the known ivar, and
  refuses unknown implementations. Crop and quality cases use API validation.
- Compose P3 primary conversion with sharpening/filter footprint and keep the
  colour fixture's crop-uniform layout synchronized with the shader ABI.
- Retain hidden-pause freeze reason 3 alongside fast-clock epoch/generation
  updates. GL import tests receive weak stubs for the clock symbols they link.
- Relocate branch-note links, preserve requested PR file lists, regenerate the
  symptom index and reconcile environment registry meanings.

## Shipping gates

Review 2 confirms a Float16/integer attachment defect, watchdog race and auxiliary
residency cleanup race. They remain for the designated fix branches. **Do not
ship default-on DM_SAFE_GPU watchdog until oot-stable-fix**, and do not accept the
visual set before oot-visual-fix. Passing tests below do not clear those findings.
Each pending *-fix replaces its parent implementation when it lands.

[FLAGS](docs/oot-notes/FLAGS.md), [PLAY-BUILD](docs/oot-notes/PLAY-BUILD.md) and
[NEXT-MERGES](docs/oot-notes/NEXT-MERGES.md) carry the exact choices and blockers.
Play requires full ahead-of-time shaders. Lazy shaders remain off; partial maps
and source-compiling diagnostics are excluded. Runtime driver compilation has
not been proven absent by this source integration.

## Verification

Before review-1 replacements: 397 graphics Python tests pass (2 skips); the full native graphics run and host build pass. Raw GPU checks pass 61 scalar plus 226 scalar/quad comparisons. Tools discovery reaches 1,274 tests with one architecture failure: the incoming stable code hard-coded a title ID. That default is now a profile key (`safe_gpu on`, generated DM_GAME_SAFE_GPU), preserving behavior while keeping host code general. Full verification repeats after the newly authorized fix merges.
Evidence root: `/Users/ankur/Documents/Crypt/Projects/_work/nxnative/oot-hyper/`.
The one verification owner is this implementation agent. The parent owns an
independent review and later full shader/game/display acceptance.

## Generated storage

Task-generated translator source snapshot, audited feed, private package cache
and publish roots are recorded under the evidence root. Test binaries, dSYM and
host generated roots are confined to this worktree. Evidence, source, Git state,
unknown paths and other agents' artifacts are preserved. Final cleanup/retention
is recorded after verification and open-file checks.

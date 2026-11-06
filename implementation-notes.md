# Ocarina integrated branch

The branch is `oot-hyper`, based on oot-stack `8284776d`. Branch snapshots are
preserved in [docs/oot-notes](docs/oot-notes/FLAGS.md). Local commits only; no push,
PR, game run, regress.py, full shader build or protected baseline/game writes.

## Merge order and review replacements

Separate merge commits bring in oot-stable, oot-visual, oot-cpu, oot-idle,
oot-upscale, oot-bench, oot-msl, oot-tbdr, oot-stagecache, oot-vqa, oot-quality
and oot-clock, in that order. The final history places stability immediately
after oot-stack and visual correctness immediately after stability.

The initial growing integration merged oot-mem and oot-1203, then reverted both
merge commits using `git revert -m 1` after the stop-change review. That history
is retained as `oot-hyper-before-early-safety`. The final ordered history omits
both blocked merges entirely; the original correcting border path remains.
The four review-1 fixes are now merged: stack-fix, idle-fix, mem-fix and 1203-fix;
memory and border replacements are last and default-off. No source branch was rewritten. The temporary ordered branch is retained locally.

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
  in FILES and the applicable builder/key paths. The fixed inline border_plain pass is cached, and border_split enters chain options.
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

## Review-1 integration follow-up

Merged replacement heads: stack 694ad30d, idle a9f24c03, memory 13d03613,
border 2ec3d25d. No C# source changed in these repairs, so the audited translator
rebuild remains valid. Border_split now participates in the chain and complete
cache key, and border_plain runs through the stage cache. Coverage tests include
its fingerprint. The new AST library fixture includes the real stage dispatcher.

The mem/stable merge keeps raw-pool mark filtering before restore/residency and
combines texture-only transient uploads with dedupe. Both memory diagnostic lines
and stable idle-alias counters are retained. The stable pressure-driven staging
trim is named guard_trim_uploads to distinguish it from the opt-in age-based
up_trim routine. Both policies retain their original call sites and defaults.
The audio fix orders pause before clock freeze, and resume after clock thaw.

The next required work is visual/stable review-2 fixes, then oot-brent 209835ae,
then a separate oot-hyper-main variant on upstream 865cc35f. The read-only main
merge preview currently reports 19 paths after all other feature integrations;
Brent's earlier 13-14-path forecast covered a narrower source set. Generated
header, lock and managed assemblies will be regenerated from combined source.
No incoming fork or upstream managed binary will be run as the final translator.

Upstream-main update: start the second variant from origin/main as resolved at
creation, currently reported a334797d (e9d71e27 64 GB alias region plus #1336 PCM
blocks fix). On that variant remove the DM_OOT_BRENT alias-layout copy and use
upstream's implementation. Retain other Brent gates and compose audio pause with
the upstream renderer repair. The earlier 865cc35f preview is historical only.

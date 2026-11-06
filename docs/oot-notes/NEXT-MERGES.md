# Next Ocarina merges

The finished stable, visual, MSL, TBDR, stage-cache, VQA, quality and clock
branches are integrated. No unfinished branch was awaited. The requested 18
upstream PR file lists were inspected; the historical forecast is preserved in
[PR-FILES.md](PR-FILES.md). The following replacement and feature branches remain pending. Each `*-fix`
branch replaces its parent implementation when it lands; do not treat the buggy
parent as an independently shippable alternative.

The independent review in
`/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/review-astra.md` blocks
the original memory and border branches. Both are absent from the final ordered
history. The recovery branch records their merge reverts. Merge fixed branches
only after inspecting their complete implementation and fix together.

| Pending branch | Required repair | Predicted conflicts with oot-hyper |
| --- | --- | --- |
| `oot-stack-fix` | Apply the independent stack review repairs from review-fixes.md | Growing-table/quad-load tests, translator/cache fingerprint conventions, host pool lifetime and inherited stack notes |
| `oot-visual-fix` | Prevent Float16 variants from changing integer attachment bits | `lim_key`, limited library selection, `dmsh_limit16.py`, mixed-output producers/tests and stage fingerprints |
| `oot-stable-fix` | Synchronize watchdog state and stop-aware auxiliary residency ownership | `nvn_safe_gpu.inc`, presentation/snapshot residency setup and cleanup; concurrent transition tests |
| `oot-mem-fix` | Complete restores before consumers; pin or bounce every kernel-read source through the syscall | `nvn_mtl.m` pool/residency and visual write ranges; dirty tracking, filesystem/socket paths, submission lifetime, env table and game note |
| `oot-1203-fix` | Handle both split-handle word orders, retain correcting default library, fail safely when assets are missing | `dmsh_build.py` border/limit16 library selection and cached stages, PSO bits, `dmsh_chain.py` FILES/options, header and new modules' stage coverage |
| `oot-idle-fix` | Freeze queued PCM consumption and release events with guest clocks | `front_mac.m` visibility, `hle_audio.c`, `hle_os.c` clock epoch/generation, quality/colour presentation; pause remains do not use |

The #1203 replacement will need particular care in `dmsh_build.py`,
`dmsh_chain.py`, the border PSO keys and stage-cache routing. Preserve visual
limit16 variants, raw_load_quads, storage_runs and cbuf_reuse. Add every new
`dmsh_*` module to FILES, CODE_FP and actual stage fingerprints; the coverage
test must remain green. The current unsplit correcting border path stays active.

Memory fixes must preserve #1394 address marks, dynamic table growth, completion
lifetimes, visual texture-write ranges and DM_SAFE_GPU refusal behavior. Idle
fixes must reconcile the fast-clock generation/epoch state with audio consumption,
visibility and presentation. `DM_ECO_HIDDEN=pause` remains **do not use:
audio/clock mismatch, fix pending**.

Archive replacement notes, resolve source first, rebuild the translator only if
its sources change, update the lock and regenerate the header. Repeat tools,
graphics and host verification. Full shader builds and gameplay remain a separate
parent acceptance step.

## Review 2 and upcoming work

Review 2 (`review-astra-2.md`) confirms two high-severity defects: Float16
clamping can corrupt integer attachments, and the watchdog can stop newly started
healthy work. It also confirms a medium-severity auxiliary residency cleanup race.
**Do not ship the default-on DM_SAFE_GPU watchdog until oot-stable-fix is merged.**
The visual set likewise needs oot-visual-fix before enabled play acceptance.
Source defaults are retained in this integration; green synthetic suites do not
clear these independently reproduced review findings.

`oot-stack-fix`, `oot-idle-fix`, `oot-1203-fix` and `oot-mem-fix` are reported ready;
`oot-visual-fix`, `oot-stable-fix` and `review-astra-2-fixes.md` are being produced.
The referenced `review-fixes.md` was not present at the supplied shared-context
path when checked. Read both repair reports before accepting replacements.

| Upcoming branch | Predicted integration work |
| --- | --- |
| `oot-brent` | Fork-harvest source may overlap translator, host graphics and caches. Read brent-compare.md, reject shipped binaries, preserve all chain options and repeat module-key coverage. |
| `oot-waste` | Shader-pass ordering, dependency keys and CODE_FP/FILES may overlap MSL passes and stage caching; preserve visual correctness gates and default-off experiments. |
| `oot-res` | Internal target sizing overlaps game profile, rewrite, viewport/scissor, NDSR, quality and presentation paths. Keep scale changes opt-in and separate from output scaling. |

The play-build rule is hard: **no runtime shader compilation**. Build all shader
libraries ahead of time; lazy shaders stay off. Do not use partial/seen-only
libraries or enable source-compiling diagnostics. Incoming branches must preserve
this rule and prove full offline coverage before play acceptance.

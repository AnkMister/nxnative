# Next Ocarina merges

The finished stable, visual, MSL, TBDR, stage-cache, VQA, quality and clock
branches are integrated. No unfinished branch was awaited. The requested 18
upstream PR file lists were inspected; the historical forecast is preserved in
[PR-FILES.md](PR-FILES.md). The following replacement and feature branches remain pending. Each `*-fix`
branch replaces its parent implementation when it lands; do not treat the buggy
parent as an independently shippable alternative.

The original memory and border merges were excluded after review 1. Their
fixed replacement branches now bring in the full repaired implementations.
The recovery branch retains the original merge reverts.

| Pending branch | Required repair | Predicted conflicts with oot-hyper |
| --- | --- | --- |
| `oot-visual-fix` | Prevent Float16 variants from changing integer attachment bits | `lim_key`, limited/plain border library choice, `dmsh_limit16.py`, mixed-output producers/tests and stage fingerprints |
| `oot-stable-fix` | Synchronize watchdog state and stop-aware auxiliary residency ownership | `nvn_safe_gpu.inc`, profile-driven safety default, presentation/snapshot residency setup and cleanup; concurrent transition tests |

Review-1 replacements are now merged at the requested heads: oot-stack-fix
694ad30d, oot-idle-fix a9f24c03, oot-mem-fix 13d03613 and oot-1203-fix 2ec3d25d.
Memory and border fixes landed after the other merges and remain default-off.
Their report is [review-fixes.md](review-fixes.md). Each replaces its parent's
implementation; the original branches remain historical evidence.

The integrated border replacement preserves the correcting `_b`/`_bx` path,
adds optional `_bn` assets and caches its pure border pass. Future shader changes
must preserve limit16 variants, all chain options and actual stage module keys.
Memory fixes compose restore-before-residency with #1394 marks and visual texture
write ranges. Idle fixes preserve fast-clock generation updates while stopping
queued PCM consumers. Real gameplay/window acceptance remains unverified.

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

`oot-visual-fix`, `oot-stable-fix` and `review-astra-2-fixes.md` are being produced.
Read the second repair report before accepting those replacements.

| Upcoming branch | Predicted integration work |
| --- | --- |
| `oot-brent` | Fork-harvest source may overlap translator, host graphics and caches. Read brent-compare.md, reject shipped binaries, preserve all chain options and repeat module-key coverage. |
| `oot-waste` | Shader-pass ordering, dependency keys and CODE_FP/FILES may overlap MSL passes and stage caching; preserve visual correctness gates and default-off experiments. |
| `oot-res` | Internal target sizing overlaps game profile, rewrite, viewport/scissor, NDSR, quality and presentation paths. Keep scale changes opt-in and separate from output scaling. |

The play-build rule is hard: **no runtime shader compilation**. Build all shader
libraries ahead of time; lazy shaders stay off. Do not use partial/seen-only
libraries or enable source-compiling diagnostics. Incoming branches must preserve
this rule and prove full offline coverage before play acceptance.

## Expanded integration requested

The user authorized oot-brent at 209835ae after the final visual/stable fix
branches. Follow its Integrator merge notes: combine nvn_mtl.m by hand, retaining
safety gates, raw exposure generations, storage classification, growing tables,
original-map write-log completion and optional completed-log cleanup. Preserve
both sets of tests. Its report is currently at the shared task root and will
be archived with its implementation notes before merging.

After oot-hyper passes, create oot-hyper-main on upstream 865cc35f and integrate
the same changes. Preserve main's packed library loading and guest-file setup.
Rebuild generated translator artifacts from the final source. The play recipe
must name the variant that passes checks; no runtime shader compiles or lazy
shaders are allowed on either variant.

Upstream-main update: start the second variant from origin/main as resolved at
creation, currently reported a334797d (e9d71e27 64 GB alias region plus #1336 PCM
blocks fix). On that variant remove the DM_OOT_BRENT alias-layout copy and use
upstream's implementation. Retain other Brent gates and compose audio pause with
the upstream renderer repair. The earlier 865cc35f preview is historical only.

# Integrated Ocarina community build

The final branch starts from official main through d928699b. It takes the
maintainer's Ocarina fixes, profile tables and overlapping shader behavior.
Only missing serial ownership, texture/view repairs, upload caches, guarded
mesh behavior, optional pool/retirement work, GPU safety and HDR are retained.
The earlier four-lane integration remains on oot-play-1444-pre-main.

A locally source-built translator includes optional HMMA reuse, disabled by
default. Restore used only the audited local feed of 57 cooled NuGet versions.
The universal launcher is built from launcher.c, and SPIRV-Cross is locally
built from the pinned source. No PR-shipped translator DLL was executed.

Both review-5 P1 cases have GPU regressions and an independent Astra source
re-check. Full integration exposed stale loader/presentation fixtures, a
coarse fallback-clock assertion and a public-fence requirement in MetalFX
validation. The exact fixes and evidence are in the reference/game notes and
the external integration report.

The after-exit pipeline union has 12,176 TSV rows plus four JSON states. The
external build recipe adds one observed readable-tile request through a derived
profile, preserving every upstream source table. It enables strict offline AOT
while runtime AOT remains off. The reference environment enables worker and
mesh prediction modes and keeps lossy BC targets off for the first comparison.
No game, install, push or PR is part of this integration. Generated roots and
evidence are retained for the full app build.

## Earlier lane notes

# PR #1456 shader port

Started p1456 from origin/main 75c1a8cf, including official Ocarina support.
Ported 48ec785d's HMMA chain/A reuse source and tests. Added an independent
DMSH_HMMA_CHAIN=1 gate, preserving the default ordinary helper ABI/body and
main's gather-offset fix. The user chose documentation of the #1334 tensor
merge contract instead of importing that fork feature. The _bf regression
covers both HMMA option names without restricting ordinary Mac compilation.

A GPU probe exposed upstream slot-zero corruption when a standalone HMMA
interrupts a live chain (8,089 outputs beyond tolerance). Reserved slot 7 for
temporaries, leaving seven chain slots and register fallback on exhaustion.
Both translator and GPU regressions now pass. The slot-capacity test also passes.
Numerical errors stay within upstream's f16 thresholds.

Built a private test translator from source using a live age audit of all 57
exact NuGet versions and an existing-only local feed. Nothing was published or
copied into the shipped bundle. Two translator suite runs each passed 149 tests
with one unrelated native geometry harness skip; the added capacity test passed
separately. Mac-only loop selectors avoid iOS work. No game/full shader/host
build ran. Evidence, scope limits and retained generated roots are documented
in docs/oot-notes/p1456.md. Final lock/header and translator publication belong
to the lead's integrated rebuild.

# PR 1459 and PR 1461 port

Base: origin/main at 0cefa8687bb94ce5dd38a6cbed610e7ec98a1ab0. Initially
fetched 75c1a8cf, then rebased when upstream advanced with its readable-tile
function-cache optimization. Branch: p1459. Ported PR 1459 at ddeae47d9755ac58d9ef3a8434227de179fcb87b
and PR 1461 at da9d801d554dbd21051035fd15bfbb9f81dd94bc. Skipped PR 1460.

The existing DM_UPSCALER=metalfx opt-in now recognizes agl_ndsr_vr.pck and
agl_ndsr_vr_light.pck. No curve constants and no EX2/LG2 power selects the
existing no-conversion colour path. A power with no recognized constants keeps
the game's shader. The default remains DM_UPSCALER=game. The Ocarina profile
header contains 59 distinct eligible keys on this source snapshot.

DM_SCREEN selects the first case-insensitive display-name substring match.
Unset, empty, unmatched and invalid UTF-8 values preserve default placement.
The pure name matcher has nine native checks. Selection happens before layer
setup so local HDR capability and backing-scale reads use the chosen screen.
The ordinary center call stays in its original place when no screen matched.

DM_QUALITY and HDR presentation are local features outside this branch's plain
upstream base. Source comparison against oot-play e8c3bc22 preserves quality(),
fx_encode() and present_encode_m4() byte for byte in a three-way source probe.
The local HDR output-format choice still uses normalized tex.pixelFormat.
Internal NDSR replacement and final presentation scaling remain independent;
enabling both requests two scaling stages. The renderer source probe merges without conflicts. The front end needs both
the local nvn_eco.h include and the new front_screen.h include. The source probe
is not an integrated build proof.

Native upscaler checks pass for Ocarina, Bananza and Splatoon Raiders. Each
profile passes 94 checks with immediate encoding, 94 with the encoding thread,
and 15 with the game's upscaler. Python profile/settings/environment tests pass
(12), docs tests pass (11), the screen matcher passes nine checks, and the final
Ocarina host build passes. Environment inventory and symptom checks pass; the
inventory retains two pre-existing unused-documentation warnings.

Builds ran at full speed as requested, with at most four jobs. No game, full
shader chain, third-party executable, install, push or PR ran. No physical
multi-monitor/fullscreen, HDR monitor or gameplay image acceptance is claimed.
A/B visual acceptance and the final integrated local feature stack remain the
lead's gates. Reports and logs are outside Git. Existing checkout outputs were
reused, and newly generated test outputs are retained while the checkout has
active runtime working directories. No deletion sweep ran.

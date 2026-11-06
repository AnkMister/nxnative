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

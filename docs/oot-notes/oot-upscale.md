# Ocarina upscaler implementation notes

## Scope and result

Worktree `.`, branch `oot-upscale`, base `ee9b7765` (`oot-base`). The initial worktree was clean. Read the shared `agent-context.md` before investigation. Work was performed directly as the implementation sub-agent. No nested delegation, installation, game run, regression run, full shader build, iOS work, push or PR was performed. The per-game user `env.txt` was not written. Changes are uncommitted for the parent to review; the repository requires an explicit commit request.

The task assumed Ocarina had no upscaler wiring. Source and the generated header show that `game.py` already derives its 22 standard NDSR compute keys, exactly as for Bananza and Splatoon Raiders. Adding a new profile key or a second list would duplicate that mechanism. The profile change therefore documents the existing opt-in. Tests exercise the real profile header and launcher, and protect the exclusion of VR and NDVE. Runtime defaults and the shader chain are unchanged.

The task's render-scale examples also need a qualification. Ocarina has no render-scale rewrite. `DM_RENDER_SCALE=0.75`, `0.67` or `0.5` has no effect. `DM_DYNAMIC_RESOLUTION` is a NieR-specific control and has no effect here either. The game has its own resolution palettes. A new arbitrary render-scale rewrite would require a separate investigation and rewritten-main build; it was not added without that proof.

## Changes

- `dm/games/0400486024DEC000/game.tsv` documents the automatically selected 22 keys and the opt-in.
- `dm/tools/tests/test_game_profile.py` checks the exact real Ocarina header and excludes similarly named VR and NDVE sources.
- `dm/tools/tests/test_settings.py` covers Ocarina and Splatoon in the existing upscaler setting test, and checks that unsupported resolution controls stay hidden for Ocarina.
- `dm/games/0400486024DEC000/README.md`, section `Upscaler and render scale`, contains the shader-key table, binding evidence, handheld/docked paths, A/B assignments and work estimates. Game-specific findings live there once.

## Evidence

The shared extraction was inspected read-only at `${OOT_READONLY_GAME_ROOT}/0400486024DEC000_build`. Its `extract/v131072/ExeFS/main` has build ID `e0f3ccfaf50065ae4ea01eb5aeb13b1a`, matching the committed profile's `v0` main. No fixed addresses were added to the host or rewriter.

Analysis outputs are in `${OOT_SHARED_CONTEXT}/oot-upscale/`. `audit_shaders.py` reads the package records in memory, verifies all audited shader hashes, reports control sizes and bindings, and reproduces the host's colour classification. `shader-audit.tsv` contains 78 compute variants across standard NDSR, VR and NDVE. All 22 standard compute resource reports confirm one sampled texture handle 8 (NVN slot 0), one image handle 74 (NVN slot 1), push bank 24 and storage reads only. Eleven have the half-float sRGB decode accepted by the existing host. The remaining eleven stay on the guest shader.

The first analysis assumed every cached shader had a final reflection JSON; seven standard variants did not. The follow-up used their existing translator resource reports and MSL in `tmp/dmsh_92gnntz5`. No translation or compilation of game shaders was started. Another overly strict audit assertion expected bank 24 to be the only constant buffer. Some variants also read bank 0. The corrected check requires bank 24 and verifies the actual texture/image contract; the host does not prohibit other constant-buffer reads.

`audit_resolution.py` reads the RomFS image without extraction, decompresses Bootup in memory using the shipped dictionary, and parses the relevant BYML parameters. `resolution-audit.txt` retains the mode dimensions and dynamic palettes. `opmode-disassembly.txt` retains the original-main instruction ranges used to trace the host's mode values into the renderer. The REA tool rejected NSO input as `unsupported binary format`, so this evidence comes from the repository NSO reader and the already installed Capstone, not a REA decompilation. No ELF or extracted game binary was written elsewhere.

Handheld selects resolution enum 1 at `main+0xe83310`; `main+0x31a9c50` maps it to hash `0b46e9da`. The shipped parameter gives 1920×1080 base/final size and a top scene scale of 0.75. Docked enums 0 and 2 both have 2560×1440 base/final size and top scale 0.75. Thus the configured top scene is 1440×810 handheld versus 1920×1080 docked. Those are static configuration-derived dimensions, subject to integer rounding and the active dynamic level. Runtime attachment sizes were not observed.

At equal palette scale, handheld has 56.25% of docked's scene and final-image pixels. The resulting 43.75% reduction applies to pixel-proportional work, not to the whole frame. Both palettes approach the same scene-size floor. The tables do not record scene dispatch grids or the active variant, so there is no measured absolute per-frame thread count or GPU saving. The game note gives exact group-size formulas and a clearly labelled normalized instruction estimate. MetalFX internals are not available for an instruction-count comparison.

## Validation

All commands used `TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch` and the shared uv venv's Python. Builds used at most four jobs.

```sh
make -j4 -C dm/host GAME=0400486024DEC000 dmhost
make -j4 -C dm/gfx/tests GAME=0400486024DEC000 check_t_upscaler_mfx
make -j4 -C dm/host/tests GAME=0400486024DEC000 build/t_oe
DM_OPMODE=0 dm/host/tests/build/t_oe
python -m unittest discover -s dm/tools/tests -p test_game_profile.py
python -m unittest discover -s dm/tools/tests -p test_settings.py
python -m unittest discover -s dm/tools/tests -p test_docs.py
```

The host build passed. It reported 57 compiler warnings. The MetalFX tests ran on the Apple M4 Max and passed 91 checks with the encoding thread off, 91 with it on, and 12 stock-path checks with Metal validation. The operating-environment test passed 53 checks. Python tests passed 9 profile, 4 settings and 11 documentation tests. Build/test logs are in the analysis output directory. `git diff --check` passed.

No runtime A/B, screenshot, energy measurement or gameplay regression was performed, as required by the handoff. The MetalFX checks exercise synthetic images and do not prove Ocarina's active shader, image quality or frame cost. Independent review belongs to the parent.

## Parent handoff

The first efficiency candidate is handheld with the existing MetalFX spatial swap. Propose these exact contents for `~/Library/Application Support/nxnative/0400486024DEC000/env.txt`, without writing it during this task:

```ini
DM_OPMODE=0
DM_UPSCALER=metalfx
```

Ocarina's default profile has no host FPS target or frame-step rewrite. The Splatoon recipe's `DM_FPS_HOLD=off` is unnecessary here. No new FPS target should be assumed from that recipe.

Use the game note's matrix for docked stock, docked swap, nominal scale 0.75/0.5, handheld stock and handheld swap. The scale rows are negative controls in this build. Check the first-dispatch replacement log, actual input/output rectangles, GPU pass costs and moving-image quality at the same save and camera. The handheld-plus-swap recommendation remains a candidate until those checks pass.

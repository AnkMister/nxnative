# Ocarina quality mode implementation

## Result and scope

Branch `oot-quality` starts at `oot-base` / `ee9b7765` in `/Users/ankur/.t3/worktrees/nxnative-oot/t3-ff09367e`. The checkout was clean before switching from `t3/ocarina-quality-mode`. Read the shared `agent-context.md` first. The user explicitly requested a local commit. No push, PR, dependency install, game run, regression-harness run, iOS work or full game-shader build was performed. The baseline worktree, game build, saves and user `env.txt` were not changed.

The implemented subset is `DM_QUALITY=max`, with independent anisotropy, trilinear, supersampled spatial presentation and sharpening controls. With no settings, or `DM_QUALITY=off` and no individual overrides, the existing rendering choices remain. Scene supersampling, NDSR temporal reconstruction and interpolation are deferred with their missing contracts documented. This does **not** establish better visuals than Switch 2. Gameplay and console-reference comparisons remain with the parent.

The [game note](dm/games/0400486024DEC000/README.md#quality-mode-current-opt-in-gameplay-acceptance-open) contains the per-feature table, labelled GPU cost estimates, resolution/NDSR investigation and exact Kokiri Forest screenshot recipe. The [reference entry](docs/reference/rendering.md#opt-in-filtering-and-supersampled-presentation) explains the general mechanism. Findings live in those locations once.

## Changes

- `nvn_mtl.m` reads a small typed `quality_config` through `dispatch_once`. It does not mutate the process environment. Explicit settings override the preset. Numeric inputs reject non-finite values and trailing garbage. Settings take effect at process start, which avoids changing sampler caches while commands are in flight.
- The sampler port applies at `samp_by_id`, before caching both the sampler and its resource ID. `samp_fast`, ordinary bindings and `pool_gpu` all consume that object. It preserves comparison/reduction samplers and requires linear minification **and** magnification with an existing mip filter, which is stricter than PR #335's original policy. More anisotropy requested by the game is preserved. Border twins inherit the same descriptor.
- The presentation port reconstructs to an optional multiple of the native viewport, within Metal's dimension limit, then samples a grid across each output pixel's source footprint. Fractional reductions use the ceiling tap count. Classic and Metal 4 paths initialize the widened constants, including offscreen screenshots. The drawable itself is not resized.
- Sharpening uses the same footprint filter as the ordinary present. PR #345's original `sharp` replaced its box filter and lost its supersampling benefit. The new test pattern fails under that bypass. Clamping stays within the local filtered colour range, and alpha is preserved. The extra pipeline is created only when sharpening is requested. No additional render pass is added.

The existing `DM_UPSCALER=metalfx` swap remains separate from the preset. A second spatial reconstruction after NDSR has a subjective tradeoff, which the independent flags and A/B recipe expose. The max preset uses 1.5 presentation output and sharpening 0.2 as an initial quality candidate. It does not assert that the highest permitted reconstruction multiplier gives the best picture.

## Upstream investigation

Read the bodies and source heads of [PR #354](https://github.com/seedds/nxnative/pull/354), [#491](https://github.com/seedds/nxnative/pull/491), [#405](https://github.com/seedds/nxnative/pull/405), [#345](https://github.com/seedds/nxnative/pull/345), [#335](https://github.com/seedds/nxnative/pull/335) and [#301](https://github.com/seedds/nxnative/pull/301). Fetched them only as `origin/pr-<number>` refs. No PR-shipped binaries were executed.

| PR | Inspected head | Decision |
|---|---|---|
| 354 | `d1bd6796ee728f2a44aa5fe1d603dfa9d44263d3` | A higher loader ceiling does not create the absent Ocarina rewrite. Pool capacity must be proven first. |
| 491 | `b584e777ea69708b372388cdb1b9562de2b2981c` | Its texture binding scale correction does not cover dynamic bindless pools. Compute image writes keep their original coordinate grid. Do not port it as a working Ocarina control. |
| 405 | `10e6c3182cbe4391eb215de825f1f9bcc433a0a3` | More complete target scaling, but written images demote and its generic upscaler resolve identifies FSR constants. Ocarina needs an NDSR-specific resolve and captured-pass validation. |
| 345 | `022bf5b8c6b99a1fc8d06d1ba06bf8e262ddc42c` | Ported the sound presentation ideas with shared filtering, fractional footprint coverage, classic-present support and native-input reconstruction. |
| 335 | `b1ea32e7c3e43f53d175990932702f62967e6a1a` | Ported sampler floors and mip blending, with stricter protected-sampler checks and real pool/mip tests. |
| 301 | `81980b92` | No camera block, scene/UI split or cut/reset contract is established for Ocarina. Do not port static-world camera motion as if it were this game's object motion. |

Read `git show oot-upscale:implementation-notes.md`, then re-ran its read-only `audit_shaders.py` and `audit_resolution.py` against this checkout and the shared build. This verified current package hashes, standard NDSR reflection and RomFS parameters without rewriting or extracting game files. The scripts were supplied by the preceding implementation work. Audit outputs are in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-quality/`. The game note records the conclusions and limits. No hardcoded game addresses or profile shader inputs were added.

## Validation

Commands used `TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch`. Python tests used `/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python`, the existing uv venv. Builds used at most four jobs. No packages were installed.

| Command | Result |
|---|---|
| `make -j4 -C dm/host GAME=0400486024DEC000 dmhost` | Passed. The build reported 57 warnings in existing code. Final up-to-date rebuild passed. |
| `make -j4 -C dm/gfx/tests GAME=0400486024DEC000 check_t_quality` | Passed on Apple M4 Max. Six independent environments, 239 checks each, 1,434 total. |
| `make -j4 -C dm/gfx/tests GAME=0400486024DEC000 check_t_present_crop` | Passed, 88 checks. |
| `make -j4 -C dm/gfx/tests GAME=0400486024DEC000 check_t_upscaler_mfx` | Passed, 91 checks with encoding thread off, 91 with it on, 12 with the stock path. |
| `python -m unittest discover -s dm/tools/tests -p test_docs.py` | Passed, 11 tests. |
| `python -m unittest discover -s dm/tools/tests -p test_env_switches.py` | Passed, 1 test. |
| `git diff --check` | Passed. |

The quality cases cover unset/off defaults, max, explicit overrides back to stock, independent feature settings and malformed values. GPU checks exercise actual sampler creation, pool registration and base offsets, cache reuse and re-registration, and a mip-colour sample through the production sampler. Image checks exercise classic and Metal 4 presentation, raw sRGB scan-out, crop edges, letterboxing, clamped sharpening, and an analytic stripe pattern that requires footprint averaging even with sharpening enabled. Native-input MetalFX reconstruction is checked by its actual return path.

Metal API validation was enabled for the stock, forced-stock and malformed-input cases. The MetalFX cases run without it because this existing Metal 4 scaler hits its own internal barrier-stage assertion under validation. `t_quality` compiled with 57 warnings from the included backend and none in the new test itself. The first test iteration exposed three test-only compiler warnings, which were corrected before the final run. Host-only Metal shaders were compiled by the normal host build. The game's shader chain and `DMSH_CHAIN` are unchanged.

Logs are in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-quality/`: `host-build.log`, `host-build-final.log`, `quality-tests.log`, `presentation-regression-tests.log`, `docs-tests.log` and `env-tests.log`. The tests establish synthetic GPU behaviour, not actual Ocarina sampler usage, gameplay image quality or frame cost.

## Parent review and remaining gates

The user assigned implementation-sub-agent work, so no nested agents or independent reviewer were started. The parent owns independent review. The pstack and ponytail skills guided the investigation and bounded implementation. The plain-writing skill was read before these notes and the commit message.

The throughput checkpoint kept the work under one owner. Reading the shared context, branch/worktree status and actual rendering paths were the blocking steps. Investigation lanes were read-only; all implementation paths share `nvn_mtl.m`, so edits were serialized. Further decomposition would duplicate that shared state.

The feature playbook's runtime proof, broad gameplay regression, independent review and PR-opening steps are omitted because this task prohibits gameplay/full shader builds, assigns this agent implementation only and prohibits push/PR actions. No omission is treated as acceptance. For the parent, prioritize Ocarina with unset/off/max, then Bananza and Splatoon Raiders for the existing NDSR swap, Breath of the Wild for classic attachment/sampler use, and Tears of the Kingdom for many depth and screen-space passes. This is the five-game impact shortlist, **not** a regression report. Run only in a separately authorized gameplay pass.

Before calling the preset visually accepted, run the note's isolated Kokiri comparisons on the current complete shader set and compare total GPU cost against the 33.3 ms budget. Existing foliage and fog defects must be tracked separately. Before adding scene supersampling, identify the engine allocation and dynamic-resolution contracts, the complete depth/image/history graph and a colour-correct NDSR downsample resolve. Before temporal/interpolation work, establish motion vectors, jitter, reset/camera cuts, and the UI boundary on the exact main build.

# The Legend of Zelda: Ocarina of Time

The Switch 2 base dump reaches its title screen on the Mac. VideoToolbox decodes the 1920×1080 AV1 track. The movie library runs its NDVE compute shaders to produce the background behind the logo and menu. Gameplay validation is open.

## Profile

SDK 22.2.8, NVN API 231.40, with Nintendo's sead, agl and gsys. The three loaded modules are `main`, `subsdk0` (NintendoSDK_movie), and `sdk`. The NPDM declares 48 MiB of system resources. Startup requests a 6.20 GiB heap, which fits in the profile's 12 GiB reservation with the stack and alias regions. The registered build is the supplied base dump (`v0`).

## Mac dry run

Use the rewritten `patched_v0` and the original extracted `base/romfs`. Build the host with `make -C dm/host GAME=0400486024DEC000` and use the [Mac shader build](../../../docs/development.md#build-by-hand-mac). From the repository, set `DUMP` to the folder containing `base` and `WORK` to the build and run workspace beside it.

```sh
mkdir -p "$WORK/run/save" "$WORK/run/temp" "$WORK/font"
python3 dm/tools/make_ext_font.py "$WORK/font/nintendo_ext.ttf"
DM_ROOT="$WORK" DM_ROMFS="$DUMP/base/romfs" DM_SAVE="$WORK/run/save" \
  DM_TEMP="$WORK/run/temp" DM_MSL_DIR="$WORK/shader/cache" DM_FONT_DIR="$WORK/font" \
  DM_NVN_SHMAP="$PWD/dm/games/0400486024DEC000/shader_map.tsv" \
  DM_WINDOW=1 DM_METAL_HUD=1 DM_FOCUS_KEEP=1 DM_AUDIO=1 \
  dm/host/dmhost "$WORK/patched_v0"
```

`DM_FOCUS_KEEP=1` lets the title keep playing while another app has focus. The profile prewarms the 11 NDVE compute pipelines used by the title. On the Apple M5 that took 17.7 s on a cold run, with a progress screen, and 7 ms with the archive warm. Compiling the same pipelines during the first submission had blocked the first movie frame for tens of seconds. The larger scene shader set also triggers a separate graphics-pipeline prebuild. On the first run with that set, the startup screen took 86.9 s to hand out all pairs, and the remaining workers finished after 110.6 s total.

Start a new game to reproduce the opening scene transition. With the test save and title flow, `DM_KEYS=f2600:A,f2950:A` advances the menu automatically. `DM_NVN_SHDUMP` saves control sections and code for missing keys to the directory it names.

For a run past the opening, copy the committed save folder to the new run's `DM_SAVE` and load slot 00 from the menu. The checkpoint contains both `slot_00/progress.sav` and `slot_00/caption.sav`. The load screen identifies it as **Kokiri Forest Autosave**. A windowed reload reached the playable scene with the HUD and controls, so rendering can be tested without replaying the movie.

## Upscaler and render scale

The profile already supports `DM_UPSCALER=metalfx`. As with Bananza and Splatoon Raiders, `game.py`'s `upscaler_keys()` reads the shader map and emits `DM_GAME_UPSCALER_KEYS` and `DM_GAME_UPSCALER_N=22`. There is no `upscaler_keys` row to add to `game.tsv`. The default remains `DM_UPSCALER=game`. The launcher already offers the choice.

### Shader contract

The map has 66 rows with `#NDSR` in their source. Of those, 64 are from agl's packs and two are from the separate NDVE movie pack. Only the 22 compute shaders in the exact `agl_ndsr.pck` pack qualify. The other agl rows are three vertex shaders, five pixel shaders, 18 compute shaders in `agl_ndsr_vr.pck`, and 16 in `agl_ndsr_vr_light.pck`.

Static inspection of the extracted packages and existing translation results confirms that all 22 standard compute variants read one 2D texture at slot 0 and write one 2D image at slot 1. They also read network data from storage slot 2. Their push constants are 72 bytes in bank 24. The first 32 bytes describe the input and output rectangles, as required by `up_mfx_encode`. `shader_facts.tsv` gives `[128,1,1]` threads and 4,608 to 12,672 bytes of guest shared memory. The map and facts do not contain resource bindings; those came from the translated reflection and the translator's intermediate resource reports.

The standard variants form 11 pairs. One member has no output decode that the host accepts; the other decodes sRGB to linear with half-float constants. The host's existing colour test accepts the latter for MetalFX perceptual spatial scaling, followed by a decode to linear. It keeps the former on the game shader. Static instruction counts below are code bytes divided by the Ampere instruction width of 16, including padding and instructions on conditional paths.

| Game shader kept | Static slots | MetalFX colour eligible | Static slots |
|---|---:|---|---:|
| `abef20ad0d9a9b12` | 1600 | `725bcf5c3f4bb3f3` | 2392 |
| `e9213c7fba8ccf93` | 1256 | `87bdc29ac7ce9adb` | 2008 |
| `aa1243f635baa8e8` | 656 | `54c6b94ddf539d9f` | 1592 |
| `1de2a54f4b81e4e0` | 1616 | `18f53257e4a46245` | 1984 |
| `3fe6b091bb8c40ce` | 2120 | `e16733ed9a14fc7a` | 2880 |
| `fdeb898427db8562` | 1616 | `a326e7353ec81e2c` | 2064 |
| `4acef5afefba098b` | 1008 | `c78798281d3519c1` | 1304 |
| `37121447f861a7d3` | 1616 | `add52a00627e7e84` | 2040 |
| `fb5038f1befcd03b` | 2200 | `fbe679b956a85e1f` | 2848 |
| `196dfe02185a7518` | 944 | `0253bd17deceee79` | 2016 |
| `028bd0b187f7342c` | 2024 | `f54f031dbc6f65f5` | 2664 |

Eligibility also requires Metal 4 MetalFX support, a direct dispatch, supported textures and rectangles, and a larger output. Otherwise the host keeps the game shader. Look for `upscaler: first dispatch of <key> drawn by MetalFX` to confirm an actual replacement. Naming a key in the header alone does not prove a replacement ran.

The VR packs stay excluded even when individual variants have one texture and one image. Their constants are 116 bytes, and some use multiple textures or different output slots. For example, VR-light `a335c1db6270c355` reads textures 5 and 3 and writes image 2. The eight graphics shaders cannot enter the compute swap. The source table does not identify a standalone sharpen pass among the 22 standard compute variants; their translated code contains matrix-network work. Keep the separate graphics and VR stages unchanged rather than assigning them an unverified role.

All 22 NDVE programs stay excluded, including the two with `#NDVE#NDSR` labels. `c2fc2ddd604c25e7` reads textures 2 and 1 and writes image 0 with 12 push bytes. `4f41ccf24f163e0d`, which the movie prewarm manifest names, reads textures 0 and 3 and writes image 1 with 84 push bytes. Neither meets the scene swap contract. `pso_manifest.tsv` records 11 movie compute pipelines, not scene-upscaler dispatches; `pso_pairs.tsv` and `shader_pairs.tsv` contain graphics pairs, not compute grid dimensions.

### Handheld and docked paths

Static evidence is for main build `e0f3ccfaf50065ae4ea01eb5aeb13b1a`, also present in the local extraction labelled `v131072`. No new gameplay run was made for these settings.

`hle_oe.c`'s `dm_opmode()` reads `DM_OPMODE` once. The default is 1. The host answers `GetOperationMode`, `GetPerformanceMode` and `GetCurrentGraphicsScale` with handheld/normal/0 for mode 0, and console/boost/1 for mode 1. Ocarina has no `perf_mode boost` override. The host does not lower the Mac's clocks in handheld mode. Its default display-size query returns 1280×720 or 1920×1080, but Ocarina's main does not import that query and defines its own rendering sizes.

The game caches those mode queries at `main+0xe376c0`, `+0xe376c8` and `+0xe376d8` in an object at global `main+0x4e97dd8`, fields `+0x20`, `+0x24` and `+0x2c`. The renderer at `main+0xe832fc` reads operation mode and forces resolution entry 1 for handheld. Docked uses entry 0 or 2 according to another graphics flag. The enum-to-parameter hash table at `main+0x3f08210`, read by `main+0x31a9c50`, maps entries 0/1/2 to `eeb1db9f`/`0b46e9da`/`d30fdb96`. The selection path at `main+0xe82f30` reads the resolution parameters and selects the dynamic palette; `main+0xe83240` also distinguishes handheld from the two docked entries.

The shipped `Pack/Bootup.Nin_Ounce_NVN2.pack.zs` contains `System/GameGraphics/ModelSceneExtensionParam/Default.game__gfx__ModelSceneExtensionParam.bgyml`. Its `ResolutionParam` entries and `DynamicResolutionParam.LevelPaletteDict` define:

| Setting | Base and final image | Palette scale range | Scene at highest palette level | Scene near lowest level |
|---|---|---|---|---|
| `DM_OPMODE=1` | 2560×1440 | 0.75 to 0.33334, 10 levels | 1920×1080 | about 853×480 |
| `DM_OPMODE=0` | 1920×1080 | 0.75 to 0.4445, 8 levels | 1440×810 | about 853×480 |

The scene dimensions are inferred from base size times palette scale, before the renderer's integer rounding. The active level and actual attachment extents remain unmeasured. Handheld selects palette hash `90e0a495` with load threshold 108 and reduce counter 3; docked selects `2ebeca77` with threshold 95 and reduce counter 2. Both have increase counter 30. Comparing different modes can therefore compare different dynamic levels too.

### A/B settings

Use the same save, camera, window size and other environment for every row. Restart for each row because the host caches the switches. These are complete assignments for the four relevant variables; retain other required launch paths from [Mac dry run](#mac-dry-run).

| Variant | Exact environment | Expected image change |
|---|---|---|
| Docked stock | `DM_OPMODE=1 DM_UPSCALER=game DM_RENDER_SCALE=1 DM_DYNAMIC_RESOLUTION=0` | The game's docked network and resolution palette. |
| Docked swap | `DM_OPMODE=1 DM_UPSCALER=metalfx DM_RENDER_SCALE=1 DM_DYNAMIC_RESOLUTION=0` | Eligible scene dispatches use MetalFX spatial. Final image size stays the game's size. Fine detail, edges and shimmer may change. |
| Docked swap plus 0.75 | `DM_OPMODE=1 DM_UPSCALER=metalfx DM_RENDER_SCALE=0.75 DM_DYNAMIC_RESOLUTION=0` | Same as docked swap in this build. The render-scale switch has no consumer. |
| Docked swap plus 0.5 | `DM_OPMODE=1 DM_UPSCALER=metalfx DM_RENDER_SCALE=0.5 DM_DYNAMIC_RESOLUTION=0` | Same as docked swap in this build. |
| Handheld stock | `DM_OPMODE=0 DM_UPSCALER=game DM_RENDER_SCALE=1 DM_DYNAMIC_RESOLUTION=0` | The game's handheld scene and 1920×1080 final image. Expect less fine detail than docked at matching palette levels. |
| Handheld swap | `DM_OPMODE=0 DM_UPSCALER=metalfx DM_RENDER_SCALE=1 DM_DYNAMIC_RESOLUTION=0` | Handheld sizes with MetalFX spatial on eligible dispatches. This is the first efficiency candidate to test. |

`DM_RENDER_SCALE=0.67`, `0.75` and `0.5` do not resize Ocarina's targets. The loader only writes that factor into a frame-step state page, and Ocarina has neither a `FRAME_STEP`/render-scale patch nor `FPS_STATE_OFF`/`RENDER_SCALE` fixup metadata. `DM_DYNAMIC_RESOLUTION` is a build-gated NieR control in `hle_fpslock.c`; neither 0 nor 1 disables or enables Ocarina's own dynamic-resolution controller. Both settings are hidden in its launcher. A working manual render scale would need a separately verified game rewrite and a new build of the rewritten main.

`DM_UPSCALER=metalfx` selects the spatial scaler only. The host's temporal scaler serves the separate NVN2 DLSS path and cannot replace NDSR through this setting. `DM_FPS_HOLD=off` controls late-frame holds when host frame stepping is active. Ocarina's profile has `fps_target=0` and no frame-step state page, so the Splatoon recipe's hold switch does not establish a cap or an efficiency gain here. Keep the game's own pacing for these comparisons.

For the parent to propose in `~/Library/Application Support/nxnative/0400486024DEC000/env.txt`, use the following contents. That file was not written. This is an unmeasured candidate, subject to the first-dispatch log and picture-quality check.

```ini
DM_OPMODE=0
DM_UPSCALER=metalfx
```

The packaged Mac launcher reads that file before bundled settings and saved choices. A variable already set in the launch environment wins. Running `dm/host/dmhost` directly does not read the launcher's per-game file; pass the variables in its process environment.

### GPU work estimate and remaining measurements

At the same palette scale, handheld has `(1920/2560)^2 = 0.5625` of docked's scene and final-image pixels, a 43.75% reduction in pixel-proportional work. At scale 0.75 the scene drops from 2,073,600 to 1,166,400 pixels, and the final image from 3,686,400 to 2,073,600 pixels. Geometry, fixed-size passes, CPU work and presentation to the same Mac drawable need not fall by that amount. The modes' lowest palette levels have almost the same scene size, so the 43.75% scene saving does not apply when both are at their floors. Handheld's final-image work is still smaller.

For a standard NDSR dispatch of `Gx×Gy×Gz` groups, launched threads are exactly `128×Gx×Gy×Gz`. For one colour-eligible dispatch per frame, the static straight-line budget is 1,304 to 2,880 instruction slots per thread, or `166,912×G` to `368,640×G` lane instruction slots with `G=Gx×Gy×Gz`. For example, an assumed 1,000-group frame would launch 128,000 threads and have a 166.9 to 368.6 million slot budget. This is a normalized estimate, not an observed Ocarina grid or a count of executed instructions. Predicates, branches and the Metal lowering of matrix instructions change the work. Do not add all 22 variants together as if they run each frame.

The committed tables contain thread-group sizes but no per-frame dispatch dimensions, active shader key or push-constant rectangles. An absolute thread count per frame or an M4 Max GPU saving cannot be recovered from them. MetalFX's internal kernel instruction and thread counts are also unavailable. The replacement removes the eligible guest network dispatch and adds a spatial scaler plus input/output conversion draws where required. The [existing Bananza measurement](../../../docs/reference/rendering.md#a-games-own-upscaler-drawn-by-metalfx) is on an M1 and must not be treated as an Ocarina M4 Max result.

The first runtime check should compare handheld stock, handheld swap and docked stock at the same scene and the game's own cap. Record the actual swap log, dynamic sizes, `DM_NVN_GPUPROF` pass costs and image quality. `DM_NVN_GPU_TS=segment` is an independent optional experiment if the game's dynamic controller is receiving misleading whole-submission timestamps. Keep its value equal across each comparison. No shader-chain change or shader rebuild is required for the existing swap.

## Found on this game

- Open experiment: [visual source ports](../../../docs/reference/shaders.md#ocarina-visual-source-ports-experimental) are default-off on `oot-visual`. Ten extracted v131072 targets now translate and compile on the M4 Max, including the foliage, output-payload task, float-reduction, SMAA and deep-expression compute targets. Numeric GPU and focused host fixtures pass. The Open entries below describe the earlier runtime findings; visual/gameplay acceptance remains open.

- Open experiment: [absolute direct-present cadence](../../../docs/reference/frame-rate.md#absolute-cadence-experiment-for-direct-presentation) is available with `DM_PRESENT_ABSOLUTE=1` on the Mac. It is off by default and has no gameplay latency result yet.

- Mac CPU experiments are available for [uniform-copy consumer waits](../../../docs/reference/frame-rate.md#uniform-copy-consumers-spin-while-their-worker-is-delayed) and [compile pool limits](../../../docs/reference/frame-rate.md#compile-pools-compete-with-other-apps). Gameplay A/B validation is open.
- The [game-upscaler swap](../../../docs/reference/rendering.md#a-games-own-upscaler-drawn-by-metalfx) already names the 22 standard NDSR compute variants. Eleven have the colour shape accepted for MetalFX spatial scaling; the VR packs and NDVE movie pipelines remain excluded. Handheld uses the game's smaller resolution parameters, as detailed in [Upscaler and render scale](#upscaler-and-render-scale). Runtime A/B validation is open.
- [Experimental constant-word reuse and storage runs between grid points](../../../docs/reference/shaders.md#experimental-constant-word-reuse-and-storage-runs-between-grid-points), currently default off; see the experiment below.
- Source audit: [Mac SDR output without a source colour space](../../../docs/reference/rendering.md#mac-sdr-output-without-a-source-colour-space). Opt-in colour tagging and a GPU pass scan are available; visual acceptance in Kokiri Forest remains open.

- The online library's [eventfd for its poller](../../../docs/reference/services.md#eventfds-served-offline) and the [virtual audio input list](../../../docs/reference/audio.md#no-virtual-audio-input-devices-sdk-22) blocked startup.
- The SDK's [NDVE pack](../../../docs/reference/shaders.md#the-movie-librarys-ndve-shader-pack) contains 22 compute programs. The title route uses 11.
- The [raw write log and pool lookup](../../../docs/reference/frame-rate.md#a-full-frame-shader-overflows-the-raw-write-log) took the windowed title movie from a 47.6 ms median to 16.67 ms on an Apple M5, at 1920×1080 decode. A steady 300-frame window averaged 60.0 fps and its GPU median was 15.94 ms. A simultaneous ten-worker shader build caused additional stalls. The same run returned to 60.0 fps when the build paused.
- A [play report send](../../../docs/reference/services.md#an-asynchronous-play-report-opens-prepou) aborted at the first gameplay transition after a failed `prepo:u` connection. A Mac dry run with the offline completion finished the 9,254-picture opening movie and continued submitting the live scene. The title-only shader set left the scene black.
- The white 3D scene was agl's [conditional depth clears](../../../docs/reference/rendering.md#conditional-rendering-evaluated-at-replay) run unconditionally (resolved; the profile sets `render_cond on`). The main opaque pass tests `EQUAL` against a copy of the prepass depth that agl clears under a condition right after copying, a clear the console skips. Without the key the copy was 1.0, no lit geometry passed, and the full-screen sky (`943d8c0ece545cc8`) showed through. With the key the saved Kokiri Forest scene renders: Link, the ground, the props, lighting and the HUD.
- Mesh-shaded models were missing, among them the door of Link's house: the split read six stage slots of each BNSH program, and NVN2 keeps [task and mesh shaders in slots 7 and 8](../../../docs/reference/shaders.md#task-and-mesh-shaders-in-nvn2-bnsh-program-slots-7-and-8) (resolved). The new split adds 491 mesh and 17 task shaders to the map, 53 of the 54 keys the Kokiri Forest scene had asked for. 511 of their 520 build; the door renders.
- Kokiri Forest ran at about 20 fps with the GPU two-thirds idle: the [bindless pool table was rebuilt for every registration](../../../docs/reference/frame-rate.md#a-bindless-pool-table-rebuilt-for-every-registration), and about 12,000 descriptors of finalized texture objects churned the ghost ring (resolved). The frame is now 16–21 ms at the median on an Apple M5, submit 5–8 ms, and the GPU (14–21 ms) is the limit.
- The first 3D scene exhausted Metal memory when [bindless pool walks churned finalized textures](../../../docs/reference/nvn-objects.md#a-bindless-pool-churns-finalized-textures-within-a-submission). On the Apple M5, the failing run reached 18,930 MiB of residency. With submission-local backing, residency was 7,946 MiB about ten seconds after the movie and 7,871 MiB at 35 seconds. The opening 3D scene and its subtitles presented, and the test host exited normally.
- [Opt-in filtering and supersampled presentation](../../../docs/reference/rendering.md#opt-in-filtering-and-supersampled-presentation) supplies the quality preset below. Synthetic GPU checks pass; gameplay acceptance is open.

## Quality mode (current, opt-in, gameplay acceptance open)

`DM_QUALITY=max` selects anisotropy 16, trilinear filtering, MetalFX spatial presentation at 1.5 times the native viewport, and sharpening 0.2. `DM_QUALITY=off` is the default. Individual feature variables override either preset, including explicit zero/off values. Restart between comparisons because the settings and sampler objects are cached. This is an opt-in candidate for better texture detail and presentation. No console comparison or gameplay test establishes that it looks better than Switch 2 yet.

The implementation follows [the shared sampler and presentation mechanism](../../../docs/reference/rendering.md#opt-in-filtering-and-supersampled-presentation). Comparison, reduction, nearest and non-mipmapped samplers keep their original filtering. Linearly filtered UI textures can still be affected. The preset preserves the game's own NDSR, scene dimensions and frame cadence. Interpolation is absent.

All costs below are **planning estimates**, additional GPU work on an M4 Max for roughly 1440p to 4K presentation. They are not measurements and are not additive guarantees. The profile's 14 to 21 ms GPU numbers came from an M5, so they do not establish this Mac's spare capacity inside a 33.3 ms frame budget.

| Feature and flag | Expected visual gain | Extra GPU cost estimate | Risk and status |
|---|---|---|---|
| `DM_ANISO=16` (`0` keeps game) | More distant ground and wall detail at glancing angles | 0.1 to 2 ms, depending on texture sampling and bandwidth | Implemented, including bindless pools. Does not generate new texture detail. More texture traffic and possible shimmer. |
| `DM_TRILINEAR=1` (`0` keeps game) | Softer transitions between mip levels | 0 to 0.5 ms | Implemented on ordinary linear mip samplers. Slightly softer transitions. |
| `DM_PRESENT_UPSCALE=metalfx` (`off` default) | Alternative spatial reconstruction at the display's backing resolution | 0.5 to 3 ms when enlargement is needed | Existing option. Changes reconstructed edges and HUD. No motion history. |
| `DM_PRESENT_UPSCALE_OUT=1.5` (`1` default, up to `4`) | Reconstructs 2.25 times as many presentation pixels, then averages down | 0.5 to 4 ms including spatial reconstruction and reduction | Implemented from PR #345 with corrected filter composition. This is presentation supersampling, not new scene samples. Can soften detail; output allocation grows quadratically. |
| `DM_SHARPEN=0.2` (`0` default, up to `1`) | More local contrast in the finished picture | 0.1 to 1 ms; more when combined with the grid filter | Implemented in the existing present pass. Neighbourhood clamping prevents overshoot but cannot prevent extra shimmer or enhancement of existing artifacts. Affects HUD too. |
| `DM_QUALITY=max` | Combines the above; preserves NDSR and 30 game fps | Budget roughly 1 to 7 ms extra, then measure | Implemented. Explicit feature settings win. Not gameplay approved. |
| Scene scale 1.5 or 2 | More geometry samples, less geometric aliasing | Pixel work grows 2.25 or 4 times; if all of the quoted GPU work scaled, totals would be 31.5 to 47.3 or 56 to 84 ms | **Not implemented.** The game allocation sizes, compute coordinates, depth, shadows and NDSR resolve need coordinated validation. These totals are scaling illustrations, not M4 Max predictions. |
| `DM_UPSCALER=metalfx` (`game` default) | Optional replacement of eligible NDSR dispatches by the existing spatial scaler | Could save work; no quality or cost measurement here | Existing option, deliberately outside max. It changes the game's reconstruction. Check the first-dispatch log before assuming it applied. |
| Temporal MetalFX | Could reduce edge shimmer using motion history | Unestimated until motion, jitter and reset contracts are known | **Not implemented for NDSR.** Its audited standard kernels expose one sampled colour input and no motion texture. |
| Frame interpolation | Could show 60 pictures from 30 game frames | PR #301 quotes 7.7 ms per generated frame on M1 Pro; no transferable M4 Max estimate | **Not ported.** Needs this game's camera, scene/UI split and cut detection. Moving actors, particles and HUD can ghost. PR #301 estimates half a game frame of extra latency, about 16.7 ms at 30 fps. |

### Scene size investigation (open)

`DM_RENDER_SCALE` has no effect on this profile because there is no `patches.py` render-scale stub or loader state page. PR #354's higher ceiling only helps games with those stubs. Neither `DM_RESCALE` from PR #491 nor `DM_UPSCALE` from PR #405 exists in this base host. They have not been added as ineffective settings.

Read-only inspection of the supplied v131072 RomFS found `System/GameGraphics/ModelSceneExtensionParam/Default.game__gfx__ModelSceneExtensionParam.bgyml` in Bootup. Its docked resolution entries `d30fdb96` and `eeb1db9f` both declare base/final size 2560x1440 and use palette `2ebeca77`, whose top `ResolutionReduceScale` is 0.75. That gives a configured top scene size of 1920x1080. The handheld entry `0b46e9da` declares 1920x1080 with the same top fraction, giving 1440x810. Actual dynamic levels and runtime attachment sizes were not observed here.

The palette exposes a plausible engine-side control. Raising 0.75 to 1.125 or 1.5 would nominally request 2880x1620 or 3840x2160 docked scenes. Those exceed the declared base/final size. It is unknown whether the engine sizes its pools, history, dispatches and post-processing from that fraction or assumes a fraction at most 1. There is no sound address-only patch yet. Even raising it to 1.0 requires proving the allocations and all dependent passes.

PR #491 scales screen-like attachments while excluding images written by compute. Its binding correction does not cover this game's dynamic bindless texture pools. PR #405 is more complete, but conservatively demotes textures written as images and its generic upscaler bypass decodes FSR constants, not NDSR rectangles and colour transforms. Scaling only the raster targets can therefore be undone or give incorrect integer reads and compute footprints. NDSR's constants and the existing MetalFX swap describe enlargement, not a tested resolve of a scene larger than its output. A full port is not justified without gameplay and frame-capture validation.

The re-run NDSR audit verified all 22 standard compute kernels against their package hashes and resource reports. Each has one sampled texture at handle 8, one image at handle 74, read-only storage resources and push bank 24. Eleven have the half-float sRGB decode accepted by the existing spatial swap. VR and NDVE variants are different contracts. This does not identify any temporal input, jitter sequence or history reset. The host already implements NVN2 DLSS through temporal MetalFX when the game explicitly supplies depth, motion, jitter and reset data, which is a separate path from these NDSR kernels.

PR #301 derives camera motion for static world pixels and requires a build-specific camera block, scene-end marker and complete HUD separation. None is established for this profile. NDSR's lack of an exposed motion texture does not prove the game never makes motion data, but it prevents a correct temporal or interpolation port based on NDSR alone.

### Kokiri Forest comparison recipe

Run this only in the parent's gameplay pass. This task did not run it. The save source must be the parent's **Kokiri Forest Autosave** checkpoint containing `slot_00/progress.sav` and `slot_00/caption.sav`. Do not copy a save while the baseline host is writing it. Supply `SAVE_REF` and `FONT_DIR` from the parent's working baseline launch. The remaining paths match the shared extraction.

```sh
export REPO=/Users/ankur/.t3/worktrees/nxnative-oot/t3-ff09367e
export BUILD=/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build
export COMPARE=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-quality/compare
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
# Set these to the parent's known baseline paths before continuing.
: "${SAVE_REF:?Set SAVE_REF to the Kokiri Forest checkpoint directory}"
: "${FONT_DIR:?Set FONT_DIR to the working baseline font directory}"
test -f "$SAVE_REF/slot_00/progress.sav" && test -f "$SAVE_REF/slot_00/caption.sav"
mkdir -p "$COMPARE"
```

Define the following shell function. It starts a fresh process with an independent save, temp directory and pipeline cache. It reads the existing rewritten game and shader libraries. It does not change the launcher or the user's `env.txt`. Tags must be new so each run starts from the same checkpoint.

```sh
quality_run() {
    tag="$1"; shift
    run="$COMPARE/$tag"
    test ! -e "$run" || return 1
    mkdir -p "$run/temp" "$run/root"
    cp -cR "$SAVE_REF" "$run/save"
    : > "$run/control.txt"
    (
        cd "$run" || exit 1
        env -u DM_QUALITY -u DM_ANISO -u DM_TRILINEAR -u DM_SHARPEN \
            -u DM_PRESENT_UPSCALE -u DM_PRESENT_UPSCALE_OUT \
            -u DM_RENDER_SCALE -u DM_RESCALE -u DM_UPSCALE \
            -u DM_FPS -u DM_FPS_TARGET -u DM_FPS_HOLD \
            -u DM_KEYS -u DM_REC -u DM_NVN_SHOT \
            DM_QUALITY=off DM_UPSCALER=game DM_OPMODE=1 \
            DM_WINDOW=1 DM_FULLSCREEN=1 DM_FOCUS_KEEP=1 DM_AUDIO=1 \
            DM_ROOT="$run/root" DM_SAVE="$run/save" DM_TEMP="$run/temp" \
            DM_ROMFS="$BUILD/extract/v131072/RomFS.img" \
            DM_MSL_DIR="$BUILD/shader/cache" DM_FONT_DIR="$FONT_DIR" \
            DM_NVN_SHMAP="$REPO/dm/games/0400486024DEC000/shader_map.tsv" \
            DM_PSO_USER="$run/pso_user.tsv" DM_PSO_ARCHIVE="$run/pso_archive" \
            DM_CTL="$run/control.txt" DM_NVN_SHOT_OUT=3840x2160 \
            "$@" "$REPO/dm/host/dmhost" "$BUILD/patched_v131072" \
            > "$run/log.txt" 2>&1
    )
}
```

`3840x2160` gives a fixed 4K comparison artifact even on a differently sized screen. To capture exactly the displayed pixels instead, replace it in **every** run with the `front end: drawable WxH` size logged in fullscreen. The front end already sizes the drawable in native backing pixels. Never compare a raw swapchain `shot` against a presentation-filtered `shot`.

Start each case in the first terminal, load slot 00, and leave the camera at the same reload position. In a second terminal set `COMPARE` to the same path and append the screenshot request for its tag, for example `printf 'shot %s\n' "$COMPARE/stock/still.png" >> "$COMPARE/stock/control.txt"`. Capture another frame after the scene settles. Quit normally before starting the next case. Use a recorded, identical camera pan for moving comparisons rather than claiming pixel identity from two live frames.

```sh
quality_run stock
quality_run aniso DM_ANISO=16
quality_run trilinear DM_TRILINEAR=1
quality_run present DM_PRESENT_UPSCALE=metalfx
quality_run supersampled DM_PRESENT_UPSCALE=metalfx DM_PRESENT_UPSCALE_OUT=1.5
quality_run sharp DM_SHARPEN=0.2
quality_run max DM_QUALITY=max
quality_run swap DM_UPSCALER=metalfx
```

These are separate sequential launches, not one automatic batch. Use stock versus aniso for distant ground, stock versus trilinear for mip transitions, present versus supersampled for reconstruction footprint, stock versus sharp for edge contrast, and stock versus max for the preset. `swap` tests the existing game-upscaler replacement separately. Its log must contain `upscaler: first dispatch` before attributing a result to MetalFX. No such replacement log is expected for max.

Check Link, thin branches, the house door, ground at a shallow angle, fog, shadow edges and cascade joins, the horizon, subtitles and HUD text. Reject new flicker, bright dots, missing foliage, shifted UI, halos or colour changes. Pre-existing missing foliage shaders and the open fog issue above remain baseline defects. Sharpening can make either more obvious. Compare motion as well as stills. Record steady GPU medians and tails for both game submissions and `present command buffer GPU time`; presentation work is separate from the game's quoted GPU time. Discard first-use pipeline creation and screenshot-readback spikes. Acceptance requires the total to fit the 33.3 ms game budget without a worse image.

## MSL mining experiment (open)

A stage-stratified sample of the in-progress Mac build is recorded in [implementation-notes.md](../../../implementation-notes.md), with source hashes, stage coverage, the pattern table, four compiler comparisons, and the parent's A/B recipe. The [experimental passes](../../../docs/reference/shaders.md#experimental-constant-word-reuse-and-storage-runs-between-grid-points) default off. Compute constant-word reuse is the first GPU A/B candidate; the pixel compiler example has no instruction reduction. Storage grouping adds wrap-fallback branches and needs a separate test. No M4 Max frame-time, energy or image-equivalence result is claimed.

## Counter read census, v131072

Current static measurement on the supplied update, independent of the v0 profile addresses. The original ExeFS text words were checked against `patched_v131072/*.sites.tsv`, `*.gates.tsv` and the rewrite logs. No game files or rewritten outputs were modified.

| Module | NSO build ID, first 16 bytes | CNTPCT sites | CNTVCT sites | CNTFRQ sites |
|---|---|---:|---:|---:|
| main | `e0f3ccfaf50065ae4ea01eb5aeb13b1a` | 0 | 0 | 0 |
| subsdk0 | `b0110087a7b339ef74588d3bd0b4dd5d` | 0 | 0 | 0 |
| sdk | `1643a838814f9c10c696f930ed681e7f` | 45 | 0 | 0 |

The SDK destinations are x0 (14), x8 (11), x11 (1), x20 (7), x21 (9) and x22 (3). Every measured site can use the optional [integer-only counter entry](../../../docs/reference/rewriter.md#counter-reads-save-a-full-simd-context). The update's SDK uses the Switch 2 frequency of 31.25 MHz. Static sites do not establish dynamic read frequency or total CPU saving. Runtime counts, gameplay A/B, audio/pacing checks and machine sleep/wake validation remain open. TLS specialization was deferred to keep executable offset fixups outside the clock change.

## Open

- The opt-in [idle and hidden-window host policies](../../../docs/reference/frame-rate.md#repeated-scan-out-and-unwatched-window-work) have unit and offscreen Metal coverage only. Ocarina skip rates, energy, wakeups and real focus/occlusion transitions remain unvalidated. The detector skips repeat scan-out without intervening submissions; it never omits the game's draw/compute work.

- Of the task and mesh shaders, nine do not translate: eight foliage shaders stop at Ampere opcode `0x243` (packed conversion, source A `RZ`, mode `0x0000c4ff`; three of them, `604134a5262ff670`, `ecead5cd0569091f` and `fed302d791a4ba43`, are drawn in Kokiri Forest), and one at ISBERD mode `0xb8` in a task or mesh shader. The scene also asks for `d17eefaff4f0bc23`, whose code is in none of the shader archives.
- The title-only build logged 3,331 distinct mapped libraries it could not open, including 363 shaders that failed when setting up programs. A targeted build for those programs and their dependencies translated 6,132 of 6,134 shaders. The two failures are foliage compute shaders `8692b34b521225be` and `83df46a0b1b379b4`, both with Ampere opcode `0x243`.
- With `render_cond` on and the shader build still incomplete, Kokiri Forest showed a hard horizontal cut, sky colour above the horizon over the trees. The volumetric fog composite (`888c1068ac8f7043`, agl) takes a pixel whose R32Float depth copy reads above 0.9999 as sky and paints the sky lookup there. The pass that fills that copy draws with agl's full-screen vertex shader `fb1ed54be1baced1`, which that build had not reached yet, so the host skipped the draw (`draw skipped: no render pipeline`) and dropped the target's store. Retest with the stamped full build. The sky lookup's peaks (about 105, 67 and 36 in RGB) are unverified against the console.
- The opening scene calls `nvnCommandBufferDrawMeshTasksIndirect`, which the host does not implement. On `v0` the probe caught the return at `main+0x2be2dc0`; the branch builds the command buffer pointer in `x0` and the indirect argument address in `x1`. It does not set `x2` on that path. A separate sample of the first 64 bytes at the indirect address returned zeros after the call; the populated record's layout is still unverified. The title-only run logged 11 keys missing from the map. The expanded run captured seven of them before the memory failure. A byte-for-byte comparison found none of those seven code areas in the extracted shader package.
- The 3D scene's CPU cost (37–59 ms a frame, with pool walks of about 33,000 descriptors) is [resolved](../../../docs/reference/frame-rate.md#a-bindless-pool-table-rebuilt-for-every-registration). Open: the GPU's 14–21 ms a frame in Kokiri Forest, which still drops frames below 60 fps; TBDR optimizations are off for this bindless game (`DM_NVN_TBDR=1` turns them on), and attachments load and store about 330 MB a frame.
- The Nov. 4 Lichii branches offer two shader leads. Its [packed conversion lowering](https://github.com/zortos293/Lichii/commit/35c043b3efaa147d1c1afe8a52cdf19fa92b77bf) handles opcode `0x243` with source A set to `RZ` and mode `0x0000c4ff`; both of this game's failed foliage programs use two registers and mode `0x000004ff`, which needs independent verification. Its [floating-point global reduction](https://github.com/zortos293/Lichii/commit/3aa89d1cdbe58a2bd5ded06b9c615c78da2ade70) matches a separate `F32FtzRn` diagnostic in the Mac shader build, where the translator drops that operation. Neither of the two shaders in the sky lookup and draw uses those instructions or the gather opcodes from Lichii's [fog work](https://github.com/zortos293/Lichii/commit/375c4a472bd95fdfaae0de6e3f192499cd14f806).

## Safety build (oot-stable)

The Mac build defaults to [fail-stop GPU safety](../../../docs/reference/memory.md#fail-stop-gpu-safety-for-a-mac-shared-with-other-apps) with `DM_SAFE_GPU=1`. A first GPU error, lost feedback or memory cap ends the process without draining failed work. Progress since the last save is lost. This is a safeguard for the still-open failure in #1326. It cannot promise that a kernel or WindowServer failure already in progress is recoverable. Unit tests and a host build are the acceptance evidence here; gameplay has not been run.
## Tile-memory experiment

The `oot-tbdr` experiment ports the source and tests of [#1340](https://github.com/seedds/nxnative/pull/1340) (`9e141cc8`) and [#1367](https://github.com/seedds/nxnative/pull/1367) (`c82a370f`) onto `oot-stack` (`8284776d`). It changes no shader tool or shader-chain stamp. `DM_NVN_TBDR=1` enables it. The normal setting stays off. No game was run for this port.

### What may be discarded

The [store lookahead](../../../docs/reference/rendering.md#store-lookahead-and-bindless-readers) keeps every candidate texture stored when a later draw or dispatch has a pooled, uniform-buffer, array or dynamic texture handle, or an unknown program. Candidates include the current attachments and textures carried by the validity ledger. This includes every mip, layer and depth/stencil plane of those candidates. A known slot read also retains its target. An attachment whose later use is undecided at submission end is stored.

A store can be discarded when the same subresource is unconditionally cleared in full before any possible read or attachment load in the same submission. The clear must cover the whole subresource's scissor and the whole colour/depth/stencil write mask. The local proof for an unchanged, loaded attachment also remains valid because its bytes already exist in memory. The required image-only attachment rule remains unchanged. A conditional clear is never used as an overwrite proof. This is necessary here because agl conditionally skips depth clears after copying the prepass depth. The original lookahead did not track conditional rendering or the scissor; this experiment adds those guards.

`DM_NVN_XV=1` now separately opts into prediction from previous submissions. Leave it unset or `0` for this experiment. A history of three clears cannot prove that a later loading screen will not sample the target. This is a deliberate deviation from the two ports. No attachment or depth surface is made memoryless. A memoryless surface cannot serve a later reader or a pass that reloads its contents.

### Shader evidence and allow-list

`dm/tools/tbdr_shader_audit.py` reads the profile and one generated reflection directory. It produces an allow-list of shader stages whose texture reads can be resolved from slots, plus separate unresolved and missing lists. It does not declare an attachment dead and the host does not trust the file. The host applies the conservative rule directly to each loaded reflection, so a stale allow-list cannot weaken it.

The read-only audit of the supplied `b-d1f10abd26a7` cache found 42,851 profile keys and 40,801 reflection files. There are 35,981 slot-resolvable keys, 4,820 unresolved keys and 2,050 missing keys. The inventory was captured at 2026-11-06 01:12:40 UTC; another process was still adding shaders, so later audits can differ. The profile's 4,123 facts rows contain only `local` and `shared`; they say nothing about attachment lifetimes. The cache is from an older chain than the integrated stack. These counts describe its coverage, not the shaders drawn by a complete new build.

| Stage | Slot-resolvable | Unresolved |
| --- | ---: | ---: |
| Pixel | 17,598 | 4,758 |
| Vertex | 13,780 | 50 |
| Compute | 4,103 | 1 |
| Mesh | 481 | 11 |
| Task | 19 | 0 |

4,815 shaders have `tex_pool` and `samp_pool`, and five have uniform-buffer texture handles. The material pixel shader `dbda7678a92ef6e5` has both pool and fixed-slot textures. The fog composite `888c1068ac8f7043` and sky shader `943d8c0ece545cc8` have fixed-slot textures. Their slots must still be checked against the actual attachments at replay. The fullscreen vertex key `fb1ed54be1baced1` has no reflection in this cache. Missing coverage therefore cannot justify an optimization or a visual pass.

Reflection alone cannot identify which attachment a GPU-selected handle will name. Every registered target reachable through the bound pool must be treated as readable, including aliases. There is no safe static allow-list of discardable Ocarina attachment IDs in these inputs. The executable allow-list is the runtime proof above: an unconditional full overwrite before a reader, or an unchanged loaded attachment. The generated slot list is an inspection aid only.

### Same-pass depth readers

[#1385](https://github.com/seedds/nxnative/issues/1385) reports about 74 feedback splits out of 178 passes per frame in Link's house. [#1396](https://github.com/seedds/nxnative/pull/1396) separates the causes. Its docked M4 run reports 71.7 depth splits after pooled shaders per frame, zero colour or named-depth splits, and 74.7 pool draws whose tables could contain depth. Its narrower pool test saves zero passes. In that run a registered view of the 1920×1080 depth target is itself in the table, and about 8,000 of 16,600 IDs overlap its storage. These are upstream measurements from another host and scene, not local results.

This experiment adopts #1396's split-cause categories only. It preserves the original conservative pool/dynamic reader rule. A precise future exclusion must inspect the tables bound for that draw and prove that no entry can reach the depth storage, including views, aliases, sparse mappings and unknown storage. Shader names, material classification and previous frames do not prove that.

[#901](https://github.com/seedds/nxnative/pull/901) copies a named same-pass depth texture and redirects that binding. Its final source defaults this on only for Tropical Freeze, with an explicit override in that PR. It does not redirect `tex_pool` entries. Porting that slot path would not remove Ocarina's pooled depth splits. Redirecting every overlapping pool entry to a snapshot would need immutable table variants with the right type and view, generation invalidation, retained resources, and snapshots scoped by barrier, submission and depth subresource. That is separate work. This branch does not suppress a possible depth reader or claim the unsound 175-to-103-pass experiment as a safe gain.

### Bytes, counters and risks

The earlier Open entry's roughly 330 MB per Kokiri Forest frame is a historical nominal attachment estimate. The host already exposes `mtl_bw`, the residency log, `DM_NVN_TSV` metrics `@rt_load_mb` / `@rt_store_mb`, and `DM_NVN_GPUPROF` per-pass load/store estimates. Their `MB` labels use 1,048,576 bytes. They are not physical DRAM counters. No matching saved pass trace was available here to divide that total into safe-to-drop stores and mandatory stores.

The conservative planning estimate is therefore still roughly 330 nominal MB per frame, with zero demonstrated saving. This is a reference budget, not a bound on what TBDR will do. Reordering, clear handling and tile-read eligibility can change other passes and may increase traffic. For a measured future reduction, subtract the proven discarded stores and avoided loads/stores from the same scene's baseline. A 1920×1080 Depth32Float plane is 8,294,400 bytes. Avoiding one full store/load cycle would save 16,588,800 nominal bytes, provided that no replacement copy or reader needs them. #1396's separate Link's-house run reports 444 MB loaded plus 460 MB stored per frame in both arms. Do not combine that with the 330 MB Kokiri figure.

`DM_NVN_ATTPROF=1` adds `[attprof]` rows per frame, serial, mip, slice and plane, with integer `load_bytes`, `store_bytes`, `dontcare_bytes` and attachment uses. A total row gives passes, pass ends, `blit_splits`, `uniform_conflicts`, `fb_color_splits`, `fb_depth_named_splits` and `fb_depth_pool_splits`. A pass can meet several split categories, so do not sum them as independent savings. `pass_ends` includes ordinary target changes and submission ends. The `end_op` rows identify the ending replay opcode; 0 also means outside replay. Rows flush at the next present, so the last partial frame is absent.

The new rows reuse the draw-pass ledger's size estimates. They exclude helper encoders, standalone clears, compressed-target shadow attachments, sampling traffic and physical compression/cache effects. Layered passes, restricted render areas and uncommon pixel formats retain that ledger's approximations. Use the same settings and scene for both arms. Capture detailed telemetry separately from energy runs because logging adds work.

A wrong `DontCare` can produce black or garbage rectangles, old pixels, missing geometry, depth-test holes, broken fog/shadows, or flicker at barriers and scene transitions. An unsound reader exclusion can let an earlier draw see a later depth write. A clean log cannot establish visual equivalence. Check the fixed camera and loading transitions as well as moving through the scene. Gameplay, energy and GPU benefit remain unverified on this branch.

### A/B recipe for the parent

First integrate the `oot-bench` and `oot-vqa` tools, and use a complete stamped shader build matching the stack's chain. They are separate branches and are not copied into this port. Prepare a writable candidate build outside the protected baseline folders. The same candidate host can serve both arms, with identical modules, shaders, save, camera and handheld/docked mode. Keep the game at its own 30 fps cap. Leave `DM_NVN_XV=0` in both env files. Set only `DM_NVN_TBDR=0` in `off.env` and `=1` in `on.env`. Other stack switches must match.

With `PY` set to the approved uv interpreter and `OUT` to a new durable work directory, run this only when the parent authorizes gameplay:

```sh
"$PY" scripts/oot_ab.py --a "$CANDIDATE_BUILD" --b "$CANDIDATE_BUILD" \
  --a-host "$CANDIDATE_HOST" --b-host "$CANDIDATE_HOST" \
  --a-env "$OFF_ENV" --b-env "$ON_ENV" --save "$FIXED_SAVE" \
  --route "$SMOKE_ROUTE" --runs 3 --out "$OUT"
```

Use one route and its steady measurement window in both arms. Compare bytes per presented frame from `@rt_load_mb` and `@rt_store_mb`, passes and GPU span, CPU work, wakeups and kernel energy counters. `oot_ab.py` reports billed energy in opaque counter units, not GPU joules. The existing task-energy log is CPU energy only. Neither proves whole-device GPU power savings. Check each run's 30 fps cap and workload before comparing energy. Repeat with `DM_NVN_ATTPROF=1` in both env files for a diagnostic run, and inspect the same frame range. Confirm that store savings do not come from skipped draws or missing libraries.

Run the VQA log check on every run folder, using the same window as the A/B measurement:

```sh
"$PY" scripts/oot_vqa.py "$OUT/A-1" --window "$MEASUREMENT_WINDOW" --out "$OUT/A-1-vqa.md"
"$PY" scripts/oot_vqa.py "$OUT/B-1" --window "$MEASUREMENT_WINDOW" --out "$OUT/B-1-vqa.md"
```

Repeat for the other run folders. Reject new skipped pipelines, missing or untranslated shader keys, nonfinite pixels, ledger violations, or new `[RED]` types. Existing failures must be reconciled, not hidden by a smaller byte count. Pair that check with screenshots and a visual comparison allowing only the scene's normal animation. Include Link's house, Kokiri Forest, the fog horizon, menus and a loading transition. No such VQA or game comparison has been performed for this port.

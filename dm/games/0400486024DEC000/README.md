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

- The [game-upscaler swap](../../../docs/reference/rendering.md#a-games-own-upscaler-drawn-by-metalfx) already names the 22 standard NDSR compute variants. Eleven have the colour shape accepted for MetalFX spatial scaling; the VR packs and NDVE movie pipelines remain excluded. Handheld uses the game's smaller resolution parameters, as detailed in [Upscaler and render scale](#upscaler-and-render-scale). Runtime A/B validation is open.

- The online library's [eventfd for its poller](../../../docs/reference/services.md#eventfds-served-offline) and the [virtual audio input list](../../../docs/reference/audio.md#no-virtual-audio-input-devices-sdk-22) blocked startup.
- The SDK's [NDVE pack](../../../docs/reference/shaders.md#the-movie-librarys-ndve-shader-pack) contains 22 compute programs. The title route uses 11.
- The [raw write log and pool lookup](../../../docs/reference/frame-rate.md#a-full-frame-shader-overflows-the-raw-write-log) took the windowed title movie from a 47.6 ms median to 16.67 ms on an Apple M5, at 1920×1080 decode. A steady 300-frame window averaged 60.0 fps and its GPU median was 15.94 ms. A simultaneous ten-worker shader build caused additional stalls. The same run returned to 60.0 fps when the build paused.
- A [play report send](../../../docs/reference/services.md#an-asynchronous-play-report-opens-prepou) aborted at the first gameplay transition after a failed `prepo:u` connection. A Mac dry run with the offline completion finished the 9,254-picture opening movie and continued submitting the live scene. The title-only shader set left the scene black.
- The white 3D scene was agl's [conditional depth clears](../../../docs/reference/rendering.md#conditional-rendering-evaluated-at-replay) run unconditionally (resolved; the profile sets `render_cond on`). The main opaque pass tests `EQUAL` against a copy of the prepass depth that agl clears under a condition right after copying, a clear the console skips. Without the key the copy was 1.0, no lit geometry passed, and the full-screen sky (`943d8c0ece545cc8`) showed through. With the key the saved Kokiri Forest scene renders: Link, the ground, the props, lighting and the HUD.
- Mesh-shaded models were missing, among them the door of Link's house: the split read six stage slots of each BNSH program, and NVN2 keeps [task and mesh shaders in slots 7 and 8](../../../docs/reference/shaders.md#task-and-mesh-shaders-in-nvn2-bnsh-program-slots-7-and-8) (resolved). The new split adds 491 mesh and 17 task shaders to the map, 53 of the 54 keys the Kokiri Forest scene had asked for. 511 of their 520 build; the door renders.
- Kokiri Forest ran at about 20 fps with the GPU two-thirds idle: the [bindless pool table was rebuilt for every registration](../../../docs/reference/frame-rate.md#a-bindless-pool-table-rebuilt-for-every-registration), and about 12,000 descriptors of finalized texture objects churned the ghost ring (resolved). The frame is now 16–21 ms at the median on an Apple M5, submit 5–8 ms, and the GPU (14–21 ms) is the limit.
- The first 3D scene exhausted Metal memory when [bindless pool walks churned finalized textures](../../../docs/reference/nvn-objects.md#a-bindless-pool-churns-finalized-textures-within-a-submission). On the Apple M5, the failing run reached 18,930 MiB of residency. With submission-local backing, residency was 7,946 MiB about ten seconds after the movie and 7,871 MiB at 35 seconds. The opening 3D scene and its subtitles presented, and the test host exited normally.

## Open

- Of the task and mesh shaders, nine do not translate: eight foliage shaders stop at Ampere opcode `0x243` (packed conversion, source A `RZ`, mode `0x0000c4ff`; three of them, `604134a5262ff670`, `ecead5cd0569091f` and `fed302d791a4ba43`, are drawn in Kokiri Forest), and one at ISBERD mode `0xb8` in a task or mesh shader. The scene also asks for `d17eefaff4f0bc23`, whose code is in none of the shader archives.
- The title-only build logged 3,331 distinct mapped libraries it could not open, including 363 shaders that failed when setting up programs. A targeted build for those programs and their dependencies translated 6,132 of 6,134 shaders. The two failures are foliage compute shaders `8692b34b521225be` and `83df46a0b1b379b4`, both with Ampere opcode `0x243`.
- With `render_cond` on and the shader build still incomplete, Kokiri Forest showed a hard horizontal cut, sky colour above the horizon over the trees. The volumetric fog composite (`888c1068ac8f7043`, agl) takes a pixel whose R32Float depth copy reads above 0.9999 as sky and paints the sky lookup there. The pass that fills that copy draws with agl's full-screen vertex shader `fb1ed54be1baced1`, which that build had not reached yet, so the host skipped the draw (`draw skipped: no render pipeline`) and dropped the target's store. Retest with the stamped full build. The sky lookup's peaks (about 105, 67 and 36 in RGB) are unverified against the console.
- The opening scene calls `nvnCommandBufferDrawMeshTasksIndirect`, which the host does not implement. On `v0` the probe caught the return at `main+0x2be2dc0`; the branch builds the command buffer pointer in `x0` and the indirect argument address in `x1`. It does not set `x2` on that path. A separate sample of the first 64 bytes at the indirect address returned zeros after the call; the populated record's layout is still unverified. The title-only run logged 11 keys missing from the map. The expanded run captured seven of them before the memory failure. A byte-for-byte comparison found none of those seven code areas in the extracted shader package.
- The 3D scene's CPU cost (37–59 ms a frame, with pool walks of about 33,000 descriptors) is [resolved](../../../docs/reference/frame-rate.md#a-bindless-pool-table-rebuilt-for-every-registration). Open: the GPU's 14–21 ms a frame in Kokiri Forest, which still drops frames below 60 fps; TBDR optimizations are off for this bindless game (`DM_NVN_TBDR=1` turns them on), and attachments load and store about 330 MB a frame.
- The Nov. 4 Lichii branches offer two shader leads. Its [packed conversion lowering](https://github.com/zortos293/Lichii/commit/35c043b3efaa147d1c1afe8a52cdf19fa92b77bf) handles opcode `0x243` with source A set to `RZ` and mode `0x0000c4ff`; both of this game's failed foliage programs use two registers and mode `0x000004ff`, which needs independent verification. Its [floating-point global reduction](https://github.com/zortos293/Lichii/commit/3aa89d1cdbe58a2bd5ded06b9c615c78da2ade70) matches a separate `F32FtzRn` diagnostic in the Mac shader build, where the translator drops that operation. Neither of the two shaders in the sky lookup and draw uses those instructions or the gather opcodes from Lichii's [fog work](https://github.com/zortos293/Lichii/commit/375c4a472bd95fdfaae0de6e3f192499cd14f806).

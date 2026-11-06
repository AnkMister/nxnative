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

## Found on this game

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
| `DM_OOT_RENDER_RES=1440` or `2160` | More scene samples before presentation | See the [internal-resolution estimates](#expected-gpu-cost-inferred-not-measured) | Experimental engine override, separate from max. Requires a freshly rewritten main. [Visual acceptance is open](#internal-render-resolution-current-experimental-visual-acceptance-open). |
| `DM_UPSCALER=metalfx` (`game` default) | Optional replacement of eligible NDSR dispatches by the existing spatial scaler | Could save work; no quality or cost measurement here | Existing option, deliberately outside max. It changes the game's reconstruction. Check the first-dispatch log before assuming it applied. |
| Temporal MetalFX | Could reduce edge shimmer using motion history | Unestimated until motion, jitter and reset contracts are known | **Not implemented for NDSR.** Its audited standard kernels expose one sampled colour input and no motion texture. |
| Frame interpolation | Could show 60 pictures from 30 game frames | PR #301 quotes 7.7 ms per generated frame on M1 Pro; no transferable M4 Max estimate | **Not ported.** Needs this game's camera, scene/UI split and cut detection. Moving actors, particles and HUD can ghost. PR #301 estimates half a game frame of extra latency, about 16.7 ms at 30 fps. |

### Scene size investigation (open)

`DM_RENDER_SCALE` has no effect on this profile because there is no `patches.py` render-scale stub or loader state page. PR #354's higher ceiling only helps games with those stubs. Neither `DM_RESCALE` from PR #491 nor `DM_UPSCALE` from PR #405 exists in this base host. They have not been added as ineffective settings.

Read-only inspection of the supplied v131072 RomFS found `System/GameGraphics/ModelSceneExtensionParam/Default.game__gfx__ModelSceneExtensionParam.bgyml` in Bootup. Its docked resolution entries `d30fdb96` and `eeb1db9f` both declare base/final size 2560x1440 and use palette `2ebeca77`, whose top `ResolutionReduceScale` is 0.75. That gives a configured top scene size of 1920x1080. The handheld entry `0b46e9da` declares 1920x1080 with the same top fraction, giving 1440x810. Actual dynamic levels and runtime attachment sizes were not observed here.

The palette exposes a plausible engine-side control. Raising 0.75 to 1.125 or 1.5 would nominally request 2880x1620 or 3840x2160 docked scenes. Those exceed the declared base/final size. It is unknown whether the engine sizes its pools, history, dispatches and post-processing from that fraction or assumes a fraction at most 1. The fixed-resolution override below raises the declared base/final size, fixes the palette at 1.0 and handles final-size selection. Allocation and dependent-pass acceptance remain open.

PR #491 scales screen-like attachments while excluding images written by compute. Its binding correction does not cover this game's dynamic bindless texture pools. PR #405 is more complete, but conservatively demotes textures written as images and its generic upscaler bypass decodes FSR constants, not NDSR rectangles and colour transforms. Scaling only the raster targets can therefore be undone or give incorrect integer reads and compute footprints. NDSR's constants and the existing MetalFX swap describe enlargement, not a tested resolve of a scene larger than its output. A full port is not justified without gameplay and frame-capture validation.

The re-run NDSR audit verified all 22 standard compute kernels against their package hashes and resource reports. Each has one sampled texture at handle 8, one image at handle 74, read-only storage resources and push bank 24. Eleven have the half-float sRGB decode accepted by the existing spatial swap. VR and NDVE variants are different contracts. This does not identify any temporal input, jitter sequence or history reset. The host already implements NVN2 DLSS through temporal MetalFX when the game explicitly supplies depth, motion, jitter and reset data, which is a separate path from these NDSR kernels.

PR #301 derives camera motion for static world pixels and requires a build-specific camera block, scene-end marker and complete HUD separation. None is established for this profile. NDSR's lack of an exposed motion texture does not prove the game never makes motion data, but it prevents a correct temporal or interpolation port based on NDSR alone.

### Kokiri Forest comparison recipe

Run this only in the parent's gameplay pass. This task did not run it. The save source must be the parent's **Kokiri Forest Autosave** checkpoint containing `slot_00/progress.sav` and `slot_00/caption.sav`. Do not copy a save while the baseline host is writing it. Supply `SAVE_REF` and `FONT_DIR` from the parent's working baseline launch. Set `BUILD` to the existing extracted game build and `WORK_ROOT` to the external task workspace before continuing.

```sh
export REPO="$(git rev-parse --show-toplevel)"
: "${BUILD:?Set BUILD to the existing extracted game build directory}"
: "${WORK_ROOT:?Set WORK_ROOT to the external task workspace}"
export COMPARE="$WORK_ROOT/oot-quality/compare"
export TMPDIR="$WORK_ROOT/setup/scratch"
# Set these to the parent's known baseline paths before continuing.
: "${SAVE_REF:?Set SAVE_REF to the Kokiri Forest checkpoint directory}"
: "${FONT_DIR:?Set FONT_DIR to the working baseline font directory}"
test -f "$SAVE_REF/slot_00/progress.sav" && test -f "$SAVE_REF/slot_00/caption.sav"
mkdir -p "$COMPARE" "$TMPDIR"
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

## Open

- Of the task and mesh shaders, nine do not translate: eight foliage shaders stop at Ampere opcode `0x243` (packed conversion, source A `RZ`, mode `0x0000c4ff`; three of them, `604134a5262ff670`, `ecead5cd0569091f` and `fed302d791a4ba43`, are drawn in Kokiri Forest), and one at ISBERD mode `0xb8` in a task or mesh shader. The scene also asks for `d17eefaff4f0bc23`, whose code is in none of the shader archives.
- The title-only build logged 3,331 distinct mapped libraries it could not open, including 363 shaders that failed when setting up programs. A targeted build for those programs and their dependencies translated 6,132 of 6,134 shaders. The two failures are foliage compute shaders `8692b34b521225be` and `83df46a0b1b379b4`, both with Ampere opcode `0x243`.
- With `render_cond` on and the shader build still incomplete, Kokiri Forest showed a hard horizontal cut, sky colour above the horizon over the trees. The volumetric fog composite (`888c1068ac8f7043`, agl) takes a pixel whose R32Float depth copy reads above 0.9999 as sky and paints the sky lookup there. The pass that fills that copy draws with agl's full-screen vertex shader `fb1ed54be1baced1`, which that build had not reached yet, so the host skipped the draw (`draw skipped: no render pipeline`) and dropped the target's store. Retest with the stamped full build. The sky lookup's peaks (about 105, 67 and 36 in RGB) are unverified against the console.
- The opening scene calls `nvnCommandBufferDrawMeshTasksIndirect`, which the host does not implement. On `v0` the probe caught the return at `main+0x2be2dc0`; the branch builds the command buffer pointer in `x0` and the indirect argument address in `x1`. It does not set `x2` on that path. A separate sample of the first 64 bytes at the indirect address returned zeros after the call; the populated record's layout is still unverified. The title-only run logged 11 keys missing from the map. The expanded run captured seven of them before the memory failure. A byte-for-byte comparison found none of those seven code areas in the extracted shader package.
- The 3D scene's CPU cost (37–59 ms a frame, with pool walks of about 33,000 descriptors) is [resolved](../../../docs/reference/frame-rate.md#a-bindless-pool-table-rebuilt-for-every-registration). Open: the GPU's 14–21 ms a frame in Kokiri Forest, which still drops frames below 60 fps; TBDR optimizations are off for this bindless game (`DM_NVN_TBDR=1` turns them on), and attachments load and store about 330 MB a frame.
- The Nov. 4 Lichii branches offer two shader leads. Its [packed conversion lowering](https://github.com/zortos293/Lichii/commit/35c043b3efaa147d1c1afe8a52cdf19fa92b77bf) handles opcode `0x243` with source A set to `RZ` and mode `0x0000c4ff`; both of this game's failed foliage programs use two registers and mode `0x000004ff`, which needs independent verification. Its [floating-point global reduction](https://github.com/zortos293/Lichii/commit/3aa89d1cdbe58a2bd5ded06b9c615c78da2ade70) matches a separate `F32FtzRn` diagnostic in the Mac shader build, where the translator drops that operation. Neither of the two shaders in the sky lookup and draw uses those instructions or the gather opcodes from Lichii's [fog work](https://github.com/zortos293/Lichii/commit/375c4a472bd95fdfaae0de6e3f192499cd14f806).

## Internal render resolution (current, experimental, visual acceptance open)

`DM_OOT_RENDER_RES=1440` requests a 2560x1440 scene and final game image. `2160` requests 3840x2160. Unset, empty, `0` and `off` preserve the game. Restart to change it. Use docked mode (`DM_OPMODE=1`) for the initial comparisons. The override replaces every resolution entry, including handheld entries if the mode changes, while other mode-dependent tuning stays with the game. It does not change the display refresh rate or game timing.

The Mac host must load main build `e0f3ccfaf50065ae4ea01eb5aeb13b1a` rewritten with this profile's new `patches.py`. A host rebuild alone cannot add the gates to an existing rewritten main. All three gates must be present or the host logs a red warning and leaves resolution unchanged. Rewriting main is needed for activation; game shaders and `DMSH_CHAIN` are unchanged. The implementation task did not rewrite the shared game build or run the game. Treat this as an experimental engine override, not a visually accepted resolution preset.

The earlier [resolution investigation](#scene-size-investigation-open) describes the stock 0.75 palettes. `DM_RENDER_SCALE` is only read after `dm_fps_state_apply` finds a rewriter state page. Ocarina has neither that page nor a render-scale stub, so changing the variable reaches no sizing code. `DM_DYNAMIC_RESOLUTION` is a separate NieR control. Mode queries in `hle_oe.c` feed Ocarina's mode cache at `main+0xe376c0` and the renderer chooses entry 0/1/2 at `+0xe832c0`. Performance mode is cached too; the traced resolution selector reads operation mode. The game does not use the host's default display-size query to choose these dimensions.

Read-only disassembly of the supplied v131072 main extends that trace:

- `+0x31ac680` visits `BaseResolution`, `FinalImageResolution` and `ResolutionLevelPaletteType`. Its common exit at `+0x31ac7e0` still has the parameter object in x20. The first gate writes the two integer pairs at `+0x38` and `+0x40` and sets their own-value bits at `+0x4c` and `+0x4d`. Inherited settings cannot silently restore a smaller pair.
- `+0x31914f0` visits a dynamic level's `ResolutionReduceScale` and `Priority`. At its exit `+0x31915ec`, the second gate sets only the scale at x20 `+0x3c` to 1.0 and its own-value bit at `+0x40`. Priorities, load thresholds and counters remain. All levels have the same scale, so lowering the dynamic priority cannot lower the requested resolution. `+0x31c3cac` reads the scale through `+0x31917f0` and copies it into the live palette.
- `+0xe82f30` selects the resolution object, reads its base pair through `+0x31aca50`, clamps against framework dimensions and, on a separate branch, can select a fixed 1920x1080 final size. The third gate at `+0xe83050` follows both branches. It sets the final float pair at x19 `+0xe54/+0xe58` and w21, which the displaced `scvtf s0,w21` converts before the game's store at `+0xe50`. Raising the resource pair alone would leave those limits active.

The NVN layer receives the sizes and rectangles the engine emits. There is no heuristic matching of screen-shaped textures, no host viewport/scissor multiplication, no shader-coordinate patch, and no rescaling of assets or shadow maps by texture shape. The intended benefit is that the game's own code calculates depth, half-resolution effects, kernels, copy regions, viewport/scissor and UI layout from one consistent resolution. Static analysis and callback tests establish the override values, but do not prove every downstream pass follows them. That remains an explicit runtime gate.

Standard NDSR is spatial in the audited contract. Its 22 kernels expose a colour input, an output image and rectangle constants; they expose no motion-vector texture or temporal reset. The override keeps the game responsible for those rectangles and dispatch grids. Scene and final dimensions now match, so the engine may skip reconstruction or dispatch NDSR at 1:1. The current MetalFX game-upscaler swap refuses equal-sized input/output rectangles and keeps the guest shader. Do not assume `DM_UPSCALER=metalfx` supplies an identity resolve. Whether this NDSR route is valid and visually neutral at 1:1 is unverified. No temporal jitter or motion-vector scaling is invented. The separate presentation supersampling in `DM_QUALITY=max` still applies after the game's final image.

### Required Kokiri Forest checks

Start with `DM_QUALITY=off DM_UPSCALER=game DM_OPMODE=1`, explicitly clear independent quality overrides, and compare `DM_OOT_RENDER_RES=off`, `1440`, then `2160`. Keep the same save, camera and 4K backing size. Use the existing [capture recipe](#kokiri-forest-comparison-recipe) for screenshots. Enable `DM_NVN_PASSDUMP` with `DM_NVN_PASSDUMP_ALL=1` for one scene frame and retain the log before accepting a preset.

- Confirm the actual main colour and depth extents, all viewport (`O`) and scissor/draw rectangles, half/quarter buffers, image-write (`W`) dispatches and copy (`T`) regions. Expect a 2560x1440 or 3840x2160 scene, not a larger final presentation of a 1920x1080 scene. Check the log's engine-size confirmation separately from the actual attachment sizes. Check all NDSR input/output rectangles, active keys and whether the engine skips reconstruction.
- Inspect the house roof, fence, Link's silhouette and tree trunks for cleaner edges, missing strips, clipped geometry or bright dots. Pan slowly across foliage for shimmer, disappearing grass, flicker and unstable dither. Test camera motion and a room transition for any hidden history, reset or motion-vector dependency.
- Compare bloom radius and intensity around bright areas, depth-of-field focus transitions, SSAO at ground contacts, shadow edges, fog, water and blur width at the same output size. Pixel kernels or effect buffers could still assume the original dimensions. Fixed-resolution shadows should retain their intended world-space size.
- Check hearts, buttons, minimap, dialogue and small text for identical screen-relative size and placement. Open and close menus. Check screen corners and texture-copy seams. Then repeat each resolution with `DM_QUALITY=max` and, separately, the MetalFX game-upscaler option. Watch colour, gamma, halos, blur, transparency and alpha edges. A sharper screenshot alone is insufficient.

Other open risks are earlier fixed-capacity engine allocations, specialized compute dispatch limits, hidden hardcoded texel sizes, resolution inheritance or runtime settings applied after deserialization, movie/menu transitions and increased transient/resident memory. The three hooks have not been exercised inside a rewritten game process. No correct-image or 30 fps claim is made without that run. Restore `off` for any mismatch; do not hide it with a generic clamp or a forced upscaler bypass.

### Expected GPU cost (inferred, not measured)

Against the configured top docked 1920x1080 scene, 1440p has 1.778 times the scene pixels (3,686,400), and 2160p has 4 times (8,294,400). The final game image is already nominally 2560x1440 in stock docked settings, so 1440p keeps that final pixel count; 2160p raises it by 2.25 times. Raster and screen-space effects tend to follow scene pixels. Post-reconstruction/UI passes tend to follow final pixels. Geometry, CPU simulation and many shadows do not scale by those factors. The 1:1 NDSR path can change reconstruction cost independently.

A useful planning model is `fixed + scene_factor * scene_cost + final_factor * final_cost + reconstruction_cost`, with factors `(1.778, 1)` for 1440p and `(4, 2.25)` for 2160p. Memory depends on actual engine allocations, aliasing and live buffer sizes; do not multiply total resident memory by the scene factor. The M4 Max and 30 fps cap do not establish enough headroom for either setting. Measure GPU pass costs and memory after visual acceptance. Presentation supersampling from `DM_QUALITY=max` is a separate additional cost.

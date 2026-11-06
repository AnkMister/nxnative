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

- Open experiment: [absolute direct-present cadence](../../../docs/reference/frame-rate.md#absolute-cadence-experiment-for-direct-presentation) is available with `DM_PRESENT_ABSOLUTE=1` on the Mac. It is off by default and has no gameplay latency result yet.

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

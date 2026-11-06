# Cheemu Ocarina source harvest

Base: `oot-latest` at `041234275097b1075ead88940807f51216b22363`.
Fork: `cheemu/kid-with-sword-remake` at `26a2646e38e888844bb37fea53ca8ed0ce5857bb`.
Isolated worktree: `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-cheemu-wt`.
Main checkout was read only; no push or PR. No game files, community binaries or translator DLLs were copied or executed.

All 31 non-merge commits classified: 17 HAVE, 2 TAKE, 12 SKIP. HAVE identifies equivalent useful behavior, not an identical full commit; incidental binary/profile/doc changes remain excluded.

| Fork SHA | Decision | Evidence / port decision |
|---|---|---|
| `06f47f57` | HAVE | b1d7c707: F2IP and task payload reads in the official source. |
| `e3f8ef8c` | HAVE | b1d7c707: F2IP rounding and RZ source handling. |
| `9cb1fe2a` | HAVE | b1d7c707: indirect task/mesh replay and atomic image handling; keep the newer MDX implementation. |
| `10e53364` | HAVE | b1d7c707: NDVE discovery, eventfd/offline services and no virtual input startup. |
| `9fb44679` | HAVE | b1d7c707: official profile, conditional clears, NVN2 stage discovery and residency. |
| `ee9b7765` | HAVE | b1d7c707 and a0f5e939: pool registration/storage notes and incremental table patching supersede the early implementation. |
| `46975a20` | HAVE | c8521eeb: g_gww intervals retain wide writes across submissions. |
| `bd766c4d` | HAVE | b1d7c707: one ListVirtualInputDevices answer; newer SDK input-stream handling remains intact. |
| `d7f5b403` | HAVE | b1d7c707: newer raw-table ABI covers the reported pool capacity failure. The dynamic allocation scheme is superseded, not copied. |
| `02bd6a3d` | HAVE | 04df08d4: ATOMG.CAS 0x3a9 in source, already integrated. |
| `fa26fa93` | HAVE | 04df08d4 and 87564a6b: deep bracket Metal compile limit already raised. |
| `d0952dc2` | HAVE | b1d7c707: float ADD uses EmitAtomicAddF32 compare-and-swap instead of being dropped. |
| `04aba437` | SKIP | Translator binary/chain rebuild. Never import its DLLs. |
| `72275f7a` | SKIP | FPS overlay and launcher/UI plumbing only; no Ocarina frame-time fix. Avoid expanding the host/frontend interface for this harvest. |
| `cd94ea37` | SKIP | Window paused label is UX feedback, not a hang fix or a Mac performance improvement. |
| `8bca33fb` | SKIP | Selective bracket compiler convention changes shader-chain tools. Existing unconditional raised limit handles the Ocarina nesting; do not change chain. |
| `e2a20428` | SKIP | WIP Opus/thread/video diagnostic logging, not an audio fix; extra hot-path logging is unsuitable for hitch reduction. |
| `2c4a08f4` | SKIP | Partial diagnostic follow-up and game note. Does not repair the guest Opus idle periods. |
| `5ec8a62b` | HAVE | b1d7c707: ndsr_shaders advances 8 bytes past a data entry, then takes control/code together. Donor synthetic odd-entry tests added and pass for both header offsets. |
| `b114a464` | SKIP | Cause/documentation update only; no source behavior to port. |
| `34d04efb` | HAVE | b1d7c707: EmitAtomicOp routes AtomSize.F32FtzRn ADD through EmitAtomicAddF32 CAS retry; exposure sums are retained. See source equivalence limits below. |
| `ef72f7c5` | HAVE | b1d7c707: official raw global pool table and ABI supersede the fork A-1 design; preserve current chain. |
| `84b13565` | SKIP | Merged translator DLL rebuild and chain lock/header only. No binaries imported. |
| `a3844dc6` | HAVE | 6121fd75, retained by a0f5e939: pool_table_take/give reuse resident buffers after g_done reaches their fence. Current bounded cache has 16 spares rounded to 64 KiB instead of 64 exact-size slots. |
| `58adddbd` | SKIP | Empty code diff: speculative frame-generation design note, no implemented feature. |
| `ad998585` | SKIP | Mixed iPhone memory/default changes, guest anonymous remapping, lossy/mip-discard features, launcher replacement packaging and shader-chain edits. Useful upstream parts already exist (b1d7c707, 6121fd75, a0f5e939; profile already uses segment GPU timestamps). Do not import this broad bundle or its default-on upscale-chain skipping. |
| `5314fd48` | HAVE | 87564a6b already records/replays RO_R_MESH_IND, fixing the relevant indirect mesh selector boundary. Skip incidental app-overlay packaging, resolution generator and fork build diary. |
| `0803c304` | SKIP | iPhone Metal 4 pipeline default and build-history notes only. |
| `2de238f3` | TAKE | Profile-only frame-controller hook, composed with the existing render-scale hook. Preserve registers; keep fps_target absent/default 0. Manual DM_FPS_TARGET=30/60 opts in after repacking main. Skip iPhone touch layout. |
| `c2218343` | SKIP | Fix is specific to g_up_chain_in early-stage skipping introduced by ad998585. That mechanism and upscaler_chain are absent here. #1459 uses the retained per-shader path; no earlier stages are skipped. Importing that prerequisite would introduce the black-frame failure being avoided. No need for this fallback on the current path. |
| `26a2646e` | TAKE | Host-only mode selection for explicitly supplied DM_ROMFS_OVERLAY roots. Do not ship the resolution overlay generator/data or alter console mode, dynamic resolution, or scaling defaults. |

## Ports and defaults

1. `2de238f3`: reuse the existing build-gated FRAME_STEP entry and state page. `apply` emits both the render-scale ceiling and controller hook. The original instruction is asserted before patching. Unlike the donor, save/restore x9, x16 and x17; x0 receives the original mov result. ARM64 execution checks target 0/30/60, steps 0/1/2/3, interval/fps stores, counter and untouched registers/flags. No profile fps_target is added: the game's choice remains the default. Repack main before using manual `DM_FPS_TARGET=30` or `60`. The source addresses and controller semantics originate in the fork's analysis; local disassembly against game files and actual game-speed/cutscene acceptance remain open.
2. `26a2646e`: each configured overlay root searches its existing mode directory before the root, maintaining ordered fallback to RomFS. The selected mode is captured at mount. Tests cover handheld/docked, later mode changes without remount, root/base fallback and existing filesystem operations. No resolution data or generator is imported. This host mechanism is inert without DM_ROMFS_OVERLAY.
3. Retain the synthetic `5ec8a62b` NDSR regression fixture as executable evidence of HAVE. No splitter source or shader tables change.

No game.tsv defaults, GPU implementation, shader tools, ABI, chain header/lock or translator binary changes. DM_AOT=0, the requested launch configuration SERIAL_HELD=1, and upscaler off are preserved: this harvest does not edit launch configuration or defaults. The pre-existing DM_NVN_SERIAL_HELD environment switch is not made default-on in source. No iPhone-only setting is imported.

## Important source checks

- Float atomics (`34d04efb`): inspect `dm/third_party/ryujinx/src/Ryujinx.Graphics.Shader/Instructions/InstEmitMemory.cs`: F32FtzRn ADD dispatches to EmitAtomicAddF32; load, FPAdd, AtomicCompareAndSwap and retry all exist in b1d7c707 and remain in HEAD. Thus the dropped-add cause of washed-out scenes is fixed in source. The donor explicitly calls FlushDenormal around operands/result; the official source does not use that identical lowering here. This is functional equivalence for retaining the exposure sum, not proof of identical subnormal semantics or local outdoor rendering. No translator change/rebuild is made.
- Retired tables (`a3844dc6`): pool_table_give stamps g_fence+1; pool_table_take only reuses after g_done passes it. It keeps residency and caps retained buffers. Both table patch and rebuild paths use it. Do not replace this newer implementation with the old fork cache.
- NDSR (`5ec8a62b`): all 3 donor tests pass, including data entries between programs, two such shifts and both +0x10/+0x14 header starts. The 4-byte payload occupies an 8-byte record; the current 8-byte fallback stride covers it.
- MetalFX (`c2218343`): no g_up_chain_in or early-stage suppression is present. Skipping the donor fix does not remove a guard from #1459. Any future adoption of whole-chain skipping must include refusal/final-stage detection and visual validation. It may lose one frame in the donor fallback, so it is not a no-black-frame guarantee.
- Shader-chain proposals excluded: dynamic raw-table ABI variants, selective bracket tool changes, optimizer/translator changes and all DLL rebuilds. Existing equivalent source is named above; missing alternatives require a separate shader-chain task and matching rebuild, not this harvest.

## Verification

- PASS: 34 Python tests, zero skips, including test_oot_render_scale.py (actual Unicorn ARM64 execution), donor test_split_ndsr_entries.py, test_docs.py and test_nsp_chain.py.
- PASS: filesystem programs t_fs 148, t_fs_case 51, t_fs_directory 19, t_fs_commit_list 98 and t_save_sync 54 checks: 370 checks, zero failures.
- PASS: `taskpolicy -b nice -n 19 make -j6 -C dm/host GAME=0400486024DEC000 dmhost`. Existing compiler warnings remain in host-build.log; this is not a warning-free build claim.
- PASS: git diff --check. Chain files and dmsh_xlate_bin have no diff against 04123427.
- BLOCKED: five-game runtime harness exited 2 before running because REGRESS_ROOT and REGRESS_GAMES are unset. Requested games: Ocarina (profile/controller and overlays), Mario Kart World (NVN2 and RomFS), Tears of the Kingdom and Breath of the Wild (existing frame-step and shared RomFS consumers), Star Fox (NVN2/RomFS). No game, shader rebuild, FPS measurement, visual proof, iOS build or device test was run.
- Initial docs check found the generated patch index stale after adding the hook; regenerated it and reran successfully. Initial NDSR fixture invocation lacked DM_GAME; final invocation sets it explicitly. Neither initial failure is hidden as a pass.

Commands use TMPDIR=harvest-audit/scratch. Heavy builds/tests use taskpolicy -b nice -n 19, at most -j6. No pnpm dependencies installed. Unicorn 2.1.4 was published 2025-09-09 (verified with PyPI JSON before installation), then selected via `uv run --no-project --with unicorn==2.1.4 --exclude-newer '1 week'`; it has no extra dependencies. Standard uv cache reused; no private cache.

## Storage and handoff

Generated roots: dm/host/gen, dm/host/dmhost, dm/host/tests/build, harvest-audit/scratch. The scratch directory is empty. Keep host binary and isolated build roots for the requested build and pending gameplay continuation. Source, report and logs are committed; no generated build binaries are committed. No generated storage removed, no other checkout/dependency/cache touched, no processes stopped. No external paths were used for temporary work.

Authors credited: cheemu21 for the two selected source ports; Pedro Nascimento for the NDSR fixture. No subagents were started by this implementation sub-agent. Independent parent review remains separate.

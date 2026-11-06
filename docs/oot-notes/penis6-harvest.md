# Community Ocarina source harvest

This report audits the already-fetched `penis6/oot2` at `e80de39fd65d9bb24b8922843c720aac8bb823fc` against `oot-next` at `3e7a7f16c940e5d580c09960b477af176c903e2b`. The requested range contains **84**, not 83, non-merge commits with the fetched refs. Rows 1-83 cover the stated set; row 84 is the additional requested `e80de39f`. No fetch changed that range during this task.

The implementation is isolated in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-next2-wt`, branch `oot-next2`. The protected `pr1444-main-wt` was not written. There is no push, PR, game-app build, game launch, signing or device installation.

Decisions total 42 HAVE, 11 TAKE and 31 SKIP. HAVE means the relevant Ocarina behavior has an existing equivalent at the named SHA, not that every incidental file, diagnostic or profile value in that mixed commit is identical. TAKE means source selected for the port; it does not assert measured FPS gain. SKIP records an explicit scope, safety or architectural reason.

## What gives 60 fps

There is no newly discovered 60 fps unlock in these commits. The game already targets 60. The community note documents a 60.0 fps **title movie** window on an Apple M5, obtained by removing raw-write-log/pool-lookup overhead, with Kokiri Forest described separately as 16-21 ms medians on that M5. Its later commit messages on an M4 Pro report 27.1 -> 24.9 ms from dispatch overlap, 24.9 -> 24.5 ms from raw-load quads, then 24.5 -> 22.5 ms from replacing the four-dispatch NDSR chain with MetalFX. A 22.5 ms frame is about 44 fps. These are source-recorded claims from other hardware, not local measurements or a locked 60 proof on M4 Max.

Our inherited upstream `b1d7c707` and `6121fd75` separately report Kokiri Forest 60 fps on an M6 at up to 1536x864 internal resolution. Their useful mechanisms are pool read/registration tracking, observed depth-reader classification, GPU-aware segment commits, and mapped pipeline archives. They are already in oot-next. Optional MetalFX can trade the game's upscaling work for cheaper spatial scaling, but our p1459 path remains off unless requested and is not the community's default-on hard-coded four-dispatch replacement. Neither refresh rate nor present caps creates extra game frames. No local gameplay benchmark was run, so **locked 60 on this harvested branch is unverified**.

## Complete classification

| # | Community SHA | Decision | Existing SHA or reason and resolution |
|---:|---|---|---|
| 1 | `ff1367d1` | SKIP | The retained-object wait rewrite changes kernel handle lifetime and cancellation globally. No Ocarina failure tied to that contract was established; it is not the Saria GPU-memory fix. |
| 2 | `6e6bb41f` | SKIP | Microphone capture, permissions and input service implementations add no demonstrated Ocarina playback gain. Keep the existing no-virtual-input startup answer. |
| 3 | `98b6c83c` | SKIP | Mixed builder/API expansion. Existing pool access checks and the selected null-getter port cover the relevant boundary. No Ocarina builder-state failure justifies the remaining broad prototype changes. |
| 4 | `06f47f57` | HAVE | b1d7c707 implements F2IP and the task payload read in the official Ocarina base. Keep the source-built translator. |
| 5 | `e3f8ef8c` | HAVE | b1d7c707 implements F2IP rounding and the RZ source form used by foliage. Do not replace the official opcode handler. |
| 6 | `9cb1fe2a` | HAVE | b1d7c707 supplies native indirect task/mesh draws through MDX and image atomic handling; 1ecc150e retains the alias/view repairs. Its IXC implementation is not copied over MDX. |
| 7 | `4651ffb7` | SKIP | Transfer-memory ownership rewrite is a separate kernel/service contract. No Ocarina crash or memory gain from this patch was demonstrated. |
| 8 | `a324cab3` | SKIP | Adds native asynchronous prepo services. b1d7c707 already answers the Ocarina startup/report path offline; extra service machinery gives no demonstrated gain here. |
| 9 | `10e53364` | HAVE | b1d7c707 includes the official Ocarina profile, NDVE shader discovery, eventfd/offline services and no-virtual-input answer. Keep the newer official profile and tables. |
| 10 | `9fb44679` | HAVE | b1d7c707 covers conditional clears, task/mesh stage discovery, movie shaders and residency with the official game tables. No replacement profile or bundled binaries. |
| 11 | `ee9b7765` | HAVE | b1d7c707 supplies registration/pool read tracking and descriptor lifetime handling; 6121fd75 reuses tables. Keep the newer official table implementation. |
| 12 | `fc815c37` | HAVE | b1d7c707 has large-pool chunking and texture-only upload behavior. Its Ocarina-relevant memory solution is retained; do not turn on PRAGMATA mip dropping. |
| 13 | `ac024428` | SKIP | Lint-baseline refresh has no game behavior. Importing another branch baseline would hide local findings. |
| 14 | `46975a20` | HAVE | c8521eeb already keeps wide writes in g_gww intervals across submissions, with conservative overflow. The larger 128-slot variant has no established additional M4 Max gain. |
| 15 | `c7264fee` | SKIP | Alternate Ampere ALU corrections need independent ISA fixtures and a wider translator review. No Ocarina shader failure requiring these extra opcode changes was established in the official base. |
| 16 | `b6367705` | SKIP | Alternate NDVE scaling path changes movie conversion and color assumptions. No M4 Max title-movie bottleneck requiring replacement of the existing decoder/renderer was established. |
| 17 | `9e141cc8` | HAVE | b1d7c707 retains conservative bindless store lookahead. Keep it with the upstream pool-read tracking rather than import an older scanner. |
| 18 | `6941aa84` | HAVE | b1d7c707 preserves inputs of a multi-output producer with another live destination in Optimizer.RemoveNode. Equivalent wind/foliage liveness fix. |
| 19 | `d7a43c2a` | HAVE | 52190603 scans Update then UpdateImpl for the SDK lock offset, and is already in oot-next ancestry. It supersedes the branch-specific scan. |
| 20 | `e9d2e537` | SKIP | Star Fox sRGB image handling is outside the demonstrated Ocarina delta. Retain the existing shared-view and pixel-class logic; require a dedicated color/image fixture before broadening it. |
| 21 | `6542d07e` | SKIP | Graphics-scale tier change was measured on Star Fox. It can increase render resolution and GPU load; no Ocarina need was established. |
| 22 | `0b91ce92` | SKIP | Star Fox display-layer sizing and DLSS logging do not establish an Ocarina gain and can increase output resolution. Keep the existing presentation integration. |
| 23 | `5ec8a62b` | HAVE | b1d7c707 walks NDSR entries individually and discovers the missing variable-ratio programs. Keep current NDSR and NDVE readers. |
| 24 | `5292ae49` | HAVE | a2d39a26 removes st_dev from RomFS identity. Already merged into oot-next. |
| 25 | `2e1f4953` | SKIP | Renames packing scratch folders for Spotlight. This task does not pack an app; task scratch is already explicitly isolated. No runtime improvement. |
| 26 | `3f4d54b9` | SKIP | Shader-cache summary text only. No FPS, memory or correctness change in the running game. |
| 27 | `072f8674` | TAKE | Compile Mac and iOS Metal with -fbracket-depth=1024 so deeply nested compute shaders are accepted. Compiler convention changes the chain; source only. |
| 28 | `34d04efb` | HAVE | b1d7c707 lowers RED/ATOMG float-add atomics through compare-and-swap with denormal handling. Keep the official exposure fix. |
| 29 | `eaa7a1da` | HAVE | b1d7c707 expands the official raw table to 8192 entries, covering the reported 4100-4522 Ocarina pools, and integrates its ownership. The community dynamic-capacity variant is not identical and is not needed for the cited failure. |
| 30 | `7cd6750b` | HAVE | 1ecc150e and 39805173 retain native mesh preparation and draw-preserving worker behavior. Do not replace them with the older prewarm path. |
| 31 | `7f5f2fcf` | HAVE | 3d3de7f2 and e7f4cc4c retain GPU-loss stop and safety handling, with the later integration in 1ecc150e. Keep the existing stop policy. |
| 32 | `b44bcafd` | HAVE | eab0aaac is the same heap/alias-region sizing correction in upstream ancestry. |
| 33 | `60632a6e` | HAVE | e9d1ef2c is the same nso_match.recipe plain-dict lint correction. |
| 34 | `7536af7b` | HAVE | b1d7c707 has one ListVirtualInputDevices hook. There is no duplicate hook to remove in this base. |
| 35 | `b403f4cc` | SKIP | Translator binary refresh. No community executable or DLL is copied or executed. |
| 36 | `2d6f86f8` | SKIP | Unconditional LDSM barriers were written for the older translator. The retained TensorPass/MatrixLoad path has different lowering and reuse analysis. Do not insert barriers into it without its own translator/GPU acceptance; no M4 Max movie fault was reproduced. |
| 37 | `d234d4f6` | SKIP | dav1d software AV1 frame parallelism targets older Macs. M4 Max uses the existing hardware VideoToolbox path. Preserve the existing decoder-worker ownership from 75c1a8cf. |
| 38 | `3b588ca6` | SKIP | Movie-clock frame dropping depends on the previous software-decoder queue changes and changes playback policy. No M4 Max decode shortfall established. |
| 39 | `3604b403` | TAKE | The official base lacks opcode 0x3a9 despite other atomic support. Add the 32-bit ATOMG.CAS handler from source; refuse unsupported encodings and test compare/replacement operands. |
| 40 | `83d10be6` | SKIP | Translator binary refresh. Rebuild our translator from source instead. |
| 41 | `e3b792c1` | HAVE | 1ecc150e retains command/submission shader context and f956ffb0 fault attribution. Equivalent diagnostics are already present. |
| 42 | `005ed817` | SKIP | Documents DM_CV_LATE for an unselected movie frame-drop implementation. Do not advertise an unsupported switch. |
| 43 | `235b7c41` | SKIP | Unsigned app-packing behavior is outside this task, which must not build the game app. No runtime gain. |
| 44 | `50f10c26` | HAVE | b1d7c707 and the integrated test baseline already contain a complete, compilable t_cpu_tex fixture. No stale closing-brace patch needed. |
| 45 | `822ee586` | HAVE | b1d7c707 supplies the official addressed-pool/residency handling; 1ecc150e keeps optional alias/release repairs. Keep official profile sizing and movies, rather than the older profile and DM_MOVIE_SKIP portions. |
| 46 | `417326f3` | SKIP | 417326f3 contains untrusted translator binaries. They are never used. |
| 47 | `16e86fdc` | TAKE | Track GPU writes by texture storage range instead of rejecting every CPU texture in a mixed pool. Remove ranges with pool finalization. Port CPU terrain/storage tests. |
| 48 | `5122c24d` | HAVE | 1ecc150e has the pre-commit residency guard and the retained DM_SAFE_GPU path uses a stricter budget. Do not replace it with a second 95-percent guard. |
| 49 | `8cf26912` | SKIP | Do not copy the community timer drain across this branch's submission/residency ownership boundaries. It reads mutable open-submission state off-thread and commits residency from the timer. DM_FOCUS_KEEP=1 avoids the cited idle route in the selected play configuration. The underlying no-submit retirement backlog remains open; existing safety is not a fix for it. |
| 50 | `a885f4be` | HAVE | b1d7c707 exposes only address-used pools to raw shaders via mtl_pool_addressed/addr_meets. Keep the official selective table. |
| 51 | `8f5dc5d9` | HAVE | b1d7c707 already supplies the reviewed addressed-pool implementation this backout was preparing for. Applying the historical backout would remove useful code. |
| 52 | `cb323d6d` | HAVE | 69cb9b6e stores and returns an NVN event's pool and offset. Exact equivalent is in oot-next ancestry. |
| 53 | `5466fab0` | HAVE | c83c48f2 retains compatible cube/array views and the current image usage path refuses compressed shader-write usage. Keep it with 1ecc150e owner-aware upgrades. |
| 54 | `e81bfaba` | HAVE | 6121fd75 makes defer_drain linear. No quadratic middle-removal loop remains. |
| 55 | `7780a985` | HAVE | b1d7c707 includes chunk hints and per-entry write bitmap logging for the official raw table. Do not mix a community dynamic-count ABI into this host. |
| 56 | `039a3905` | TAKE | Cap the initial shared-event wait at 100 ms, then recheck feedback. Preserve our remaining-time-budget fix. The older-SDK protocol needed by the neighboring chunk port is retained too. |
| 57 | `36f498a3` | SKIP | Runtime demand-shader build workflow is unnecessary for the selected full-library build and introduces a separate tool/runtime protocol. No gain once libraries are complete. |
| 58 | `1c1d4533` | TAKE | Retire redundant chunk buffers when an address-exposed pool acquires its whole-pool mapping. Preserve addr_meets so unexposed pools stay chunked. |
| 59 | `58c001d9` | TAKE | Unwrap cached NvPkg by its Objective-C class, independently of CPU-write membership. This closes the packaged-holder crash boundary while preserving lifetime fixes. |
| 60 | `f5371478` | HAVE | 6121fd75 reuses pool table buffers and tracks resolved texture types; b1d7c707 supplies pool read selection. Equivalent reduction in redundant table work is already present. |
| 61 | `168290c6` | TAKE | Add the missing RO_R_MESH_IND recording and replay method. Native indirect mesh draws otherwise send an unsupported selector when the encode thread is enabled. |
| 62 | `f684c7eb` | SKIP | Commit-time table-word replacement assumes the community dynamic table and its page-based logging. Our raw table uses per-entry bitmap logs tied to a specific table. Swapping just the table would misattribute writes. A correct joint table/log update needs a separate ownership change; not silently enabled here. |
| 63 | `449cb253` | SKIP | Additional geometry timestamp heap is diagnostic overhead, not a demonstrated FPS or picture improvement. |
| 64 | `5cb7d718` | HAVE | 6121fd75 uses observed pool depth reads (pool_ds_read), which solves the pass-splitting problem without assuming that every depth-writing draw cannot sample depth. Keep the more precise rule. |
| 65 | `64a114a5` | SKIP | This patch optimizes community IXC mesh conversions. Our b1d7c707 routes mesh records through MDX, not IXC. Do not transplant IXC epoch/cache assumptions into MDX. A separate MDX optimization would need its own measured benefit and invalidation tests. |
| 66 | `45996122` | HAVE | 1ecc150e retains O(1) serial-held counts, including view ancestors and local lifetime repairs. Keep its opt-in control rather than overwrite it with the earlier counter implementation. |
| 67 | `5208584a` | TAKE | Port consecutive game-dispatch overlap with game/host/copy ordering tests. Use only DM_NVN_DISPATCH_OVERLAP=1, default off; no new per-game profile key or default-on change. |
| 68 | `a9120fae` | TAKE | Make null buffer and pool getters return zero or NULL. Preserve CPU_NO_ACCESS map refusal and add null-input tests. |
| 69 | `15436340` | HAVE | 1ecc150e supplies nvn_dirty_discard for the retained release path, with stricter local eligibility checks. Do not add a second discard API. |
| 70 | `8a94c1fc` | SKIP | Alternate raw-load quad transformation assumes a different MSL helper signature. oot-next already has 3e7a7f16/#1464 range reuse. Do not replace that tested transform for an unmeasured extra community 0.4 ms claim. |
| 71 | `c1527492` | HAVE | 133d4a0c/p1459 is the selected alternative. Keep DM_UPSCALER=metalfx as the sole opt-in scaler with shader-derived color handling and existing fences. The community DM_NDSR hard-coded four-dispatch replacement defaults to MetalFX and exposes manual color overrides; it is not imported. Their 2 ms claim is not established for our alternative. |
| 72 | `cd3522dd` | HAVE | 1ecc150e includes optional texture-page release and GPU donor copies, with stronger local file-backed/shared-storage exclusions. Leave DM_TEX_RELEASE off. |
| 73 | `6c2bdd8e` | SKIP | The 4096 cap and permanent draw suppression hide bad mesh records and can drop legitimate work. Existing DM_SAFE_GPU stops on faults; the current optional MDX validation remains. Do not add another unconditional clamp. |
| 74 | `b99e2dda` | HAVE | 1ecc150e has the pool placement heap port with allocation checks, owner-aware upgrades and no self-copy. DM_NVN_POOL_HEAP=1 remains opt-in. The reported 3 GB to 0.7 GB saving is not measured on this branch. |
| 75 | `5ef30214` | HAVE | 1ecc150e has the Saria-related live-only alias ages/retired-key suppression. It additionally preserves the stricter safety budget, skips heap-backed textures and refuses destructive-release combinations. DM_NVN_ALIAS_RETIRE=1 remains opt-in. No Saria playthrough proves this combined branch yet. |
| 76 | `03e58c99` | SKIP | Switch documentation for unselected mesh clamp/breaker code. Keep only switches the host implements. |
| 77 | `ce1662b6` | HAVE | 1168bf3c already stubs front_picture_shape in loader-only fixtures. |
| 78 | `f2b24298` | SKIP | Native ultrawide adds build-gated game patches and increases rendering load. It is outside the requested M4 Max performance/stability harvest. |
| 79 | `c9d5312b` | HAVE | 8feddfee already answers IsOunceVibrationDeviceMounted in the official base. |
| 80 | `9f6ad246` | HAVE | 6121fd75 sets mem_map_limit on in the official Ocarina profile. Preserve it. |
| 81 | `c32dded1` | SKIP | This stub fixes the community-only t_vi_display fixture added by its display changes. That fixture is absent from oot-next, so there is nothing to link or repair here. |
| 82 | `6517f8b9` | TAKE | Port mesh/pixel output padding, point topology and point-size decoding, with the 1284 added shader-pair rows. Preserve the current builder, cache dependency logic and all upstream tables. |
| 83 | `47c390f7` | HAVE | 39805173 already excludes mesh_stage reflections from pso_offline vertex planning. Keep that guard. |
| 84 | `e80de39f` | TAKE | Apply the same mesh exclusion in runtime pre_desc so a mesh pair does not invalidate the entire vertex archive during probing. |

## Source ports and conflict resolutions

The missing `0907c1e2` was initially applied as `d1f25de6`. Tests exposed its dependency on `42658776`, the split-archive predecessor absent from oot-next. The final adaptation uses this branch's one-file-per-architecture output (`dst`) rather than a nonexistent `saved['parts']`. The regression verifies that a reused archive loses obsolete split parts, while the selected archive remains and no compiler is called. Existing cleanup still removes architectures no longer requested. No unrelated split-archive implementation was pulled in.

`16e86fdc` conflicted at CopyBufferToTexture and at the CPU-texture test main. The resolution keeps our `rec_copy` state/stride snapshot and applies range tracking to its snapshotted destination. It also keeps every existing copied-object lifetime assertion and adds the range cases. The unconflicted CPU-storage fixture follows the renamed range API.

`58c001d9` conflicted on the RED_ONCE array bound and the same fixture main. The resolution preserves the larger local bound of 157 and combines the new packaged-holder check with all prior tests. The type check is independent of membership in the CPU-written set.

`1c1d4533` conflicted in gmem_map. The resolution calls big_full only for addr_meets pools. Unexposed pools remain chunked; promoted pools retire chunk buffers through the existing deferred GPU fence and clear the obsolete chunk index. The compatibility protocol for macOS/iOS 27 temporal scaler offsets lets older SDK headers compile the existing setters, without changing their OS availability check.

`5208584a` applied to the host cleanly. Its profile key and game.tsv default were deliberately omitted. The general environment switch is off unless its value is exactly `1`. No second per-game scheduling control was added. Host dispatches, copies, inline updates and explicit game barriers retain ordering. Tests include both encoder modes and the default-off path.

`039a3905` was ported only at the event wait. Our finite elapsed-budget accounting stays intact. A synthetic unsignaled-event case completes via feedback; finite and infinite timeout cases cover the 100 ms transition.

`168290c6` applied without a source conflict. A recorder probe checks that the native indirect selector records and replays the GPU address and object/mesh threadgroup widths. This closes the unsupported-selector boundary, independent of game shader content.

`3604b403` adds the missing ATOMG.CAS opcode in the source translator. Inspection confirmed that the other global atomic handlers did not imply support for opcode 0x3a9. Its synthetic translation test traces expected and replacement operands through the generated helper. The DLLs were rebuilt again after this source change.

`6517f8b9` applied to the current shader builder, mesh wrapper and splitter without source conflicts. Its 1284 added mesh/pixel pair rows were merged into the existing official table, not used to replace it. Tests check point topology and initialization of missing outputs in both depth entry points. `47c390f7` was already equivalent in our planner. `e80de39f` adds the corresponding runtime archive-probe guard.

`a9120fae` adds only null-safe getters and preserves CPU_NO_ACCESS behavior. `072f8674` adds the bracket-depth compiler flag for Mac and iOS. No community DLL, launcher, SPIRV-Cross binary or other executable was imported. The local translator and launcher were rebuilt from this branch's source. All 57 local NuGet feed packages were checked against their saved publish dates (older than seven days) and SHA256 values before offline restore. The four restored project package sets were checked against that allowlist. The source-built DLL fingerprints were recorded in dmsh_chain.lock; the header was regenerated after the final fingerprints were recorded.

## Validation

The initial chain check correctly rejected a stale header before regeneration. The initial archive-reuse test exposed the missing split-manifest prerequisite, which was corrected. These failures are not reported as final passes.

Full shader rebuild and multi-game runtime acceptance remain blocked by storage and local harness availability. The existing Ocarina cache is 27 GB; the same volume had about 5.8 GiB free before builds. It is unsafe to start another isolated full cache there. No existing cache or unrelated storage was removed to make room. The repeatable full-build preflight records current free bytes and refuses insufficient headroom before writing shader output. No complete new c1_full.tsv/cb_extent.tsv or inputs.tsv stamp is claimed.

Only Ocarina assets are present under the local games root. Five local games cannot be tested. The relevant follow-up coverage is Ocarina (mixed CPU/GPU textures and mesh), Mario Kart World (mesh and terrain storage), Tears of the Kingdom (CPU texture updates), Breath of the Wild (shared target/deferred lifetime), and Star Fox (compute ordering and image views). Only Ocarina is local, and its full shader rebuild is blocked. Synthetic checks and a host compile do not establish runtime acceptance of those games.

## Storage and handoff

The new worktree is preserved. Source diffs, classification metadata, compiler logs, test logs and the source-built translator output are under `harvest-audit`. The local NuGet feed/cache was reused without changing package versions. Task scratch is under `harvest-audit/scratch`; TMPDIR never points to /tmp or /private/tmp. The untouched 27 GB play cache was read only for size and as the candidate input location for the deferred shader build. Generated storage was retained for review and the blocked shader-build continuation. Exact roots are listed in `harvest-audit/generated-roots.json`. No generated roots were removed. Compiler outputs are isolated from the protected play worktree. No unrelated processes were stopped.

## Final verification results

- The combined Python suite passed 173 tests, including real source-built translator invocations, the new ATOMG.CAS case, mesh stage Metal compilation, pair padding, archive planning/reuse, raw-range transforms, zstd split tests, test_docs.py and test_nsp_chain.py. The inherited raw-range fixture emits a non-failing unclosed-file ResourceWarning.
- The native suite passed all 22 runs under low process priority. Fifteen texture/renderer runs cover both encoder modes for CPU textures, storage and pool promotion; three dispatch-overlap modes include default off. Existing alias, heap, image and view regressions pass. Three GPU performance-order runs pass. Four additional CPU completion runs cross fast-wake on/off with wait-ledger on/off and check the new event-to-feedback timeout cases.
- Those 22 native runs contain 2007 assertions, with zero failures. Detailed modes, exit codes and log paths are in native-results.json, perf-results.json and wait-budget-results.json.
- `make -j2 -C dm/host GAME=0400486024DEC000 dmhost` passed on the final chain. The host path, size and SHA256 are in host-artifact.json. The compiler emitted existing warnings; the build is not a warning-free claim. No game app was built.
- `tool_lock.py --check-tools` passed after rebuilding the translator and launcher from source. Final chain is `97456a242c1d`. The Mac and iOS compiler conventions are stamped; no iOS game library or IPA was built.
- All 1284 added mesh/pixel pairs name keys present in our current shader map. No community shader binaries were used.
- `git diff --check` passed. The final docs and chain checks were repeated after formatting the six new reference entries and regenerating the symptom index.
- Python lint did not pass its repository-wide ratchet: 391 findings versus 384 in its baseline, seven above the ratchet. Every reported diagnostic location maps to an unchanged oot-next source line, verified in lint-inherited.json. No baseline was expanded and no unrelated lint code was changed.
- C compilation-database generation passed. clang-tidy was unavailable, so C lint is unverified; no dependency was installed to bypass that gate.
- `regress.py check --games 0400486024DEC000,0400C3F00006E000,0100F2C0115B6000,01007EF00011E000,0400E88025B1A000 --jobs 2` exited 2 before running because REGRESS_ROOT and REGRESS_GAMES are not configured. Only Ocarina assets are local. No five-game runtime pass is claimed.
- The full shader build preflight exited 2 before writing output. It measured about 5.5 GiB free against a conservative 32 GiB minimum, based on the existing 27 GB cache plus reserve. Run `harvest-audit/run-full-shaders.sh` after providing disk headroom to build the new full Mac libraries with J=6. This gate and gameplay acceptance remain open. Parent-task independent review is also not supplied by this implementation sub-agent.

All heavy commands used `taskpolicy -b nice -n 19`. Build parallelism never exceeded -j6; .NET and native verification used two workers. TMPDIR always named the explicit task scratch directory. No new online dependency resolution occurred; the existing audited local feed and standard uv download cache were reused. Source-built DLLs, the chain lock/header, source changes, tests and this report are committed locally with the requested AnkMister identity. There is no push or PR.

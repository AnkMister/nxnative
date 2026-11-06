# Harvest 3 for the Ocarina lead

Branch `oot-r3` starts at `oot-play` `e8c3bc222b06413347d533fca7e060a69943c57a`.
Initial implementation head before this report was `3febd0b7`. Follow-up implementation head is `a80677b6`. All commits use AnkMister's requested identity. No push, GitHub comment, PR, dependency install or third-party executable run occurred.

The initial delivery was static while the user's game ran as PID 92070. The follow-up was compiled and tested after the user explicitly allowed background builds during play. Full host, shader and gameplay acceptance remain pending. Nothing in the running app, its game folder, its environment or the protected baseline checkout was changed.

## Item decisions

| Item | Status | Overlap | Verdict | Host-only or shader-chain |
|---|---|---|---|---|
| #1453, `3d700bb7` | Ported in `a21a5566` | No existing pool-owned render-target heap. p1444-tex has related heap-preserving usage upgrades. | Default-off `DM_NVN_POOL_HEAP=1`. Keep placement ownership and skip self-copies during upgrades. Upstream's 3 GB to 0.7 GB saving is unmeasured here. Aliasing needs visual and stability checks. | Host-only |
| #1447 terrain ranges, `2a18e3ec` | Already covered; no duplicate port | oot-play #1390 `0c2dbf41` already tracks texture storage ranges through record and image paths. p1444-tex retains those ranges. Its removal also preserves the two fragments of a merged range. | Keep existing `DM_NVN_VISUAL=1`. Do not add `DM_NVN_GPUW_RANGE` or a second interval set. Terrain has no new implementation in this branch. | Host-only |
| #1447 release, `0034c911` | Ported in `52834fb2` | Separate from recoverable #1386 dedupe and p1444's texture lifetimes. | `DM_TEX_RELEASE` remains off. Probe is available. Refuse file-backed guests, active dedupe, kernel-visible tracked ranges and shared registrations. GPU donor copies are included. Mode 2 can still lose content without a matching live donor; do not enable for ordinary play yet. | Host-only |
| #1446, `a9120fae` | Covered by p1444-tex; not copied into oot-r3 | All eight getter guards are in `604dca80`, gated by `DM_NVN_P1444_TEX`. That lane also guards GetBufferAddress, builders and initialization. | Merge the texture lane once. The standalone oot-r3 branch intentionally does not duplicate its guards. A null-safe getter does not fix the guest allocation failure. | Host-only |
| #1450, PR head `9bd4ef98`, feature diff against origin/main | Ported in `bddbc1dc` | No p1444 lane owns copy-stride state. Destination writes must retain the #1390 range API. | Default-off `DM_NVN_COPY_STATE=1`. Strides are recorder state with per-copy snapshots; legacy mode keeps OP_COPY_STRIDE. Old capture layouts remain accepted. | Host-only |
| `f956ffb0` GPU diagnostics | Ported in `3f7d55a4` | oot-play already has cbn submission/shader logging, safe-GPU feedback and GPU-loss handling. | Keep existing logging and safety paths. New shader failure ranking is off unless `DM_NVN_CBS_FAULT=1`; late retirement reports use `DM_RES_CHECK=1`. | Host-only |
| `8feddfee` uniform handle tables and `3e193e07` decode assertion | Ported in `478979b6` | p1444-xlate changes other translator operations and post-passes in the same files. It does not provide these tables. | Enabled as merged upstream correctness fixes. Host-built tables replace the 32-entry sampled-texture limit. Translator lengths, image/buffer caps, MSL pointers, ABI/reflection, c2 sampler selection and framebuffer feedback all travel together. | Shader-chain plus host |
| `8feddfee` sparse vertex capture | Ported in `478979b6` | Existing index caches are retained. p1444-stutter's indirect mesh observation and p1444-tex's mesh bounds remain separate. | Enabled as the merged allocation/capture fix. Sorted unique IDs use compact records and a geometry-stage remap. Keep the existing 256 MiB bounds. | Host-only for compaction; topology helper rewrite also changes the chain |
| `8feddfee` remaining general changes | Ported in `478979b6`, with one deliberate exclusion | Existing NDSR/NDVE parsing and Ounce vibration hooks predate this port. p1444-svc owns additional Ocarina services and profile values. | Keep both NDSR and NDVE discovery. Add PMAP records, guard-band opcode recognition, bindless TMML, distinct Opus manager keys and missing extended NFC calls. Keep the existing Switch 1 actuator answer instead of upstream's different Ounce mounted answer. No Kirby profile, shader tables, gallery or binaries imported. | Mixed tool/host/shader-chain |
| `52190603`, merged #1345 | Reconciled in `2edb339c` | Replaces gated `bf17b4c2` and earlier fixture `8f535d7e`. | Use the merged Update-then-UpdateImpl scan for every SDK, with a red diagnostic on failure. Removed the DM_OOT_BRENT gate for this correctness fix. Replaced old fixture with upstream's wider SDK/PLT cases. | Host-only |
| `a2d39a26`, merged #1354 | Reconciled in `2edb339c` | Replaces `6a010417`'s gated identity and old-stamp compatibility path. | Use upstream's device-independent identity and strict stamp comparison. Source hashing already invalidates old packer stamps, so the compatibility path was ineffective. | Tool-only, outside shader-chain |
| `16e3e24f`, merged #1333 | Ported in `3febd0b7` | No competing p1444 package reader. | Adopt merged shader-package robustness and Oodle table decoding from source, with its fixtures. No decoder executable was run. | Extraction tool-only, outside shader-chain |
| `c83c48f2` and `2202d610` | Already in oot-play ancestry | Layer-view correction and present shape/crop correction, with later local fixtures and fixes. | No duplicate application. Preserve local fixes. | Host-only |
| #1455, `bc604379` | Ported in `a80677b6`; focused tests pass | Reconciles #1391 eviction, DM_SAFE_GPU, #1404/#1394 residency, #1439 held ancestors, #1453 heaps and #1447 release. | Default-off `DM_NVN_ALIAS_RETIRE=1`. Live-only ages and retired-key suppression prevent stale descriptor walks recreating idle textures. Respect the lower existing safety budget; preserve deferred residency. Skip heap-backed textures and disable retirement with destructive guest release. No gameplay freeze or memory-saving claim is established here. | Host-only |
| Upstream `69cb9b6e`, merged #1401 | Ported in `121764ed`; t_nvn passes | Event builder already knew its pool/offset; event objects did not retain them. | Cheap general correctness fix, enabled. Store the builder pool/offset and answer both event queries. Capture command layout is unchanged. | Host-only |
| #1454 test stubs | Skipped as requested | Already supplied by p1444-stutter. | No duplicate stub port. | Host-only |

## Upstream and lane pins

Initial `git fetch origin` completed. `git log eab0aaac..origin/main` returned the following eight commits, newest first. That fetched main was `a2d39a26306c499183b755f0de32ef8a4246f104`.

```text
a2d39a26  merged #1354 RomFS identity
16e3e24f  merged #1333 unreadable packages/Oodle tables
52190603  merged #1345 audio lock scan
3e193e07  handle-table decode assertion
8feddfee  Kirby/general fixes
f956ffb0  failed-command-buffer shader and lifetime diagnostics
c83c48f2  compatible layered texture views
2202d610  present shape and crop
```

Comparison pins are p1444-xlate `7e1f6b6f`, p1444-tex `604dca80`, p1444-stutter `73914c12` and p1444-svc `d3d2923e`. The lead pin used for the static merge is oot-play-1444 `9bb60b88`.

## Merge instructions

A `git merge-tree --write-tree oot-play-1444 oot-r3` static comparison found code conflicts only in two `tex_upgrade` blocks in `dm/gfx/nvn/nvn_mtl.m`. The other conflict is the appended `implementation-notes.md` entries.

For both code conflicts, keep oot-r3's owner-aware behavior without an additional `p1444_tex_on()` condition. Pool placement is already gated by `DM_NVN_POOL_HEAP`. Once a heap-backed texture exists, upgrading it must stay on that heap and avoid copying it over itself even when the broader texture flag is off. Keep p1444-tex's other ancestor/view handling, serial invalidation, held counts and guards. Append both sets of notes.

The static merge automatically combined the recorder changes with p1444's guards and the general shader changes with p1444-xlate. Automatic merging is not build or behavioral proof. The integrated chain header must be regenerated after merging.

## Verification gates

The initial delivery completed static source comparison, `git diff --check`, conflict resolution and the static merge check. Added or updated upstream fixtures include pool-heap GPU reads, dirty-page discard, command/capture layouts, fault attribution, geometry compaction, handle-table reflection, audio-lock decoding, RomFS identity and package readers. Only the follow-up t_nvn and t_capture runs listed below have since exercised parts of that earlier fixture set; the other earlier fixtures remain unrun.

The implementation adds 44 changed files, 1,337 insertions and 186 deletions before this report. No tracked translator binary changed. `dmsh_chain.py --header` was run as source generation, not as a shader build. The resulting source header is `22c4a0d4825c`; the old translator lock is intentionally unchanged and does not certify the modified source. Tool-lock source checking must fail until the translator is rebuilt. Do not pair this branch's host with oot-play's old shader libraries.

The original verification gate required the game to exit. The user has now authorized builds and tests during play with `taskpolicy -b nice -n 19` and at most `-j4` or the equivalent concurrency cap. Apply that newer rule to remaining verification. Use the existing uv Python and set `TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch`. Install nothing.

Build the translator and any required SPIRV-Cross executable from inspected source into this task's storage. Do not execute the repo's prebuilt translator or SPIRV-Cross. Refresh the lock using only source-built tools, regenerate the chain header, and build matching Mac shader libraries through the lead's authorized build path. No iOS work is needed. A full shader build, game launch or regress.py run remains outside this implementation agent's authorization.

Then build the Mac host with `nice -n 19 make -C dm/host -j4 GAME=0400486024DEC000 dmhost`. Relevant focused fixtures are t_nvn, t_capture, t_dirty_discard, t_geometry, t_cbs_fault, t_pool_heap (both encoding modes and off), t_image_alias, t_audren_layout, t_nfc and the changed Python fixtures. Translator fixtures must use the source-built XLATE path. Keep artifact and cache output under task storage.

Gameplay acceptance belongs to the lead. Check pond terrain, clothing masks and foliage, ambient light, scene transitions, Hyrule entry, GPU errors and restop totals. Compare identical routes with the new opt-in switches off and on. Neither visual parity, stability nor a memory saving is established here.

## Storage and boundaries

No generated dependency or build roots were created or removed in the initial static delivery. Follow-up generated roots and retention are listed below. Kept source patches and static merge evidence in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/harvest-3-src/` for review. Kept this report at the requested external path and a matching committed copy in `docs/oot-notes/harvest-3.md`. No running process was stopped. No files were stored under /tmp, /private/tmp or a session scratchpad. Local commits only, per agent-context.md.

## Follow-up reconciliation and verification

Fetched main now points at `69cb9b6effee89eef18f7f7e96ac63075633f86d`; #1455 was read at `bc6043793078af660b536079b591fce4ebd0de91`. Both additions are host-only. The shader-chain source header and translator lock remain as in the initial delivery. No prebuilt translator or other third-party executable was run.

#1455 uses an effective retirement budget equal to the minimum of Metal's working set, a smaller DM_NVN_WS_MB override, the existing guard stop and the safe GPU cap. The 85 percent trigger and 75 percent target apply to that budget. With the usual 70 percent DM_SAFE_GPU cap they correspond to 59.5 and 52.5 percent of the native working set. Commit preflight, the wall, wired-memory cap, stop timer and fault handling are unchanged. Retirement is best-effort and cannot rescue a submission already stopped by the guard.

The existing #1391 guard calls the same retirement helper when opted in. The legacy eviction behavior remains when off. A live serial's texture ancestors are protected through #1439's held-count map, with a linear census fallback. Both ghost tables preserve residency through ordinary deferred release. #1404/#1394 raw-pool exposure, address filtering and residency are unchanged. Shared-view sweeping now observes idle retirements, and finalized descriptors over retired keys stay suppressed until a live texture is successfully rebuilt.

Heap-backed candidates are skipped because the pool still owns their allocation. DM_TEX_RELEASE=1/2 disables this new retirement because it could otherwise recreate a texture from discarded guest bytes. DM_TEX_RELEASE=probe is compatible. Neither #1455 nor release is enabled by default. Visual parity after Saria, Hyrule entry, materials and transitions still needs the lead's gameplay check.

Source fixtures were built with `taskpolicy -b nice -n 19 make -C dm/gfx/tests -j4 GAME=0400486024DEC000 t_alias_retire t_nvn t_capture`. Tests used the same background/low-priority prefix and the prescribed external TMPDIR. No install was needed.

| Run | Checks | Failures | Coverage |
|---|---:|---:|---|
| t_nvn | 243 | 0 | Includes both new event queries and earlier copy-stride cases. |
| t_capture | 83 | 0 | Command/capture compatibility. |
| t_alias_retire, direct encoding, held-count walk/check | 11 | 0 | A live view protects its parent; stale lookups do not prevent retirement or recreate a retired key. |
| t_alias_retire, deferred encoding, fast held map/check | 11 | 0 | Same behavior with held counts and encoder worker. |
| t_alias_retire off | 8 | 0 | Explicit flag-off behavior. |
| t_alias_retire default | 8 | 0 | Default-off behavior. |
| t_alias_retire release | 8 | 0 | Destructive guest release disables retirement. |
| Total | 372 | 0 | Focused fixtures only. |

The alias fixture also checks that a budget cannot exceed the safe cap or existing guard, that a smaller override is respected, and that an unknown working set prevents retirement. Builds completed with warnings; no compilation errors. No full dmhost build, game run, full shader build or regress.py run was performed. Logs and the machine-readable result are in the external harvest-3-src directory as followup-*.log and followup-tests.json.

The updated static merge comparison adds conflicts where p1444's packaged-alias declarations and pool-finalization cleanup meet the new live-age/tombstone tables. Keep both declarations and both cleanup loops; keep p1444's atomic eviction counter update once. Preserve the earlier owner-aware heap-upgrade resolution. The Makefile conflict must retain both BC render-target and alias-retirement targets. Append both sets of implementation notes. The integration lead must rerun tests after resolving these conflicts.

Generated roots retained for the lead's acceptance are dm/host/gen/0400486024DEC000, dm/host/gen/msl-macosx, and dm/gfx/tests/t_alias_retire, t_nvn, t_capture plus each matching .dSYM directory. They hold source-built fixtures and symbols; no generated storage was removed during this follow-up. Total fixture binaries are about 4.2 MiB and host/gen about 1 MiB, excluding symbols. No running game process or installed app was touched.

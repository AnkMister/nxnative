# Ocarina fork flags

Source defaults remain upstream unless an optional fork feature is selected.
The reference play environment is explicit so inherited shell settings do not
enable experiments. Shader tables and overlapping chain inputs use upstream.

| Setting | Reference play | Purpose and limit |
| --- | --- | --- |
| `DM_AOT` / `DM_AOT_STRICT` | `0` / `0` | Keep runtime exact AOT off. Offline packing enables AOT and records refusals. Counters remain diagnostic, not a runtime compile ban. |
| `DM_PSO_LEARN` | `1` | Record portable final/base states and typed constants, including packed libraries. |
| `DM_NVN_SERIAL_HELD` | `1` | #1439 counted holds include view ancestors and every serial writer. |
| `DM_NVN_P1444_STUTTER` | `1` | Guarded upload/cache additions around upstream packaged sharing. |
| `DM_NVN_P1444_TEX` | `1` | Remaining texture/view and retired-descriptor fixes. |
| `DM_NVN_MESH_INDIRECT` | `1` | Preserve upstream indirect conversion with the fork's count/overflow refusal. |
| `DM_NVN_MESH_PREDICT` | `1` | Queue native mesh pipelines on bounded workers; preserve every draw and wait if needed. |
| `DM_SAFE_GPU` / `DM_GPU_LOST_STOP` | `1` / `1` | Working-set/wired-memory protection, first GPU error stop and watchdog safety. |
| `DM_NVN_BCRT` | `0` | Experimental BC1/BC4 target re-encoding. Change only this line for B. Lossy; requires game comparison. |
| `DM_NVN_POOL_HEAP` | `0` | #1453 placement-heap experiment. Existing owners remain valid during upgrades even when other texture flags are off. |
| `DM_TEX_RELEASE` | `0` | #1447 guest texture release. Conservative safety refusals are retained. |
| `DM_NVN_ALIAS_RETIRE` | `0` | #1455 retirement, capped by working set and safe-GPU limits. |
| `DM_NVN_COPY_STATE` | `0` | #1450 per-copy stride snapshots; older captures remain supported. |
| `DM_HDR` | `0` | Optional HDR service, layer and present conversion. SDR uses the selected colorspace. |
| `DM_PRESENT_COLORSPACE` | `srgb` | Match layer tagging and present conversion. |
| `DM_FPS_TARGET` | `0` | This title has no registered frame-step override. |
| `DM_PRESENT_LINK` / `DM_PRESENT_HZ` / `DM_PRESENT_INTERVAL` | `2` / `60` / `game` | Native cadence on the user's 120 Hz display. |
| `DM_FOCUS_KEEP` | `1` | Keep the game active when focus changes. |

The old `DMSH_OOT_VISUAL`, Brent audio and SDK22 service takeover gates do not
select upstream's merged fixes. Do not reintroduce the old translator, service
or profile implementations. The old dynamic raw-map and commit-word experiments
also do not replace upstream's 8,191-entry pool table, `pool_ds_read` or `sub_cut`.

See [PLAY-BUILD](PLAY-BUILD.md) for the full build command and acceptance limits.

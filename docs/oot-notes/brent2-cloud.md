# Brent round 2 host source harvest

This branch ports host and runtime sources for Ocarina of Time on an M4 Max.
Mac build and gameplay acceptance remain open. Nothing was installed. No
third-party translator binary was copied or executed. The shader chain, shader
inputs and translator bundle were left unchanged.

## Source audit

The starting branch and oot-hyper-main were both `a14fb78c`. Upstream origin/main
was fetched and resolved to `c83c48f2`. Brent's source branch was
`brent-oot-combined-new`, head `89a0ff52`; the audit covered its changes after
`a54b2092`. Presence was checked by ancestry and source comparison, including
our existing ports. Ranking is an estimate of value for Mac Ocarina, not a
measured performance result.

All port rows below were missing from the starting integrated branch. They were
also missing from upstream except the crop correction `2202d610`, which upstream
already merged as a correctness fix.

| Priority | Item and source | Verdict | Reason |
|---|---|---|---|
| Highest | #1434, `9eeacbbf`, merged as `ff315e07` | Port | Five SDK 22 service takeovers, including the Ocarina note abort #1433. |
| High | #1332, `7f5f2fcf`, merged as `73df8e20` | Port | End a process whose GPU access was permanently revoked, with the shared Mac alert path. Keep our safe GPU policy. |
| High | #1392, `8cf26912` | Port | Drain retired buffers while unfocused and no longer submitting. Keep our accounting and linear cleanup. |
| High | #1417, `1c1d4533` | Port | Retire redundant chunks after whole-pool mapping. Preserve our raw-address filter. |
| High | #1428, `f5371478` | Port | Reuse completed pool table buffers in both incremental and full rebuilds. Keep existing descriptor-class checks. |
| Medium | #1320, `46975a20` | Port | Reduce false overlap of wide GPU writes and unrelated uniforms. |
| Medium | #1377, `d234d4f6` | Port | Parallel dav1d decoding and packet timestamps. M4 hardware decoding may bypass this path. |
| High | AV1 clock, `3b588ca6` | Port | Preserve movie speed and sound synchronization below the movie frame rate. Drops overdue pictures only when opted in. |
| High | #1379, `7ee81e91` | Port | Guest-clock timing and catch-up after host stalls, with actual game pauses treated separately. |
| Medium build value | #1355, `2e1f4953` | Port | Optional tmp.noindex avoids Spotlight work during builds. |
| High build value | #1438, `ea680b3e` | Port | Optional shader.noindex avoids Spotlight work on generated shader files. |
| Low immediate Ocarina value | Crop/layer, `2202d610` | Port, already upstream | General compositor correctness. Default-on exception applies. |
| Required fixture | `51ea3df8` | Port | Square present fixtures declare their square layer after crop correction. |
| Quality loss | #1331, `b6367705`, `76c20edb`, `943b0bea` | Skip | Bilinear scaling replaces the game's NDVE reconstruction and skips its passes. This sacrifices intended image reconstruction despite fixing corruption. |
| Existing dependency | #1390, `16e86fdc` | Already present | Our `4eacb1d7` already tracks texture storage ranges. Keep it; no NDVE adaptation is needed. |
| Quality loss | #1418, `4b13851d`, `1269a71f` | Skip | Removes fine compressed texture mip levels. Default-off is insufficient because the task explicitly rejects quality loss. |
| Assigned elsewhere | #1436, `01cce669` | Skip here | poolstat/texstat belongs to the Mac agent under the brief's explicit ownership split. |

The Mac agent also owns #1430, #1334 HMMA, #1427, shader-table splitting and
`0eeccf00`. None was ported here.

## Existing branch fixes retained

| Fix | Existing port | Integration decision |
|---|---|---|
| #1391 memory guard | `aa741191` | Keep our stop thresholds, alert helper and DM_SAFE_GPU behavior. #1392 uses existing g_res_bytes instead of adding a second pending counter. |
| #1382 failed-work names | `d07d79e4` | Keep our shader and command-buffer diagnostics. Add revoked-access handling without replacing them. |
| #1409 unsignaled feedback | `3915de46` | Keep our fence feedback correction. |
| #1408 linear deferred cleanup | `7fbb04aa` | Keep our linear queue processing; add idle draining around it. |
| #1420 packaged texture lookup | `0669a775` | Keep our fix and cached texture behavior. |
| DM_SAFE_GPU | Existing branch implementation | Keep first-fault and memory-limit behavior. Revoked-access handling is a separate opt-in. |

## Activation and quality

All new runtime and build behavior defaults off except the upstream crop fix.
Set each desired flag to `1` before starting the host or build script.

| Flag | Enables |
|---|---|
| DM_SDK22_SERVICES | SDK 22 takeovers at symbol registration, including strict-force accounting. |
| DM_GPU_LOST_STOP | Revoked-access stop, alert and completed-fence wakeups. |
| DM_NVN_IDLE_RETIRE | Idle retirement and pending-resource guard accounting. |
| DM_NVN_RETIRE_CHUNKS | Retire chunk mappings after full promotion. |
| DM_NVN_POOL_TABLE_REUSE | Reuse pool buffers and cache exact incompatible texture types. |
| DM_NVN_WIDE_INTERVALS | Wide cross-submission write intervals. |
| DM_AV1_PARALLEL | Queued dav1d frame decoding outside the picture lock. |
| DM_CV_LATE | Guest-clock movie timing and dropping overdue pictures. |
| DM_BUILD_NOINDEX | tmp.noindex and shader.noindex build folders. Use the same value for benchmark/regression readers. |

Movie timing does not lower decoded pixel quality, but it deliberately displays
fewer pictures during overload to maintain playback speed. It remains off by
default. NDVE reconstruction and texture detail are preserved. No measured
performance, memory or visual improvement is claimed for this Linux harvest.

The mechanisms and current validation status are recorded in the linked
[game note](../../dm/games/0400486024DEC000/README.md#second-host-source-harvest-open).

## Review and verification

Independent same-family review identified a decoder admission/reset race and stale
shader-directory selection when toggling DM_BUILD_NOINDEX. Both were addressed
with regression checks. Cross-family fresh-eyes review was unavailable because
the Claude provider is not authenticated; no cross-family result is claimed.

The same existing Python 3.14.2 interpreter ran the complete tools suite on the
starting source and the candidate. Source files were backed up outside the repo,
restored to the starting revision for the baseline, and restored to the candidate
in a finally block before the candidate run. No binary files were changed.

| Check | Result |
|---|---|
| Baseline tools suite | 1,132 tests; 10 failures, 150 errors, 61 skipped. |
| Candidate tools suite | 1,139 tests; the same 10 failures, 150 errors, 61 skipped. |
| Failure-name comparison | No new or resolved failures/errors. |
| Affected portable packaging tests | 51 passed, including noindex migration and reader selection. |
| Docs and environment table | 12 passed after symptom-index regeneration. |
| Actual SDK gate and movie-clock functions | GCC with ASan/UBSan passed flag, pause, stall, focus and timestamp-loop checks. |
| Actual Submit/Reset functions | GCC with ASan/UBSan and pthreads passed decode ordering, output-lock access, BUSY unlock and null-decoder checks. |
| Actual wide-write functions | GCC build and execution passed both flag modes, collision, page rounding, completion and interval-capacity assertions. |
| C syntax | hle_codec_video.c, hle_hid.c, hle_misc.c, hle_offline.c, gfx/hle_vi.c and t_gpu_lost_front.c passed GCC syntax checks using a generated Ocarina profile header. HID/BSD mergesort and existing attributes produce platform warnings. |
| Apple-only C syntax | hle_sdk16.c, loader.c and hle_movie_av1.c stop at missing pthread/qos.h, TargetConditionals.h or VideoToolbox headers on Linux. |
| Source hygiene | git diff --check passed; translator, chain header, chain lock and third-party sources are unchanged. |

The full suite is not green. Existing blockers include missing capstone and lz4,
Mac-only libproc.dylib and cp options, Clang, .NET and platform binary fixtures.
No packages were installed to bypass these constraints. The initial system
Python 3.10 run was also recorded, but the comparison above uses the same 3.14
interpreter for both revisions.

The full native Mac codec/Metal fixtures have not run. Extracted C checks prove
only the portable functions they execute, not VideoToolbox or Metal behavior.
The Python regress module cannot import on this Linux machine because it loads
libproc.dylib. No game, shader build, regress check or device install was run.

## Commits

Each source item has its own commit. Integration fixes and diagnostic support
have separate commits. The PR-to-source mapping is in the audit table above.


| Commit | Change |
|---|---|
| `ba9b827d` | Port PR #1320 wide GPU write intervals behind an opt-in flag |
| `74ffe152` | Port optional Spotlight exclusion for build temporaries (#1355) |
| `21a4ece1` | Port PR #1417 chunk retirement behind DM_NVN_RETIRE_CHUNKS |
| `a4af36a5` | Port SDK 22 service hooks from PR #1434 behind an opt-in flag |
| `865029be` | Port PR #1428 pool table reuse behind DM_NVN_POOL_TABLE_REUSE |
| `49722cbe` | Port optional parallel AV1 decoding from d234d4f6 |
| `ba308cf9` | Port optional shader folder Spotlight exclusion (#1438) |
| `90d09229` | Port optional AV1 playback clock from 3b588ca6 |
| `40aaba0f` | Port PR #1392 idle pool retirement behind DM_NVN_IDLE_RETIRE |
| `f86e8a21` | Port AV1 pause and stall clock handling from 7ee81e91 |
| `6e9b99c4` | Port PR #1332 revoked GPU handling behind DM_GPU_LOST_STOP |
| `027c6732` | Port the focus control command from PR #1392 |
| `cb189e86` | Keep shader readers consistent with the noindex build flag |
| `4bfe9d0c` | Port upstream crop and layer shape fix from 2202d610 |
| `19c866af` | Port square present fixture fix from 51ea3df8 |
| `cd34a04f` | Serialize parallel AV1 submissions with reset and finalization |

## Mac acceptance still required

Every source port remains pending a Mac check. Build the Ocarina host with
`GAME=0400486024DEC000`, then test flags one at a time against their defaults.
No new behavior should become a normal play flag until its Mac comparison passes.

| Commits | Required Mac proof |
|---|---|
| SDK hooks | t_symbols, t_hid and t_pctl; open and close the Ocarina note without #1433's abort. |
| Parallel AV1, playback clock and lock follow-up | Full t_codec_video, both VideoToolbox and forced dav1d, timestamp/EOS/reset checks, title movie and cutscene audio sync. Compare decoded pictures and identify intentional overdue-picture drops. |
| Wide intervals | t_sbw and render-pass/image comparison. |
| Chunk retirement | t_pool_retire; raw-address pool access, fences and memory after whole-pool promotion. |
| Table reuse | t_pool_table; both incremental/full paths, in-flight fences, memory and residency commits. |
| Idle retirement and focus command | t_res_guard and t_hid; repeated focus/unfocus while streaming, memory bounded and gameplay resumes. |
| Revoked GPU access | t_gpu_lost with the gate off/on; DM_TEST_GPU_LOST injection, fullscreen exit, alert and completed-fence wakeups. Recheck DM_SAFE_GPU independently. |
| Crop and square fixture | t_present_crop, t_present_alloc, t_nro and t_symbols; 16:9 presentation and taller-screen behavior without color or sharpening changes. |
| Noindex ports and reader follow-up | Existing build migration, both folder names present, flag toggling, cache reuse and actual Spotlight exclusion on the user's macOS. |

After native tests pass, run the Mac regression harness on five available games
most likely to exercise these paths. Proposed set: Ocarina of Time (SDK 22,
AV1 and NVN2), Fire Emblem Fortune's Weave (AV1 and texture pools), Breath of the
Wild (uniform updates and alternate screen shape), Super Mario Galaxy 2
(anamorphic crop) and Super Mario Bros. Wonder (baseline NVN pool/present path).
Use the installed game set and usage manifests to refine this selection. These
five games were not tested here. No performance or gameplay result is inferred
from their proposed selection.

## Local evidence and delivery

Detailed Linux logs and source-extraction receipts are under
`~/Documents/Crypt/Projects/_work/nxnative/brent2-cloud/` and
`~/Documents/Crypt/Projects/_work/nxnative/brent2-runtime/`. The tracked C/Metal
fixtures preserve the behavior assertions for native verification. The report
is also copied to `~/code/nxnative-research/reports/brent2-cloud.md`.
The authorized destination is `ankmister`, branch `oot-brent2-cloud`. No PR is
opened and no other remote branch is updated.

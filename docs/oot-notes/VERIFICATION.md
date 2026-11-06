# oot-play verification

The combined source includes final `oot-play-fixes` at `94c64008`. The selected
play settings are in [PLAY-BUILD](PLAY-BUILD.md). The entries below supersede
the earlier variant results for this branch.

| Check | Result |
| --- | --- |
| Full tools discovery | PASS: 1,383 tests, 10 skips |
| Full graphics Python discovery | PASS: 420 tests, 2 skips |
| Native graphics run | PASS: 134 targets, plus four pull and five TBDR-budget tests |
| Native host tests | PASS |
| Native texture tests | PASS: 5,344 checks, zero sRGB violations |
| Ocarina host compile and link | PASS |
| Lock, header and source/distribution fingerprints | PASS: 435 matching fingerprints |
| Default chain | `e16dbb187984` |
| Play chain, visual translation on and tensor off | `4323760be52f` |

Graphics Python checks enable the source-built translator, Metal, GPU execution
and native geometry, PrimitiveID, transform-feedback and border helpers. The AOT
fixture tests real archive/prewarm requests for SDR and HDR present pipelines.
The direct common-encoder HDR fixture preserves MetalFX for original sRGB inputs
with both HDR destinations and counts scaler creation. Idle-retirement lifetime
and stalled-watchdog checks pass with the option off for play.

The translator was published once from source using 57 cooled, audited NuGet
versions. SPIRV-Cross was built from pinned source. Generated conflicts were
rebuilt. No PR-shipped translator binary was executed. Heavy steps used nice 19,
with at most four native make jobs and two source-build jobs.

Optional Python lint still reports 28 new-to-baseline findings in five inherited
Ocarina analysis/test files that are byte-identical to oot-1439. The baseline
was not weakened. Required test groups pass; builds retain compiler warnings.

The existing package uses chain `992d6981956f`. A full shader and archive rebuild
is required before the matching host can use oot-play. Gameplay, display colour,
indirect-mesh layout and zero compiler entries during play remain open gates.
Strict AOT reports misses and still compiles them to preserve geometry. No game,
full shader build, user settings write, push or remote default-branch change ran.

Evidence, exact commands and the next full-build environment are in the external
oot-play report and oot-play-evidence folder. Retained build and evidence roots
were not removed because process working directories remained open in this
checkout. Earlier failed attempts and corrected reruns are preserved.

# Integrated verification

Both final source variants pass. oot-hyper-main is selected as the basis for the
parent's next play build. This is source/fixture acceptance, not a finished app.

| Check | oot-hyper | oot-hyper-main |
| --- | --- | --- |
| Validated source | 8e339f35 | 5f066f7d |
| Full tools discovery | PASS: 1,306 tests, 24 skips | PASS: 1,368 tests, 24 skips |
| Full graphics Python discovery | PASS: 417 tests, 1 skip | PASS: 417 tests, 1 skip |
| Native graphics run | PASS: 127 targets, plus four pull and five TBDR-budget tests | PASS: 127 targets, plus four pull and five TBDR-budget tests |
| Ocarina host build | PASS | PASS |
| Crop and six quality configurations under Metal validation | PASS: 88 crop checks, 239 per quality case | PASS: 88 crop checks, 239 per quality case |
| Mixed Float16/integer attachment regression | PASS: 29 GPU checks | PASS: 29 GPU checks |
| Growing raw pool table and scalar/optimized comparison | PASS: 61 scalar and 226 comparison checks; 8,192 entries, 5,001 marked ranges | PASS: same fixture |
| New read-only grouping/CAS/F2IP fixtures | PASS, included in graphics suite | PASS, included in graphics suite |
| AOT real archive/prewarm/learning fixture | PASS: three tests, including strict miss accounting and repack | PASS: same fixture |
| Stage-cache coverage | PASS: every FILES module covered, 25 tests | PASS: same coverage plus upstream storage adapter |
| Clock, eco clock, GPU-stop lifecycle and engine resolution | PASS | PASS |
| Audio, renderer layout, SPSC and filesystem | PASS; filesystem 138 checks | PASS; includes upstream per-renderer PCM blocks |
| SVC memory and real dirty tracking | PASS: limited/unlimited, 16K ASan/UBSan, alias probes | PASS: upstream alias/heap implementation |
| Tool lock and regenerated default header | PASS, clean | PASS, clean |
| Default chain | 0d0146e341bb | edc19761647e |
| Correctness play chain (DMSH_OOT_VISUAL=1, other experiments off) | 735446b8c867 | 992d6981956f |
| Distinct build-option combinations | 64 | 64 |

Main was created from origin/main eab0aaac96540500237248fa4e6410375596bb66,
resolved when the branch started. It contains e9d71e27's 64 GB alias layout,
a334797d's per-renderer PCM fix and the subsequent provisional heap correction.
The gated Brent alias/heap copies are removed on main. Other Brent experiments
remain off. Packed shader libraries and single-file compile storage are retained.
A new regression compares AOT rows, library digests and extraction before/after
packing, including built-in helpers. The final translator bundle is source-built
once for the byte-identical merged C# inputs used by both variants.

Graphics checks enable the bundled translator, Metal, GPU execution and native
geometry, PrimitiveID, transform-feedback, border and AOT replay helpers. Native
compilation uses at most four task jobs. Optional fixture skips remain explicit.
Synthetic tests do not prove gameplay pictures, display colour, real GPU-fault
survival, full-map shader compatibility or zero gameplay compiler entries.
No game, regress.py, full shader build, app signing or device operation ran.

The initial hyper graphics invocation omitted DM_GAME and failed module loading;
its corrected complete rerun passes. Main's first complete Python graphics run
found the miner's legacy folder-reader API mismatch. The read-only adapter was
fixed; its corrected complete rerun passes. Neither test was weakened. Earlier
verification records and failed-attempt logs remain external evidence.

Final logs use late-* names under the external oot-hyper/ and oot-hyper-main/
evidence roots. Quality/crop and AOT focused logs, chain option matrices, package
age/asset audits, source fingerprints and all requested PR file lists are retained.
See [storage](STORAGE.md) for generated-root cleanup and retained artifacts.

## Review 3 follow-up

The table above records 64a163ba and its earlier integration. The review repair
branch is oot-review3. Its [report](review-astra-3-fixes.md) supersedes those
chain stamps and the indirect-mesh play setting. Game/image and complete AOT
acceptance remain open. The running play build was not modified.

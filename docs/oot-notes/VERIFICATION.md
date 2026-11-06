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

# Integrated verification

## Earlier oot-hyper checkpoint (before final AOT/foliage merges)

| Check | Result |
| --- | --- |
| Full `dm/tools/tests` discovery | PASS: 1,305 tests, 24 skips |
| Full `dm/gfx/tests` Python discovery | PASS: 409 tests, 1 skip; bundled source-built translator, Metal and GPU fixtures enabled |
| Native graphics `make run` | PASS: 126 run targets, plus pull and TBDR-budget Python checks |
| Host build, Ocarina profile | PASS |
| Crop under Metal validation | PASS: 88 checks |
| Quality under Metal validation | PASS: six configurations, 239 checks each |
| Mixed Float16/integer GPU regression | PASS: 29 checks under validation |
| Raw pool GPU reads | PASS: 61 scalar checks plus 226 four-word scalar/optimized comparison checks, 8,192-entry table and 5,001 marked ranges |
| Clock/eco-clock and host GPU-stop lifecycle | PASS: five clock modes, freeze composition and cleanup/exit fixtures |
| Audio, SPSC, renderer layout and filesystem | PASS; filesystem 138 checks |
| Internal engine resolution callbacks | PASS: 15 startup cases, 120 checks |
| Memory SVC variants | PASS: map-limited/unlimited, 16K ASan/UBSan, real dirty tracking and both Brent alias probes |
| Tool lock and generated header | PASS; default chain `d393105673d1`, visual play chain `6b308249ed3d` |
| Build option combinations | 32 distinct chain hashes across visual, raw quads, cbuf reuse, storage runs and border split |

Commands use the existing Python environment and configured persistent scratch.
Native build concurrency never exceeds four task compiler jobs. Logs are retained
in the external task evidence workspace; source and docs remain in this repository.
Skipped tool cases require optional fixtures, and the graphics skip is recorded
by unittest. Synthetic tests do not establish gameplay, display colour, driver
fault survival, full-map shader compatibility or zero runtime compilation.
No game, full shader build or regress.py run was performed.

## Upstream-main variant

The second variant will be based on origin/main resolved at creation. Its checks
and selected play-build basis will be recorded after integration.

## Final oot-hyper source

| Check | Result |
| --- | --- |
| Full tools discovery | PASS: 1,306 tests, 24 skips |
| Full graphics Python discovery | PASS: 417 tests, 1 skip; source-built translator, GPU, Metal and native helpers enabled |
| AOT archive fixture | PASS: three tests, archive-only startup, exact hits, strict miss accounting and learned-descriptor repack |
| Crop and quality together under Metal validation | PASS: crop 88 checks, six quality cases of 239 checks |
| Host build and focused host/memory fixtures | PASS: clocks, GPU-stop lifecycle, resolution, audio, filesystem, real dirty tracking, sanitizer/alias variants |
| Stage cache | PASS: 25 tests; every FILES module covered, all merged options retained |
| Chain and tools | PASS: clean default header `0d0146e341bb`; 64 distinct option combinations |

The first graphics invocation omitted DM_GAME and failed module loading. The
corrected full rerun above passes. Historical logs and both invocations remain
in the external evidence folder. No test was weakened for that setup error.
Final native graphics results follow when its complete run exits.

# Oot V2 implementation log

Branch `oot-vqa`, based on this worktree's `oot-base` checkout. No game, regress,
shader-chain build, baseline build writes, installs, devices, push or PR work.

Process: pstack feature steps adapted for an implementation sub-agent. Trace and
sketch owned here; nested delegation and independent review left to the parent.
Blocking gates were the shared context, clean worktree and branch selection.
Colour, scanner and report are separate deliverables but share the host pipeline;
one writer owns them. No shared mutable state with the running baseline.
PR and regression steps are skipped under the explicit task restrictions.

Data shapes: pass attachment metadata + ordered shader-key candidates; one GPU
count per 16x16 tile; structured log event groups; frame/@metric/value TSV rows.
Reuse the main Metal 4 command buffer, commit callbacks and `scripts/bench.py`.

## Delivered behaviour

- `DM_PRESENT_COLORSPACE=srgb|auto` tags encoded SDR output as sRGB.
- `DM_PRESENT_COLORSPACE=p3` converts sRGB primaries to Display P3 in linear light,
  then uses the shared sRGB transfer curve and a Display P3 layer tag. Offscreen
  screenshots made through the present shader get the matching colour tag.
- Unset preserves the legacy layer and present shader. No game-specific cuts or
  shader-chain changes. No new packages. Only the host's own MSL is rebuilt.
- `DM_NVN_NANSCAN=1` scans every stored float render attachment at pass end.
  `DM_NVN_NANSCAN_EVERY=N` samples every Nth presented-frame index, default 1.
  The count includes RGBA, all multisample samples, once per pixel. 2D attachments,
  2D-array mip/layer views and layered targets are supported. Discarded targets,
  memoryless/unreadable targets and 3D targets have explicit skip records.
  Integer and normalized targets cannot store NaN or Inf and need no GPU scan.
- The scanner runs on the main command buffer, with barriers between render store,
  scan and later writes. Counts use independent, fence-retired buffers. Completion
  callbacks log zero counts as coverage and hits with frame/pass/target/view and
  candidate fragment keys. Earliest pass is sorted by replay order in the report.
  A pass key is not proof that its fragment shader introduced the non-finite value.
  Loaded contents, image writes and compute work may be the source. Merged passes
  have physical pass granularity. Uninitialized pixels can also trigger hits.
- `DM_NVN_VQA=1` logs skipped-pipeline draws outside PASSDUMP, actual source-format
  changes and the first HDR-status query. It adds `@compile_ms` to `DM_NVN_TSV`.
  Display colour profile and current/potential EDR headroom are logged when VQA or
  a colour mode is enabled. Logging itself is diagnostic overhead.
- `scripts/oot_vqa.py` accepts a log file or an `oot_ab.py` A-1/B-1 directory.
  It emits Markdown or strict JSON. `--frames`, `--window start,length`, `--fps`,
  `--format` and `--out` are available. It never launches games or modifies inputs.
  It reuses `bench.frames`, `bench.summary` and nearest-rank percentiles, the same
  underlying parser used by `oot_ab.py` on `oot-bench`. It retains frame IDs only
  for cluster calculation. No changes to `oot_ab.py` and no duplicate runner.
- Pacing reports include target-relative histogram bins, the strict >1.5x count,
  consecutive-frame stutter clusters, on-screen interval standard deviation, RMS
  target error, p95 absolute target error and missing/dropped interval counts.
  The report distinguishes whole-run log evidence from windowed timing data.
  Compilation on long frames is evidence of work, not proof of stall causation.
  Sparse long-frame logs cannot substitute for the full timing TSV.

## Colour audit

Locations refer to the final source on `oot-vqa`. Severity is the consequence
when the stated condition holds. Static evidence is not a console comparison.

| Severity | Finding and evidence | Disposition |
|---|---|---|
| P2, confirmed source defect | `dm/host/front_mac.m:1340` creates BGRA8Unorm; the legacy path leaves `colorspace` nil. Apple's CAMetalLayer contract says nil content is not colour matched. Display-native interpretation can change saturation on P3 or other wide-gamut displays. | Opt-in source tags fix the contract. Actual user's display match remains untested. `srgb` is the recommended first check. |
| Info, existing correct behaviour | `dm/gfx/nvn/nvn_mtl.m:4131` attaches explicit sRGB views and the pipeline uses their actual format. Metal encodes linear fragment output on sRGB writes. `present_raw_src` at `:12834` then substitutes non-sRGB views for RGBA8/BGRA8 scanout, avoiding decode without a corresponding encode into BGRA8Unorm. | Preserve the raw encoded scanout. Adding another global gamma curve would be wrong. |
| P2 if mistagged, prevented in new path | `dm/gfx/msl/present.metal:10` converts sRGB primaries before a Display P3 tag. Changing only the tag would reinterpret sRGB channel values as P3 and oversaturate them. `dm/gfx/nvn/nvn_mtl.m:12587` also tags converted offscreen shots separately from raw dumps. | GPU output checked against ColorSync. `auto` deliberately means sRGB SDR source; it does not guess the source gamut from the screen. |
| P3, precision limit | `dm/gfx/tex/nvn_fmt_mtl.c:54` maps RGB10A2Unorm to Metal RGB10A2Unorm. The present samples normalized full-range values. `dm/gfx/msl/present.metal:7` writes those values to an 8-bit layer. No 16-235/64-940 limited-range expansion, PQ decode or HDR metadata transform occurs. | Ten-bit input can lose precision at the 8-bit output. Ten-bit storage alone does not prove HDR. Do not apply a range conversion without guest display metadata. |
| P2 if HDR forced, open capability | `dm/gfx/hle_vi.c:88` reports HDR disabled, format 0, peak 0; `:93` reports 203-nit paper white, read only when HDR is active. `:120` through `:134` discard gamut, tone-map, luminance and Bezier metadata. | Host output is SDR by contract. A global EDR toggle alone would be incorrect. |
| Info, HDR-capable game interfaces found | Read-only string inspection of Ocarina update v131072 `main.patched.bin` found QueryDisplayHdrStatus, QueryDisplayHdrPaperWhite, gamut/luminance/tone-map metadata imports and ToneMapping/AfterToneMapping names. `dm/gfx/hle_vi.c:85` documents the same service family in Donkey Kong Bananza. | Supports HDR-capable engine/API plumbing. Does not prove Ocarina's active output transfer, primaries, mastering peak or actual HDR rendering. The new query log can establish calls in the first session. |
| Info, upscaler colour handling | `dm/gfx/nvn/nvn_mtl.m:12920` scales encoded scanout in MetalFX perceptual mode before the final colour conversion. `:13010` recognizes game-upscaler variants by curve constants; linear/HDR and encoded/perceptual variants use different MetalFX paths. Ocarina's NDSR keys are not enabled as a game-upscaler replacement in this profile. | No demonstrated missing gamma conversion here. Nintendo's use of float HDR intermediates does not imply HDR scanout. |
| P2, existing validation failure | `dm/gfx/nvn/nvn_mtl.m:12957` invokes the Metal 4 spatial scaler without setting its outputTextureBarrierStages. Existing `t_present_crop` aborts inside MetalFX with `_outputTextureBarrierStages not set` under Metal API Validation on this machine. | Outside V2 colour scope; left for `oot-upscale`. Ordinary crop/sRGB checks preceding the scaler completed. Do not count the whole crop suite as passed. |

Apple primary references:

- [CAMetalLayer colorspace](https://developer.apple.com/documentation/quartzcore/cametallayer/colorspace): nil is not colour matched.
- [Display P3](https://developer.apple.com/documentation/coregraphics/cgcolorspace/displayp3): P3 primaries, D65 white, sRGB transfer function.
- [EDR tone mapping](https://developer.apple.com/documentation/metal/performing-your-own-tone-mapping): an extended linear layer with RGBA16Float and EDR enabled.
- [Layer EDR metadata](https://developer.apple.com/documentation/quartzcore/cametallayer/edrmetadata): tone mapping metadata; no automatic tone mapping when metadata is nil.

## Proposed HDR path, not implemented

`DM_PRESENT_EDR=1` should be a future opt-in only after the guest display contract
is decoded. Store per-layer HDR transfer, gamut, luminance and tone-map metadata,
report HDR support only for a compatible output, and use RGBA16Float with an
extended linear colour space and `wantsExtendedDynamicRangeContent=YES`.
Decode the declared guest transfer (for example PQ when actually declared), map
its primaries to the layer space, and scale by the negotiated reference white.
Use the screen's changing EDR headroom plus metadata-aware tone mapping. Keep a
correct SDR fallback when the window moves to a screen without HDR headroom.
The EDR path must also bypass perceptual SDR present scaling and update screenshot
encoding. Do not infer HDR from RGB10A2, float bloom targets or the word HDR in a
shader. No `DM_PRESENT_EDR` flag is exposed by this branch.

## First Kokiri Forest session recipe for the parent

Combine `oot-vqa` with `oot-bench` first. No save usable for a deterministic
Kokiri load was found in the shared save research. Use a parent-owned save copy
if one exists, otherwise navigate the first session normally and create one.
The commands below are a recipe only; this agent did not run the game.

From the combined checkout, create a new output directory outside both baseline
folders. Reusing `oot_ab.build_paths` keeps asset discovery identical to the A/B
runner. The baseline build remains read-only; saves, temp, PSO writes and logs go
under the new run directory.

```sh
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
export VQA_RUN=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/vqa-kokiri-first
export VQA_HOST="$PWD/dm/host/dmhost"
export VQA_BUILD=/Users/ankur/Documents/Crypt/Gaming-rea/_work/games/oot/0400486024DEC000_build
PY=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python
PYTHONPATH="$PWD/scripts" "$PY" - <<'PY'
import os
from pathlib import Path
import subprocess
from oot_ab import build_paths
out = Path(os.environ['VQA_RUN'])
out.mkdir()  # refuses an existing run
(out / 'save').mkdir()
(out / 'temp').mkdir()
(out / 'ctl').touch()
exe, modules, flags = build_paths(Path(os.environ['VQA_BUILD']), os.environ['VQA_HOST'])
env = {k: v for k, v in os.environ.items() if not k.startswith('DM_')}
env.update(flags)
env.update(DM_ROOT=str(out), DM_SAVE=str(out/'save'), DM_TEMP=str(out/'temp'),
           DM_CTL=str(out/'ctl'), DM_NVN_TSV=str(out/'frames.tsv'), DM_NVN_TSV_CALLS='0',
           DM_PSO_USER=str(out/'pso_user.tsv'), DM_PSO_ARCHIVE=str(out/'pso_archive'),
           DM_WINDOW='1', DM_FPS_TARGET='30', DM_NVN_VQA='1',
           DM_PRESENT_COLORSPACE='srgb', DM_NVN_NANSCAN='1', DM_NVN_NANSCAN_EVERY='30',
           DM_PRESENT_UPSCALE='off', DM_UPSCALER='off', DM_NVN_SHOT_OUT='1920x1080')
with (out/'log.txt').open('w') as log:
    subprocess.run([str(exe), str(modules)], cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
PY
```

In another terminal, once Link and the camera respond in Kokiri Forest, record
an actual window start from the latest `@t_s` row. Walk and turn the camera along
a repeatable route; record the end the same way. Capture a still after that window:

```sh
awk -F '\t' '$2 == "@t_s" { t=$3 } END { print t }' "$VQA_RUN/frames.tsv"
printf 'shot %s/kokiri.png\n' "$VQA_RUN" >> "$VQA_RUN/ctl"
```

After quitting, substitute the recorded start and end-minus-start as `START,LENGTH`:

```sh
"$PY" scripts/oot_vqa.py "$VQA_RUN" --window START,LENGTH --out "$VQA_RUN/vqa.md"
"$PY" scripts/oot_vqa.py "$VQA_RUN" --window START,LENGTH --format json --out "$VQA_RUN/vqa.json"
```

Check the reported actual source format, display profile, HDR query, first NaN
pass and skipped/missing work before judging bloom. Keep the still and the log.
For colour acceptance repeat the same view with legacy, `srgb`, and `p3`, changing
only the colour flag. A correct sRGB/P3 conversion should preserve appearance
within output quantization; it should not add saturation. Compare against a known
console reference before declaring visual parity.

For clean frame pacing and energy comparisons, disable NANSCAN and screenshots
in the measurement window. Use `oot_ab.py` unchanged, then run VQA on each `A-1`,
`B-1`, etc. with the same `--window` that A/B used. A scanner-enabled diagnostic
session is not a clean efficiency measurement. Log events are whole-run evidence.

## Verification and limits

- Host built successfully with `make -C dm/host -j4 GAME=0400486024DEC000 dmhost`.
- Parser/summarizer unit tests: 6 passed.
- Existing benchmark parser tests: 6 passed.
- Documentation tests: 11 passed; symptom index regenerated.
- Production NaN kernel: 14 checks passed under Metal API Validation.
- Present colour shader: 84 checks passed under Metal API Validation, against
  independent CoreGraphics/ColorSync references, including endpoints, primaries,
  gray, a mixed colour and transfer-curve boundary values.
- Production Metal 4 pass-timeline test: bad target followed by a finite overwrite
  produced counts 256 then 0. Default-off run produces no scanner events.
- Existing `t_present_crop`: aborted in its MetalFX path as described above.
- Final host build has 59 warnings in existing code; no new scanner/colour warnings.
- No game, regress harness, shader-chain build, iOS work or device installation.
  No real Kokiri VQA results, fps claim, display visual match or HDR passthrough proof.
  Independent review belongs to the parent. All checks above are local, synthetic
  or source checks, except the documented existing test failure.

The CLI was also run against the actual synthetic pass-test log. It reported two
scanned targets and the first pass's 256 bad pixels, with pacing unavailable.
Reports are in `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/vqa-v2-verification/`.
Build/test logs are in the mandated scratch directory as `oot-vqa-*.log`.
Changes remain uncommitted on `oot-vqa`, because the repository requires an
explicit commit request. Nothing was pushed or published.

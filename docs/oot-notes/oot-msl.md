# Ocarina Mac stack implementation notes

## Result and scope

`oot-stack` now contains the source changes from #1360, locally compiled translator
assemblies, #1405 adapted to this base, #1161, and an optional Mac presentation
experiment. Base is `ee9b7765d579c46e45a7297493565e098f3bda33`, preceded on this
branch by report commit `8d79e304`. These are patch integrations, not merges of
unrelated upstream ancestry. Nothing was pushed or posted to GitHub.

The protected baseline checkout and game work folder were neither read nor
modified. No game build, `build_ipa_from_nsp.py`, `regress.py`, full shader build,
iOS build, signing, or device installation ran. The requested tools tests use
synthetic package fixtures. They do not establish gameplay acceptance.

The earlier report's description of an 8,192-entry Ocarina table was inaccurate
for this base. Its source and shipped translator use 4,096 entries plus tagged
lookup hints and bitmap write logs. Both local features were preserved.

## PR status

| PR | Inspected source head | Local status | Verification | Remaining risk |
| --- | --- | --- | --- | --- |
| [#1360](https://github.com/seedds/nxnative/pull/1360) | `eaa7a1daed0eca9427941889462f683234235c44` | Integrated as `c88eefef`, excluding every PR binary and its lock/header. Managed artifacts rebuilt locally. | 60 translator tests; pool/bitmap 95 checks; raw GPU load 61 checks, Metal validation. | Game shaders and host must be rebuilt together. Gameplay not run. |
| [#1405](https://github.com/seedds/nxnative/pull/1405) | `3fe33bc3997aaba9ef15b0497b5e80c1895edabe` | Integrated as `453083a4`, including growing-table and bit-cast-root adaptations. Off by default. | 11 wide tests; 61 integrated translator tests; real emitted quad compiles; scalar/quad GPU comparison 179 checks. | No full-map translation or game image/performance comparison here. |
| [#1161](https://github.com/seedds/nxnative/pull/1161) | `b21178a2b22366e86595012e3195640257a54ad4` | Integrated unchanged as `5a052984`. | `check_t_feedback`: 167 checks, zero failures. | Ocarina benefit and full-game regression unmeasured. |
| Local presentation experiment | `e7c50787` | `DM_PRESENT_ABSOLUTE=1`, off by default; Mac direct path only. | Pacer 250 checks; offscreen present allocators 19 checks, Metal validation. | Plausible cause only. On-screen cadence and latency unmeasured. |

The #1405 typing-only follow-up touched tests absent from this base. Its unrelated
test additions from three-way conflict context were not imported. The wide-load
implementation and relevant tests were integrated.

## NuGet audit and build provenance

Built with `~/.dotnet`, SDK **10.0.403**, runtime **10.0.14**, on the M4 Max.
Before restore, every package in the translator's shipped dependency closure was
checked against its nuget.org registration index. All **57** exact versions
passed the minimum seven-day age gate. No version substitution or cooldown
exception was needed. The four direct references match `Directory.Packages.props`;
all transitive versions match the shipped `dmsh_xlate.deps.json`.

The audit fetched
`https://api.nuget.org/v3/registration5-gz-semver2/<lowercase-id>/index.json`
and checked each matching catalog entry's `published` field. The table below
records the UTC publication date. Only after the entire audit passed were these
exact nupkgs downloaded to an isolated local feed. A custom NuGet.Config cleared
all other feeds. Restore used an isolated NUGET_PACKAGES directory, disabled
parallel restore and audit network queries, and had no source from which it
could select a newer transitive package. Each resulting project.assets.json was
checked against this allowlist after restore.

| Package | Exact version | Published (UTC) |
| --- | --- | --- |
| Gommon | 2.8.1.2 | 2026-04-09 |
| Humanizer | 3.0.10 | 2026-03-07 |
| Humanizer.Core | 3.0.10 | 2026-03-07 |
| Humanizer.Core.af | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ar | 3.0.10 | 2026-03-07 |
| Humanizer.Core.az | 3.0.10 | 2026-03-07 |
| Humanizer.Core.bg | 3.0.10 | 2026-03-07 |
| Humanizer.Core.bn | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ca | 3.0.10 | 2026-03-07 |
| Humanizer.Core.cs | 3.0.10 | 2026-03-07 |
| Humanizer.Core.da | 3.0.10 | 2026-03-07 |
| Humanizer.Core.de | 3.0.10 | 2026-03-07 |
| Humanizer.Core.el | 3.0.10 | 2026-03-07 |
| Humanizer.Core.es | 3.0.10 | 2026-03-07 |
| Humanizer.Core.fa | 3.0.10 | 2026-03-07 |
| Humanizer.Core.fi | 3.0.10 | 2026-03-07 |
| Humanizer.Core.fil | 3.0.10 | 2026-03-07 |
| Humanizer.Core.fr | 3.0.10 | 2026-03-07 |
| Humanizer.Core.he | 3.0.10 | 2026-03-07 |
| Humanizer.Core.hr | 3.0.10 | 2026-03-07 |
| Humanizer.Core.hu | 3.0.10 | 2026-03-07 |
| Humanizer.Core.hy | 3.0.10 | 2026-03-07 |
| Humanizer.Core.id | 3.0.10 | 2026-03-07 |
| Humanizer.Core.is | 3.0.10 | 2026-03-07 |
| Humanizer.Core.it | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ja | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ko | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ku | 3.0.10 | 2026-03-07 |
| Humanizer.Core.lb | 3.0.10 | 2026-03-07 |
| Humanizer.Core.lt | 3.0.10 | 2026-03-07 |
| Humanizer.Core.lv | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ms | 3.0.10 | 2026-03-07 |
| Humanizer.Core.mt | 3.0.10 | 2026-03-07 |
| Humanizer.Core.nb | 3.0.10 | 2026-03-07 |
| Humanizer.Core.nl | 3.0.10 | 2026-03-07 |
| Humanizer.Core.pl | 3.0.10 | 2026-03-07 |
| Humanizer.Core.pt | 3.0.10 | 2026-03-07 |
| Humanizer.Core.pt-BR | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ro | 3.0.10 | 2026-03-07 |
| Humanizer.Core.ru | 3.0.10 | 2026-03-07 |
| Humanizer.Core.sk | 3.0.10 | 2026-03-07 |
| Humanizer.Core.sl | 3.0.10 | 2026-03-07 |
| Humanizer.Core.sr | 3.0.10 | 2026-03-07 |
| Humanizer.Core.sr-Latn | 3.0.10 | 2026-03-07 |
| Humanizer.Core.sv | 3.0.10 | 2026-03-07 |
| Humanizer.Core.th | 3.0.10 | 2026-03-07 |
| Humanizer.Core.tr | 3.0.10 | 2026-03-07 |
| Humanizer.Core.uk | 3.0.10 | 2026-03-07 |
| Humanizer.Core.uz-Cyrl-UZ | 3.0.10 | 2026-03-07 |
| Humanizer.Core.uz-Latn-UZ | 3.0.10 | 2026-03-07 |
| Humanizer.Core.vi | 3.0.10 | 2026-03-07 |
| Humanizer.Core.zh-CN | 3.0.10 | 2026-03-07 |
| Humanizer.Core.zh-Hans | 3.0.10 | 2026-03-07 |
| Humanizer.Core.zh-Hant | 3.0.10 | 2026-03-07 |
| Microsoft.IO.RecyclableMemoryStream | 3.0.1 | 2024-06-11 |
| MsgPack.Cli | 1.0.1 | 2019-02-03 |
| System.CodeDom | 4.4.0 | 2017-08-11 |

Build procedure, used for both the archived unchanged base and the integrated
source, with the audited local feed at `AUDIT/NuGet.Config`:

```sh
export PATH="$HOME/.dotnet:$PATH"
export DOTNET_ROOT="$HOME/.dotnet"
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
export DOTNET_PROCESSOR_COUNT=4
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
export AUDIT=${OOT_EVIDENCE_ROOT}/oot-stack
export NUGET_PACKAGES="$AUDIT/nuget-packages"
# SOURCE is either an archive of ee9b7765 or this checkout.
# PUBLISH is an isolated output folder, never the protected baseline.
dotnet restore "$SOURCE/dm/gfx/tools/dmsh_xlate/dmsh_xlate.csproj" \
  --configfile "$AUDIT/NuGet.Config" -p:NuGetAudit=false \
  -p:RestoreDisableParallel=true -m:4
dotnet publish "$SOURCE/dm/gfx/tools/dmsh_xlate/dmsh_xlate.csproj" \
  -c Release --self-contained false --no-restore -m:4 -o "$PUBLISH"
```

The isolated unchanged source was made with `git archive ee9b7765` of just
`dm/gfx/tools/dmsh_xlate` and `dm/third_party/ryujinx`. No source was edited in
that archive. An initial restore with `-r osx-arm64` requested framework runtime
packs outside the audited feed and failed closed without downloading them.
Publishing without `-r` produced the required AnyCPU managed assemblies and an
arm64 apphost using the installed SDK/runtime.

There is no x64 SDK/runtime installed. The newly built arm64 apphost was used
for the unchanged-base comparison. For the installed translator, the original
base's generic universal .NET launcher was retained. It contains no shader
translation logic and can launch the locally built AnyCPU assemblies. No x64
SDK or apphost package was downloaded; no new universal launcher was produced.
All managed publish files were copied over the base bundle, excluding that
launcher. Unchanged dependency files stayed byte-identical. Only locally built
project DLLs/PDB and the portable deps manifest changed. None of #1360's
replacement artifacts were installed or executed.

The repo tools then wrote the lock and header:

```sh
PY=${OOT_PYTHON}
"$PY" dm/gfx/tools/tool_lock.py --update-lock
"$PY" dm/gfx/tools/dmsh_chain.py --header
"$PY" dm/gfx/tools/tool_lock.py --check-tools
```

Committed tool fingerprints are `983bc9bc912cc136` for dmsh_xlate.dll,
`c4cf4e15992ec53e` for Ryujinx.Graphics.Shader.dll, and `33cc22f259005142`
for Ryujinx.Common.dll. Source digest remains `71adcdd020e03a64`.
SPIRV-Cross and compiler identities are unchanged. The lock tool also queries
the iPhone Metal compiler identity; it did not compile any iOS shader or app.
Scratch source archives, publish folders, NuGet caches/feed and local build
intermediates were removed after verification. Rebuilding later requires
recreating the audited feed and rechecking publication dates.

## Unchanged-source faithfulness

Four instruction fixtures from `test_dmsh_ampere_mem.py` were translated with
both the shipped ee9b7765 translator and the locally rebuilt unchanged source.
They cover SUATOM, a raw pointer load, a shared-memory store, and a raw 128-bit
load. All four SPIR-V files and all four reflection files are **byte-identical**.
SHA-256 prefixes, equal in both arms:

| Fixture | SPIR-V | Reflection |
| --- | --- | --- |
| SUATOM | `637190252608cdd9` | `e93791bf59d3a945` |
| Raw scalar load | `0a0f3aca17daef69` | `47673416be0051bf` |
| Shared store | `1ff0f4dbf408250c` | `ace62210142475fc` |
| Raw quad load | `e17775324efccd69` | `64ac2787a32851d4` |

This demonstrates faithful output for these fixtures, not byte reproducibility
of the managed assemblies or coverage of every shader instruction.

## Growing-table integration and safety

The host grows its table from 4,096 through powers of two up to 2^20 and writes
its capacity into entry 0 word 4. The translator loops over that count. The
existing hints retain their 12-bit entry index: the host only emits hints for
entries below 4,096, and higher entries take the complete search. Bitmap write
logs now allocate from their bound table size, and completion reads use the
original retained map's length, including when the current table has shrunk.
Tests cover learning a write above entry 4,095 and old-map completion.

#1405's original matcher does not recognize this helper. The integrated matcher
verifies the count-driven loop, optional exact hint prefix and scalar load tail,
and preserves the verified search prefix in the shared lookup. It also
recognizes the bit-cast address roots emitted by this base. The next-entry check
uses `table._m0[4]`, not the compile-time minimum. It still requires a complete,
four-byte-aligned 16-byte guest and GPU span inside the winning interval and
before the next start. Otherwise all four original scalar resolutions run.
Raw write-log shaders remain excluded by dmsh_build.py.

`fixtures/raw_global_growing.metal` records the actual emitted 128-bit fixture.
Tests reject altered counts, loop shifts, hint masks/range checks, interval
comparisons, carry comparisons and intervening side effects. The live translator
test emits the fixture again and compiles its optimized source with Metal.
A separate GPU probe ran the original and optimized emitted kernels against the
host's real 8,192-entry table with 5,001 ranges. All 179 checks passed, including
all four words, high entries, missing pools and reads crossing an interval end.

## Presentation experiment

The [#1405 PR text](https://github.com/seedds/nxnative/pull/1405) reports lower
GPU cost but higher enqueue-to-display latency at its direct-present 30 fps
cap. Those are upstream measurements, not measurements on this M4 Max.

The direct host path uses `presentAfterMinimumDuration:period`, while the host
acquire pacer retains an absolute phase after a small miss. A relative hold that
misses a refresh boundary can accumulate delay against that phase. This is a
plausible cause, not a proven root cause of the reported runs.

`DM_PRESENT_ABSOLUTE=1` uses `presentAtTime` and the existing `nvn_pace` policy
on Mac direct presentation. Small misses retain phase; a full-period stall
restarts it. Display-link or uncapped frames reset the experiment's phase.
Default behavior is unchanged. The offscreen test validates submission and
completion, not actual scanout timing. Keep this flag off for the first scalar
versus quad comparison, then toggle it with the same host and libraries.

## Verification

All commands used the specified uv venv Python, explicit TMPDIR, and at most
four build jobs or six package-fetch workers. No pip, pnpm or other package
manager installation ran.

- `python -m unittest discover -s dm/tools/tests`: **1,217 tests, OK, 23 skips**.
- `python dm/gfx/tests/test_dmsh_wide.py`: **11 tests, OK**.
- Integrated `test_dmsh_ampere_mem.py` with DMSH_TEST_XLATE set: **61 tests, OK**.
- `test_nsp_chain.py` plus `test_docs.py`: **28 tests, OK**, after the present docs.
- `tool_lock.py --check-tools`: clean.
- `dmsh_chain.py --header`: repeat generation leaves the committed header clean.
- `check_t_pool_chunks`: **95 checks, zero failures**.
- `check_t_gmem_raw`: **61 checks, zero failures**.
- Scalar/quad real GPU fixture comparison: **179 checks, zero failures**.
- `check_t_feedback`: **167 checks, zero failures**.
- `check_t_pace`: **250 checks, zero failures**.
- `check_t_present_alloc`: **19 checks, zero failures** with the new flag on;
  existing display-link allocator scenarios are included.

Graphics probes used GAME=0400486024DEC000 and Metal validation where their
check target enables it. Existing compiler warnings remain. No full graphics
suite or gameplay regression was requested or run. Parent review and gameplay
acceptance remain separate gates.

## Parent Mac A/B recipe

The committed header is the default scalar chain **9b29ea5a3be2**.
The quad chain is **40c099989c87**. The chain changed, so **each arm re-translates
all approximately 42,851 shaders**. Unchanged MSL may reuse Metal compiler cache
entries, but this is not a one-library swap.

These commands are for the parent to run after arranging independent prepared
inputs. They were not run here. Set the four required OOT_* input variables to
the parent's existing v131072 shader package, rewritten module directory,
RomFS image and save seed. Their exact locations under the protected game work
folder were deliberately not inspected. Do not change the profile's version
rows or extract/rewrite the game as part of this A/B.

```sh
cd .
export PATH="${OOT_PYTHON_BIN}:$HOME/.dotnet:$PATH"
export DOTNET_ROOT="$HOME/.dotnet"
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
export PY=${OOT_PYTHON}
export DM_GAME=0400486024DEC000 GAME=0400486024DEC000 J=6
export AB=${OOT_EVIDENCE_ROOT}/oot-ab
unset IOSOUT XLATE DMSH_RAW_LOAD_QUADS
: "${OOT_SHADER_PKG:?set to the existing v131072 shader package folder}"
: "${OOT_MODULES:?set to the existing rewritten v131072 module folder}"
: "${OOT_ROMFS:?set to the existing v131072 RomFS image}"
: "${OOT_SAVE_SEED:?set to an independent save seed folder}"
mkdir -p "$AB"

for arm in scalar quad; do
  if [ "$arm" = quad ]; then export DMSH_RAW_LOAD_QUADS=1
  else unset DMSH_RAW_LOAD_QUADS; fi
  "$PY" dm/gfx/tools/dmsh_chain.py --header
  "$PY" dm/gfx/tools/tool_lock.py --check-tools
  mkdir -p "$AB/$arm/profile" "$AB/$arm/run/temp" "$AB/$arm/run/save"
  "$PY" dm/gfx/tools/dmsh_build.py "$OOT_SHADER_PKG" "$AB/$arm/shaders"
  make -C dm/host -j6 GAME="$GAME" dmhost
  cp dm/host/dmhost "$AB/$arm/dmhost"
  cp dm/gfx/nvn/dmsh_chain.h "$AB/$arm/dmsh_chain.h"
  # Save each arm's matching c1/extent tables beside its map. Copying the
  # executable changes the relative lookup path, so set DM_NVN_SHMAP below.
  cp dm/games/0400486024DEC000/*.tsv "$AB/$arm/profile/"
  cp -R "$OOT_SAVE_SEED/." "$AB/$arm/run/save/"
done
unset DMSH_RAW_LOAD_QUADS
"$PY" dm/gfx/tools/dmsh_chain.py --header
```

Run one arm at a time with the same independent save seed, graphics settings,
scene, window/display mode, existing font/prewarm settings and other load.
Retain any required parent launch environment. Use the same DM_FONT_DIR as the
baseline, or point it at the parent's existing prepared font directory.
A direct host run for the first comparison is:

```sh
arm=scalar  # repeat with quad, then reverse the order with fresh save copies
DM_ROOT="$AB/$arm/run" DM_ROMFS="$OOT_ROMFS" \
DM_SAVE="$AB/$arm/run/save" DM_TEMP="$AB/$arm/run/temp" \
DM_MSL_DIR="$AB/$arm/shaders" DM_NVN_SHMAP="$AB/$arm/profile/shader_map.tsv" \
DM_PRESENT_LINK=0 DM_FPS=30 DM_PRESENT_ABSOLUTE=0 \
DM_NVN_TSV="$AB/$arm/run/frames.tsv" \
"$AB/$arm/dmhost" "$OOT_MODULES" > "$AB/$arm/run/host.log" 2>&1
```

Then repeat both arms with `DM_PRESENT_ABSOLUTE=1` to isolate the presentation
experiment from shader changes. Do not enable a VRR/game-speed modification.
Check the log accepts the expected chain and input stamp, with no stale
c1/extent table warning. Compare matched scene/dispatch windows, whole-frame
GPU work, frame intervals, drops, enqueue-to-display latency and energy per
frame at the 30 fps cap. A lower GPU duration alone is not acceptance if latency
or game speed regresses. No M4 Max gameplay, latency or energy claim is made here.


---

# Task F: Ocarina MSL waste mining

## Scope and boundaries

- Base `ee9b7765d579c46e45a7297493565e098f3bda33` (`oot-base`, PR #1299). Work branch `oot-msl`.
- Read-only source `${OOT_READONLY_GAME_ROOT}/0400486024DEC000_build/`. No builds, cache writes, gameplay runs, push, or GitHub comments.
- Corpus and compiler outputs in `${OOT_SHARED_CONTEXT}/msl-mining/`.
- Python `${OOT_PYTHON}`. All commands set `TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch`. No installs. At most four jobs.
- Parent owns independent review, integration with A2, full shader rebuilds, and M4 Max gameplay A/B. A source-site count or successful Metal compile is not GPU performance proof.

## Decision log

1. Read AGENTS.md, shader reference, existing wide-load tests, cache publication code, and A2's raw-load quad implementation. Keep new work separate from #1405.
2. The baseline was still compiling. The requested `shader/cache/cas.db` does not exist in this build. Its actual chain is `d1f10abd26a7`, using the old folder cache. The current main checkout has `shader_cache.py`, but the task's base predates it. No database opened or modified.
3. Use only completed old-cache publications. `publish_cache()` in `dmsh_build.py` writes each digest's output files first and atomically writes `cas/index/<key>.json` last. Snapshot those immutable indexed entries, requiring MSL, reflection and metallib. Never read the live `b-*/` MSL while it is being compiled. The mining tool also supports the newer database through the repo's own Store reader with read-only SQLite and disabled recovery writes.
4. Select the lowest SHA256(shader ID) per stage among the published entries at snapshot. This is a deterministic stage-stratified sample, not a claim of representativeness of the unfinished build or runtime draws. Count only main0, so generated output variants do not multiply counts.
5. Costs are explicit instruction-equivalent guesses. Compute and pixel sites contribute to the hot score; other stages are reported separately. No GPU cost in milliseconds is inferred.

## Plan and deviations

Use the pstack prototype checklist. Scope the empirical question, gather prior passes, build corpus and prototypes, expose default-off switches, verify synthetic and real MSL, and report a recommendation. The user explicitly requires source and tests in the repository, overriding the generic throwaway-only prototype location. No child agents are launched because this task is itself the research sub-agent lane. Parent must supply independent review.

The Explain the Number principle requires labeling static scores as guesses. Prove It Works requires compiling changed real sources and comparing behavior where feasible; a GPU frame-time claim remains outside this lane.

## Corpus and pattern table

Snapshot `corpus-1/manifest.json` names every source, original cache entry, SHA256, size, source package and chain. It holds 2,373 shaders (261 MiB on disk): 1,024 compute, 1,024 pixel, 295 mesh, 10 task and 20 vertex. The publication snapshot offered 2,503 compute, 13,693 pixel, 295 mesh, 10 task and 20 vertex. The profile contains 4,123 compute, 22,356 pixel, 500 mesh, 20 task and 15,852 vertex keys (42,851 total). Thus vertex coverage is very poor, and even compute/pixel selection covers only the already-published portion. Do not extrapolate these numbers to the whole corpus or a frame's shader mix.

A correction during analysis added `dm_stage_body` to the primary mesh/object entry. Counting only a `kernel` or `fragment main0` had missed mesh bodies. Final counts include that helper once and exclude generated integer/dual-source variants.

`report-final.json` contains the rerunnable detailed report. C/P/M/T/V mean compute/pixel/mesh/task/vertex source sites. Score is (C + P) × the guessed cost per site. Mesh and task sites are reported but excluded from that requested hot-stage score. Raw cost 80 assumes a full pool-table search; the hinted path is cheaper. The broad constant-repeat row and the strict-reuse row overlap and must not be added together.

| Pattern | Count | C / P / M / T / V | Guessed cost per site; hot score | Example shader ID |
|---|---:|---|---|---|
| Independent raw pool-table load calls (existing #1405 lane) | 31,887 | 31,115 / 0 / 772 / 0 / 0 | 80; 2,489,200 | `96843c3dbdded1e7` |
| Repeated literal constant words (broad candidates) | 81,556 | 3,552 / 45,122 / 31,972 / 905 / 5 | 4; 194,696 | `78f695ad8ec2f1a3` |
| Constant reads removed by strict prototype | 46,188 | 3,072 / 23,799 / 18,416 / 896 / 5 | 4; 107,484 | `78f695ad8ec2f1a3` |
| Calls to optnone spvFAdd (preserved) | 501 | 0 / 501 / 0 / 0 / 0 | 8; 4,008 | `6a3dbd7c875b9f22` |
| Storage word addresses shared by strict prototype | 4,816 | 0 / 115 / 4,690 / 11 / 0 | 6; 690 | `7f36d56444efdd1c` |
| Repeated exact texture dimension queries | 163 | 85 / 72 / 6 / 0 / 0 | 4; 628 | `2da742366934d2a3` |
| Nested as_type round trips | 0 | 0 / 0 / 0 / 0 / 0 | 0; 0 | none |
| Precise min/max/clamp (required semantics) | 82,747 | 7,051 / 73,229 / 1,983 / 484 / 0 | 0; 0 | `5c7a86728b475517` |
| Local arrays of at least 256 words | 10 | 1 / 0 / 9 / 0 / 0 | 0; 0 | `5c7a86728b475517` |

## Prototypes and compiler evidence

Both switches default off and enter `dmsh_chain.options()`, so the chain version and per-shader tool fingerprint separate A/B outputs. The new module is in both the chain's FILES list and CODE_FP. Preserve A2's `raw_load_quads` option when integrating the options string. Neither prototype changes raw-memory helpers or duplicates #1405.

- `DMSH_CBUF_REUSE=1`: reuse only literal components of verified constant float4 arrays. No speculative address or changed arithmetic. Writes, barriers and braces end reuse regions. Unknown layouts, dynamic indices, out-of-bounds literals and block comments fall back unchanged. Explicit locals may change scheduling/register lifetime even when Metal already performs common-subexpression elimination.
- `DMSH_STORAGE_RUNS=1`: widen read-only storage runs starting at any four-byte step, beyond #994's 16-byte grid. All address definitions stay within a pure straight-line region. Unknown calls, writes, barriers and braces close it. Already-transformed names and multiline or unterminated block comments fall back unchanged. Inline comments terminate a region. The original byte sums wrap at 32 bits; a vector that would cross that wrap falls back to scalar indices modulo 2^30. Wider loads are only four-byte aligned and read exactly the originally requested words.

The second candidate was selected despite its lower C/P score because mesh bodies have many eligible sites and the transform preserves arithmetic. `spvFAdd` is not rewritten: its no-contraction behavior needs a separate floating-point proof. Precise min/max/clamp are explicitly required by the shader reference's NaN case.

Four real before/after source pairs compile with `xcrun -sdk macosx metal -c -O1 -fpreserve-invariance`. Textual AIR comes from the same options with `-S -emit-llvm`. The table counts opcodes in the primary `main0` definition, after inlining; it is not backend machine code or a GPU measurement.

| Pass and stage | Shader ID | Source sites removed/shared | AIR instructions before → after | AIR loads before → after |
|---|---|---:|---:|---:|
| cbuf_reuse_removed_reads (ps) | `78f695ad8ec2f1a3` | 296 | 1814 → 1814 | 99 → 99 |
| cbuf_reuse_removed_reads (cs) | `8f9cdc220f1625ef` | 226 | 5766 → 5430 | 317 → 275 |
| storage_runs_saved_addresses (ps) | `69444ddb014ddc59` | 2 | 4920 → 4916 | 331 → 331 |
| storage_runs_saved_addresses (ms) | `7f36d56444efdd1c` | 32 | 3211 → 3207 | 160 → 170 |

The constant compute case also reduces AIR branches from 444 to 318. The pixel constant case has the same opcode histogram, so its 296 source repetitions cannot be claimed as saved GPU instructions. Storage's pixel case removes only four AIR instructions. The mesh case removes 32 shifts and 26 extensions but adds 12 branches and 10 loads from wrap fallbacks, for a net four-instruction reduction. That can regress on the GPU.

Recommendation: first A/B constant-word reuse on compute-heavy scenes. Keep storage grouping separate and default off. Do not enable either globally based on these counts. Check whether the example compute shader is actually dispatched in Kokiri Forest, its invocation count and its GPU cost before predicting any frame saving. All GPU frame-time, energy, occupancy and image-equivalence results remain open.

## Reproduce mining and compiler checks

Run from this worktree. Source game data remains read-only. Output folders must be new. `snapshot` uses only the repository's read-only cache inspection functions from the old build module, loaded by AST without importing/running the build. For cas.db it uses Store with SQLite mode=ro and disabled schema/recovery writes. Database extraction follows each current index digest, avoiding duplicate historical versions.

```sh
export TMPDIR=${OOT_SHARED_CONTEXT}/setup/scratch
task_py=${OOT_PYTHON}
task_work=${OOT_SHARED_CONTEXT}/msl-mining
task_build=${OOT_READONLY_GAME_ROOT}/0400486024DEC000_build
# Reuse the existing snapshot for exactly the reported counts.
"$task_py" dm/gfx/tools/dmsh_mine.py report "$task_work/corpus-1" "$task_work/report-replay.json"
"$task_py" dm/gfx/tools/dmsh_mine.py compare "$task_work/report-replay.json" "$task_work/compile-replay"
# To take a newer, independent publication snapshot with the old folder cache:
"$task_py" dm/gfx/tools/dmsh_mine.py snapshot "$task_build/shader/cache/cas" "$task_work/corpus-parent" --per-stage 1024
# For the newer cache format, use cas.db instead and add:
# --reader ./dm/tools/shader_cache.py
"$task_py" -W ignore::ResourceWarning -m unittest dm/gfx/tests/test_dmsh_reuse.py dm/gfx/tests/test_dmsh_mine.py dm/gfx/tests/test_dmsh_wide.py dm/tools/tests/test_dmsh_code_fp.py dm/tools/tests/test_nsp_chain.py
```

## Parent A/B recipe (not executed here)

This branch is rebased onto A2's completed `oot-stack` commit `8284776d` (#1360/#1405/#1161 and its default-off presentation experiment). All three shader flags are retained, and constant reuse runs after raw quads. When picking the commit onto a newer parent, preserve that option composition and regenerate the header. Run the tests on that integrated tree. The sampled baseline's old hinted/static raw helper is not accepted by A2's growing-table quad matcher, so this corpus cannot establish post-#1405 coverage. Re-mine the parent's freshly translated output before attributing an incremental gain over #1405.

The following builds only into new scratch directories, reads the existing package, and copies one matching host per chain. It must be run by the parent, not this research lane. Do not point any output or DMSH_CAS at the baseline folder. Each variant keeps #1405 ON. A/B the two new switches independently before trying both.

```sh
unset DMSH_CAS IOSOUT DMSH_TARGETS
export DM_GAME=0400486024DEC000 DMSH_RAW_LOAD_QUADS=1 J=4
for task_variant in base cbuf storage; do
  export DMSH_CBUF_REUSE=0 DMSH_STORAGE_RUNS=0
  if [ "$task_variant" = cbuf ]; then export DMSH_CBUF_REUSE=1; fi
  if [ "$task_variant" = storage ]; then export DMSH_STORAGE_RUNS=1; fi
  task_output="$task_work/ab/$task_variant"
  mkdir -p "$task_output"
  "$task_py" dm/gfx/tools/dmsh_chain.py --header
  "$task_py" dm/gfx/tools/dmsh_build.py "$task_build/shader/pkg" "$task_output/msl" > "$task_output/shaders.log" 2>&1 || exit 1
  make -C dm/host -j4 GAME="$DM_GAME" > "$task_output/host.log" 2>&1 || exit 1
  cp dm/host/dmhost "$task_output/dmhost"
done
```

The base has no Ocarina `bench.tsv` route. The parent benchmark lane must provide a validated route and fixed slot-00 Kokiri Forest save. Set `OOT_BENCH_ROUTE` and `OOT_BENCH_SAVE` to those exact inputs; do not substitute an unverified title-menu sequence. Keep resolution, camera, save and all runtime switches identical. Stop concurrent shader builds and other GPU workloads before measurement. The benchmark copies saves and writes only to `--out`, outside the baseline folder.

```sh
"$task_py" scripts/bench.py "$task_build" \
  --route "${OOT_BENCH_ROUTE:?set the validated Kokiri Forest bench route}" \
  --save "${OOT_BENCH_SAVE:?set the fixed Kokiri Forest save}" \
  --fps 30 --runs 6 --pso-archive off \
  --variant "base:host=$task_work/ab/base/dmhost,msl=$task_work/ab/base/msl" \
  --variant "cbuf:host=$task_work/ab/cbuf/dmhost,msl=$task_work/ab/cbuf/msl" \
  --variant "storage:host=$task_work/ab/storage/dmhost,msl=$task_work/ab/storage/msl" \
  --out "$task_work/ab/forest"
```

Check screenshots and new red lines first. Compare paired per-run GPU p50/p95/p99 and dropped/over-budget frames, not FPS alone at the 30 fps cap. Run a separate matching pair with `--env DM_NVN_GPUPROF=every:60` into a new output folder to attribute changed passes; profile overhead is not clean frame timing. Repeat with reversed variant order if the result is small. Require matching pictures and a stable GPU reduction before enabling a flag. Restore the default-off header after experiments and rebuild the production host for the chosen chain. Keep each compiled host beside its own chain's shaders.

## Validation and remaining gates

- Synthetic transforms, scalar wrap arithmetic, fallback conditions, default-off flags/cache-version separation, snapshot completeness and primary-entry counting are unit-tested.
- Four real shader A/B pairs compile. Detailed `.metal`, `.air`, `.ll`, compiler logs and `results.json` remain under `compile-final/` in the assigned scratch folder.
- No full chain, host build, gameplay, production cache write, push or GitHub comment was run in this lane. Five-game regression and independent review are parent gates under the explicit no-full-chain boundary.
- No runtime speedup is claimed. The sample is from the unfinished baseline, not from A2's new translator; incremental post-stack behavior requires the parent's rebuild.

### Pre-stack checks

- 53 selected transform, miner, chain/cache and documentation tests pass.
- The default wide-load mode matches the original `ee9b7765` implementation on all 2,373 corpus sources, with zero differences (`default-parity.json`).
- New tools/tests pass direct Ruff and Pyright checks. The full repository lint check reports 392 findings against 389 baseline entries. Its three added findings are in unchanged base tests: `test_nsp_mac.py:176-177` (assigning `NSP_FOLDER` on a ModuleType) and `test_tree_tar.py:107` (float supplied for integer `days`). Both source fragments were verified with `git show ee9b7765:<path>`. They remain outside this lane's scope; the lint check is not green.
- Use plain-writing for the research log and commit prose. No review delegate was run because the user assigned this lane as a sub-agent. Independent review remains with the parent.


### Final integrated checks

- Rebased onto `oot-stack` at `8284776d`. A2's raw-quad matcher and helpers are unchanged. Its implementation log is preserved above this Task F section.
- Storage matching now requires scalar declarations in each pure region and rejects increment/decrement, nested assignments, arbitrary stores and unknown calls. Inline `/* inf */` annotations terminate a region; multiline/unterminated comments fall back unchanged. The final full-sample storage recount is 4,816 shared word addresses across 341 shaders: 115 pixel, 4,690 mesh and 11 task. The table and `report-final.json` contain those final counts.
- The four compiled candidate sources exactly match the final integrated transforms. Exact primary-entry AIR counts were independently re-read from their `.ll` artifacts; all match the compiler table. None of the sampled sources contains a multiline comment.
- 59 integrated transform/miner/raw-quad/chain/cache/docs tests pass. Six impact-map tests also pass (65 selected tests total). Full repository lint still has exactly the same three unchanged-test findings described above; no additional finding belongs to these tools or tests.
- Default-off chain is `600b458bd0d1`. `DMSH_RAW_LOAD_QUADS`, `DMSH_CBUF_REUSE` and `DMSH_STORAGE_RUNS` compose without discarding a flag. Every variant needs its own regenerated header and matching host.
- Read-only `regress.py impact` ran. It initially reported both new tools as unmapped; the map now marks constant reuse as affecting NVN shader stages when enabled and the miner as offline analysis only. Most profiles have no usage manifest, so absence from the affected list is not proof of no reach.
- Suggested parent regression set: Ocarina (`0400486024DEC000`, target compute/pixel/mesh), Splatoon Raiders (`0400380020056000`, established wide-load sensitivity), Donkey Kong Bananza (`040074A01BF12000`, Ampere compute), Tears of the Kingdom (`0100F2C0115B6000`, existing storage lowering), and Breath of the Wild (`01007EF00011E000`, constant/driver-buffer consumers). Not run because this lane forbids full chains and game builds.

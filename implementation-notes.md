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
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
export DOTNET_PROCESSOR_COUNT=4
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
export AUDIT=/Users/ankur/Documents/Crypt/Projects/_work/nxnative/oot-stack
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
PY=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python
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
cd /Users/ankur/.t3/worktrees/nxnative-oot/t3-91962084
export PATH="/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin:$HOME/.dotnet:$PATH"
export DOTNET_ROOT="$HOME/.dotnet"
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
export PY=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin/python
export DM_GAME=0400486024DEC000 GAME=0400486024DEC000 J=6
export AB=/Users/ankur/Documents/Crypt/Projects/_work/nxnative/oot-ab
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


# Ocarina visual correctness ports

Branch `oot-visual` starts at `oot-stack` (`e7c50787`). Source ports follow the
requested PR order. No PR binaries, locks or generated headers are imported.
The translator will be rebuilt once after all source changes. New translator
paths require `DMSH_OOT_VISUAL=1`; its value is part of the shader chain stamp.
Host and splitter gates are described below. No game run or full shader build
is allowed in this task. Tests on the rebuilt translator follow at the end.

## #1300: adapted

Head `e3f8ef8c6d982f7d5e07c3c70c0daa6a34db23a0`, including `06f47f57`.
Imported the C# F2IP and ISBERD changes and their ALU and memory fixtures.
Added the default-off gate and chain option required by agent-context.md.
F2IP accepts unsigned byte conversion with C=RZ only, rounds by bits 78..79
(nearest even, floor, ceiling, truncate), clamps to 0..255, maps NaN to zero,
and packs B low and A high. CuAssembler's sm_86 nvdisasm records independently
identify `04ff` as U8.F32.NTZ. NVIDIA PTX's cvt rounding and narrow integer
saturation rules support the numeric model; its cvt.pack uses the same B-low
order. The game's PRMT/store sequence provides additional packing evidence.
Neither PTX alone nor Lichii proves undocumented SASS behavior on hardware.
ISBERD b8 reads the output payload at stage[2], matching the 927 b8 store;
the PR identifies a write at +0x70 and read at +0x80 in task 5d3a096025e375a1.
Expected symptom improvement is missing foliage and rejected task draws.
Risks remain untested console parity, unsupported signed/C-merge forms, and
visual acceptance. No source bug found in the supported encoding so far.

Semantics sources:
- https://docs.nvidia.com/cuda/parallel-thread-execution/
- https://github.com/cloudcores/CuAssembler/blob/master/CuAsm/InsAsmRepos/DefaultInsAsmRepos.sm_86.txt
- https://github.com/seedds/nxnative/pull/1300

# Ocarina Mac stack implementation notes

Current branch: `oot-visual`. The visual-port results and activation flags are in
[Ocarina visual correctness ports](#ocarina-visual-correctness-ports) below.
The original `oot-stack` report is retained as provenance.

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

Branch `oot-visual` starts at `oot-stack` (`8284776d08b215e56c67acbcd5f54d1abacb71e3`). Source ports follow the
requested PR order. No PR binaries, locks or generated headers are imported.
The translator was rebuilt once after all C# source changes. New translator
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

## #1359: adapted

Head `34d04efbe93ba88f5c82f0bcf2ac264218f79e4a`. Imported its RED/ATOMG
float-add CAS lowering and memory fixtures. Enabled only for global F32FtzRn
under `DMSH_OOT_VISUAL=1`; shared float adds have different denormal semantics.
NVIDIA PTX documents round-nearest-even and sign-preserving FTZ for inputs and
results of global atom/red.add.f32. A native Metal float atomic add cannot
independently flush the accumulator and result, so the CAS implementation stays.
Found and fixed two source issues: FlushDenormal loses negative zero's sign;
the initial ordinary load races with atomic writes. The adapted helper flushes
by exponent/magnitude bits and keeps the sign. The initial read uses CAS(0,0).
Expected symptom improvement is the washed-out outdoor scene from missing sky,
probe and shadow accumulation. Numeric/concurrency GPU results are recorded in the final verification below. Risks include CAS contention and console NaN payload
parity; gameplay remains unverified.

## #1312: adapted

Head `ac0244286663545b5980509b0133bc2b47295da7`, including `9cb1fe2a`.
Imported host/Metal sources and the mesh-indirect, image-usage and deferred
release tests. No lint baseline or binaries imported. Integer-image upgrades
and the equivalent deferred-release partition require `DM_NVN_VISUAL=1`.
Indirect mesh draws require `DM_NVN_MESH_INDIRECT=1`. The API takes only a
command buffer and address, consistent with the v0 call-site probe.
The PR assumes {count, first}, matching GL/VK NV_mesh_shader, and converts it
on the GPU to Metal XYZ plus the first-task uniform. This is not proof of NVN2
layout. Added a completion log of the first eight records and an explicit
provisional-layout warning. Zero-count and GPU-produced records have fixtures.
Image atomics use R32 integer storage with an RGBA8 color view, retaining heap
lifetime. The image test checks a clear survives and atomic OR reaches the color
view. Expected improvements are missing mesh/texture effects; no picture tested.
Risks include unverified NVN2 layout and resource/view lifetime across full
gameplay. Converter synchronization is retained from the PR for correctness.

## #1343: adapted

Head `6941aa847dee2eeec66da4734f192067158a2269`. Imported the optimizer
change and SurfaceLoadLiveness fixtures, behind `DMSH_OOT_VISUAL=1`.
A multi-result load with one live result must retain all its input uses.
Checking only side effects recursed into the producer after detaching a dead
component and deleted coordinates still needed by another component.
The PR's IsUnused check preserves those inputs and still removes wholly dead
loads. Tests cover both component orders and side-effecting atomic addresses.
Expected improvement is foliage simulation jitter. No semantic issue found;
full-game optimizer coverage and visual acceptance remain unverified.

## #1390: adapted

Head `16e86fdc17543e7bc2b247c5763252d573cc89e6`. Imported host range
tracking and CPU texture/storage tests. Resolved the test conflict by keeping
#1360's finalized-bindless-pool test and adding the range tests.
`DM_NVN_VISUAL=1` selects range ownership; off preserves whole-pool ownership.
The ranges merge, split and disappear with their pool. Render targets, image
stores, clears and copy destinations mark their own storage instead of the
whole pool. The tests cover adjacent/overlapping tiles and reused storage.
Expected improvement is the missing ground and floating stone path, because
CPU-filled height tiles can coexist with GPU-written textures in one pool.
No source bug found in the reviewed range algorithms. Aliased pools and full
gameplay ordering remain risks; no game run was made.

## #1353: adapted

Head `5ec8a62b7114516e8c25fb1d5bb23832767e3778`. Imported the entry-wise
NDSR reader and synthetic pack tests. `DMSH_OOT_VISUAL=1` enables the 8-byte
walk; off retains the 16-byte walk. Fixed a source edge case: the entry-offset
score used iter_unpack on a potentially incomplete slice, which throws for a
short pack at candidate offset 0x14. It now inspects only complete entries,
with a regression fixture. Expected improvement is recovery of d17eefaff4f0bc23
(SMAA weights), reducing stair-stepped foliage/prop edges. The targeted extraction
verified its update-build presence; the repository map is not regenerated.
The shader must be added to the parent's map and rebuilt before gameplay.

## #1357: adapted

Head `072f8674caf07ac45067393004399efc97754b60`. Imported the Mac
compiler-depth change and BracketDepth tests. `DMSH_OOT_VISUAL=1` enables
-fbracket-depth=1024. Per the Mac-only context, no iOS source was changed and
the new iOS test was omitted. The fixture compiles 300 nested parentheses and
checks unchanged byte output within the old limit. Expected improvement is
restoring compute work from 1f78730053feb036 and e172bd7ec218ab8e. No semantics
change is intended. Full generated expressions will be compiled when extractable.

## #1368: adapted

Head `9c53d9ae5c10e53b69ee3408bb01ace333730207`, including `7cd6750b`.
Imported native mesh prewarm/key code and PSO key/warm tests. Preserved #1312's
indirect state and write tracking in the overlapping mesh draw.
`DM_NVN_VISUAL=1` selects required synchronous compilation and M-row prewarm;
off keeps the old asynchronous pipeline path in a separate cache.
The serialized key includes mesh, fragment and optional task function identity,
and warm results are installed only for the live functions they were built for.
Expected improvement is first-use foliage that previously vanished while its
pipeline compiled. No source bug found in the reviewed key/publication paths.
A required first-use compile can stall submission; prewarm benefits need a
matching captured M row. Gameplay and prepare-screen behavior remain untested.

## #1128: adapted

Head `6c13132839606c4305fbe8830655a5b82e887c16`. Imported the limit16
rewriter, format selection and side-library loader, and its Python/host tests.
Adapted the old separate alpha/logic-library code to this stack's combined
_bx library without replacing the alpha loader. Preserved NVN2 high-attribute
keys. Generation requires `DMSH_OOT_VISUAL=1`; selection requires
`DM_NVN_VISUAL=1`. Mac only. Float32 attachments retain the original values.
Reviewed closed #1149 at `fa565c1c2f3257dd820ea670ab5ab29182d5fe15` only as
a reference. Its global NaN/Inf-to-zero and varying changes are not imported.
Found and fixed a numeric source issue in #1128: precise::clamp turned NaN
into a finite bound on the M4 Max. The helper now preserves NaN using a bit
test. A GPU regression failed before the change and passes after it.
The #1128 patch clamps only outputs copied from constant buffers, to +/-65504.
It deliberately leaves computed overflow, mixed limited Float16/Float32
outputs, alpha-tested draws and specialized tile fragments outside coverage.
Therefore it is a narrow overflow correction, not a general bloom cure.
Expected benefit is removing bright dots/blobs where that exact constant-output
pattern overflows a Float16 target. No Ocarina occurrence or picture is claimed.
The tests check rewrite scope, target formats, loading and Metal compilation.
Risks include heuristic MSL matching and limited path coverage.

## Upstream 95f9a6a9: adapted

Source `95f9a6a929ede91ab35177987aa8fa15a7dfa031`. Imported the AVote
uniform destination correction and Vote fixtures, retaining #1300's tests.
`DMSH_OOT_VISUAL=1` selects the fix. The opcode 886 destination is UPd,
not Pd; vote input and instruction guard remain lane predicates. Tests check
UP use, preservation of the lane predicate and unchanged VOTE behavior.
Baseline reproduced two failing Vote tests before the port. Expected effect
is correct subgroup guards, potentially restoring effects selected by them;
Ocarina-specific visible impact is unmeasured. No source bug found.

## Upstream 4a0551e4: adapted

Source `4a0551e4b9abc75ea736006e4dbd30fcac0d03a4`. Imported guarded
bindless handle resolution and phi-lookup changes with six guarded-read fixtures.
`DMSH_OOT_VISUAL=1` enables the changed candidate/undefined-phi rules.
The full texture|sampler candidate supersedes an intermediate texture-only
word, handles can come from the game's own constant bank, and a nested phi's
one-defined-input shortcut must not resolve an outer handle prematurely.
Expected improvement is missing guarded texture effects; Yoshi water is the
upstream motivating case, not an Ocarina picture demonstrated here.
Risks include handle provenance assumptions at unmatched guards and shader
shape coverage. No additional source defect found during this port.

## Remaining foliage opcode 0x3a9: source port

Issue #1347 also names global compare-and-swap, which #1300 does not implement.
Ported only AAtomgCas and its registration from existing source commit
`6f973380` (also present in `42203e33`), behind `DMSH_OOT_VISUAL=1`.
CuAssembler sm_86 records identify 3a9 as ATOMG.E.CAS, with extended-address
bit 72, expected B, replacement C, and old-word result D. Added a refusal for
non-PT predicate results instead of silently dropping that output. Only the
32-bit non-uniform form is accepted. A fixture uses the exact issue encoding.
This closes a further foliage translation gap. Console parity and ordering
beyond the translator's existing relaxed atomic model remain unverified.

## Final source build and verification

All nine requested PRs were adapted, not rejected. Their semantic source changes
were preserved except for the corrections and default-off gates described above.
No stability PR was imported. No push, PR or GitHub comment was made.

The translator was published once after the C# source ports, from source at
`afcd2b35`. The later changes affect tests, host gates, documentation and the
MSL Float16 helper, not the C# translator. The exact NuGet procedure in the
original stack report was reused with AUDIT set to
`/Users/ankur/Documents/Crypt/Projects/_work/nxnative/oot-visual`. Every one
of 57 versions was rechecked against nuget.org publication dates before its
nupkg was downloaded. All four restored project.assets.json manifests were
checked against that allowlist. Restore had only the isolated local feed,
NuGetAudit=false, RestoreDisableParallel=true, and -m:4. Publish used Release,
--self-contained false, --no-restore, -m:4 and no runtime ID. No dependency
version changed, no package manager install ran, and no cooldown exception
was needed. SDK 10.0.403 / runtime 10.0.14 were already installed.

Managed publish files replaced the bundle's managed files. The original
universal launcher was preserved. tool_lock.py --update-lock and --check-tools
measured the new assemblies and checked the source digest; dmsh_chain.py
--header regenerated the default header. Fingerprints are 9b609a2568155e59
(dmsh_xlate), 66d4494b62bda954 (Shader), and 344250bc9832022b (Common).
The embedded source digest remains 71adcdd020e03a64.

- Full tools suite: **1,223 tests, OK, 23 skips**.
- Final chain/cache/docs/compiler-depth/Makefile checks after the Float16
  helper correction: **57 tests, OK**.
- Ampere translator suites, with the installed rebuilt translator: **90 tests, OK**.
  Feature-specific tests set their own opt-in flag.
- Numeric Metal execution: **3 tests, OK**, containing 64 packed F2IP cases
  across all four rounding modes, 10 RED cases including signed input/result
  FTZ, RN tie, infinity, NaN and a contended 128-thread add, and 7 Float16
  clamp cases including NaN and negative zero. Numeric fixtures use the Mac
  build's -O1 and -fpreserve-invariance flags.
- Float16 rewrite/compile suite: **3 tests, OK**, Mac only.
- Host fixtures: indirect mesh GPU conversion and disabled-path gate; integer
  image aliasing (**50 checks**); deferred release order/retention; CPU storage
  (**32 checks**); CPU texture ranges and inherited finalized pool tests
  (**71 checks**); serialized PSO keys; native mesh warm/load/claim/draw
  (**114 checks on each of MTLDevice and Metal 4**); Float16 selection/loading
  (**15 checks**). All pass.
- The disabled translator matches oot-stack on four existing fixtures: all
  four SPIR-V files and all four reflection files are byte-identical.
- Added source-cache and environment-switch declarations. The two old doc-only
  switches DM_NVN_CUT_FIRST and DM_NVN_HANGLOG still produce informational
  warnings from the inherited notes; they are not implemented here.

The first tools run exposed missing cache/switch declarations; these were fixed.
A subsequent run saw the numeric helper before it was excluded from make run;
NOT_RUN now names it because the Python test builds and drives it.
The imported prewarm fixture hardcoded /tmp. Its first run removed its folder
on completion; it was changed to require TMPDIR and subsequent runs used the
authorized scratch directory.

Python lint has no findings in changed code. It still fails overall on three
pre-existing findings in unchanged test_nsp_mac.py (two) and test_tree_tar.py
(one). C compile-database generation succeeds (239 sources). clang-tidy is
not installed, and the no-install rule prevented running C lint. No baseline
was raised to hide findings. Existing Objective-C compiler warnings remain.

## Extracted game fixtures

Read only the v131072 extract named in the task. Used shader_split's RomFS
image reader and zstd dictionaries to scan three relevant archives, retaining
only the ten requested target programs. The package/map in the running game
workspace was not written. Records, jobs, SPIR-V, MSL, AIR and diagnostics are
in the audit folder's `fixtures/`. No raw game bytes are committed.

| Key | Coverage | Rebuilt translation / Mac Metal compile |
| --- | --- | --- |
| 604134a5262ff670 | Kokiri foliage mesh, F2IP truncate | PASS / PASS |
| ecead5cd0569091f | Kokiri foliage mesh, F2IP truncate | PASS / PASS |
| fed302d791a4ba43 | Kokiri foliage mesh, F2IP truncate | PASS / PASS |
| 8692b34b521225be | foliage compute, two-source F2IP | PASS / PASS |
| 83df46a0b1b379b4 | foliage compute, two-source F2IP | PASS / PASS |
| 5d3a096025e375a1 | ISBERD b8 task payload | PASS / PASS |
| 21d9f83e6027c565 | sky analysis RED.F32.FTZ.RN | PASS / PASS |
| d17eefaff4f0bc23 | recovered NDSR SMAA weights | PASS / PASS |
| 1f78730053feb036 | deep compute expression | PASS / PASS |
| e172bd7ec218ab8e | deep compute expression | PASS / PASS |

The oot-stack translator produced 4 SPIR-V files and rejected 6 of those jobs
(5 F2IP programs and the b8 task shader). The new translator produces all 10.
The sky analysis shader previously logged 12 dropped F32FtzRn operations;
its rebuilt reflection has no translator notes. Both deep compute MSL files
(about 3.53 MB each) fail at the default bracket limit and compile with 1024.
The fixture pipeline uses the repo's set flattening, SPIRV-Cross, precise
float rewrite, HMMA rewrite where applicable and task/mesh wrapper, followed
by xcrun metal for macosx. No full shader build or game was run.

## Activation and remaining gates

The committed default chain is **88f31285d646**. With DMSH_OOT_VISUAL=1 and
raw-load quads off, it is **b79eeb29fe00**. The parent must set the desired
flags consistently, regenerate the header, and build matching shader libraries
and host. An enabled translator experiment with a disabled-chain host is not
a valid comparison. The existing DMSH_RAW_LOAD_QUADS option is preserved.

- Build/split opt-in: `DMSH_OOT_VISUAL=1`.
- Host visual ports: `DM_NVN_VISUAL=1`.
- Provisional indirect mesh layout: `DM_NVN_MESH_INDIRECT=1`, separately.

Regenerate the parent's shader map to include d17eefaff4f0bc23, using the
entry-wise splitter. No profile shader map was rewritten here.
Default behavior remains opt-in; four disabled shader fixtures prove only
those fixtures' equivalence, not the whole corpus.
The parent still owns independent code review, NVN2 record-layout validation,
full shader/host rebuild, and Kokiri Forest visual/gameplay acceptance.
No FPS, memory, energy or image-correctness claim is made from compilation.

The installed local translator and its lock/header are committed in the final
verification commit. Isolated NuGet feed/cache, publish output, baseline bundle
and the C# build intermediates were removed after verification. Audit dates,
scripts, logs and the requested small shader fixtures remain in the audit folder.
Rebuilding requires rerunning its audit_nuget.py to recreate the cooled feed.


## Brent source harvest

This branch starts at oot-visual 622f5191. Only source patches are read from
brent-oot-combined a54b2092. Its translator binaries, lock and header are excluded.
The parent owns independent review and gameplay acceptance. No nested agents,
game run, shader corpus build, push or PR is authorized here.

- #1376 / 2d6f86f8 puts LDSM shared reads between subgroup barriers. It uses
  DMSH_OOT_VISUAL so disabled output keeps the existing translation. The upstream
  emitted-MSL ordering test is retained. Translator execution waits for our one rebuild.

- #1388 / c8aeba86 uses a four-byte search for validated control pairs, then
  consumes the complete shader record. #1353's entry-wise tests remain, and
  #1388's vertex/pixel pairing tests are added. Disabled split behavior is retained.

- #1345 / d7a43c2a reads SDK 20+ UpdateImpl's lock offset rather than using
  SDK 20's fixed +0x2d0 on SDK 22 (+0x2d8). DM_OOT_BRENT=1 enables it.
  NDSR tests pass with the required explicit DM_GAME (9 tests).

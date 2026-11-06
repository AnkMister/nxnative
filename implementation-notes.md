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

# Ocarina GPU safety branch

Base: `oot-stack` at `8284776d`. Work is source only. No game, shader build,
regress.py, protected game workspace writes, package installation, push or PR.
The user explicitly requests local commits and default-on safety for this build;
that overrides the shared context's default-off rule for the safety net.

Read issue #1326 body and all 21 comments from the saved GitHub JSON. The raw
pool table and the 262,144-entry dirty tracker are different tables. Comments
6 and 8 identify task-shader underflow into 2^27-1 loop iterations after missing
raw loads. #1360 on the base addresses capacity. Comments 15, 17 and 21 identify
whole CPU-only pools being wired and retired descriptors creating new textures;
#1404 and #1394 overlap on address exposure. Memory wiring failure can outlive
process exit. #1391 is prevention, not a recovery guarantee. Comment 16 reports
another hang with the growing table already present. #1382 names the failed
work. #1409 releases a fence wait after failed feedback. #1332 (not requested as
a port) waits for revoked access; our safety net will stop at the first fault.
#1275 is a separate stalled-completion watchdog. #1420 is a CPU object-type
crash, not a GPU hang. Alias VA exhaustion and the terrain upload defect remain
separate from this task.

## Port review

| PR | Upstream head | Verdict | Critical review / adaptation |
|---|---|---|---|
| [#1391](https://github.com/seedds/nxnative/pull/1391) | `5122c24de6ecb24291a5fb0812e6b48ca6cb92fb` | adapted | Retain `g_ghost_active` in alias release and eviction holder sets from #1299. Upstream only refuses additions at 100% and can still submit after refusal; the safety-net commit must close that gap and reserve desktop headroom. |
| [#1382](https://github.com/seedds/nxnative/pull/1382) | `c87cc8cdc9c23aaa6ba40d963078be3eb4f840b4` | adapted | Keep stack's serial/program helper beside shader recording. Per-command-buffer shader lists aid diagnosis; they do not identify one guilty shader conclusively. Fake hang test passes 12 checks in each encoding mode. |
| [#1409](https://github.com/seedds/nxnative/pull/1409) | `039a39059323af18e74f23c8e68f07e525613186` | adapted | Preserve both reference entries at the docs append conflict. The wait retains its total finite budget and falls back to published completion. The SDK declaration is source only. |
| [#1420](https://github.com/seedds/nxnative/pull/1420) | `58c001d92cf5e5f6b72b0b2c28d52c2facc7d55c` | adapted | Keep both the existing finalized-bindless fixture and the new packaged-entry fixture. Unwrap a wrapper before handing it out as MTLTexture. The upstream cause of classification removal remains open. |
| [#1404](https://github.com/seedds/nxnative/pull/1404) | `d3effb232b245a8f21ed0481221411ccbd51fdbb` | adapted | Drop the obsolete `born` field from the upstream pool shape; preserve dynamic capacity and chunk hints. Put dimension preflight in `pool_entry` so incremental and full table paths agree. Keep the stack's `gmem_map` name in the fixture. Upstream still lists unpinned entries and takes large pools whole; #1394 must filter them before use. |
| [#1394](https://github.com/seedds/nxnative/pull/1394) | `a885f4be50b42e084571a4f34ed9a9a9b442a45e` | adapted | Combine persistent address marks with #1404's explicit-binding raw flags. Keep the nonpinning bounds check from #1404 instead of the duplicate resolver. Virtual remaps and replay stay conservative. Mark the 5,000-pool fixtures; preserve #1360's growth and #1405's hints/bitmap. SDK and storage-check duplicates are omitted. |
| [#1408](https://github.com/seedds/nxnative/pull/1408) | `e81bfaba860b7ac00074729e290b8250f13b4dc8` | adapted | Keep both appended test rules and findings; the SDK shim is already present from #1409. Linear partition preserves pending order and reverse release order. The interleaved 100,000-reference fixture passes. |

## Safety net

`DM_SAFE_GPU=1` defaults on only for the Ocarina Mac build. Other builds default
off. `DM_SAFE_GPU=0` restores the ported behavior for A/B tests. The ports are
requested correctness changes. The default-off shared-context rule was not
used to disable the explicitly requested safety build.

The graphics state has a sticky stopped flag. Every NVN Metal 4 commit checks
it at execution, including queued encode-worker records, uploads, main/segment
buffers, presentation and snapshots. Every NVN Metal 3 commit also checks it.
Error callbacks trip the gate before reporting or running completion work that
might block. The first Metal error stops the process, including page faults,
revoked/ignored submissions, out-of-memory and innocent-victim errors. Safe mode
deliberately gives up recovery. Already submitted kernel work cannot be undone.
The timer also trips if work is pending with no completion feedback for ten
seconds. This measures aggregate feedback progress, not a deadline per shader.

Before residency and queue commits, the guard checks the maximum of Metal's
current allocations, tracked resource bytes including pending additions, and
the residency size observed at its last commit. GPU cap = 70% of
recommendedMaxWorkingSetSize. System wired pages are sampled every 100 ms;
their cap = physical memory minus max(30% of recommendedMaxWorkingSetSize,
2 GiB). Sampling avoids a host_statistics call per draw/allocation. Overlapping
buffers count conservatively. A lower DM_NVN_RES_LIMIT_MB is honored; a higher
value or zero cannot bypass safe mode. The underlying #1391 refusal also trips
the gate, so refused residency never leads to submission of uncommitted work.
These are conservative bounds, not a reservation of RAM against other apps.

The host handoff runs off the failing callback/submit thread. It removes the
main residency set from both queues, ends residency, clears its allocations,
and removes snapshot and display-layer residency. It does not wait for GPU
completion or call the normal graphics drain. It closes audio and exits with
code 0. The cleanup has an independent exit fallback. If the residency mutex
is stuck, the attempt is bounded and the log explicitly says release was not
possible. If a Metal removal itself blocks, the fallback exits. A kernel call
already unkillable can still outlive process exit. No software guarantee of
WindowServer survival is claimed.

A critical follow-up from issue comment 21 was reproduced after the ports:
`tex_by_id` accepted a cached texture with no parent when the current backing
was nil, because `v.parentTexture == cur` compared two nil values. The new
stale-view fixture failed exactly that check (1 of 1,082). Requiring `cur`
before comparing backing identities makes all 1,082 checks pass. This belongs
to the integration safety fix because #1404 makes empty retired backing common.

The implementation uses a single permanent stop state rather than a resettable
per-submission error flag (Model the Domain). Ports were kept as separate local
commits so each source adaptation can be inspected (Sequence Work into
Verifiable Units). Both principle leaves were read. The pstack bug-fix steps
used deterministic synthetic triggers because the user forbids a game run.
Delegation, a separate reviewer and opening a PR are skipped because this is an
implementation sub-agent with a local-only brief. The parent must review this
branch independently before any gameplay acceptance.

## Verification and limits

All commands used the existing uv venv on PATH and the prescribed persistent
TMPDIR. No dependencies were installed. At most four compiler jobs ran across
concurrent commands. No game, regress.py, full shader build, third-party binary,
iOS operation, baseline process control or protected-folder write was performed.
The existing shader chain and translator binary remain unchanged by this branch.
The requested host-only build uses the repository's own small host Metal shaders.

Source-only ports were tested as they landed, then together. Evidence files
are under `/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/oot-stable/`.
The JSON there contains the issue body and all 21 comments read for this task.

- `1391-test.log`: 20 guard checks plus 2 held-lock timer checks, all pass.
- `1382-test.log`: 12 shader-name checks in each encoding mode, all pass.
- `1409-test.log`: 162 CPU completion checks with fast wake off and 167 with it on,
  in all four fast-wake/ledger combinations; 36 ordering checks in each of three Metal configurations.
- `1404-test.log`: 1,079 raw-residency checks and 32 CPU-storage checks pass.
- `1394-test.log`: 28 address-mark checks, 95 chunk/capacity checks and 61
  actual translated GPU lookup checks pass (8,192-entry table, 5,001 ranges).
- `1408-test.log`: 100,000 interleaved references preserve retention and order.
- `integrated-gfx.log`: the above graphics targets plus 70 packaged/CPU texture
  checks pass together with the safety net present. Naming/old guard fixtures
  explicitly disable safe mode to exercise their original recovery semantics.
- `stale-view-before.log`: the added missing-backing assertion fails before
  the nil check. `final-gfx.log`: 1,082 raw-residency checks and both shader-name
  configurations pass after it; hang, ignored, pending-allocation, watchdog,
  legacy-error, debug-hook and opt-out safety fixtures pass.
- `host-stop-test.log`: actual host lifecycle code in child processes verifies
  release-before-cleanup, once-only dispatch, no graphics drain, exit status 0,
  and exit when the release operation blocks.
- `docs-tests.log`: 34 documentation, environment, graphics Makefile and chain
  tests pass. The inherited DM_PRESENT_ABSOLUTE registry row was completed;
  historical DM_NVN_CUT_FIRST / DM_NVN_HANGLOG mentions remain warnings only.

The broader Metal suite, full host suite, five-game regression, real GPU faults,
long-session residency, full-screen behavior and WindowServer survival are
unverified. A fake callback proves the host's response, not driver recovery.
Visual risk: address-exposure filtering and empty retired descriptors affect
resource lookup. Preserve the parent stack's shader ABI and compare gameplay
images during parent acceptance. The safeguard itself changes no shaders or
rendering quality settings. On a busy Mac it can stop earlier by design.

## Parent verification

Use this worktree and the existing Python environment. No game is needed:

```sh
export TMPDIR=/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch
export PATH=/Users/ankur/Documents/Crypt/Gaming-rea/nxnative/.venv/bin:$PATH
make -j2 -C dm/gfx/tests GAME=0400486024DEC000 check_t_safe_gpu check_t_res_guard
make -j2 -C dm/gfx/tests GAME=0400486024DEC000 check_t_gpu_hang_names check_t_raw_residency check_t_gmem_marks check_t_pool_chunks check_t_gmem_raw check_t_deferred_release perf-order-cpu check_t_perf_order check_t_cpu_tex check_t_cpu_storage
make -C dm/host/tests GAME=0400486024DEC000 check_gpu_stop
python -m unittest dm.tools.tests.test_docs dm.tools.tests.test_env_switches dm.tools.tests.test_gfx_tests_makefile dm.tools.tests.test_nsp_chain
make -j2 -C dm/host GAME=0400486024DEC000 dmhost
```

If the parent explicitly authorizes a gameplay check, use independent prepared
inputs and output/save directories, retaining their normal launch environment.
Set `DM_SAFE_GPU=1 DM_TEST_GPU_HANG=1` on that launch. This injects a callback
error after the first main command buffer; it does not intentionally hang the
GPU. Expect the shader-name dump, a `[RED] DM_SAFE_GPU:` stop line, the residency
release line, a clean host exit and status 0, with no later GPU commits. Do not
use the running baseline or its save/temp folders. Compare a normal windowed
run without the debug hook only after this forced-stop test and independent
review. A deliberately low `DM_NVN_RES_LIMIT_MB` can check preventive stopping
without exhausting real memory; zero does not turn safe mode off.

The final residency-boundary fixture (`final-guard.log`) adds a separate case
where Metal's set-size reading exceeds the cap while device/tracked allocations
do not. It proves the refused residency commit also closes the submission gate.
An original #1391 fixture exposed a CPU-reference race under parallel validation:
feedback publishes g_done before releasing its local ready array. Its weak
references may remain alive briefly after the fence. The fixture now waits up to
one second for those CPU references, then checks release; no product wait or
retry was added. The unchanged binary also passed immediately on replay, which
is evidence for the race rather than a reason to ignore the failed run.

Issue comment 21 also identifies alias takeover evicting the linear parent of a
live sRGB view. The same serial-holder check now follows Metal texture parents
for live and ghost holders. The guard fixture explicitly checks this ownership
before idle eviction. It is a conservative O(n) scan like the existing direct
holder scan; its gameplay CPU cost has not been measured.

Final acceptance on the completed source is in `final-acceptance.log`: 159 safe
GPU checks across eight fresh processes; 21 normal and 2 held-lock residency
checks; 1,082 raw-residency/stale-view checks; 12 shader-name checks in each
encoding mode; 70 packaged/CPU texture checks; and 32 CPU-storage checks. All
1,390 checks pass. `host-build.log` is the successful final
`make -j2 -C dm/host GAME=0400486024DEC000 dmhost` build. Compiler warnings remain;
there is no game/runtime acceptance claim. Earlier `final-guard.log` retains
the original fixture race failure; `final-acceptance.log` supersedes it.

## Review Astra 2, finding 2

A short CPU mutex protects pending work, progress updates and the watchdog
predicate as one snapshot. It covers both start and feedback writers. No Metal
call or error handoff runs under that lock. The timer skips a busy lock and
tries again on its next tick. The existing ten-second threshold is unchanged.

The review's injected start immediately after the progress read is retained in
three new tools tests. A second thread starts work at that exact point. The
old source deterministically reports stalled=1 with progress already current;
the fixed source defers the writer until the idle snapshot finishes. Other
cases cover 20,000 simultaneous feedback completions, concurrent start/feedback
and watchdog reads, idle restart, the true-stall boundary and a busy CPU lock.
All three tests and the eight existing fake GPU safety modes pass. Logs are in
the requested review-astra-2-fixes-evidence folder outside this checkout.
No game, full shader build, GPU fault, install, push or PR ran.

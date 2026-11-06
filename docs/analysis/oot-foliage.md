# Ocarina foliage translation and lookup grouping

Branch `oot-foliage`, base `oot-brent` at `209835ae`. Mac only. No game,
regression route, full shader build, iOS build, push or PR ran.

## Result and visual risk

All 27 valid programs among the 28 baseline failures now translate and compile
with `DMSH_OOT_VISUAL=1`. The five selected heavy mesh shaders also compile,
including with `DMSH_WIDE_GROUP=1`: **32 successes, one known false candidate**.
No missing grass, leaf geometry or brightness fix is claimed from compilation.
Image parity, atomic ordering across a real scene, and GPU performance remain
parent acceptance gates. Both flags default off.

The task's premise that no branch implements 0x3a9 is stale: the requested
`209835ae` base already includes `AAtomgCas`, imported by oot-visual from
`6f973380`. No duplicate opcode implementation or speculative modes were added.
This change adds numeric and refusal coverage to that implementation and extends
the existing #1405 grouping matcher to the observed read-only mesh helpers.

## Targeted build

Read only the existing baseline shader package. Extracted exactly 33 records
using the repository's `job_for` metadata rules, preserving control layout,
constant data, stage memory and profile facts. The inherited source-built Brent
translator first translated 32, refusing only `68bbe98b3bfd9876` at 0x481.
All 32 compiled through SPIRV-Cross and Mac Metal. Then the actual
`dmsh_build.py` selected-key path, with both feature flags on, produced 32
libraries with `lost without failing: nothing`. The same false candidate failed.
No full-map stamp or profile shader table was written by the partial builds.

| Baseline failure family | Programs | Result |
| --- | ---: | --- |
| F2IP 0x243 | 18 | SPIR-V and Metal PASS |
| ATOMG.CAS 0x3a9 | 6 | SPIR-V and Metal PASS |
| Auto exposure bracket depth | 2 | SPIR-V and Metal PASS with depth 1024 |
| Task ISBERD mode 0xb8 | 1 | SPIR-V and Metal PASS |
| False BAHS entry 0x481 | 1 | Remains refused at zero; no fake opcode added |

The false candidate starts with the graphics SPH word `0x020c0481` while its
incorrect extraction marks it compute. The scan already established that its
BAHS offset is inside a record, rather than an entry. This task does not alter
extraction or claim that this synthetic key is requestable in gameplay.

### Exact F2IP operands at the reported offsets

Offsets below are relative to translator instruction input, with mesh SPH
already stripped, matching the baseline diagnostics. C is RZ in every case.
All are register form 1, bits 40..63 zero, unsigned byte output, F32/NTZ.
The displayed mode is bits 72..95 followed by C; it excludes scheduler bits.

| Key | Failure offset | A | B | Mode/C | Round | Build |
| --- | --- | --- | --- | --- | --- | --- |
| `aaa785ced92a88ef` | `0x4e0` | R13 | R12 | `0x4ff` | RN | PASS |
| `99951da6e5cd38f5` | `0x530` | R13 | R12 | `0x4ff` | RN | PASS |
| `8692b34b521225be` | `0x6270` | R40 | R39 | `0x4ff` | RN | PASS |
| `e8b64d5ad83c7e22` | `0x69d0` | R38 | R33 | `0x4ff` | RN | PASS |
| `dac121a8c0b3efbd` | `0x6340` | R43 | R42 | `0x4ff` | RN | PASS |
| `00b0635ae2b9613b` | `0x6ab0` | R44 | R39 | `0x4ff` | RN | PASS |
| `83df46a0b1b379b4` | `0x6e80` | R44 | R21 | `0x4ff` | RN | PASS |
| `c26c20f61455fb9e` | `0x7640` | R39 | R28 | `0x4ff` | RN | PASS |
| `8336f2da0f51938d` | `0x7010` | R48 | R47 | `0x4ff` | RN | PASS |
| `10a2c776a57f5071` | `0x7730` | R44 | R31 | `0x4ff` | RN | PASS |
| `fed302d791a4ba43` | `0x3d0` | R255 | R9 | `0xc4ff` | TRUNC | PASS |
| `819c33c90234fcb6` | `0x3a0` | R255 | R14 | `0xc4ff` | TRUNC | PASS |
| `604134a5262ff670` | `0x38e0` | R255 | R22 | `0xc4ff` | TRUNC | PASS |
| `ca03b41694d4c196` | `0x47b0` | R255 | R210 | `0xc4ff` | TRUNC | PASS |
| `9ecd96cec34c7315` | `0x3a0` | R255 | R3 | `0xc4ff` | TRUNC | PASS |
| `740e2b04db624fb1` | `0x370` | R255 | R5 | `0xc4ff` | TRUNC | PASS |
| `ecead5cd0569091f` | `0x3c0` | R255 | R9 | `0xc4ff` | TRUNC | PASS |
| `adbaa02880733cf0` | `0x390` | R255 | R14 | `0xc4ff` | TRUNC | PASS |

The full selected code contains 42 F2IP instructions: 28 two-source RN and 14
RZ-source-A TRUNC. All satisfy the exact `AF2ip` acceptance condition, including
instructions after the first baseline failure. The two-source form places B in
the low byte and A in the next byte. The RZ/TRUNC form leaves B in the low byte.
Inherited numeric tests execute 64 pairs across all four rounding modes,
including ties, infinities, NaNs, negative zero and subnormals.

### Identification and validation of 0x3a9

[CuAssembler's sm_86 instruction records](https://github.com/cloudcores/CuAssembler/blob/master/CuAsm/InsAsmRepos/DefaultInsAsmRepos.sm_86.txt)
identify 0x3a9 as ATOMG.E.CAS.STRONG.GPU; the 32-bit samples encode the same
`0x1ee1` high operation fields as all 14 CAS sites in the six foliage programs.
The compare value is bits 32..39, replacement bits 64..71, extended address bit
72, and predicate destination bits 81..83. The surrounding foliage code loads
an expected value, computes a replacement, performs CAS and tests the returned
old value in a retry path. It must remain an atomic update.

[Mesa NAK's encoder](https://android.googlesource.com/platform/external/mesa3d/+/0f7ff6fbdcc743dc16bc2429d7a51af3de728ed0/src/nouveau/compiler/nak/sm70.rs)
independently emits 0x3a9 for CmpExch with those compare/replacement fields. The
vendored Ryujinx IR exposes `AtomicCompareAndSwap`, which lowers to a Metal
compare-exchange retry loop returning the old word. The inherited Maxwell `AtomCas` entry is only a diagnostic stub and is not
used as evidence for the Ampere encoding. The existing Ampere handler uses
that operation and captures the address before copying its result to D.

New GPU tests compare exact 32-bit results against `new = replacement if old ==
expected else old; returned = old`. Six input cases run with distinct D and with
D aliasing the low address register, for 12 cases total. They include success,
failure, all-one bits, sign bits and differing NaN payloads. All pass. Additional
translator tests refuse 64-bit types, uniform addresses, non-PT predicate
results and the disabled feature. No 64-bit or predicate-result semantics were
guessed. Existing relaxed atomic ordering is unchanged and remains a gameplay
validation limit.

## Lookup grouping

#1405's current build path excludes mesh shaders; its helper matcher also
requires writable `device` tables. Every top-five pool helper is `const device`.
An actual selected build with `DMSH_RAW_LOAD_QUADS=1` confirms zero reductions.

`DMSH_WIDE_GROUP=1` admits the same verified resolver on mesh/task lowering and
preserves its read-only table/pointer qualifiers. It does not introduce another
address optimizer. Existing groups require four adjacent calls with straight-line
address copies and proven offsets 0/4/8/12, including the correct unsigned
low-word carry into the high word. No group crosses a brace, store, atomic,
barrier, changed address variable or unknown side-effecting call. Different
per-word predicates therefore remain scalar, in their original control flow.

At runtime the existing helper validates four-byte alignment, no 64-bit guest
span wrap, 16 bytes inside the selected interval, and no intervening next pool
start. It validates the translated GPU span as well. The search prefix and
hint rules are preserved. Boundary, missing or unproven accesses use the
original scalar resolver for every word. Dynamic-table count and tagged hints
are still verified by the matcher. No store, barrier, animation math, stage
initialization or CAS retry loop is removed.

Counts are expanded static call sites in the selected output's primary entry.
They count possible branches, not execution frequency or measured GPU work.

| Shader | Baseline | Brent / #1405 | Quad groups | Remaining scalar | Fast-path lookups | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `ae104328f80e5fb8` | 971 | 971 | 226 | 67 | 293 | 69.8% |
| `7fd36d22b1f0fd14` | 971 | 971 | 228 | 59 | 287 | 70.4% |
| `7eef23eeb0784836` | 940 | 940 | 219 | 64 | 283 | 69.9% |
| `626fbf48041cb82b` | 930 | 930 | 206 | 106 | 312 | 66.5% |
| `4c7d6be5a7717c8d` | 506 | 506 | 97 | 118 | 215 | 57.5% |

Each successful quad replaces four resolutions with one. If every quad instead
fails its runtime span check after finding a pool, the shader can perform its
original scalar resolutions plus one attempted lookup per group: worst-case
static totals 1197, 1199, 1159, 1136 and 603 respectively. These are not measured
frame costs. Keep the optimization off until an image comparison and GPU timing
establish its benefit on actual mapped spans.

Synthetic checks cover adjacent pools, interval ends, unmapped words, a missing
first mapping followed by mapped words, 32-bit carry, full 64-bit wrap, overlapping
intervals, duplicate starts, partial predicates, stores and both barrier kinds.
The GPU compares original and transformed read-only helpers against a separate
nearest-start reference for twelve mapping scenarios and all four returned words.
The inherited tests also cover growing-table/hint shape rejection and modified
address arithmetic. No gameplay equivalence is inferred from these checks.

## Build provenance and portability

Used the cooled-NuGet procedure from `oot-stack:implementation-notes.md`.
Rechecked all 57 exact package versions against nuget.org publication dates
before downloading. Every version was at least seven days old. An isolated
local feed, cleared package sources, isolated NUGET_PACKAGES, disabled parallel
restore/audit network queries, and four workers maximum kept restore inside the
allowlist. All four project.assets.json manifests match that allowlist. SDK
10.0.403 and runtime 10.0.14 were already installed. No dependency version changed.

There was one initial source restore/publish, followed by one corrective publish
for portable debug paths, rather than the requested single publish. The first
publish exposed an absolute checkout path in the executable's CodeView record.
The corrective invocation reused the same restored packages with
`-p:PathMap="$PWD=/_/nxnative"`. No translator logic or package changed between
publishes. The optional PDB was omitted because its SourceLink mapping retained
an absolute workspace path despite PathMap. Changed committed assemblies contain
no workspace paths. The inherited universal launcher is retained; every installed
translator assembly was compiled locally. No PR-shipped translator ran.

The lock and default header were regenerated after the final publication.
Default chain is `fcb95fc30eb8`; visual-only is `baca7783ba16`; visual plus
wide grouping is `b797f96b3609`. The selected library evidence predates the
portable publication metadata and is not a matching library set for a final host.
The final translator's 32 SPIR-V and 32 reflection files are byte-identical to
the inherited Brent output for these targets. No additional C# opcode change
was needed on this base.

## Validation and remaining gates

- Tools: `python -m unittest discover -s dm/tools/tests`: **1,233 tests,
  OK, 23 skips**.
- Full graphics Python suite with final source-built translator,
  DMSH_TEST_METAL=1, DMSH_TEST_GPU=1 and the native geometry replay helper:
  **391 tests, OK, four skips**. This includes **92 Ampere translator cases**,
  the 12 CAS numeric cases, inherited 64 F2IP pairs, RED/Float16 numeric
  execution, grouping checks and 40 PrimitiveID GPU cases.
- Final focused wide suite: **14 tests, OK**, with twelve GPU mapping scenarios
  including low/high signed-word overflow and full wrap.
- Native `make -C dm/gfx/tests -j2 GAME=0400486024DEC000 run`:
  **all 107 native fixture targets pass**, plus the four pull tests and five
  budget tests. Existing Objective-C compiler warnings remain.
- Final docs, chain, environment and cache subset: **54 tests, OK**.
- Lock tool check, repeat default header generation and diff whitespace: clean.
- Ruff on the changed standalone tools/tests: clean. The repository's ratcheted
  Python lint reports the same three inherited findings in unchanged
  test_nsp_mac.py and test_tree_tar.py. No changed-code finding remains.
  Raw, unratcheted lint also reports inherited issues; no baseline was weakened.
  clang-tidy is not installed, so that lint gate is unverified.

The first full graphics Python invocation failed only because its explicit
native replay helper was unset; after building and supplying it, the complete
suite passed. The initial CAS numeric test omitted an instruction-barrier wait
and read a stale register in the synthetic program; its control encoding was
corrected before the final suites. No translator workaround was added.

No game run or five-game regression was attempted because this task forbids
both launches and full shader rebuilds. The changed path is generic Ampere raw
read lowering, so independent source review and broader shader/game acceptance
remain parent gates. Restore the desired flags consistently for header, shader
and host builds; a default-chain host cannot load enabled-chain libraries.

## Evidence and storage

Evidence root is `$FOLIAGE_AUDIT` (the task's `oot-foliage` audit directory).
`fixtures/jobs.json`, `fixtures/opcodes.json`, baseline translation/compilation
logs, `selected-build.log`, `quads-build.log`, `lookup-counts.json`,
`nuget-audit.json`, four-manifest audit, publish logs and final test logs remain
there. Raw shader bytes and compiled fixture artifacts stay outside Git.
The protected baseline checkout and game build were read only.

Removed the private NuGet package cache through `dotnet nuget locals
global-packages --clear`, then removed the audited feed and both private publish
folders after checking they had no open files. Audit dates, scripts, logs,
selected shader records, generated MSL/SPIR-V/AIR and partial libraries remain
as acceptance evidence. Checkout bin/obj, host generated headers, native fixture
executables and symbols remain because the harness cwd is inside the checkout.
Their exact roots are listed in `retained-generated-roots.txt`. No cleanup sweep,
unknown path deletion, maintained checkout change or protected game write ran.

# Brent Ocarina comparison and harvest

## Result and limits

Source comparison uses brent-oot-combined a54b2092, upstream main 865cc35f,
oot-visual 622f5191, oot-stable 5c534f38 and oot-stack 8284776d. The harvest
branch oot-brent starts at oot-visual. No writes were made to oot-hyper, the
running baseline checkout or its game folder. No game, full shader build,
regress.py run, device operation, push or PR ran. Only our own rebuilt
translator was executed. Brent's five replacement binaries were never checked
out, copied or run. Gameplay and image correctness remain unverified.

The quoted 51 commits include merges and shared Ocarina ancestry. The exact
range 865cc35f..a54b2092 contains 31 non-merge commits, three already ancestors
of ee9b7765, and 20 merge commits. It is not 51 additional independent fixes.
The inventory below groups repeated merge/rebuild commits with their source item.
The complete non-merge inventory is in the evidence folder's commit-inventory.tsv.

## Comparison table

V = oot-visual, S = oot-stable, K = oot-stack. “Harvest” means added to oot-brent,
not retroactively present on those original branches. Importance is for Ocarina
on an M4 Max; visual benefit takes precedence over efficiency.

| Upstream PR or source commit | Brent | Original local branches | Difference, M4 Max relevance and verdict |
| --- | --- | --- | --- |
| Ocarina bring-up 10e53364, 9fb44679, ee9b7765 | Yes, shared history | V/S/K base | Same baseline eventfds, NDVE extraction, conditional depth clear, mesh slots and descriptor patches. No duplicate port. |
| #1300, 06f47f57, e3f8ef8c; merge c00d375b | Yes | V deb4afe9 | Same F2IP/payload functionality; ours gated by DMSH_OOT_VISUAL. Keep our refusal checks and numeric tests. Restores foliage translation. |
| #1312, 9cb1fe2a, ac024428; ae6443f9, 20fca451 | Yes | V 011b5936 | Same indirect mesh/image atomics and integer image aliases. Ours keeps indirect layout provisional behind DM_NVN_MESH_INDIRECT. Brent adds a depth-only mesh fragment fallback. Harvest that missing part with #1368 resolution. |
| #1343, 6941aa84; 9672b8b6 | Yes | V 08115457 | Same liveness correction prevents removal of coordinate producers while another result is live. Ours gated. Keep ours. Foliage jitter relevance is direct. |
| #1359, 34d04efb; 9515423e | Yes | V c176b7fb | Both lower float reductions to CAS. Ours starts with atomic CAS(0,0), preserves signed zero in FTZ and restricts supported storage. Brent starts with an ordinary load and shared FlushDenormal. Keep ours for atomic access and signed-zero behavior. Outdoor color correctness. |
| #1390, 16e86fdc; 23887fb8 | Yes | V 0c2dbf41 | Both track GPU-written ranges instead of classifying a whole mixed pool as GPU-written. Ours gated. Keep ours. Missing ground/CPU texture uploads. |
| #1353, 5ec8a62b; 0b97e3fc | Yes, adapted with #1388 | V 68d8b900 | V walks 8-byte entries after a header-alignment score; Brent keeps #1388's validated word scan. Both recover odd entries. Harvest Brent's scan, retaining our disabled path and both test sets. SMAA weights and jagged edges. |
| #1388, c8aeba86; 2b98f894 | Yes | No independent port | Four-byte search handles +0x10/+0x14 starts without guessing the alignment, checks control type and minimum length, then consumes both control/code pairs. Harvest. No claim of additional recovered Ocarina shaders over V without a corpus split. |
| #1357, 072f8674; 0cc8e8e0 | Yes | V 65882d10 | Same bracket-depth=1024 compiler option; ours changes Mac path under the visual flag. Keep ours. Two compute programs otherwise fail compilation. |
| #1128, 6c131328 | No | V 8a504862 | Local-only Float16 constant-output limit. Keep ours as an experiment; it is limited coverage, not a universal NaN/bloom repair. |
| #1368, 7cd6750b, 9c53d9ae; 9a7a5ff0 | Yes | V ad796e22 | Both demand-build first-use native mesh pipelines and prewarm serialized state. Brent retains an empty fragment function for depth-only meshes and distinguishes unloaded declared pixel shaders. Harvest that missing resolution under DM_NVN_VISUAL. Actual depth-only Metal pipeline test passes. |
| Global foliage CAS, 8708bcd3 (related #1347) | Yes | V afcd2b35, from 6f973380 | Different address encoding: ours uses CAS extension bit 72; Brent uses ordinary ATOMG bit 70. Retain ours and its non-PT/uniform refusal. Source and encoding evidence below. |
| #1376, 2d6f86f8; 822e7a5a | Yes | No | LDSM consumes shared-memory rows produced by other lanes without BAR. Add subgroup barriers before reads and after them. Harvest under DMSH_OOT_VISUAL. Direct movie-filter visual relevance. Upstream image counts are not local measurements. |
| #1360, eaa7a1da; 348854c0 | Yes, adapted | K c88eefef, inherited V/S | Both dynamic table counts and sized write logs. Brent upgrades hints to separate full index/tag words; ours retains 12-bit tagged hints and falls back above entry 4095. Both can resolve high pools, but their hint ABIs differ. Keep ours consistently; do not mix host and translator halves. Prevents absent pools and task-shader GPU loops. |
| #1360 follow-up 9e5dc598 | Yes | Partial safety in K, no full cleanup | K safely rejects the selected undersized log and retains the original map for completion. Brent drops all undersized completed free logs. Harvest cleanup under DM_OOT_BRENT, keeping K's completion logic and disabled behavior. Test also verifies residency removal. |
| #1405, 00c86455, 3fe33bc3; 5877d907 | Yes | K 453083a4, inherited V/S | Keep ours. Brent's matcher is fixed-table-only despite its merged growing-table translator. On committed raw_global_growing.metal, table slot 1, ours transforms and Brent's source pass does not. Our guard also uses the dynamic count for the next interval. Brent therefore silently loses the intended optimization on this shape. |
| #1394, a885f4be; 079f3dcf | Yes | S e246c141 | Both filter the raw table to GPU-address-exposed pools while preserving growth. S layers over #1404's exposure/residency tracking and tests; Brent layers directly over main. Keep S and its span-generation handling. Avoid wiring CPU-only texture pools; stability/efficiency with resource-lookup visual risk. |
| #1393, 3a534edd; 61fa7980 | Yes, adapted | No independent port | Skip finalized IDs that hold no view, but preserve resources used by the current open submission. Brent places policy in pool_entry, so incremental patches also apply it. Harvest. S's #1404 residency fix is complementary, not a replacement for this policy. |
| fb85c524 | Yes | No | Enables pool_skip_retired in Ocarina's game.tsv. Do not enable by default here. Harvest capability but require DM_NVN_POOL_SKIP_RETIRED=1. A finalized handle can legally read surviving storage, so visual acceptance is required before a profile default. |
| #1345, d7a43c2a; 0cc96322 | Yes | No | Derive SDK 22's +0x2d8 audio update lock from UpdateImpl; hard-coded +0x2d0 excludes nothing and can corrupt the preceding field. Harvest under DM_OOT_BRENT. Stability during the opening movie. Synthetic ARM64 decoder tests cover SDK and OS mutexes and refusal cases. |
| #1373, b44bcafd; aba4977b | Yes | No | Provisional heap-check growth must retain the profile's actual alias size, not assume 1 GB. Ocarina's 6.20 GB request otherwise receives 0xb8000000 capacity. Harvest with DM_OOT_BRENT. Build/bring-up stability; an already fixed static profile is unaffected. |
| e9d71e27 | Yes | No | Reserve at least 64 GB alias address space on Mac and order heap, stacks, alias to reduce 39-bit pointer exposure. Harvest as a Mac-only DM_OOT_BRENT experiment; preserve explicit DM_ALIAS_SIZE and profile-sized heap probes. It reserves address space, not 64 GB of RAM. Ocarina benefit is preventive, not reproduced. |
| #1369, 61cd3462; 2788e415 | Yes | No | Documents Switch 2 first-scene GPU memory on an iPhone. No source fix, no M4 Max behavior to harvest. The memory lessons support S's residency work. Skip phone-only report. |
| #1354, 5292ae49; c08733b3 | Yes | No | Exclude remount-assigned st_dev from RomFS identities while accepting old image stamps. Harvest under DM_OOT_BRENT, with malformed-list validation. Prevents unnecessary multi-GB repacking after a reboot. Packaging efficiency, no rendered-image change. |
| 8708bcd3 audio takeover deduplication | Yes | No | Remove duplicate forced ListVirtualInputDevices registration; h_is_List already returns the same empty device list. Harvest as a structural duplicate removal with unchanged service result. |
| 8708bcd3 icon validation | Yes | No | Some NUP icon records hold BYML instead of JPEG/PNG. Harvest validation under DM_OOT_BRENT. Packaging correctness only. |
| 8708bcd3 regenerated shader map/pairs | Yes | No | Do not copy generated game tables across different translators and splitter flags. Parent must regenerate from prepared inputs after choosing flags. No full split/build was run here. |
| 60632a6e | Yes | No | nso_match recipe returns a plain dict for typing. No Ocarina runtime change. Leave unrelated lint-only port out; no lint baseline is weakened. |
| 6491f003 and earlier generated chain/binary changes | Yes | V/K locally built artifacts | Never copy these. oot-brent has one new source publish with its own lock and header. Parent integration requires another final combined-source rebuild. |
| #1391 | No | S 62605d26 | Local residency guard; retain. |
| #1382 | No | S f5fedb5a | Local hung-shader naming; retain. |
| #1409 | No | S 301a95bc | Local failed-work fence feedback; retain. |
| #1420 | No | S f376a0a6 | Local packaged-texture lookup correction; retain. |
| #1404 | No as PR | S 2576ed58 | Exposure/residency and retired-backing protections, including storage-only liveness checks; retain with #1394 and #1393. |
| #1408 | No | S 3056acf5 | Local linear deferred cleanup; retain. |
| DM_SAFE_GPU | No | S 5c534f38 | Local stop-on-first-fault and desktop memory reserve; retain integrator's policy. This harvest does not replace it. |
| #1161 | No | K 5a052984 | Local numeric-key readable-tile lookup; retain. |
| DM_PRESENT_ABSOLUTE | No | K e7c50787 | Local opt-in direct-present experiment; retain off for first shader comparison. |

## Evidence for disputed resolutions

### NDSR

Read ndsr_shaders in dm/gfx/tools/shader_split.py. Our earlier #1353 scans
complete entries at either +0x10 or +0x14, then picks the start with more control
pointers. Brent's #1388 searches individual words, validates a control pair and
consumes its code pair. It keeps vertex/pixel pairing in BAHS_VAR. Retaining
#1353's documentation with #1388's implementation is sound. Both synthetic test
families pass. The new implementation also rejects control lengths below 0x48.
It is still a format-recognition scanner, not a complete hostile-input parser.

### Dynamic tables, hints and wide loads

Read GlobalToStorage.TryGenerateRawStorageOp, nvn_mtl.m gmem_map and gml_take,
and dmsh_wide.py _raw_search/_raw_quad_helper. Brent uses entry words 6 and 7
as a full hint index and 32-bit chunk tag, with addrHigh below 2^21. Our stack
packs a 12-bit index and tag in word 6, with addrHigh below 512; high entries
fall back to the complete count-driven binary search. Both hosts and shaders
must agree on those words. Retain our paired implementation for integration.
A full-index hint could be a later optimization, but it also requires adapting
and re-verifying the wide matcher. Mixing Brent's hint layout into our matcher
would either disable the pass or make assumptions invalid.

The comparison executes only the two Python source passes against the same
committed MSL fixture. wide-compare.log records ours=True, Brent=False.
No Brent translator artifact is needed or run. This proves matcher coverage
on that shape, not a measured game speedup or every Brent shader's output.

#1394 removes non-exposed pools from the table. It must retain #1360's dynamic
capacity/count and regenerate hint indices against the filtered sorted ranges.
Both implementations do that. Use S's #1404/#1394 exposure machinery, preserve
our growth ABI, then apply #1393's check before tex_fast_rid in shared pool_entry.
Keep S's type-class preflight, non-wiring storage checks and backing lifetimes.

### Float atomics and foliage CAS

Our EmitAtomicAddF32 seeds its retry with AtomicCompareAndSwap(0,0), which
performs an atomic observation of a word concurrently updated by other lanes.
Brent seeds it with context.Load. Our bit-based FTZ preserves the sign of zero;
Brent calls the shared helper. Retain our numeric-test-backed implementation.
These are source-semantic reasons, not a newly measured Brent gameplay failure.

Our AAtomgCas uses AGlobalAddress(...,72,64,0) and rejects unsupported uniform
and non-PT predicate forms. Brent uses (...,70,64,0) and registers the operation
as Atom rather than AtomCas. The issue fixture's high word 0x000ea400001ee127
has bit 72 set and bit 70 clear. The prior local audit records CuAssembler's
sm_86 ATOMG.E.CAS encoding at bit 72. Brent's lowering therefore treats this
extended address as unextended. Keep our dedicated CAS instruction category,
address bit and conservative refusal checks. The fixture verifies translation;
full guest-address and console parity remain acceptance work for the parent.

### Mesh composition

Use our #1368 demand/prewarm pipeline and indirect gate, plus Brent's empty
fragment function for depth-only meshes. A failed declared pixel stage is not
an intentionally absent stage, so the port records fs_wait and skips that draw.
The real Metal prewarm fixture gains a depth-only pipeline check. No runtime
shader compiler or main-only packed-library loader was imported accidentally.

## Should the integrated work move to main 865cc35f?

Yes. Use 865cc35f as the eventual integrated base, preserve our audited source
resolutions, and build the translator from the final combined source. The prior
binary provenance blocker is solved by the cooled local-source procedure.
Staying on ee9b7765 maintains avoidable divergence in packing/library loading
and omits general correctness fixes. Do not replace oot-hyper during this task.
The integrator should perform that move in its own controlled integration step.

| Main-only commit | Benefit and Ocarina/M4 assessment |
| --- | --- |
| 58a77cc2 | Python annotation/fixture corrections; low integration cost. |
| 4a0551e4 | Guarded bindless handles/phi resolution. Already ported with gates in V; keep those audited semantics when resolving. |
| 72d00571 | Correct compiler worker count on three-level M5/M6 CPUs. M4 Max has two levels, so no direct promised improvement. General forward compatibility. |
| 95f9a6a9 | VOTEU uniform-predicate result. Already ported with a gate in V; reconcile, do not layer twice. |
| f0838733 | Standard sparse 3D tile and same-size float views for integer texture bindings. General graphics correctness. No demonstrated Ocarina-specific occurrence in this task. Accept with main and affected tests, not a separate speculative Ocarina workaround. |
| cb34473f | In-place packed shader libraries and removal of unused iPhone pulling compilation. Mac library loading/packaging benefit; touches nvn_mtl and dmsh_build interfaces. |
| 7249ee9f | In-place compile cache and one tool venv across games. Packaging/build efficiency; moderate tool integration work. |
| 6d269f93 | Four Unreal dynamic-buffer copies. Ocarina is Nintendo sead/agl, not Unreal; little direct relevance. |
| dd6ce5ba | Arceus-specific weak-reference workaround. No Ocarina behavior. |
| 865cc35f | File-backed guest memory to reduce iOS footprint. Mac-only Ocarina does not need its iOS policy, but the hle_svc initialization changes must be preserved when composing alias layout. |

A read-only git merge-tree trial of V against 865cc35f reports 13 conflicting
paths: six source/test files and seven generated artifact paths. Source/test
files are nvn_mtl.m, test_dmsh_ampere_alu.py, dmsh_build.py, InstEmitAmpereAlu.cs,
BindlessElimination.cs and Utils.cs. Artifacts are dmsh_chain.h, dmsh_chain.lock
and the five translator files. With oot-brent the count is 14, adding the
memory reference document. The hle_svc merge happens automatically in that
trial, but must still be reviewed for the guest-file initialization order.
No trial result was checked out or installed. This is moderate source conflict
cost, mostly reconciling already-ported VOTEU/guarded-handle fixes and adapting
library loading. Generated conflicts are resolved by rebuilding, never by
selecting incoming binaries. A merge-tree result is not build/runtime proof.

## Integrator merge notes

Merge only oot-brent's delta above 622f5191, or merge the branch with its shared
ancestry. Preserve oot-stable's safety, resource tracking and cleanup work.
A read-only S/oot-brent trial reports nine conflicted paths: nvn_mtl.m,
dm/gfx/tests/Makefile, t_cpu_tex.m, t_deferred_release.m, symptoms.md,
env_switches.tsv, reference/memory.md, reference/shaders.md and
implementation-notes.md. Several are inherited V/S overlaps, not this harvest.

In nvn_mtl.m combine S's ttype_apart/storage checks with this branch's skipped
counter and pool_skip_retired check. Keep S's safe-GPU shutdown checks around
all submissions and allocations, its raw exposure generations, growing table,
retained original-map write-log completion, and our optional completed-log
cleanup. Do not replace the file wholesale from either side.

For main, preserve packed lib_from_file loading when composing geometry and
on-demand pixel-stage state. Keep our empty fragment function only for programs
with no declared pixel stage. Keep the indirect mesh layout gate until validated.
Regenerate documentation indexes and environment registry after resolving docs.
Keep all test additions; combine Makefile prerequisites instead of choosing a side.

DMSH_OOT_VISUAL=1 enables the shader/NDSR ports, including LDSM barriers.
DM_NVN_VISUAL=1 enables inherited host visual ports plus depth-only mesh fallback.
DM_NVN_MESH_INDIRECT=1 remains a separate provisional record-layout experiment.
DM_OOT_BRENT=1 enables the new host/tool experiments, including alias layout,
audio-lock discovery, free-log cleanup, heap-check accounting, RomFS identity
and NUP icon validation. DM_NVN_POOL_SKIP_RETIRED=1 enables retired descriptors.
These flags are independent; initial runtime acceptance should isolate them.
No profile default was turned on by this harvest. The duplicate audio takeover
removal preserves the same empty-device result and needs no behavior flag.

The parent must regenerate its map/pairs from prepared source inputs for the
chosen splitter, rebuild all affected shader libraries and host with matching
chain flags, and then perform Kokiri foliage/ground/SMAA/color checks plus title
movie and scene-change stability acceptance. Those operations were prohibited
in this task, and no FPS, power, memory or visual parity claim is made here.

## Verification and build provenance

Evidence is under
${OOT_EVIDENCE_ROOT}/oot-brent/.
NuGet audit rechecked all 57 exact versions from our inherited deps manifest
against nuget.org publication dates before download. All exceed seven days.
Restore used only the isolated feed, no parallel restore, NuGetAudit=false,
-m:4 and no runtime ID. All four project.assets.json package sets match the
allowlist. One Release publish used --no-restore --self-contained false -m:4.
The inherited universal .NET launcher was retained; only locally built managed
project outputs changed. Lock and default header were regenerated afterward.

Measured results on the final source:

| Check | Result | Evidence file |
| --- | --- | --- |
| Full tools discovery | 1,233 tests pass, 23 skipped | full-tools-tests-final.log |
| All test_dmsh*.py, our translator, Metal and GPU enabled | 267 tests pass, 1 skipped; 40 GPU PrimitiveID cases | translator-tests-final.log |
| Pool growth and write-log cleanup | 100 checks, zero failures | affected-gfx-tests.log |
| Retired descriptors | 11 checks, zero failures | affected-gfx-tests.log |
| Raw global GPU reads | 61 checks, zero failures, 8,192-entry table | affected-gfx-tests.log |
| Pipeline prewarm and depth-only mesh | 115 checks each in MTLDevice and Metal 4 modes | affected-gfx-tests.log |
| GPU-written indirect mesh arguments | PASS | affected-gfx-tests.log |
| Explicit image usage | 50 checks, zero failures | affected-gfx-tests.log |
| Deferred resource retention/order | PASS | affected-gfx-tests.log |
| CPU textures / CPU storage | 71 / 32 checks, zero failures | affected-gfx-tests.log |
| SVC memory, unlimited map, 16K ASan/UBSan and real dirty tracking | PASS | memory-tests-final.log |
| Optional alias layout at 64 GB and 256 MB | PASS, real heap/map/stack copyback | memory-tests-final.log |
| Audio lock decoder and SDK renderer layout fixtures | PASS | audio-tests.log |
| Cheat base/range behavior | 143 checks pass | cheats-tests.log |
| Audio stream takeover behavior | PASS | audio-stream-tests.log |
| Final docs/environment/chain checks | 29 tests pass | docs-final.log |
| tool_lock --check-tools and deterministic default header | PASS | tool-lock-final.log |
| Mac Ocarina host build, -j2 | PASS; existing compiler warnings | host-build.log |

The initial full-tools run had one stale symptom-index failure; regenerated it
and reran the entire tools suite successfully. The initial translator GPU run
needed t_geometry_primitive_id; built both geometry helpers and reran all 267
translator tests successfully. Initial compile/fixture integration failures and
superseded logs are retained, not presented as final acceptance.

Python lint reports three pre-existing findings in unchanged test_nsp_mac.py
(two ModuleType attributes) and test_tree_tar.py (float days annotation).
No changed-code lint finding remains, and no baseline was expanded. C compile
database generation passes for 240 sources. C tidy is unavailable because
clang-tidy is not installed; the no-install boundary was preserved. See
lint-python-final.log, compdb.log and lint-c.log.

Default chain is f2466a5897f3. DMSH_OOT_VISUAL=1 gives 9f4500ea667b;
adding DMSH_RAW_LOAD_QUADS=1 gives 7bad6b632911. These are different library
chains, not interchangeable runtime flags for one prebuilt shader folder.
Locally rebuilt fingerprints are f40b6aa5b8d149b2 (dmsh_xlate),
8bf63b8a46b07003 (Shader), 87af5057f5d53131 (Common), with source digest
71adcdd020e03a64. One source publish ran, from the pre-verification source
snapshot 8f535d7e. Later changes are Python lint cleanup, docs and reports.
No C# source changed after that publish.

Storage cleanup used the explicit private NUGET_PACKAGES path with
`dotnet nuget locals global-packages --clear`. The generated nuget-feed and
publish directories were removed after checking for open files. Audit scripts,
publication records, logs and configs remain in the evidence folder. To rebuild,
rerun audit_nuget.py to recreate the cooled feed. Generated checkout outputs
remain because lsof found the harness node/node_repl processes holding their
cwd in this checkout. They were not stopped and no deletion sweep ran.
retained-generated-roots.txt records the exact known generated roots.

The final local source review remains the parent integrator's responsibility.
No nested reviewer or delegate was spawned because this task is itself the
implementation sub-agent assignment.

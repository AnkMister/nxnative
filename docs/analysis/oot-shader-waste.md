# Ocarina of Time shader waste investigation

Build v131072, title `0400486024DEC000`. Branch `oot-waste`, based on `oot-bench` commit `d7696c63`. Mac only. Static evidence; no game run.

## Inventory

All **42,851** mapped shaders were inspected. **42,823** have finished MSL, reflection and metallib outputs; **28** failed. The completed MSL totals 5,684,388,869 bytes. Successful stages are 15,852 vertex, 22,356 pixel, 4,104 compute, 492 mesh and 19 task. Failures are 19 compute, eight mesh and one task.

The ordered MSL manifest digest is `4a26dc019eecc25f704fb07f531c8555b1074f2901417b85cc686d468a2da452`. The census found no input modification during its reads. Detailed data is in `waste/census/shaders.jsonl`, `ranked.tsv` and `summary.json`. Relative `waste/` paths in this report are under `$NX_ANALYSIS/`.

Raw accesses occur in 2,224 successful shaders (717 compute, 90 mesh, 605 pixel, 10 task, 802 vertex). Expanded call-site totals are 522,028 raw loads, 863 raw stores and 144 raw atomic sites. The 15,168,015 table-read sites include mutually exclusive hint/search paths and repeated helper calls. They are not executed frame counts.

The scan also counts 686,994 sample/gather sites, including conditional border samples, 1,750 texture read sites, and 547,259 storage load sites. Its 17,370 lexical loops include 880 literal/exact lane-stride counts, 510 known lane-stride ranges and 15,980 unknown trip counts. Maximum lexical loop depth is 3.

The baseline packing process finished independently while this investigation was running. Its published archive metadata now confirms 30,515 bases for `applegpu_g16s`, macOS 26.0, chain `d1f10abd26a7`, depth `near=-w` and zero function-constant remainder pairs. The build folder remained read-only throughout this task. Archive metadata is a build-completion observation, not an archive hit or gameplay result.

## What the scan can establish

The Discord claim is plausible, but this scan cannot establish that five shaders dominate a frame. The strongest static leads are foliage mesh programs with hundreds of separate raw-memory word reads. A single source helper definition hides hundreds of pool lookups at its call sites. Their original SASS already does substantial animation and geometry work, so reducing translated overhead is safer than simplifying the game's math.

This is a complete build inventory, not a GPU profile. The package includes alternative quality settings, materials, debug programs, movie programs and mutually exclusive branches. A shader's presence in the build or a pipeline pair is not a draw count. The ranking is a queue for measurement. All speed estimates below refer to removed work within the shader. No GPU milliseconds, frame speedup or energy saving was measured.

The read-only input was `$OOT_BUILD` (the `0400486024DEC000_build` folder under the Ocarina NSP folder). Its pipeline archive was still building during inspection. No game, shader translator, full shader build or regression route was run. No pipeline archive file was read while being written. The scanner reads the finished shader files, reflection, package records and published build status. Each successful MSL and reflection file is checked for size or modification changes across its read. The ordered MSL content hashes feed the manifest digest below.

## Method and limits

`scripts/oot_shader_waste.py` emits one JSONL record per successfully translated shader and a separate failure list. It measures MSL bytes, primary-entry source work, loops, raw pointer operations, explicit and conditional border texture sample/gather calls, texture reads, storage-buffer loads, pool-table reads, repeated literal constant candidates, self assignments and local-array words. It counts loads at each helper call, including loop multipliers. It follows `main0` and its reachable generated helpers. Alternative depth, integer-output, alpha and geometry entry points are not added to the primary path. Overloaded SPIRV-Cross arithmetic/subgroup helpers are not expanded. Border sampling helpers are expanded.

Counts are static potential sites. Both sides of a conditional count even when one invocation takes only one. `sites` expands calls but counts loop bodies once. `estimated` multiplies literal trips and lane-stride upper bounds, with four trips for an unknown loop. `unknown_once` sets those unknown loops to one trip. Known loops are capped at 256 trips for ranking only. The JSONL records preserve uncapped literal counts and loop headers. Loop nesting is lexical within each function, not an interprocedural stack depth. Unknown loop bounds remain unknown. Empty-loop and repeated-load flags are inspection candidates, not proofs of dead code or redundant GPU instructions. In particular an empty atomic retry loop has a side effect and is not flagged as no-op work.

The cost model is explicit. Per invocation, `cost = statements + 80*raw accesses + 16*texture samples/gathers + 8*texture reads + 4*storage loads`. Raw accesses include loads, stores and atomics. The raw weight deliberately emphasizes pool lookup overhead; it is a guess, not a Metal instruction count. A gathered vector counts as one texture operation. A packed storage vector counts as one load. The pool-table read count is reported separately and is not added again to the score. Scores then multiply cost by a frequency weight. Foliage and names suggesting screen effects receive 8; other compute receives 4; other fragments receive 3; other stages receive 1. These weights are assumptions, never observed execution rates. Named program metadata in `pass-names.json` adds labels without changing the filename-based scoring rule.

A raw helper first checks a tagged 2 MiB chunk hint. A hit avoids the binary search. In the top foliage examples the miss path has twelve binary-search steps over 4,096 slots, then range validation and pointer adjustment. There are 29 potential table word reads per access on that path versus five on the hint path. Thus a counted raw access is a potential search, not proof a search executes. This scan does not incorporate the other lane's growing-table or quad-load changes. It inspects chain `d1f10abd26a7` from the baseline.

SASS is decoded directly from read-only NVN2 package records using the vendored Ampere opcode registrations and field definitions. The top-five `.sass.txt` files preserve raw 128-bit instructions, mnemonic, guard and raw register fields. This is a partial disassembly, not NVIDIA's full operand printer. LDG widths in the supporting evidence use bits 73 to 75 and the vendored `LsSize` enum. The control-section register count is the game's NVIDIA count. It is not Apple's register allocation. Guest `LDL`/`STL` counts indicate guest local-memory operations, not Apple spills. Apple register count and spill count remain null. The build logs and normal `metal --help` do not provide trustworthy backend allocation statistics. A `.metallib` byte size is not register pressure. Xcode GPU capture or supported backend statistics are needed before making an occupancy claim.

BAHS program names were recovered by a read-only RomFS/SARC pass using the repository's `romfs.py` and `shader_split.py`. The binary and program arrays associate declared program names with BAHS entry offsets. Unmatched stray entries remain unnamed. BNSH source paths, offsets and variation IDs remain the identity when a material/pass name is unavailable. The report does not invent labels such as grass or leaf for those BNSH variants. `pipelines` in each JSONL record links to descriptor kind, zero-based index, stage field and function in `pso/mac-work/bases.mtl4-json`. These are build pipeline bases, not runtime pass IDs. Compute and native mesh pipelines are absent from that file. Runtime pass association is an open measurement gate.


## Ranked top 30

All five highest scores remain the same when unknown loops assume one trip instead of four. Lower positions are sensitive to that assumption. `bc_encode` is a terrain development program, which may never run during play. Movie entries matter during video, not necessarily gameplay. The light-probe variants are alternatives, not ten independent costs per frame. NDSR/post-processing shaders were scanned but do not enter this top 30 under this cost model. Their screen coverage still makes them runtime measurement targets.

R is raw load sites per expanded primary entry. T is sample/gather sites, including possible conditional border samples. SB is storage load sites, including packed vector loads counted once. L/D is lexical loop count/depth. P is the number of regular render bases referring to this key. All top-30 entries have P=0 because these are compute or native mesh programs, which that archive script does not describe. Weight is the inferred frequency multiplier. Score is arbitrary cost units, not time.

| Rank | Shader key | Stage / program | MSL KiB | R | T | SB | L/D | Weight | Score / unknown-once |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `ae104328f80e5fb8` | mesh / foliage BNSH var3 | 533.8 | 971 | 0 | 73 | 5/2 | 8 | 2,152,704 / 2,149,728 |
| 2 | `7fd36d22b1f0fd14` | mesh / foliage BNSH var3 | 527.6 | 971 | 0 | 68 | 5/2 | 8 | 2,151,472 / 2,148,496 |
| 3 | `7eef23eeb0784836` | mesh / foliage BNSH var3 | 513.5 | 940 | 0 | 75 | 5/2 | 8 | 2,083,736 / 2,080,760 |
| 4 | `626fbf48041cb82b` | mesh / foliage BNSH var3 | 549.9 | 930 | 0 | 56 | 5/2 | 8 | 2,075,752 / 2,070,184 |
| 5 | `4c7d6be5a7717c8d` | mesh / foliage BNSH var0 | 337.9 | 506 | 0 | 53 | 5/2 | 8 | 1,142,288 / 1,136,720 |
| 6 | `17c8ab6419068d4b` | mesh / foliage BNSH var0 | 294.3 | 506 | 0 | 77 | 5/2 | 8 | 1,128,168 / 1,125,192 |
| 7 | `eed1add7c89f5d34` | mesh / foliage BNSH var0 | 297.4 | 506 | 0 | 59 | 5/2 | 8 | 1,127,992 / 1,125,016 |
| 8 | `106d0b03f3093bc3` | compute / light_probe_interpolator | 174.4 | 253 | 4 | 36 | 1/1 | 4 | 1,127,572 / 281,992 |
| 9 | `e50cd8240da0c805` | compute / light_probe_interpolator | 174.2 | 253 | 4 | 36 | 1/1 | 4 | 1,127,572 / 281,992 |
| 10 | `dc9bb120d987a9de` | compute / light_probe_interpolator | 173.2 | 253 | 4 | 36 | 1/1 | 4 | 1,127,360 / 281,900 |
| 11 | `73dc0b90c4082e43` | mesh / foliage BNSH var0 | 291.3 | 506 | 0 | 60 | 5/2 | 8 | 1,126,944 / 1,123,968 |
| 12 | `68691c9a4a821751` | mesh / foliage BNSH var3 | 299.5 | 494 | 0 | 32 | 6/2 | 8 | 1,111,440 / 1,106,736 |
| 13 | `6311cb728285f17d` | mesh / foliage BNSH var3 | 268.8 | 493 | 0 | 33 | 5/2 | 8 | 1,095,200 / 1,093,952 |
| 14 | `d15370a382630d4e` | compute / NDVE movie | 1553.4 | 384 | 0 | 258 | 0/0 | 4 | 1,063,112 / 1,063,112 |
| 15 | `bc05374f59a92b2b` | mesh / foliage BNSH var3 | 262.6 | 473 | 0 | 29 | 5/2 | 8 | 1,053,040 / 1,050,928 |
| 16 | `63c503a42355558a` | compute / bc_encode | 8596.5 | 0 | 0 | 0 | 18/1 | 4 | 1,010,400 / 655,284 |
| 17 | `d00c020b43022a68` | mesh / foliage BNSH var3 | 260.6 | 450 | 0 | 24 | 6/2 | 8 | 1,006,584 / 1,004,472 |
| 18 | `0342ab5e045200ee` | compute / light_probe_interpolator | 156.9 | 221 | 4 | 28 | 1/1 | 4 | 986,500 / 246,688 |
| 19 | `7370cdfc0cdfb186` | compute / light_probe_interpolator | 156.6 | 221 | 4 | 28 | 1/1 | 4 | 986,452 / 246,676 |
| 20 | `9263974f85fda84f` | compute / light_probe_interpolator | 156.7 | 221 | 4 | 25 | 1/1 | 4 | 986,324 / 246,644 |
| 21 | `e6be82d835fbe4d3` | compute / NDVE movie | 1200.9 | 0 | 0 | 272 | 1/1 | 4 | 926,276 / 250,580 |
| 22 | `f46b28bf3a3ec594` | compute / light_probe_interpolator | 136.4 | 157 | 4 | 36 | 1/1 | 4 | 710,348 / 177,656 |
| 23 | `ec83989ef66deb29` | compute / light_probe_interpolator | 136.3 | 157 | 4 | 36 | 1/1 | 4 | 710,316 / 177,648 |
| 24 | `c87802c2af5a5187` | compute / light_probe_interpolator | 136.4 | 157 | 4 | 36 | 1/1 | 4 | 710,264 / 177,632 |
| 25 | `919e2046032f4d4a` | compute / light_probe_interpolator | 128.0 | 157 | 4 | 36 | 1/1 | 4 | 706,480 / 176,716 |
| 26 | `083017de11d5589e` | mesh / foliage BNSH var3 | 380.9 | 254 | 2 | 24 | 6/2 | 8 | 599,064 / 597,816 |
| 27 | `96843c3dbdded1e7` | mesh / foliage BNSH var3 | 380.9 | 254 | 2 | 24 | 6/2 | 8 | 599,064 / 597,816 |
| 28 | `a76e46990e6799ba` | mesh / foliage BNSH var0 | 383.5 | 254 | 2 | 24 | 6/2 | 8 | 598,736 / 597,488 |
| 29 | `eb021183bf9b0092` | mesh / foliage BNSH var0 | 382.5 | 254 | 2 | 24 | 6/2 | 8 | 598,520 / 597,272 |
| 30 | `f85bb2e8d78b864c` | mesh / foliage BNSH var0 | 177.0 | 258 | 0 | 24 | 6/2 | 8 | 584,912 / 582,800 |

## Top-five source analysis

All five come from `/Shader/Foliage.Product.110.product.Nin_Ounce_NVN2.bfsha.zs`. They perform no texture sampling. The waste candidate is address translation around the geometry work, rather than an expensive fragment texture filter. Their raw helper has 29 possible pool-table reads and a single final 32-bit physical load. SASS has many 64/128-bit global reads, but the translated path repeats scalar lookup work for each word. The arithmetic and output stores in the original SASS remain necessary unless a separate semantic proof says otherwise.

The partial SASS listings and width histograms are retained as `waste/<key>.sass.txt` and `waste/top-five-sass.json`. MSL stays in the original read-only build. For example, the first shader defines its pool helper at line 129, calls it for adjacent words at lines 598 to 607, begins its main body at line 322, and initializes the mesh wrapper at line 13213. The four calls differ only in word address arithmetic, including carry handling. The source also has branches, so the counts below are possible paths rather than simultaneous execution.

### 1. `ae104328f80e5fb8` (BNSH@0x12c000#var3)

This is the largest lookup expansion. The SASS has 250 128-bit LDGs and 20 64-bit LDGs, while MSL has 971 separate raw word reads. Its mesh wrapper clears 2,677 threadgroup words (10,708 bytes) per workgroup and emits up to 96 vertices and 64 primitives. The repeated table lookup is translator overhead. The original 1,172 FFMA and 723 FMUL instructions show that much of the deformation math comes from the game.

Measured static evidence: 546,582 MSL bytes; 971 raw loads; 73 storage loads; 3,992 original instruction slots; LDG widths {'32': 36, '128': 250, '64': 20}; 255 guest registers and zero guest LDL/STL instructions. Pool helper `_58` begins at MSL line 130. Apple register/spill pressure is unmeasured.

**Proposed fix: generic translator or build-time post-pass.** Preserve and group eligible adjacent scalar reads from each original wide access, resolving their pool once and retaining scalar behavior on boundaries. The ideal ceiling for this shader is 971 lookups to 243 if every read formed groups of four, saving up to 728 lookups. Actual eligible grouping is not measured here. The same pool-boundary, predicate and write-order proof applies independently to this key. No per-shader override is justified. No runtime compilation is allowed.

### 2. `7fd36d22b1f0fd14` (BNSH@0x159000#var3)

This sibling has the same 971 raw accesses and the same LDG width mix as rank 1, but fewer original arithmetic instructions (1,117 FFMA and 676 FMUL). That supports treating repeated lookup work as a shared lowering problem rather than deleting this variation. It uses the same 2,677-word stage buffer and 96-vertex/64-primitive wrapper.

Measured static evidence: 540,221 MSL bytes; 971 raw loads; 68 storage loads; 3,880 original instruction slots; LDG widths {'32': 36, '128': 250, '64': 20}; 255 guest registers and zero guest LDL/STL instructions. Pool helper `_58` begins at MSL line 130. Apple register/spill pressure is unmeasured.

**Proposed fix: generic translator or build-time post-pass.** Preserve and group eligible adjacent scalar reads from each original wide access, resolving their pool once and retaining scalar behavior on boundaries. The ideal ceiling for this shader is 971 lookups to 243 if every read formed groups of four, saving up to 728 lookups. Actual eligible grouping is not measured here. The same pool-boundary, predicate and write-order proof applies independently to this key. No per-shader override is justified. No runtime compilation is allowed.

### 3. `7eef23eeb0784836` (BNSH@0x185000#var3)

This variation has 940 raw word reads versus 301 guest LDG instructions, including 242 128-bit reads. The 2,677-word stage buffer and 96-vertex wrapper have the same generic initialization cost. Its smaller arithmetic body still contains 1,088 FFMA and 646 FMUL instructions. The search-and-pointer work is added by the translator; the transform math is present in SASS.

Measured static evidence: 525,837 MSL bytes; 940 raw loads; 75 storage loads; 3,760 original instruction slots; LDG widths {'32': 49, '128': 242, '64': 10}; 255 guest registers and zero guest LDL/STL instructions. Pool helper `_58` begins at MSL line 130. Apple register/spill pressure is unmeasured.

**Proposed fix: generic translator or build-time post-pass.** Preserve and group eligible adjacent scalar reads from each original wide access, resolving their pool once and retaining scalar behavior on boundaries. The ideal ceiling for this shader is 940 lookups to 235 if every read formed groups of four, saving up to 705 lookups. Actual eligible grouping is not measured here. The same pool-boundary, predicate and write-order proof applies independently to this key. No per-shader override is justified. No runtime compilation is allowed.

### 4. `626fbf48041cb82b` (BNSH@0x1b1000#var3)

This has 930 raw reads and the largest original body among the five (4,192 SASS instructions). It also has two guest CALL sites and subgroup operations. Its wrapper clears 4,293 words (17,172 bytes) and emits up to 160 vertices and 128 primitives. Both the repeated address translation and wrapper marshaling are investigation targets. Removing helper calls or subgroup work would need a separate proof.

Measured static evidence: 563,146 MSL bytes; 930 raw loads; 56 storage loads; 4,192 original instruction slots; LDG widths {'32': 27, '128': 239, '64': 12}; 255 guest registers and zero guest LDL/STL instructions. Pool helper `_61` begins at MSL line 413. Apple register/spill pressure is unmeasured.

**Proposed fix: generic translator or build-time post-pass.** Preserve and group eligible adjacent scalar reads from each original wide access, resolving their pool once and retaining scalar behavior on boundaries. The ideal ceiling for this shader is 930 lookups to 233 if every read formed groups of four, saving up to 697 lookups. Actual eligible grouping is not measured here. The same pool-boundary, predicate and write-order proof applies independently to this key. No per-shader override is justified. No runtime compilation is allowed.

### 5. `4c7d6be5a7717c8d` (BNSH@0x1b1000#var0)

This is variation 0 of the same BNSH section as rank 4. Its original body is smaller, with 169 LDGs and 651 FFMA instructions, but still produces 506 raw scalar accesses. The wrapper clears 3,973 words (15,892 bytes) and has the same 160-vertex/128-primitive capacity. It is a useful smaller A/B candidate for the same generic lookup change. It is not a replacement for variation 3.

Measured static evidence: 346,045 MSL bytes; 506 raw loads; 53 storage loads; 2,768 original instruction slots; LDG widths {'32': 26, '128': 133, '64': 10}; 255 guest registers and zero guest LDL/STL instructions. Pool helper `_59` begins at MSL line 411. Apple register/spill pressure is unmeasured.

**Proposed fix: generic translator or build-time post-pass.** Preserve and group eligible adjacent scalar reads from each original wide access, resolving their pool once and retaining scalar behavior on boundaries. The ideal ceiling for this shader is 506 lookups to 127 if every read formed groups of four, saving up to 379 lookups. Actual eligible grouping is not measured here. The same pool-boundary, predicate and write-order proof applies independently to this key. No per-shader override is justified. No runtime compilation is allowed.

## Fix policy

Visual risk comes first. No runtime or shader behavior change is included in this branch. No new runtime compile, lazy shader path or JIT fallback is added. The promising generic pool-lookup change is already owned by the separate #1405 lane; duplicating it here would add integration risk. It also requires a proof that grouped words stay in one pool, preserve address wrap, retain invalid-address behavior, do not cross a memory write or barrier, and preserve per-word predicates. That is not a safe textual replacement of four calls with one unconditional wide load.

For each of the five candidates below, the first proposed fix is generic translator lowering or a build-time MSL post-pass that retains the original predicates and falls back to the original scalar code on a pool boundary. Its ideal local gain is up to 75% fewer lookups for eligible groups of four words. If pool lookup is fraction `f` of that shader's GPU duration and all lookups group into fours, its ideal time becomes `T*(1-0.75*f)`. For example, the assumed case `f=0.5` gives 37.5% lower shader time. This is a conditional estimate, not a prediction or a measured frame gain. Hint hits, partial groups, divergence, register lifetimes and other bottlenecks can make the gain much smaller or negative.

A second generic investigation is the mesh wrapper's stage-memory initialization and output marshaling in `dmsh_meshstage.py`. Removing an initialization is valid only after proving that every surviving read is preceded by an equivalent write across all lanes and barriers. Removing an attribute requires proving no consumer or program variant reads it. No such proof is available here. Neither clearing less memory nor emitting fewer vertices is proposed as a per-shader override. Do not remove CAS retry loops, contraction guards, precision operations or animation math merely because their MSL is large. A default-off flag alone does not make an unproven image change safe.


## Runtime confirmation without compilation during play

The first gate is pipeline completeness. Package all shader libraries and all pipeline descriptor variants needed by the chosen route at build time, including compute and native task/mesh pipelines. Verify archive/device architecture, OS compatibility, chain and profile-input stamps before entering gameplay. Build any candidate shader and pipeline changes into a separate package. Do not use an online fallback to hide incomplete coverage.

This host has no trustworthy per-shader GPU timing log. `DM_NVN_GPUPROF=every:60` uses Metal 4 counter heaps to report encoder spans with pass shape, draw counts and compute/copy counts. A render encoder may contain many shaders and a compute encoder may contain multiple dispatches. Its encoder times are not individual shader times and overlapping work must not be summed as exclusive cost. `DM_NVN_PASSDUMP` gives pass serials, pipeline keys and stage keys for association. Its periodic `every:n` mode is intentionally offset from GPU profiling, so use a matching fixed frame range for an exact same-frame join.

Do not rely on `DM_NVN_PASSGPU` for this branch. `pg_render` returns immediately and its implementation is inside `#if 0`; `enc_c_begin` ignores its descriptor and uses a Metal 4 compute encoder, so the old stage-boundary sample descriptor passed by `pg_compute` is not attached. Enabling it can still split dispatch encoders and alter scheduling without producing valid samples.

For useful shader attribution, extend the existing Metal 4 counter-heap diagnostic with a default-off selector for shader keys and sampled frames. Record frame, segment, encoder/pass, draw or dispatch ordinal, full pipeline identity, all stage keys, render extent, workgroup sizes and direct/indirect work counts. Timestamp the selected dispatch or same-pipeline draw range and resolve only after GPU completion. Report capacity overflow and dropped samples explicitly. A render interval is the whole pipeline cost, including mesh/task/fragment stages, not an isolated stage. Use Xcode stage counters/capture for stage attribution. Prefer sampling selected dispatches inside the existing encoder; a diagnostic that splits encoders or serializes passes must report that perturbation. This instrumentation loads already built pipelines and must never compile one.

Confirm that each top-five key actually runs in a fixed Kokiri Forest save and camera, then collect its invocation count and GPU share. Compare baseline/candidate packages at the game's 30 fps cap, identical resolution, settings and save. Use interleaved A/B/A runs with repeated scenes and report per-run GPU p50/p95/p99, hitch counts, missed presentations, CPU work and energy. Stop concurrent builds for this measurement. Shader/counter profiling is a separate run from clean frame and energy measurement. Do not infer a GPU win from an unchanged capped FPS number.

For equivalence, require identical read addresses, predicates, byte values, wrap and boundary behavior for the pool optimization. Add synthetic tests for adjacent words spanning two pools, 32-bit carry/wrap, missing mappings, partial predicates and stores/barriers between reads. After compilation, compare the same deterministic frame captures with pixel diffs and inspect foliage edges, motion, depth, transparency, colors, bloom and bright dots. Semantic equality of memory loads supports the change but does not replace image checks or prove an Apple scheduling improvement. No public rollout until visual checks pass and compile counters remain zero during gameplay.


## The existing host does compile pipelines during play

The ahead-of-time model is currently incomplete on `oot-bench` / this baseline. Game shaders are translated and compiled to `.metallib` during packing, but Metal pipeline creation and specialization still happen at runtime. Loading a library is distinct from compiling a pipeline.

| Path | Source evidence | Runtime result |
|---|---|---|
| Missing game shader library or reflection | `nvn_mtl.m:4689`, `:4702`, `:4920`, `:11388`; `nvn_geometry.inc:593` | Loader returns nil and logs `[RED]`. Missing compute skips its dispatch. Missing task/mesh skips its draw. These are the stages of all 28 failures here. There is no SASS-to-MSL retry or direct crash in this path. Later use of unwritten/stale buffers can still cause visual errors or downstream failures. |
| Render archive miss | `nvn_mtl.m:6933`, `:6990`, `:6780`, `:7450` | `pso_build_ex(..., compile=1)` calls `arch_capture`, which invokes the Metal compiler. The draw can wait. `compile=0` is used by archive-only probes, but a later path falls back to `compile=1`. |
| New render state on an archived base | `nvn_mtl.m:7005` | Calls `newRenderPipelineStateBySpecializationWithDescriptor`. An archived unspecialized base is not every final pipeline state. This still performs runtime pipeline work; the amount of compiler work depends on Metal. |
| Hybrid/prediction | `nvn_mtl.m:7147`, `:7436`, `:7469` | May draw using a pulling stand-in while the exact pipeline builds, or queue a missing base. Disabling hybrid makes the draw wait; it does not make the archive complete. |
| Compute cache miss | `nvn_mtl.m:11389`, `:11393`, `:7578` | Calls `newComputePipelineStateWithFunction` on first demand or prewarm, then caches by shader function. This baseline's offline descriptor script has no compute pipelines. |
| Native task/mesh cache miss | `nvn_geometry.inc:558`, `:574`, `:577` | Queues `newRenderPipelineStateWithMeshDescriptor` in the background. Returns nil until ready; affected draws are omitted. These pipelines do not use the regular render-base archive path. |
| Built-in/helper and exceptional paths | `nvn_mtl.m:10409`, `:10484`, `:10623`, `:11727`, `:12175`, `:12677`, `:12811` | Several first-use helper pipeline states and some diagnostic/exceptional MSL paths are created online. Audit them separately before claiming a global no-compile policy. They are not a fallback for the 28 failed game shaders. |

The source check identifies opportunities for runtime work, not an observed miss rate. The Ocarina build's static coverage counts are recorded below. There is no finite bound on final render-state combinations from shader count alone. Cache hits avoid repeat creation, so these are usually first encounters with distinct descriptors, not necessarily a compile every frame. Device/OS/chain mismatch can invalidate archive coverage altogether. Missing native mesh pipelines also create missing geometry while their asynchronous jobs complete, even if frame-time stutter is hidden.

Existing `mtl_pso_line` logs archive hits/misses, specializations, bases compiled, hybrid misses, background work and draws that waited. `DM_PSO_WAITLOG=1` adds slow-wait detail, but logs only a limited number of waits over its threshold and cannot prove zero compiles. Add a counter at every Metal compiler and pipeline-creation entry, including compute, mesh, helper paths and function specialization, split into startup versus gameplay. Record descriptor hash and reason. A strict AOT validation mode should reject an uncovered descriptor before gameplay with a clear diagnostic. It must not silently skip a draw or fall back to compilation. Complete the offline archive builder and preflight coverage first; making every miss fatal without doing that would make the game unusable.


## Ocarina pipeline coverage and possible miss frequency

| Static coverage item | Count | Meaning |
|---|---:|---|
| Unique vertex/pixel pair rows | 33,190 | Union of shader_pairs.tsv and pso_pairs.tsv |
| Published offline regular render bases | 30,515 | Matches the completed archive metadata and descriptor input |
| Layer-writing pairs excluded | 2,675 | Offline planner explicitly leaves these out |
| Function-constant remainder pairs | 0 | No such remainder in this build |
| Successful compute shaders | 4,104 | None represented in the offline base descriptor script |
| Compute shaders in the committed prewarm list | 11 | All NDVE title/movie entries; created at startup, not covered offline here |
| Other successful compute shader keys | 4,093 | Potential first-use pipeline creations if used and not otherwise prewarmed |
| Successful native mesh/task shader keys | 492 / 19 | No native mesh pipeline descriptor in the offline archive script |

These are exposure counts, not an expected compile count per frame. The 2,675 excluded pairs can require pipeline creation when first encountered; each may have multiple layouts or render states. New vertex layouts, MSAA, alpha-to-coverage, depth/stencil formats, integer outputs, layer/primitive requirements, merged-pass functions and blend state can create additional descriptor identities. Even covered pairs may need specialization or a layout-specific pipeline. Native mesh combinations also include the task, mesh and fragment functions plus render state, so 492 is not a bound on native mesh pipeline count. Without runtime descriptor census and counters the miss rate is unknown. A fully warmed short route cannot prove coverage of all Ocarina scenes.

## All 28 failed build candidates

The status snapshot reports 18 failures at opcode `0x243`, six at `0x3a9`, one ISBERD `0xb8` mode, one apparent `0x481` instruction and two Metal bracket-depth errors. The `0x243` and `0x3a9` instructions are not registered by this translator. Packed-conversion modes must be decoded and tested against their exact operands; the nearby implementation in another branch is not proof that all modes are covered. ISBERD is recognized, but that task/mesh mode explicitly throws. The two compiler failures are confirmed by the build log, which associates both shader IDs with `fatal error: bracket nesting level exceeded maximum of 256`. Increasing a build-time bracket limit may unblock compilation, but is not a performance fix and needs compilation and output checks.

One failure is probably a false candidate from extraction, rather than a missing instruction. `68bbe98b3bfd9876` points to BAHS offset `0x357f0`, which is inside the binary array but is not any record's actual entry at `record+0x10`. Its apparent code begins with graphics SPH word `0x020c0481`, while the accidentally selected control data marks compute. A compute translator then decodes the SPH as opcode `0x481` at zero. The record-boundary mismatch and header word are confirmed in `waste/68bb-evidence.json`; whether this synthetic key can ever be requested by the game is unverified. Do not implement a fake `0x481` operation to silence this diagnostic.

The runtime outcomes below follow the current loader and dispatch/draw guards. They are not observations from a new game run. None of these 28 has a runtime translation/compile fallback or a direct crash at library lookup. A skipped compute pass can leave stale output and cause later visual errors or failures, so "skipped" does not mean harmless.

| Shader key | Stage / declared source | Build cause | On use |
|---|---|---|---|
| `aaa785ced92a88ef` | compute / video_recorder_rgb_to_yuv | unsupported 0x243 at 0x4e0 | dispatch skipped |
| `99951da6e5cd38f5` | compute / video_recorder_rgb_to_yuv | unsupported 0x243 at 0x530 | dispatch skipped |
| `68bbe98b3bfd9876` | compute / unmatched BAHS candidate | SPH decoded as 0x481 at 0x0; spurious-entry evidence above | dispatch skipped |
| `1f78730053feb036` | compute / auto_exposure_aggregation | Metal bracket nesting > 256 | dispatch skipped |
| `e172bd7ec218ab8e` | compute / auto_exposure_aggregation | Metal bracket nesting > 256 | dispatch skipped |
| `c144d8f734fbe228` | compute / foliage_mesh_turf | unsupported 0x3a9 at 0x8830 | dispatch skipped |
| `13002657609092b4` | compute / foliage_mesh_turf | unsupported 0x3a9 at 0x8c00 | dispatch skipped |
| `8692b34b521225be` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x6270 | dispatch skipped |
| `e8b64d5ad83c7e22` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x69d0 | dispatch skipped |
| `dac121a8c0b3efbd` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x6340 | dispatch skipped |
| `00b0635ae2b9613b` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x6ab0 | dispatch skipped |
| `83df46a0b1b379b4` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x6e80 | dispatch skipped |
| `c26c20f61455fb9e` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x7640 | dispatch skipped |
| `8336f2da0f51938d` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x7010 | dispatch skipped |
| `10a2c776a57f5071` | compute / foliage_mesh_leaf | unsupported 0x243 at 0x7730 | dispatch skipped |
| `7d1481cf3458b690` | compute / foliage_mesh_leaf | unsupported 0x3a9 at 0x8370 | dispatch skipped |
| `49d003551e7dcaf1` | compute / foliage_mesh_leaf | unsupported 0x3a9 at 0x8790 | dispatch skipped |
| `de5a4f469cb990b2` | compute / foliage_mesh_leaf | unsupported 0x3a9 at 0x8720 | dispatch skipped |
| `3b8ecb1aa4207240` | compute / foliage_mesh_leaf | unsupported 0x3a9 at 0x8ae0 | dispatch skipped |
| `fed302d791a4ba43` | mesh / foliage BNSH var0 | unsupported 0x243 at 0x3d0 | mesh draw skipped |
| `819c33c90234fcb6` | mesh / foliage BNSH var3 | unsupported 0x243 at 0x3a0 | mesh draw skipped |
| `604134a5262ff670` | mesh / foliage BNSH var0 | unsupported 0x243 at 0x38e0 | mesh draw skipped |
| `ca03b41694d4c196` | mesh / foliage BNSH var3 | unsupported 0x243 at 0x47b0 | mesh draw skipped |
| `9ecd96cec34c7315` | mesh / foliage BNSH var0 | unsupported 0x243 at 0x3a0 | mesh draw skipped |
| `740e2b04db624fb1` | mesh / foliage BNSH var3 | unsupported 0x243 at 0x370 | mesh draw skipped |
| `ecead5cd0569091f` | mesh / foliage BNSH var0 | unsupported 0x243 at 0x3c0 | mesh draw skipped |
| `adbaa02880733cf0` | mesh / foliage BNSH var3 | unsupported 0x243 at 0x390 | mesh draw skipped |
| `5d3a096025e375a1` | task / light_probe_debug | ISBERD mode 0xb8 in task stage at 0x80 | mesh draw skipped |

## Reproduction and validation

The committed scanner is independent of the shader chain. It imports no build driver and never compiles a shader or pipeline. It supports at most three analysis workers; with the coordinator that is four processes. Set `OOT_BUILD` to the baseline build folder, `NX_ANALYSIS` to the analysis folder and `OOT_PYTHON` to the existing uv Python executable. The equivalent read-only census command is:

```sh
export TMPDIR="${NX_ANALYSIS:?}/setup/scratch"
export PYTHONDONTWRITEBYTECODE=1
task_py="${OOT_PYTHON:?}"
"$task_py" scripts/oot_shader_waste.py \
  "${OOT_BUILD:?}" \
  --pass-map "${NX_ANALYSIS:?}/waste/pass-names.json" \
  --jobs 3 --out "${NX_ANALYSIS:?}/waste/census-replay"
"$task_py" -m unittest dm/tools/tests/test_oot_shader_waste.py -v
```

Use a new output directory. Omitting `--pass-map` recovers BAHS names read-only from this build's `extract/v131072/RomFS.img` through the existing repository readers, then writes the recovered map alongside the census. The independent name extractor and this scanner recovered the same 6,582 key/name associations. No game files or shader sources are copied into the repository.

Fourteen focused tests cover helper-call expansion, known and unknown loops, nested loops, zero trips, per-lane bounds, atomic conditions, border samples, storage reads versus writes and pointers, packed vector loads, alternative entry exclusion, raw stores, guest SASS fields, pipeline references and the read-only output guard. Ruff and Pyright on the new tool and test pass. Broader lint and documentation results are recorded in implementation-notes.md. Independent review and gameplay/Metal equivalence checks remain parent gates. No five-game regression was run because this task explicitly forbids game launches and full shader rebuilds.

The full census, partial SASS, supplemental name/coverage evidence and compiler-help output are retained under `waste/` for review. Interrupted census attempts are removed after confirming their task processes have ended. No dependencies, builds, venvs or game files were created in the checkout. The report and compact summary are committed in docs/analysis; the requested shader-waste.md in the analysis folder contains the identical Markdown.

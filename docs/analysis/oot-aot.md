# Ocarina ahead-of-time pipeline coverage

The opt-in AOT path builds compute pipelines, layer-writing render bases, inferred native task/mesh bases, built-in compute helpers and learned exact render/mesh states into the offline archive. Startup loads the packed descriptor inventory through archive-only APIs on four workers and waits for completion before the first game submission continues.

The hard rule of zero compilation throughout Ocarina gameplay is **not yet proven**. Unknown final state, unsupported function constants, missing shader translations and unobserved task/mesh combinations remain coverage gaps. The preflight report always says `complete: false`. No game or full shader rebuild was run for this change.

## Controls and compatibility

`DM_AOT=1` enables expanded packing and runtime archive lookup, startup prewarm and descriptor recording. It defaults off. Set it for the packer and in the game's runtime environment. Existing behavior is preserved when it is unset, apart from always-on accounting and diagnostic library labels.

`DM_AOT_STRICT=1` independently marks every gameplay compiler API entry `[RED]`. It defaults off and still compiles the requested pipeline. Strict mode reports gaps while keeping the game playable. It does not assert that Apple's driver performed a machine-code compile, since pipeline creation and specialization can also use driver caches. Counting every compiler-capable API entry gives a conservative zero-work test.

`DM_AOT_LOG_SECONDS` sets the summary interval, default 5 seconds. Counters are cumulative and split into startup and gameplay compiler entries and archive API entries. Individual compiler lines identify the class, descriptor hash, identity and reason. Native render, specialization, compute, mesh, helper, function-constant specialization and library-from-source calls are accounted for. Archive calls are counted separately and do not count as compiler work. Accounting covers the NVN host and its shared helpers, including early GPU deswizzle initialization.

Startup ends at the first game present. Title and loading screens after that boundary count as gameplay too. Background compilation that crosses the boundary therefore remains visible. Summaries are emitted from compilation events and presents when the interval has elapsed and counters changed. There is no timer thread. `DM_PSO_PREPARE_THREADS=4` also bounds the older manifest prewarm, which remains separate from the new archive-only loader.

## Offline coverage

`pso_offline.py --aot` keeps the existing bounded batches and content-based cache keys. Pipeline settings, every referenced library's bytes, platform, architecture, OS minimum and compiler version remain build inputs.

- Every successful `cs` reflection with a matching chain, an existing metallib and an entry without function constants gets a compute descriptor. Missing libraries and constants are reported.
- Layer-writing pairs are included with triangle topology. The old planner excluded them. Final formats and blend state still need an exact descriptor.
- The shader map's program-source field supplies native mesh/task/fragment combinations only when the source identifies one mesh, one fragment and at most one task. A task-required mesh needs the task reflection too. The planner avoids a Cartesian product across unrelated programs. First-source-only map data loses some associations, so unmatched mesh keys remain an explicit gap.
- Known mesh combinations get bases with open color state. Exact task, mesh and fragment identities, payload, thread limits and final render state come from learned descriptors. A covered native mesh pipeline is available synchronously before its draw, avoiding the old asynchronous draw omission. An AOT mesh miss compiles synchronously and records the state, which can stall but preserves geometry.
- Built-in compute helpers are compiled from the same sources, source paths and deployment target as the host's embedded libraries. The fixture checks that their archive lookups match the embedded bytes. Helper render state is learned like ordinary render state. Helper libraries alone never prove pipeline coverage.
- Every regular render base, including the layer bases, is listed in the startup inventory. Loading a base does not specialize it. Learned exact states bypass base specialization during gameplay.

The planner handles both public-metadata length conventions emitted by `metal -c` followed by `metallib`, and by direct `metal -o`. Small actual libraries exposed this difference.

## Descriptor learning

With `DM_AOT=1`, new exact pipeline states are appended to `pso_seen.jsonl` beside the existing per-game `pso_user.tsv`. `DM_PSO_SEEN` overrides that destination. The file contains chain version, schema version, library names, entry points and numeric Metal state. It contains no machine paths or process pointers. Existing rows are read to avoid appending duplicates across launches.

The existing `pso_user.tsv` remains intact. Its binary render keys serve the older warm path. The portable `pso_seen` records serve the offline compiler and the new exact lookup path.

The Mac app packer automatically consumes the game's standard per-game `pso_seen.jsonl` when `DM_AOT=1`, or the file named by `DM_PSO_SEEN`. A direct tool invocation takes repeatable `--seen` arguments. Stale chains, absent entries, function constants and invalid references fail visibly instead of claiming coverage. Keep old-chain observations separately when rebuilding the shader chain.

After packing, `scripts/aot_preflight.py` writes the class counts, omitted categories, unknown final-state classes and packed archive sizes to `pso/mac-preflight.json` in the build folder. The runtime startup line then reports actual archive-only lookup misses on the target GPU and OS. Static inventory cannot verify those lookups.

The packed `aot.json` contains regular bases, inferred mesh bases, compute/helpers and learned exact states. Startup loads them with no compiler fallback. A missing or incompatible inventory logs `[RED]`. Existing manifests may still compile startup states that are not covered by that inventory, and those entries are counted.

## Remaining gaps

New vertex layouts, attachment formats, blending, samples, alpha-to-coverage, integer-output entries, layer/primitive requirements and merged-pass functions can create new final descriptors. Shader count alone cannot bound their combinations. The first encounter can compile. Repacking its learned descriptor removes that exact miss on the same compatible shader/device/OS inputs.

Function-constant specializations and diagnostic source shaders are counted but are not represented by the portable schema. Their values cannot be recovered from the public constant-values object by the current recorder. They need explicit schema support and producer-side recording before claiming complete coverage. Pipelines without a rasterized fragment stage can also require the legacy path because of Metal 4 descriptor restrictions.

The supplied shader-waste audit also identifies failed compute and native mesh/task translations. Pipeline archives cannot repair missing shader libraries. Their dispatches or draws can still be missing. Translation fixes and visual validation are separate acceptance requirements.

Preloading all bases and retaining exact pipelines increases startup CPU work and memory. Full-game startup memory and resource use have not been measured. The four-worker limit bounds concurrent loaders, while pipeline count and complexity determine total memory. No image equivalence or full-route stutter result is claimed.

## Archive size and build effort

The supplied static audit reports 30,515 existing render bases, 4,104 successful compute shaders and 2,675 excluded layer pairs. Compute and layer coverage add 6,779 descriptors, about 22.2 percent of the previous base count, before mesh combinations and learned state.

Using the existing archive tool's approximately 41 KiB per-base observation as a sizing assumption gives about **265 MiB extra** for those 6,779 descriptors. Budget roughly **0.13 to 0.53 GiB extra** as an initial twofold range around that estimate. Compute and mesh binaries can differ substantially from ordinary render bases. Each 1,000 learned descriptors adds approximately 40 MiB at the same assumed density. These are estimates, not measurements of a rebuilt Ocarina archive.

First-build pipeline compiler work increases by roughly 22 percent by descriptor count, plus mesh and learned descriptors. Native mesh shaders can cost more per descriptor, so that is not a wall-clock multiplier. Unchanged batches are reused. No unrelated task/mesh Cartesian product is built. The synthetic test builds 26 descriptors in sequential groups of eight and verifies that learning one new final state reuses unchanged groups and rebuilds only the changed last group. The complete fixture test, including small library creation and the learning rebuild, took about 5 to 7 seconds on this machine. It is not a production build-time estimate.

## Validation and use

The following checks passed:

- The existing offline planner suite ran 38 tests.
- The existing Mac app packing suite ran 63 tests.
- The existing pipeline bundle fixture passed 58 checks.
- The embedded host shader fixture passed 67 checks.
- The new suite passed 3 tests, including actual batched render, layer, compute, task/mesh and helper archives. Startup and covered gameplay lookups invoked zero compiler APIs. A deliberately changed format invoked one compiler API, logged `[RED]`, was recorded, and was accepted by the next archive build. The render fixture uses the same full default vertex-descriptor shape as the host.
- The Ocarina Mac host built successfully with at most four jobs. The changed Python files pass Ruff and Pyright.

The full Python lint command reports three findings in unchanged tests: two assignments to `NSP_FOLDER` in `test_nsp_mac.py` and a float passed to `days` in `test_tree_tar.py`. C lint cannot run because `clang-tidy` is absent. No dependency was installed. Independent code review, full Ocarina archive construction, route testing and image checks remain integrator gates. The requested no-game rule also prevents the usual five-game runtime regression.

Reproduce the focused checks with the existing uv Python, a persistent `TMPDIR` on the work drive and `GAME=0400486024DEC000`:

```sh
"$OOT_PYTHON" -m unittest dm.tools.tests.test_pso_offline dm.tools.tests.test_nsp_mac_app
make -C dm/gfx/tests -j4 GAME=0400486024DEC000 t_aot t_host_msl t_pso_bundle
DM_TEST_AOT="$PWD/dm/gfx/tests/t_aot" "$OOT_PYTHON" -m unittest discover -s dm/gfx/tests -p test_aot.py
(cd dm/gfx/tests && ./t_pso_bundle && ./t_host_msl)
make -C dm/host -j4 GAME=0400486024DEC000 dmhost
```

For gameplay acceptance, first pack with `DM_AOT=1` and the intended per-game census. Read `aot-preflight.json`. Then enable `DM_AOT=1 DM_AOT_STRICT=1` for an authorized route run. Require zero misses in the startup archive-only line, no gameplay compiler event and no increase in the cumulative `gameplay compiler` total. Save the full log, repack new observations and repeat every required route. Any `[RED] AOT phase=gameplay` line is a failure of the zero-compilation rule even when the picture remains playable. Also inspect foliage, colors, bloom, missing geometry and flicker. A passing short route cannot prove all scenes covered.

## Storage and delivery

The branch is `oot-aot`, based on `oot-stable-fix` at `78ccb75f`. No push, PR, game launch, full shader rebuild, signing or device installation occurred. No protected checkout or game work folder was written.

Task logs and small retained compiler probes are under the external `aot-fixtures` folder. Unit tests remove their own temporary fixture folders after completion. Generated host/test executables and generated headers are handled as recorded in `implementation-notes.md`; the abandoned synthetic `t_pso_bundle.7XIAj6` folder was removed after checking it was unused and contained no Git metadata, and its invocation log was preserved. Generated headers (13 MiB) and executables (about 9 MiB) remain for the integrator’s pending acceptance work. Source, reports and acceptance logs are retained. No cleanup sweep or dependency/cache removal ran.

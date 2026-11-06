# X1 stage cache implementation

Branch `oot-stagecache`, based on `oot-base` (`ee9b7765`). Mac scope only.

## Design and decisions

The complete-shader cache and its dependency fingerprint remain conservative. A complete hit still restores the existing artifacts. On a miss, `DMSH_STAGECACHE=1` enables the following intermediate caches. With the variable unset, tools follow the existing path. `DMSH_STAGECACHE_WARM=1` also bypasses complete hits to seed intermediates. Leave warm mode unset after migration.

1. Translation keys include the input shader bytes, every translation job field except the input pathname, and a fingerprint of every file in the selected translator distribution, including its executable, DLLs and runtime configuration. Job construction always runs, so profile answers, control-derived settings, c1 bytes, integer attribute types, architecture, geometry topology and translator flags are included as actual inputs. Raw `.spv` and `.res.json` are published together, before any SPIR-V mutation. Geometry jobs also include `.reader.spv`. Integer-input retries have distinct job keys. Failed retries cannot publish stale outputs.
2. SPIRV-Cross keys include the SPIR-V bytes after applicable rewrites, the actual converter bytes and all converter flags. Its MSL or geometry GLSL output is cached. Failed conversions are not cached.
3. Each pure MSL pass has its own key containing its arguments, flags and code fingerprint. A module pass fingerprints its whole module, transitive local Python imports and declared data files. Inline build functions fingerprint their source, referenced helper functions, constants and local modules. Nested functions' global references count. Unknown imports, unsupported global state and closures fail closed. Python's full version is included. Metadata results and `None` outputs are preserved. Pair padding reads current paired pixel locations before its pure transform is cached. Applicability remains in the builder's existing stage branches. Mesh wrapping therefore never runs on an ordinary pixel shader.
4. The existing `dmsh_mtlcache` remains unchanged. Exact final MSL, compiler identity and compile flags determine reuse. The final chain header, lock checks, profile stamp and ABI checks remain active. Every ABI header byte is in the complete-shader fingerprint and selects a new intermediate database. All intermediate stages miss after an ABI edit. An identical final Metal compile input can still reuse its library safely.

The cache hashes large MSL strings once across no-op passes and retains 32 recent decoded objects per worker. Cached mutable values are copied before return. Those choices avoid repeatedly decoding the same large source without letting callers mutate cached metadata.

## Disk layout and overhead

`<DMSH_CAS>/stages/v1-<SHA256 of dmsh_abi.h>.sqlite3` contains two tables. `entries` maps dependency hashes to output hashes. `objects` stores zlib-compressed, typed JSON output values. Tuples, bytes and dictionary key types survive round trips. Identical outputs share objects across passes. WAL transactions publish complete entries atomically. Separate processes and up to four test workers can write concurrently. WAL companion files may exist while the database is open. Copy or remove a database only after its writers stop. Hash validation treats damaged objects as misses. Bump `FORMAT` when changing cache semantics.

Existing NSP cache pruning preserves `cas/stages`, and the existing cache archive includes it. Old ABI databases and superseded stage entries currently accumulate. Deleting `cas/stages` while idle is the supported reset; keep `cas/metallib` to retain Metal reuse. There is no new package dependency.

Measured read-only samples from the running baseline, first 64 matching files in directory order, not a representative random sample:

| Artifact | Mean uncompressed bytes | Mean zlib bytes |
| --- | ---: | ---: |
| Final MSL | 117,013 | 19,179 |
| SPIR-V | 107,963 | 31,594 |
| Translator reflection | 3,012 | 327 |

The MSL sample came from `shader/cache/b-d1f10abd26a7`; SPIR-V and reflection came from `tmp/dmsh_92gnntz5`, both beneath the baseline build folder. No baseline files were written.

Planning estimate for 42,851 shaders: one translation object plus three to eight distinct compressed MSL states per shader is roughly 3.8 to 7.9 GB, before SQLite indexes, JSON/base64 overhead, metadata and geometry extras. This is a capacity estimate, not measured Ocarina cache size. No-op passes share the same object. About 15 stage entries per shader gives 642,765 index rows; budget a further 0.1 to 0.3 GB for indexes. More edits retain more objects. A synthetic warm-cache test proves output-object deduplication, but does not establish the production size.

## Rebuild estimates and limits

The read-only baseline log is `${OOT_READONLY_GAME_ROOT}/build-baseline.log`. Translation starts at 19:28:49 and compiling starts at 19:29:57, an observed 68 seconds for 42,851 shaders. The observed 20:10:07 progress row has 39,453 completed. That is 2,410 seconds after compiling starts and 41:32 of total shader-step elapsed time. At the observed average rate, the combined finishing phase projects to about 2,618 seconds, plus translation and setup, approximately 45 minutes. The log was incomplete when inspected. Competing machine work changes this rate.

The log's "compiling" phase combines SPIRV-Cross, Python passes, Metal and output publication. It does not isolate those costs. It reports complete-shader misses, not the number of actual Metal compiler invocations. A numeric 20x wall-clock result cannot be inferred from it.

For a #1405-like post-pass edit, translation tool work falls from 42,851 shaders to zero after warm-up. SPIRV-Cross also runs zero times if the SPIR-V and its flags are unchanged. The edited pass runs where applicable. Later passes run only for changed intermediate content. Metal runs only for changed final compile inputs. For a #1360-like translator edit, translation still costs approximately the observed 68 seconds; unchanged SPIR-V bypasses SPIRV-Cross, while reflection changes remain inputs to the passes that use them.

A conditional cost model is `postpass rebuild = R + P + f * D` and `translator rebuild = 68 seconds + R + f * D`. `R` is cache lookup, restore, analysis and publication effort, `P` is the edited pass's effort over applicable shaders, `D` is the downstream cold work and `f` is the fraction whose intermediate output actually changes. Exact stage boundaries make these upper-level formulas approximate.

Using the projected 2,618 seconds only as a conservative downstream-work proxy, with unmeasured `R + P = 30 to 60 seconds` and `f = 0 to 2%`, a post-pass rebuild projects to 30 to 112 seconds, approximately 24x to 90x relative to a 45-minute cold step. With unmeasured `R = 30 to 60 seconds` and the same changed-output fraction, a translator rebuild projects to 98 to 180 seconds, approximately 15x to 28x. These are scenarios, not measurements. A broad #1405 output change or a #1360 edit that changes most generated SPIR-V can be much slower. The existing Metal content cache already avoids unchanged compiles without this feature, so a warm-cache comparison will show a smaller multiplier than the cold-log comparison. Measure that denominator before claiming the target.

## Parent migration

Do this only after the running baseline finishes. Do not point `DMSH_CAS`, `WORK` or output paths at the protected baseline tree.

1. Apply this branch to the parent's integration checkout. Generate its final chain header after combining all chain edits. Keep the translator lock consistent with any translator build. Use no more than four workers.
2. Create a separate writable output root, for example `${OOT_SHARED_CONTEXT}/stagecache-eval`. Clone or copy the baseline's `shader/cache/cas/metallib` into its `cas/metallib`, preserving paths. If the baseline has archived `cas.tar`, copy and unpack that archive in the new destination. Never unpack in the baseline. The compile cache includes combined fragment/side-library units that a library-folder prefill alone cannot reconstruct.
3. Optionally set `DMSH_PREFILL` to the baseline's `shader/cache` root. It is a read source only; compatibility checks and sample compiles run in the new work directory. This imports compatible ordinary libraries, but skips combined side-library units. Copying `cas/metallib` is the more complete migration.
4. For one warm-up in the new destination, set `DM_GAME=0400486024DEC000`, `DM_GAMES_DIR` to the appropriate derived profile parent when using v131072, `DMSH_TARGETS=mac`, `DMSH_STAGECACHE=1`, `DMSH_STAGECACHE_WARM=1`, `J=4`, and a new `WORK` directory. Invoke `dmsh_build.py` with the baseline's `shader/pkg` as a read-only source and the new output root. Full builds write `c1_full.tsv` and `cb_extent.tsv` into the selected profile. Therefore copy the derived profile into the new destination first and point `DM_GAMES_DIR` there. Do not select the baseline's derived profile for a full build.
5. This first run must translate and run the passes once because final MSL cannot reconstruct raw SPIR-V or earlier MSL states. Compatible Metal cache entries avoid recompiles. Then unset `DMSH_STAGECACHE_WARM`. Keep `DMSH_STAGECACHE=1` and reuse this writable CAS across subsequent chain edits.
6. Compare enabled and disabled output trees, including MSL, libraries and normalized reflection, with identical tools and inputs. Only chain/compiler/profile stamps should differ when the source behavior did not change. Record stage and Metal cache counts, rebuild effort, cache bytes and actual Metal invocations. Perform cold review before integration.

## Validation log

- Read shared agent context first, Astra idea 9, cache-key bug history and the existing pipeline. Verified a clean worktree at `ee9b7765`; created `oot-stagecache`.
- Implemented intermediate caching without replacing complete-shader or Metal caches. Chose a database to avoid hundreds of thousands of small cache files. Kept geometry, pair dependencies and integer-input retries.
- Added synthetic pipeline tests with fake translation, SPIRV-Cross and Metal tools. Existing dependency coverage stays active. No packages installed.
- Final focused suite passed 112 tests, including 20 new synthetic stage-cache tests and the existing chain, cache-key, shader-rewrite, pool-array and documentation tests. New cache and test modules pass pyright with zero errors or warnings and ruff with zero findings. `git diff --check` passes. The repository lint ratchet reports three existing findings outside this diff: `test_nsp_mac.py:176` and `:177` assign `NSP_FOLDER` on a dynamically loaded module, and `test_tree_tar.py:107` passes a float to an integer-typed argument. The lint baseline shrank by one fixed `dmsh_build.py` finding via `lint_python.py --update`; no findings were added to it. The full lint gate remains failing on those three unrelated findings.
- No full Ocarina build, host/game run, GPU test, iOS build or regress.py check was run, as the task context forbids them. No baseline or main checkout writes. No push, PR or GitHub comment.
- Suggested later regression coverage is Ocarina and Mario Kart World for NVN2 mesh/task stages, Monster Hunter Rise for integer-input retries, Dragon Quest I & II for paired padding, and Animal Well for a small ordinary chain. These games remain untested here.
- Plan deviation: cache overhead and whole-build speedups are bounded estimates because the available log does not contain isolated stage timings. No claim of measured 20x improvement. ABI changes globally invalidate intermediate stages while identical final Metal inputs retain the existing safe content-cache reuse.

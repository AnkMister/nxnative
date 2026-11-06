# PR #1444 shader source port

Branch `p1444-xlate` starts at `oot-hyper-main` `64a163ba`. The lead will merge
this lane onto the requested final base, `oot-play`
`e8c3bc222b06413347d533fca7e060a69943c57a`.
Upstream source is PR #1444 at `e03bdc8f`, including `d3b79f38` and `37520e4b`.

## Gates and overlap decisions

- `DMSH_OOT_VISUAL=1` enables the new BarrierExits, threadgroup store fences,
  loop guard, point mesh topology/point size, mesh padding, mesh/pixel pair
  extraction, and the NDSR descriptor walk. The integrated stutter lane excludes mesh shaders from ordinary vertex descriptors unconditionally as a type-safety fix. The
  existing SULD, strict F2IP, task-payload readback, float CAS, and LDSM gates
  remain. VOTEU and guarded-handle tracing are on by default, explicitly
  requested exceptions to the shared context's default-off policy.
- AF2fp and AI2fp already match upstream; keep them unchanged. The strict
  register-only AF2ip from #1300 stays, with one registration and one method.
  PR wording calling opcode `0x243` I2FP describes the F2IP overlap; it does not
  justify replacing AI2fp or adding another AF2ip.
- #1343's existing gated `IsUnused` check already implements upstream's SULD
  fix. It retains every input when another destination remains live, while
  still respecting side effects. Existing liveness tests stay.
- Keep the strict foliage CAS address bit 72 and refusal of wide, uniform,
  and predicate-result modes. Add upstream's `0x9a9` opcode through that same
  handler. Do not adopt upstream's address bit 70. Keep the F32 FTZ CAS helper:
  both operands and result flush subnormals, and its initial observation is
  atomic; upstream's plain load and unflushed sum lose these properties.
- Preserve #1357 and #1376 tensor code unchanged. LDSM's subgroup execution
  barriers protect its collective reads; tg_fence is a memory-order fence
  after a shared store and can run in divergent code. They complement each
  other. Existing tg_spill also extends these fences to device memory.
- BarrierExits is upstream's pass, gated and restricted to Ampere compute
  entry points: it reserves Maxwell flag register 3, which Ampere leaves free.
  It skips functions with barriers inside backward branches. This lane adds
  the source to the chain's source list, without generating its header.
- Preserve #1405, #1360, DMSH_WIDE_GROUP, stage caches and the dynamic pool-map
  ABI. No bounded run-cache replacement. Keep dmsh_atomic.py unchanged: its
  raw-log OR helper already matches upstream.
- Replace the gated NDSR four-byte search with upstream's eight-byte
  descriptor walk and header selection at +0x10/+0x14. Keep bounded probing for
  short packs and existing control/type checks; upstream's fixed-length
  iter_unpack can reject a short non-aligned buffer. Synthetic tests exercise
  data descriptors between shaders and both starts.
- BNSH slots 7/8 were already present, unchanged. Add gated mesh/pixel variation
  pairs and mesh padding through the existing pad_locations/stage cache seam.
  Padding initializes both mesh depth entries with (0,0,0,1).
- Preserve pso_offline.py's romfs/shader_lib packed input support, AOT handling,
  bounded extraction, and refused-descriptor isolation. Only add upstream's
  mesh reflection exclusion; the integrated stutter lane applies it unconditionally. Do not take upstream's unrelated packed
  support removals or missing write_script calls.
- ixc.metal's dispatch/mesh clamps require host-side consumers and are left to
  the renderer lane. dmsh_abi.h's upstream diff is an obsolete fixed-table
  comment; retain the dynamic-map ABI and comment unchanged.

The loop guard is an explicit safety limit for an uninitialized or wrongly
translated bound, not a repair of that bound. One counter per function limits
nested loops together. It runs after mesh stage wrapping so the wrapper can
still recognize the kernel's initial shared-memory declaration. tg_fence runs
after border_emu and before stage wrapping/spill, preserving the wide-load
source-test extraction boundary. Both helpers return identical input bytes
when the visual gate is off. No chain override bypass or Homebrew runtime
fallback was imported.

## Tables

All six requested tables are byte-identical to `e03bdc8f`: shader_map,
shader_pairs, shader_facts, pso_pairs, pso_manifest, bf_want. The last three
already matched and produce no diff. The map's content-key set is unchanged:
42,854 rows, including 67 NDSR, 500 mesh and 20 task rows. The 1,284 added pair
rows cover 491 distinct mesh keys, per the lead's comparison-metrics.json.
The PR note's 21 describes shaders requiring padding, not all paired meshes.
The splitter was not rerun on game assets.

## Verification and remaining ownership

All test processes ran with `nice -n 19` using the existing Python environment.
No installs, translator execution, translator copying, shader build, game run,
native build, push or PR action occurred.

- Focused source helpers: 91 passed. Modules: test_bnsh_nvn2,
  test_split_ndsr_entries, test_split_ndsr_pairs, test_dmsh_meshstage,
  test_dmsh_tg_fence, test_dmsh_pairs, test_pso_offline. Native compiler tests
  were excluded. Exact mesh padding at locn4, locn10 and locn11 is checked in
  both depth entries, with idempotence and the off gate.
- Cache and wide-load helpers: 50 passed, one GPU equivalence test skipped.
  Modules: test_dmsh_wide, test_dmsh_tg_spill, test_dmsh_stagecache,
  test_dmsh_code_fp. Native compiler tests were excluded. The previously
  identified wide-load AST extraction test passes.
- All six tables compare byte-for-byte with upstream; git diff --check passes.
- Added translator tests are not run in this lane: gated early-exit barrier,
  strict alternate CAS opcode, and default-on VOTEU/guarded-handle cases.
  The lead owns the single cooled-NuGet source publish, lock/header generation,
  translator tests, full tool/gfx suites and independent review after merging.
  The inherited binary and lock/header are deliberately unchanged here.

No generated storage was deleted. No dependency or native output roots were
created in the checkout. Source-test temporary directories cleaned themselves;
logs and comparison evidence remain in the external p1444-xlate-evidence folder
for lead review. Existing shared caches and maintained checkouts were retained.

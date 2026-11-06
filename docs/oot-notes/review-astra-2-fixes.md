# Review Astra 2 fixes

Mr. Atreides, the three fixes are on `oot-visual-fix` and `oot-stable-fix`.
Use those branches in place of `oot-visual` and `oot-stable` when integrating.
All source changes are committed locally. No push or PR was made.

## Finding 1, mixed Float16 and integer outputs

`oot-visual-fix` starts at reviewed visual head `622f5191`. Commit
`d8de1f98` makes `lim_key` reject the limited library if any rewritten output
feeds a signed or unsigned integer attachment. It follows the physical to
logical output map for merged passes and preserves the Float32 exclusion.
An integer attachment on an output outside the limit mask does not block the
variant. The existing `DM_NVN_VISUAL` gate remains.

The fix uses the original shader for mixed limited targets. Generating another
family of per-format libraries would require more producer and loader changes.
No shader producer, translator, chain header or shader input changed here, so
this correction requires only a host rebuild with the existing visual inputs.

The regression retains the review's MSL and calls production `fs_uint`,
`int_outputs` and `in_word`. It generates integer mask 2 and limit mask 3,
then passes the production selector's choice to a Metal render fixture with
RGBA16Float plus RGBA32Uint attachments. The integer word is exactly
`0x47800000`, with channel 1 exactly 123. Forcing the limited library reproduces
`0x477fe000`, so the fixture detects the reviewed corruption.

- Four Python rewrite and Metal compilation tests pass, in `visual-python.log`.
- The host/Metal fixture passes 29 checks, in `visual-host-test.log`.
- The full tools suite passes 1,223 tests with 23 skips, in `visual-tools.log`.
- The Ocarina host build passes, in `visual-build.log`.

## Finding 2, watchdog snapshot

`oot-stable-fix` starts at reviewed stable head `5c534f38`. Commit
`7dec3972` protects pending work, progress updates and the watchdog predicate
with one short CPU mutex. Both start and feedback writers take it. No Metal
call or error handoff runs under that mutex. The timer skips a busy snapshot
and checks again on its next tick. The existing stall threshold is unchanged.

The regression extracts the production functions, as the review's probe did.
It injects a concurrent start immediately after the progress read. The old
source deterministically reports `stalled=1` even though progress is current;
the fixed source reports `stalled=0`. The tests also cover concurrent feedback,
concurrent start/feedback and watchdog reads, idle restart, the true-stall
boundary and a busy CPU mutex.

All three tests pass. The same three modes pass under ThreadSanitizer with no
reported race. See `watchdog-before.log`, `watchdog-probe.log` and
`watchdog-tsan.log`. The old-source failure is retained as expected evidence.

## Finding 3, auxiliary residency ownership and saves

Commit `78ccb75f` closes producer entry before emergency teardown attempts the
existing bounded residency lock. Present-layer attachment and snapshot set
creation, queue attachment, allocator/buffer creation, texture allocation,
allocation removal/addition and commits now share that lock with cleanup.
A producer waiting for ownership rechecks the sticky stop after acquiring it.
Serial publication stays outside the lock because it can release other resources.

Cleanup accounts for CPU setup already inside the boundary. If it cannot take
the lock, it leaves the live sets untouched and returns to the host exit path.
The independent exit fallback still covers a Metal call that blocks. No GPU
completion wait was added.

The controlled concurrent tests pause set creation, texture replacement and
layer attachment while cleanup and a later producer overlap. They verify that
cleanup follows the current CPU owner and that later setup is rejected. A
held-lock case verifies bounded return without touching the sets. These are
fake Metal objects; the tests submit no GPU work.

The original 159 safety checks and 38 new checks pass. The residency guard
passes another 23 checks. See `stable-host-tests-final.log`. All four new
ownership modes also pass under ThreadSanitizer with no reported race, in
`stable-tsan.log`. The host lifecycle child-process test passes cleanup order,
once-only handoff, no graphics drain and blocked-cleanup exit checks, in
`stable-stop-test.log`.

The emergency log, memory reference and game note now say exactly that the
last committed save is kept; an in-progress save can be lost. Emergency stop
does not flush saves or force a guest transaction to commit. No save commit
was added.

The initial full stable suite exposed an inherited architecture failure from
the hardcoded Ocarina title ID in the original safeguard. The default now comes
from the validated `safe_gpu` profile key and `DM_GAME_SAFE_GPU`. Ocarina sets
it on; other profiles default off. It remains Mac-only by default, and
`DM_SAFE_GPU` overrides it. A regression covers absence, on, off and invalid
values. The host-only key does not change shader inputs or the chain.

The final full stable tools suite passes 1,221 tests with 23 skips, in
`stable-tools-final.log`. The initial failure remains in `stable-tools.log`.
The final Ocarina host build passes, in `stable-build-final.log`. Compiler
warnings remain. Python lint reports no findings in changed files, but the
repository check still fails on three inherited findings in unchanged
`test_nsp_mac.py` and `test_tree_tar.py`, in `stable-python-lint-final.log`.
No lint baseline was changed. `clang-tidy` is not installed.

## Integrator notes

Use `oot-visual-fix` and `oot-stable-fix` instead of the reviewed branches.
The visual branch contains one fix commit. The stable branch contains two,
in watchdog then residency order. Each commit includes its regression test
and an update to `implementation-notes.md`.

Keep the integer rejection and Float32 exclusion when merging the pipeline
selector. Keep all auxiliary residency producers on the same `g_res_mu`
boundary as `mtl_safe_gpu_release`, and retain the stop check after acquisition.
Carry the new profile key, header generation and Ocarina row together.

A read-only merge-tree check reports the same eight conflict paths for the
original pair and the replacement pair. They are `dm/gfx/nvn/nvn_mtl.m`,
`dm/gfx/tests/Makefile`, `dm/gfx/tests/t_cpu_tex.m`,
`dm/gfx/tests/t_deferred_release.m`, `docs/agents/symptoms.md`,
`docs/env_switches.tsv`, `docs/reference/shaders.md` and
`implementation-notes.md`. Preserve both branches' production and test changes,
combine the notes, and regenerate the symptom index after resolving the
reference pages. See `merge-tree.txt` and `merge-tree-original.txt`. No merge
was applied to either branch or the working tree.

These corrections require no new game shader build. The visual branch's
previously planned matching translator, shader libraries, chain/header and
host rebuild remain integrator work. Keep provisional mesh-indirect execution
separately gated until its record layout is verified.

No game, full shader build, regress.py run, genuine GPU fault, device operation
or independent review was performed in this implementation task. Synthetic
Metal output and CPU race tests do not establish gameplay image quality,
driver safety for outstanding GPU work or WindowServer recovery. The final
combined stack still needs the integrator's review and acceptance.

## Evidence and generated storage

Evidence is in `review-astra-2-fixes-evidence/` in the external task workspace.
The original review evidence was read and preserved. Work stayed in the
assigned checkout; the protected running baseline and game work folder were
not written. Existing Python and Apple tools were used. Nothing was installed.

Both standalone ThreadSanitizer executables and the generated
`stable-safe-tsan.dSYM` were removed after confirming they were no longer open.
Temporary Python and Metal fixture directories cleaned themselves up under the
required scratch root. Source probes and logs remain as acceptance evidence.

The checkout still has persistent `node` and `node_repl` processes with working
directories inside it, recorded in `open-files-final.txt`. The storage policy
therefore prevents deleting its generated roots during this handoff. Retained
roots are `dm/host/gen`, `dm/host/dmhost` and its dSYM, `dm/host/tests/build`,
and `dm/gfx/tests/t_limit16`, `t_safe_gpu`, `t_res_guard` and their dSYMs.
Python caches and the observed `dm/tools/nx_extract/obj` were also preserved.
The exact inventory is in `retained-generated-roots.txt`. Unknown artifacts,
other processes, credentials, settings, source and existing evidence were not
removed. All verification subprocesses have finished. Git has no uncommitted
source changes.

The later commit-identity instruction is acknowledged. Existing commits were
left unchanged as requested. Future commits must use AnkMister. Both fix ranges
were checked and contain no absolute `/Users/` paths in their additions.

# Ocarina independent review fixes

All five findings are addressed on the four requested local fix branches. The
original branches are unchanged. No push, PR, game run, regress.py run, or full
shader build was performed. All host builds used
`make -C dm/host -j4 GAME=0400486024DEC000 dmhost` in the task checkout.

| Finding | Branch | Fix commits | Regression and result | Residual risk |
| --- | --- | --- | --- | --- |
| 1. Split border handles | `oot-1203-fix` | `707c75cb`, `bcfa83b2` | `t_border`: both word orders, sampler changes across draws, GPU border samples driven by the split-handle key. Old single-word read fails; fixed native checks pass 55/55 in each mode. | Synthetic samples pass; full Ocarina images remain untested. |
| 2. Incomplete restoration exposed to GPU residency | `oot-mem-fix` | `3cedba6f`, `aeaa9dcc` | `t_dirty_dedupe`: holds an actual backup `pread` beyond BUSY_WAIT_MS; restore returns failure and a concurrent residency consumer remains blocked until the bytes are restored. Old implementation authorizes the consumer prematurely; fixed test passes. | Persistent restore failure stops the host before GPU access. This is intentionally fail-closed, not recovery from permanent disk failure. |
| 3. Kernel copy-in EFAULT | `oot-mem-fix` | `3cedba6f`, `aeaa9dcc`, `a6ac14c5`, `13d03613` | `t_dirty_dedupe`: reproduces real EFAULT, writes and verifies a file from a released texture page, races 64 writes against release attempts. `t_fs` requires the exact syscall source span to have been prepared; file read destinations are excluded before copy-out too. Old implementation fails file and exclusion assertions; fixed tests pass. | Kernel-visible tracked ranges retain their guest copies until retirement, reducing dedupe savings. New kernel consumers must use the hook or a bounce copy. |
| 4. Audio advances during clock pause | `oot-idle-fix` | `a9f24c03` | `t_audio`: queued partial dialogue, start while paused, late device callback, mute transitions, unchanged queue/position/release state, release on resume. Mapping pause to the old suspend policy fails; the distinct pause policy passes. | Real AppKit hide/resume, physical audio latency and game dialogue acceptance remain untested. |
| 5. Default baseline | `oot-stack-fix`, `oot-1203-fix` | stack `79c63c23`, `42546c9d`; border `707c75cb`, `bcfa83b2`, `2ec3d25d` | Stack: a seeded numeric memo must be bypassed when off; default build must not read quad-only reflection. Both fail before and pass after. Border: freshly compiled default `_b` and `_bx` bytes match the original compile-unit path; the pre-fix builder fails the comparison. Missing optional assets retain the correcting function through `pso_desc`, including cached failure. | #1360 deliberately changes defaults, as detailed below. Border byte comparison covers a correcting fixture, not every game shader. Chain/profile metadata differs; matching asset rebuilds remain required. |

The memory pre-fix probe uses production `oot-mem` dirty code with only a
success-return signature adapter and a wrapper for the new test API. The original
unchecked `dd_take` behavior is preserved. No GPU work is submitted against
incomplete pages. The border split-handle repro restores the original one-word
read in the otherwise corrected host, then reruns the native regression.

**Upload trim can ship independently.** The original `8830915b` was already a
separate commit, but its patch required dedupe context. The durable local tag
`oot-upload-trim-only` names `e0be0eef2bbaa6d92e75a589edd59fb2d48f8c08`, directly
parented by `oot-base`. It contains only trim, its test and documentation, with
no dedupe dependency. Its production source compiles independently and passes
11 checks with trim off and 13 with trim on under Metal validation. Cherry-pick
that commit for trim alone; the requested four fix branches remain separate.

**The honest stack baseline.** With every experiment flag off, #1360 still:

- Grows the host raw pool table from a 4,096-entry minimum to the next power of
  two needed, up to 1,048,576 entries; records capacity in entry 0; uses a
  temporary CPU range array on rebuild and can allocate a larger GPU table.
- Uses the source-built translator's count-driven raw lookup instead of its old
  fixed-capacity loop. Tagged hints keep their representable index limit.
- Sizes and reads bitmap write logs against the actual table capacity.
- Requires the changed translator/ABI/lock and matching host/shader chain.

These are accepted correctness changes, not an unchanged `ee9b7765` control.
#1405 requires build flag `DMSH_RAW_LOAD_QUADS=1`; its extra reflection read is
also gated. #1161's numeric memo requires runtime `DM_NVN_FEEDBACK_MEMO=1`.
`DM_PRESENT_ABSOLUTE=1` remains opt-in. The original string-key feedback lookup
and original present path run with those flags off. No translator source changed
for these fixes, so no translator rebuild or NuGet restore was needed. Existing
locally source-built assemblies and their audited lock were retained.

Border builds keep the original correcting `_b` and `_bx` compile path. Only
builds with `DM_NVN_BORDER_SPLIT=1` add disposable plain `_bn` assets. Runtime
opt-in selects `_bn` only when no bound sampler needs correction. Build or load
failure keeps `_b`. Default builds are safe even if runtime opt-in is enabled.
The border chain is `ade320c6c955`; the stack chain is `79c6653b35b9`. These are
independent branch experiments and must not share mismatched assets.

**Validation completed.**

| Branch | Existing and added checks run | Host build |
| --- | --- | --- |
| Border | Border native 55 checks off/on; final Python border 18 tests, all pass with GPU enabled; earlier border/side/alpha/logic/chain suite 57 tests, one GPU skip covered by the enabled run; alpha 788 checks; logic 929; PSO key 3 cases; docs 11 tests. | Passed |
| Memory | Dirty dedupe, concurrent restore/kernel tests, dirty race, retirement race and slots; Metal dedupe 7; trim 11 off / 13 on; upload slots 305 per mode; NVN 234 per mode; fs 138 plus case/commit/directory executables; tools discovery 1,217 tests (23 skipped), graphics discovery 348 (86 skipped), iOS tools 43; docs 11. | Passed |
| Idle | New audio pause plus existing lifecycle, silent/real output, release order and stall recovery; SPSC 100,000 buffers; OutputStream, audio stats/device, eco clock; eco detector and wait off/pause/slow; offscreen eco present 23; graphics suspend 15; present allocators 13; rescue 80; docs 11. | Passed |
| Stack | Wide/chain 29 tests; source-built translator suite 61; pool/bitmap 95 checks; raw GPU loads 61 checks with 8,192 entries; feedback 168 checks in each mode; pacer 250; present allocators 19 in each invocation, including off/on paths; docs 11. | Passed |

Tests include expected diagnostics for missing assets, injected I/O errors and
BUSY timeouts. Host builds retain existing compiler warnings, including Metal
encoder protocol warnings. Passing these checks does not establish gameplay,
energy savings, full-map shader compatibility or a fresh independent review.
No new review delegate was started because this task was explicitly assigned
as implementation sub-agent work.

**Evidence.** Logs, pre-fix probes and storage inventory are retained at:
`/Users/ankur/Documents/Crypt/Gaming-rea/_work/nxnative/setup/scratch/review-fixes/`.
Key files are `border-repro.log`, `border-before-bytes.log`,
`border-final-python.log`, `border-extra.log`, `mem-before.log`,
`mem-concurrent.log`, `mem-native.log`, `mem-fs-scope.log`, `mem-python-*.log`, `idle-before.log`,
`idle-audio.log`, `idle-more.log`, `stack-before-python.log`,
`stack-before-memo.log`, `stack-native.log`, `stack-translator.log`,
`trim-only-0.log`, `trim-only-1.log` and each branch's `*-host*.log`.
Regressions and validation commands are committed with the branch source.

**Storage handoff.** No generated storage was removed. The required open-file
check found runtime processes with their cwd in this checkout (see
`open-files.log`), so the cleanup precondition was not satisfied. Generated
roots retained include `dm/host/gen/`, `dm/host/tests/build/`, `dm/host/dmhost`
and its dSYM, the named graphics test executables/dSYMs, Python bytecode caches
and the extraction tool's `obj/`. Exact detected paths are in
`review-fixes-storage.txt` and the external `generated-storage.txt`. Unknown
paths were preserved. Reports, acceptance evidence, sources, `.git`, shared
caches and the checkout remain intact. No baseline checkout or game work folder
was modified. Nothing was written under `/tmp` or `/private/tmp`.

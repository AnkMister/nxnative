# Border review fixes

Branch: `oot-1203-fix`, based on `oot-1203`.

## Findings 1 and 5

Scalar SAMPU selection now uses `ubo_bind_handle(1, b)`, as encoding does.
Both split-word orders and sampler changes between draws are covered by the
native border test. Restoring the old single-word read fails the texture-first
case (53 checks, 1 failed); the fixed implementation passes all 53.

The baseline _b and _bx libraries now use the original oot-base compile path,
source and output names. DM_NVN_BORDER_SPLIT unset/0 at build time emits no
plain variant or border metadata. The flag at runtime leaves the original
function and key unchanged. Shader payloads retain the original compilation
inputs; chain stamps necessarily change because the tool changed.

Build with DM_NVN_BORDER_SPLIT=1 to add optional _bn plain libraries. Runtime
DM_NVN_BORDER_SPLIT=1 selects them only when no sampler needs correction.
_b always corrects. Missing, incompatible or failed optional assets keep _b.
Alpha/logic and readable-tile variants retain correction. A default build is
safe with the runtime flag enabled too. No translator rebuild was required.

Validation logs: setup/scratch/review-fixes under the shared nxnative work root.
- Native border: 53 checks off and on; GPU border suite 17 tests passed.
- Native alpha 788 checks; logic 929; pipeline serialization 3 cases passed.
- Python border/side/alpha/logic/chain: 57 tests, one GPU test skipped in this
  invocation (covered by the native-enabled invocation).
- Host-only build passed, at most four jobs.
- No game, regress.py or full shader build. Actual Ocarina border pixels and
  cross-game acceptance remain unverified. Synthetic GPU border samples pass.

Front-ends: build and runtime DM_NVN_BORDER_SPLIT=1 are opt-in; _b now always
contains correction, _bn is optional plain. Rebuild matching chain assets before
running; do not mix old split _b assets with this host.

Final border regression extension: native checks are now 55 off and on. A
missing optional library is exercised through pso_desc twice, including the
cached failure, and retains the correcting base. Synthetic GPU border samples
now derive correction from border_key's real split-handle decision; a wrong key
therefore changes sampled pixels and fails the test. The native-enabled Python
border suite still passes all 17 tests. The unchanged-default library tests run
against the pre-fix builder fail; retained log border-before-libraries.log.

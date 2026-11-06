# PR #1456 shader port

Started p1456 from origin/main 75c1a8cf, including official Ocarina support.
Ported 48ec785d's HMMA chain/A reuse source and tests. Added an independent
DMSH_HMMA_CHAIN=1 gate, preserving the default ordinary helper ABI/body and
main's gather-offset fix. The user chose documentation of the #1334 tensor
merge contract instead of importing that fork feature. The _bf regression
covers both HMMA option names without restricting ordinary Mac compilation.

A GPU probe exposed upstream slot-zero corruption when a standalone HMMA
interrupts a live chain (8,089 outputs beyond tolerance). Reserved slot 7 for
temporaries, leaving seven chain slots and register fallback on exhaustion.
Both translator and GPU regressions now pass. The slot-capacity test also passes.
Numerical errors stay within upstream's f16 thresholds.

Built a private test translator from source using a live age audit of all 57
exact NuGet versions and an existing-only local feed. Nothing was published or
copied into the shipped bundle. Two translator suite runs each passed 149 tests
with one unrelated native geometry harness skip; the added capacity test passed
separately. Mac-only loop selectors avoid iOS work. No game/full shader/host
build ran. Evidence, scope limits and retained generated roots are documented
in docs/oot-notes/p1456.md. Final lock/header and translator publication belong
to the lead's integrated rebuild.

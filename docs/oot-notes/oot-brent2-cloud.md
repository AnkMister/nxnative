# Ocarina round two: four host ports

This report follows `glass-oot-brent2-cloud.md`. This branch owns only #1434,
#1332, #1417 and #1428. Other glass and Mac agents own all other items. The
previous broad harvest is superseded. Its out-of-scope ports, follow-up fixes,
tests and documentation were removed with a cleanup commit, preserving published
history on `oot-brent2-cloud`.

## Audit and verdicts

The integrated starting revision `oot-hyper-main` is `a14fb78c`. A fresh fetch of
origin/main resolves to `c83c48f2`. Brent's source is `brent-oot-combined-new`
`89a0ff52`, surveyed after `a54b2092`. All four source items are missing from both
the starting integrated branch and upstream by ancestry and source comparison.
The ranking below is inferred value for Mac Ocarina, not a measured improvement.

| Priority | Item | Source SHA | Verdict and reason |
|---|---|---|---|
| Highest correctness value | #1434 | `9eeacbbf104f2551d7870afa87d6068e64313642` | Port. Five SDK 22 calls prevent unserved service paths, including the Ocarina note abort #1433. |
| High stability value | #1332 | `7f5f2fcf967532d0bf6fbd824371277a032965b0` | Port. Detect permanently revoked GPU access, stop presents, release completed-fence waits and use the existing Mac alert path. |
| High memory value | #1417 | `1c1d4533d36e972b424c64bd576a03b605666198` | Port. Retire obsolete chunks after whole-pool mapping, behind completion fences. |
| High efficiency value | #1428 | `f53714789f95b2918f4d6d70c003d5872d192d5c` | Port. Reuse completed pool table buffers in both full rebuilds and incremental patches. |

None of these four lowers image quality. No image-quality tradeoff was enabled.
No shader inputs, translator files, chain header or third-party sources changed.
Nothing was installed and no third-party binary was copied or executed.

## Retained commits and activation

| Commit | PR | Default-off flag |
|---|---|---|
| `a4af36a5` | #1434 | `DM_SDK22_SERVICES=1` |
| `6e9b99c4` | #1332 | `DM_GPU_LOST_STOP=1` |
| `21a4ece1` | #1417 | `DM_NVN_RETIRE_CHUNKS=1` |
| `865029be` | #1428 | `DM_NVN_POOL_TABLE_REUSE=1` |

Each source port has its own commit with the source SHA and PR. The cleanup
commit removes all other ports and corrects SDK diagnostic hit counts so disabled
hooks are not reported as hits. The SDK gate affects forced-hook registration;
when off, relocation keeps the SDK definitions. `DM_TEST_GPU_LOST=<n>` injects
revoked access for native testing and requires the stop flag to be enabled.

The branch retains its own #1390 storage ranges, #1391 memory guard, #1382
failed-work names, #1409 fence feedback, #1408 linear deferred cleanup, #1420
packaged-texture fix and DM_SAFE_GPU policy. Revoked-access handling reuses the
existing Mac stop-alert helper. Chunk retirement preserves address-marked raw
pool selection and excludes unrelated MetalFX SDK declarations from its source
commit. Table reuse covers our existing incremental path as well as full
rebuilds, preserving descriptor-class and storage checks.

Mechanism details are in the [game note](../../dm/games/0400486024DEC000/README.md#second-host-harvest-scope-four-items-open)
and its linked reference entries.

## Verification

The scoped Linux checks are recorded below. Native Metal execution and Mac
builds remain open for every retained source commit.

- Source review found no remaining dependency on the removed AV1, crop,
  wide-write, idle-retirement, focus-control or noindex ports.
- Scripts, Python tools, AV1 sources, the present interface and DM_SAFE_GPU
  implementation match the integrated starting revision byte for byte.
- GCC syntax checks cover the changed portable C files using a generated Ocarina
  profile header. Loader and SDK font code require missing Apple headers.
- Portable SDK registration checks exercise all five symbols with the gate off,
  zero and one, and verify disabled entries do not inflate hit diagnostics.
- Full Python 3.14.2 tools suite: 1,132 tests, 10 failures, 150 errors,
  61 skipped. The baseline at a14fb78c has identical counts and identical failure
  names. No new failures or errors were introduced. Missing capstone/lz4,
  Mac-only libproc/cp options, Clang, .NET and platform fixtures remain blockers.
  No dependencies were installed. An earlier run during documentation replacement
  had two transient docs failures; the completed-source rerun above supersedes it.
- Documentation and environment table: 12 tests pass. The symptom index was
  regenerated and git diff --check passes.
- Production SDK gate and force_check functions compiled with GCC,
  -Wall -Wextra -Werror, ASan and UBSan and passed all five disabled/enabled
  symbols plus hit-accounting assertions.
- GCC syntax checks passed for hle_hid.c, hle_misc.c, hle_offline.c and
  t_gpu_lost_front.c. Existing BSD mergesort/attribute platform warnings remain.
  loader.c and hle_sdk16.c stop at missing TargetConditionals.h and pthread/qos.h.
- Native Mac tests have not run for any retained port. No game, shader build,
  device install or regression-harness run was attempted.

Receipts are under
`~/Documents/Crypt/Projects/_work/nxnative/brent2-cloud/`: scoped-tools-314.log,
scoped-docs.log, scoped-*.log and scoped-checks/sdk_gate.c. The comparison baseline
is baseline-tools-314.log from the original integrated source. These portable
checks do not establish Metal behavior or visual acceptance.

## Required Mac verification

| Commits | Required proof |
|---|---|
| #1434 | Build the Ocarina host; run t_symbols, t_hid and t_pctl; open and close the note without #1433's abort. |
| #1332 | Run t_gpu_lost with the gate off/on; inject DM_TEST_GPU_LOST; verify completed-fence wakeups, fullscreen exit and alert. Recheck DM_SAFE_GPU independently. |
| #1417 | Run t_pool_retire; verify chunk/full-pool raw access, completion fences and memory. |
| #1428 | Run t_pool_table; exercise incremental/full rebuild paths and in-flight buffers; measure allocations and residency commits. |

After native fixtures pass, compare Ocarina gameplay with one flag enabled at a
time. No flag should become a normal play setting before its comparison passes.
For the repository's five-game regression check, proposed games are Ocarina of
Time and Fire Emblem Fortune's Weave for texture pools, Breath of the Wild for
raw pool memory and fence behavior, Super Mario Bros. Wonder for baseline NVN
pool/present behavior, and Splatoon Raiders for storage-backed pool usage. Refine
this selection with available game files and usage manifests. No games or
regress checks were run on Linux.

## Delivery

The target remains `ankmister`, branch `oot-brent2-cloud`. The requested report
is `~/code/nxnative-research/reports/oot-brent2-cloud.md`. The earlier report
`brent2-cloud.md` is superseded. No PR is opened and no other branch is updated.

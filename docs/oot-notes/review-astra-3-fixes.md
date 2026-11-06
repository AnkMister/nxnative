# Astra review 3 fixes

Branch: `oot-review3`, created from `oot-hyper-main` at
`64a163ba22ed0b37bcee0ab138d0e1014a05cae1`. Local commit only. The running
play build and every protected game folder were read-only throughout.

## Result

Finding 3 is fixed. Upstream VOTEU and guarded-handle corrections are always
active. Finding 1 remains an explicitly unverified layout, with stronger
validation and the flag off in the play recipe. Finding 2 remains report-only,
as requested. A future reject policy is documented without runtime changes.

No game, regress.py, full shader build, device operation, push or PR ran.
No third-party dmsh translator binary was executed.

## Indirect mesh records

[Static evidence and remaining gaps](mesh-indirect-layout.md) give the module
build IDs, guest call, SDK resolver, function table and command writer offsets.
The driver inserts exactly two words from the supplied GPU address. The direct
method writes count then first, but uses a different macro. The indirect macro's
value flow and the game's record producer were not proven. EXT's XYZ structure
is therefore excluded for this call; the NV count/first interpretation is still
a hypothesis.

The compute-package census records 33,305 STG instructions in 3,871 programs,
including 12,090 two-word stores. Raw instruction evidence is retained, but a
store cannot establish field meanings until its destination is tied to this
buffer. No runtime records or game pictures were collected.

`DM_NVN_MESH_INDIRECT=0` is now explicit in PLAY-BUILD. The opt-in converter
uses the existing cap of 49,152. Count above cap and unsigned first-plus-count
overflow produce zero groups, followed by a host refusal and `[RED]`. The host
waits for producer/converter completion and independently checks the snapshot
before submitting its mesh draw. Unavailable snapshots are refused. The first
eight records are logged as raw hex words and provisional count/first values.
These checks cost performance only on the experimental path. They do not make
the layout proven, and disabling the path still omits its geometry.

The native fixture covers GPU copies, deferred writes, zero count, exact cap,
cap+1 and unsigned overflow. Synthetic records establish conversion and refusal,
not the game ABI. Reference-image acceptance remains open.

## Upstream fixes and shader output

AVote now always passes `toUniform` to ASetPred. BindlessElimination.cs and
Utils.cs are byte-identical to upstream `eab0aaac`. Local F2IP and other
experimental additions retain their existing gates. Vote and guarded-handle
fixtures now run without the visual flag.

An isolated reference was compiled from upstream `eab0aaac` source. The prior
64a163ba translator was used only after every distribution file matched its
committed source-build provenance hashes. No upstream-shipped translator was
executed.

- Eight targeted fixtures pass in all four configurations. Fixed default MSL
  exactly matches source-built upstream default. Fixed play MSL exactly matches
  64a163ba with `DMSH_OOT_VISUAL=1`.
- Thirty-eight sampled Ocarina compute shaders across shader, lib and effect
  packages all translate under the play flag. Every SPIR-V and reflection file
  is byte-identical before and after this patch, 76 matching files.
- The broader default comparison is deliberately bounded. Both upstream and
  this branch translate 37 of those 38 shaders and reject the same remaining
  shader's gated float-reduction opcode. All 37 reflection files match; 26
  SPIR-V files match and 11 differ. The branch already contains raw-memory
  translation changes beyond upstream. Blanket default equivalence is not
  claimed. The eight fixtures establish parity for the fixes in Finding 3.

No sampled game shader output changes under the play flags. The gate removal
also selects the same implementations that the old play flag selected.
However, the host `ixc` helper shader changes, and rebuilding the translator
changes the chain stamp. Default chain is `a5bce6f0626c`; play chain is
`881576f93033`. The currently running old build can remain untouched. Adopting
this branch requires a matched host and rebuilt library package because the
host rejects the old chain stamp, even where translated game bytes are equal.
No rebuild of the running play package was performed here.

## Strict AOT

No strict-mode implementation changed. `DM_AOT_STRICT=1` reports compiler entries
and preserves visible fallback. The [AOT notes](oot-aot.md#follow-up-design-for-dm_aot_strictreject)
describe a future `DM_AOT_STRICT=reject` policy covering render, compute, mesh,
constants, source helpers and every device fallback before compiler entry.
Rejection would stop visibly rather than silently omit geometry. The setting
is not implemented, and no complete gameplay coverage is claimed.

## Source build and checks

The final translator was restored and published once after all C# edits. A
separate source-built upstream reference was produced only for comparison.
Both used the same cleared-source, private local NuGet feed and at most four
jobs. All 57 exact package versions were rechecked against official NuGet
publication dates before restore. Every package exceeded seven days of age;
every downloaded SHA256 matches the prior audit. The four asset manifests for
each source tree have exactly the audited package union. No runtime pack or
other package was admitted. Publish used --no-restore and --self-contained false.

PathMap is `/_/nxnative`. PDBs are omitted. The original launcher is unchanged.
Source/distribution fingerprints, tool lock and default chain header are updated.
The rebuilt distribution contains no absolute user paths.

| Check | Result |
| --- | --- |
| Tools Python suite | 1,368 tests, 10 skips, pass |
| Graphics Python suite, translator enabled | 417 tests, 10 skips, pass |
| Translator suite, Metal and GPU enabled | 295 tests, 2 skips, pass; 40 PrimitiveID GPU cases |
| Targeted output comparisons | 8 fixtures in 4 configurations, pass |
| Sampled game play translation | 38 shaders, 76 identical output files |
| Native graphics make run | Pass; 128 native targets, plus 4 pull and 5 budget checks |
| Final mesh fixture and host build | Pass |
| Documentation and chain checks | 28 tests, pass |
| C compilation database | Generated for 266 sources |
| clang-tidy | Unavailable; no installation performed |

The first GPU translator invocation lacked DM_TEST_GEOMETRY_PRIMITIVE_ID and
failed its fixture-presence assertion. The native fixture was built and the
complete corrected run passed. Failed-attempt logs are retained.

## Evidence and storage

External evidence is under `${OOT_SHARED_CONTEXT}/review-astra-3-fixes-evidence/`.
It includes the module/table probes, raw SASS store census, shader jobs and
hash comparisons, NuGet date/hash audit, asset checks, source-build logs and
verification logs. The requested external report is review-astra-3-fixes.md
beside that evidence folder. Game-derived bytes remain outside Git.

The candidate and upstream translator source archives, private feed/package cache,
publish folders and shader samples are retained in the evidence directory for
independent review and reproduction. All eight worktree .NET bin/obj roots are recorded separately. No generated
storage was removed: lsof still shows T3 processes with working directories in
this checkout, so the required zero-open-process cleanup gate did not pass.
The host binary, generated host roots, native fixtures and dSYM outputs also
remain for parent review and replay. No other agent's storage is modified.

The CPU-priority instruction arrived after translator publication, Python suites
and host builds. The remaining native make and its children were verified at
nice 19. Subsequent heavy commands also use nice 19. The play build log showed
no EXIT at that check.
Independent review, complete-map rebuilding, game records, image comparison and
zero-gameplay-compile acceptance remain separate gates for the parent task.

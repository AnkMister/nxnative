# Next Ocarina merges

All finished requested branches are integrated, including their review-1 and
review-2 replacements, oot-res, and the Brent harvest. Each *-fix replaces its
parent implementation; the original branches remain historical evidence.
The [review-1 report](review-fixes.md) and [review-2 report](review-astra-2-fixes.md)
are archived. Their confirmed defects are repaired in the integrated source.

The requested 18 PR file lists are preserved in [PR-FILES.md](PR-FILES.md).
Brent's [Integrator merge notes](brent-compare.md#integrator-merge-notes) remain
relevant when moving the combined source onto upstream main. The second variant
will use origin/main resolved at creation, including upstream alias layout and
renderer PCM blocks. Keep its packed library loader and repaired source gates.

| Pending branch | Predicted conflicts and required checks |
| --- | --- |
| `oot-aot` (from oot-stable-fix) | Full offline pipeline coverage, compile counters and pso_seen learning overlap native mesh prewarm, packed library loading, stage-cache/side-library outputs, quality presentation and safety commit gates. Preserve no runtime shader compilation. Confirm all compute/native mesh/specialized pipeline classes and fail visibly on misses. |
| `oot-foliage` (from oot-brent) | Opcode 0x3a9 overlaps the existing global CAS port and translator refusal checks; wide-load grouping overlaps raw_load_quads, storage_runs, constant reuse and actual marked-pool table semantics. Merge source, retain exact numeric/bit tests, update FILES/stage fingerprints, rebuild translator and regenerate artifacts. |

The scanner is bench tooling, not a shader optimization. Its static scores do not
prove executed cost or permit skipping effects. Keep performance experiments off
for the initial correctness play build.

Archive incoming notes before merging. Resolve source and preserve all safety
and audio repairs; regenerate indexes, registry, lock and header. Repeat tools,
graphics and host checks. Full shader rebuilding and gameplay remain separate
parent acceptance, including the hard AOT rule. **Lazy shaders stay off.**

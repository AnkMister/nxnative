# Next Ocarina merges

All finished requested branches are integrated, including their review-1 and
review-2 replacements, oot-res, and the Brent harvest. Each *-fix replaces its
parent implementation; the original branches remain historical evidence.
The [review-1 report](review-fixes.md) and [review-2 report](review-astra-2-fixes.md)
are archived. Their confirmed defects are repaired in the integrated source.

The requested 18 PR file lists are preserved in [PR-FILES.md](PR-FILES.md).
Brent's [Integrator merge notes](brent-compare.md#integrator-merge-notes) remain
relevant to future rebases. oot-hyper-main uses origin/main eab0aaac resolved
at creation, including upstream alias layout and renderer PCM blocks. Its
packed library loader and repaired source gates are retained.

No requested finished branch is pending. oot-aot and oot-foliage are integrated
after their reviewed stable/Brent ancestors. Existing committed history is kept.
Future changes to AOT must preserve packed-library loading, all final render
state (including depth/stencil), colorspace, quality helpers and mesh safety.
Future grouping changes must preserve marked pool bounds and stage fingerprints.

The scanner is bench tooling, not a shader optimization. Its static scores do not
prove executed cost or permit skipping effects. Keep performance experiments off
for the initial correctness play build.

Archive incoming notes before merging. Resolve source and preserve all safety
and audio repairs; regenerate indexes, registry, lock and header. Repeat tools,
graphics and host checks. Full shader rebuilding and gameplay remain separate
parent acceptance, including the hard AOT rule. **Lazy shaders stay off.**

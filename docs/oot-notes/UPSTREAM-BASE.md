# Ports replaced by the upstream Ocarina base

The community fork starts from the maintainer's tested Ocarina implementation.
`b1d7c707` and `6121fd75` replace the earlier PR1444-only comparison baseline;
`75c1a8cf` also moves movie decoding onto its own worker. Their gameplay results
remain upstream evidence, not acceptance of this combined fork.

| Earlier fork or PR work | Selected implementation |
| --- | --- |
| #1300 F2IP and PR1444 I2FP/F2FP overlap | Upstream opcode handlers and tests. |
| #1343 SULD/multi-output liveness and RemoveNode | Upstream optimizer and wind fix. |
| #1359 exposure float atomics | Upstream RED.F32.FTZ.RN CAS lowering and tests. |
| #1312 gather offsets / dotted NDSR rows | Upstream constant-offset lowering. |
| #1360 raw-table growth and commit experiments | Upstream 8,191-entry pool table and ownership. |
| #1390/#1394 ranges and residency overlap | Upstream range/exposure/residency implementation. |
| #1345 audio, #1434/Ounce and SDK22 services | Upstream service implementations; old takeover gates dropped. |
| Old 16-GiB alias/profile values and PR1444 tables | Upstream game.tsv, shader facts/map/pairs, prewarm inputs and map limit. |
| Earlier depth-reader and segment-submission experiments | Upstream pool_ds_read and sub_cut. |
| Reading pipeline archives into RAM | Upstream mapped archive loader. |
| Round 3 handle tables, compact geometry, event queries, package/audio/identity fixes | Already in the new upstream ancestry; no duplicate port. |

Retained additions are limited to missing serial-held ownership, texture/view
repairs, guarded upload caches, optional BC targets, pool heaps/release/retirement,
copy-state snapshots, GPU safety/watchdogs, learning/counters and optional
HDR/colorspace. The texture integration must preserve upstream's weak packaged
sharing, NvAtomicRaw storage and compact geometry; older files are not copied
wholesale.

The two Astra review-5 P1 cases require GPU regression evidence: shared sRGB
serials preserve their view semantics after upgrade, and both registered alias
families observe a shared package's replacement without a CPU dirty event.
The cached pool-table retirement regression keeps its original failing assertion
and adds new-table dummy / old-table immutability checks.

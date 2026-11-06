# Indirect mesh record evidence

Status: field order remains open. The user selected `DM_NVN_MESH_INDIRECT=1`
for play after considering PR #1444's gameplay report. The source default stays
off. The two-word interpretation remains a diagnostic hypothesis, with the
existing cap, overflow refusal and host snapshot checks retained.

## Static guest evidence

The extracted v131072 modules match the profile's build IDs. Main is
`e0f3ccfaf50065ae4ea01eb5aeb13b1a`, SDK is
`1643a838814f9c10c696f930ed681e7f`, and subsdk0 is
`b0110087a7b339ef74588d3bd0b4dd5d`.

Main's loader at `0x12a15cc` requests
`nvnCommandBufferDrawMeshTasksIndirect` and stores the result through GOT
`0x4c8e7a8` into `0x4d47da0`. The opening-scene call at `0x2be2dbc`
loads that pointer. It passes the command buffer in x0 and a calculated GPU
address in x1. The address combines the object's buffer at +0x80, its stride
at +0x48 and an aligned allocation index at +0x88. It does not pass a count
in x2 or populate the record at that call site.

The SDK resolver at `0x656500` uses string offsets at `0xc7fae0`, relative to
`0xc7a652`. The function table at `0xeb6528` maps entry 125 to
`CommandBufferDrawMeshTasksIndirect`, SDK `0x6814e0`. Direct mesh draws use
entry 122, SDK `0x681470`.

Direct draws write command `0xa0020ea2`, then w2 (count), then w1 (first).
The indirect function writes the command ending in `0xa0020e62`, then inserts
a GPU command segment using the supplied x1 address. At `0x681654` to
`0x68166c` it records that address, a length of **two words**, and segment flag
2. MultiDrawMeshTasksIndirect at `0x6816e0` independently passes record size
8 to its helper at `0x680e20`. The 3D forms are separate entries.

The two-word length excludes treating this particular call as an EXT XYZ
record. The direct and indirect methods differ, however, so direct method
argument order alone does not establish what the indirect macro does with its
words. The macro's value flow has not been decoded.

## Producer boundary

The draw call derives an address into a buffer and does not initialize its
contents. A static census of STG instructions in the three extracted compute
packages records possible GPU writers, with instruction offsets and raw SASS
words, in the external review evidence. The census finds 3,871 programs with
33,305 STG instructions, including 12,090 B64 stores. For example,
`cs_shader.bin` record 60 (`dc9bb120d987a9de`) at +0x720 contains raw instruction
`004fe8000810ab06 0000000c1d00a986`, a B64 store of R12/R13 through R29 plus
its uniform address component. Adjacent register stores establish the byte
order of those register values, but do not identify them as count and first.
Stores alone cannot connect a compute
binding to this draw's dynamic x1 address. No producer or CPU initialization
was proven to write the two fields of this particular buffer. The earlier
all-zero runtime sample also cannot establish their meanings.

Do not infer field order from unrelated stores or a synthetic `{3,17}` fixture.
The remaining proof requires following the buffer's allocation and bindings to
its writer and tracing the two consumed macro operands. A game run with known
populated records and reference pictures remains a separate acceptance gate.

## Public references

Khronos defines [VkDrawMeshTasksIndirectCommandNV](https://docs.vulkan.org/refpages/latest/refpages/source/VkDrawMeshTasksIndirectCommandNV.html)
as taskCount followed by firstTask. The [EXT structure](https://docs.vulkan.org/refpages/latest/refpages/source/VkDrawMeshTasksIndirectCommandEXT.html)
has groupCountX, groupCountY and groupCountZ. Neither specification states NVN2's
ABI. The vendored Ryujinx subset has no GPU command processor or NVN2 mesh
implementation to establish the macro's interpretation.

## Diagnostic protection

The provisional converter keeps its two-word interpretation only behind the
existing opt-in. It writes zero groups for a count above `IXC_CAP` or an unsigned
first-plus-count overflow. It snapshots both raw words and a rejection bit
beside the converted arguments. It never truncates an excessive draw to the cap.

The host submits and waits for the producer and converter segment before any
mesh draw using that result is submitted. It checks every snapshot, refuses
unavailable or rejected records and logs `[RED]`. It dumps the first eight raw
records, including count, first and cap. The GPU guard also prevents excessive
dispatch if a diagnostic wait fails. The synthetic test covers GPU-written
records, deferred writes, zero count, the cap, cap+1 and unsigned overflow.

The synchronous checks are deliberately costly and limited to this unverified,
opt-in path. They establish plausibility, not record semantics or visual parity.

#include <metal_stdlib>
using namespace metal;
// Classify IEEE exponent bits: fast-math must not fold away isnan/isinf checks.
inline bool nonfinite(float4 v) { return any((as_type<uint4>(v) & 0x7f800000u) == 0x7f800000u); }
inline void reduce_bad(uint bad, device uint *out, uint2 tile, uint tiles_x, uint li, threadgroup uint *s) {
    s[li] = bad;
    threadgroup_barrier(mem_flags::mem_threadgroup);
    for (uint n = 128; n; n >>= 1) {
        if (li < n) s[li] += s[li + n];
        threadgroup_barrier(mem_flags::mem_threadgroup);
    }
    if (!li) out[tile.y * tiles_x + tile.x] = s[0];
}
kernel void scan(texture2d<float, access::read> t [[texture(0)]], device uint *out [[buffer(0)]],
                 uint2 p [[thread_position_in_grid]], uint2 tile [[threadgroup_position_in_grid]], uint li [[thread_index_in_threadgroup]]) {
    threadgroup uint s[256];
    uint bad = p.x < t.get_width() && p.y < t.get_height() ? nonfinite(t.read(p)) : false;
    reduce_bad(bad, out, tile, (t.get_width() + 15) / 16, li, s);
}
kernel void scan_ms(texture2d_ms<float, access::read> t [[texture(0)]], device uint *out [[buffer(0)]],
                    uint2 p [[thread_position_in_grid]], uint2 tile [[threadgroup_position_in_grid]], uint li [[thread_index_in_threadgroup]]) {
    threadgroup uint s[256]; uint bad = 0;
    if (p.x < t.get_width() && p.y < t.get_height())
        for (uint i = 0; i < t.get_num_samples(); i++) bad |= nonfinite(t.read(p, i));
    reduce_bad(bad, out, tile, (t.get_width() + 15) / 16, li, s);
}

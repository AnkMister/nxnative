// NEW host work, absent from PR #1444. DM_NVN_BCRT redirects BC colour targets.
#include <metal_stdlib>
using namespace metal;
static uint rgb565(float3 c) {
    uint3 v = uint3(round(saturate(c) * float3(31, 63, 31)));
    return (v.r << 11) | (v.g << 5) | v.b;
}
static float3 from565(uint c) {
    uint3 v = uint3((c >> 11) & 31, (c >> 5) & 63, c & 31);
    return float3((v.r << 3) | (v.r >> 2), (v.g << 2) | (v.g >> 4), (v.b << 3) | (v.b >> 2)) / 255.0f;
}
kernel void bc_decode(texture2d<float, access::sample> src [[texture(0)]],
                      texture2d<float, access::write> dst [[texture(1)]],
                      constant uint &srgb [[buffer(1)]], uint2 p [[thread_position_in_grid]]) {
    if (p.x >= dst.get_width() || p.y >= dst.get_height()) return;
    constexpr sampler s(coord::normalized, address::clamp_to_edge, filter::nearest);
    float4 c = src.sample(s, (float2(p) + 0.5f) / float2(dst.get_width(), dst.get_height()), level(0));
    // The shadow's linear view exposes encoded bytes even when its attachment is sRGB.
    if (srgb) c.rgb = select(12.92f * c.rgb, 1.055f * pow(max(c.rgb, 0.0f), float3(1.0f / 2.4f)) - 0.055f, c.rgb > 0.0031308f);
    dst.write(c, p);
}
kernel void bc_encode_bc1(texture2d<float, access::read> src [[texture(0)]],
                          device uint2 *out [[buffer(0)]], constant uint &allow_alpha [[buffer(1)]], uint2 block [[thread_position_in_grid]]) {
    uint2 size(src.get_width(), src.get_height());
    if (any(block >= (size + 3) / 4)) return;
    float4 px[16]; float3 lo(1), hi(0); bool alpha = false, opaque = false;
    for (uint i = 0; i < 16; i++) {
        px[i] = src.read(min(block * 4 + uint2(i & 3, i >> 2), size - 1));
        if (!allow_alpha) px[i].a = 1.0f;
        alpha |= px[i].a < 0.5f;
        if (px[i].a >= 0.5f) { lo = min(lo, px[i].rgb); hi = max(hi, px[i].rgb); opaque = true; }
    }
    if (!opaque) lo = hi = float3(0);
    uint a = rgb565(hi), b = rgb565(lo);
    if (alpha) { uint t = a; a = min(a, b); b = max(t, b); }
    else if (a <= b) { if (b < 65535) a = b + 1; else b = a - 1; }
    float3 pal[4]; pal[0] = from565(a); pal[1] = from565(b);
    pal[2] = alpha ? (pal[0] + pal[1]) / 2 : (2 * pal[0] + pal[1]) / 3;
    pal[3] = alpha ? float3(0) : (pal[0] + 2 * pal[1]) / 3;
    uint indices = 0;
    for (uint i = 0; i < 16; i++) {
        uint best = 0; float error = INFINITY;
        if (alpha && px[i].a < 0.5f) best = 3;
        else for (uint j = 0; j < (alpha ? 3u : 4u); j++) {
            float3 d = px[i].rgb - pal[j]; float e = dot(d, d);
            if (e < error) { error = e; best = j; }
        }
        indices |= best << (2 * i);
    }
    out[block.y * ((size.x + 3) / 4) + block.x] = uint2(a | (b << 16), indices);
}
kernel void bc_encode_bc4(texture2d<float, access::read> src [[texture(0)]],
                          device uint2 *out [[buffer(0)]], uint2 block [[thread_position_in_grid]]) {
    uint2 size(src.get_width(), src.get_height());
    if (any(block >= (size + 3) / 4)) return;
    uint px[16], lo = 255, hi = 0;
    for (uint i = 0; i < 16; i++) {
        px[i] = uint(round(saturate(src.read(min(block * 4 + uint2(i & 3, i >> 2), size - 1)).r) * 255));
        lo = min(lo, px[i]); hi = max(hi, px[i]);
    }
    uint pal[8]; pal[0] = hi; pal[1] = lo;
    for (uint i = 2; i < 8; i++) pal[i] = ((8 - i) * hi + (i - 1) * lo) / 7;
    ulong bits = ulong(hi | (lo << 8));
    for (uint i = 0; i < 16; i++) {
        uint best = 0, error = 256;
        for (uint j = 0; j < 8; j++) {
            uint e = uint(abs(int(px[i]) - int(pal[j])));
            if (e < error) { error = e; best = j; }
        }
        bits |= ulong(best) << (16 + 3 * i);
    }
    out[block.y * ((size.x + 3) / 4) + block.x] = uint2(uint(bits), uint(bits >> 32));
}

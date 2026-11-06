// The present: the frame drawn into the drawable, cropped (nvn_mtl.m present_pipeline)
#include <metal_stdlib>
using namespace metal;
struct V { float4 p [[position]]; float2 uv; };
vertex V vs(uint id [[vertex_id]]) { float2 uv = float2((id << 1) & 2, id & 2); V o; o.p = float4(uv * float2(2, -2) + float2(-1, 1), 0, 1); o.uv = uv; return o; }
struct Crop { float4 rect; float4 edge; float4 box; };
// The grid covers one output pixel's source footprint. Sharpening uses the same filter so it cannot discard the reconstructed samples.
static float4 filtered(float2 uv, texture2d<float> t, sampler s, constant Crop& c) {
    int n = int(c.box.x);
    if (n <= 1) return t.sample(s, clamp(uv, c.edge.xy, c.edge.zw));
    float4 a = 0;
    for (int y = 0; y < n; y++) for (int x = 0; x < n; x++) {
        float2 o = ((float2(x, y) + 0.5f) / float(n) - 0.5f) * c.box.yz;
        a += t.sample(s, clamp(uv + o, c.edge.xy, c.edge.zw));
    }
    return a / float(n * n);
}
fragment float4 fs(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) {
    return filtered(in.uv * c.rect.zw + c.rect.xy, t, s, c);
}
static float4 sharpened(float2 uv, texture2d<float> t, sampler s, constant Crop& c) {

    float2 d = c.box.yz;
    float4 e = filtered(uv, t, s, c);
    float3 n0 = filtered(uv + float2(-d.x, 0), t, s, c).rgb;
    float3 n1 = filtered(uv + float2( d.x, 0), t, s, c).rgb;
    float3 n2 = filtered(uv + float2(0, -d.y), t, s, c).rgb;
    float3 n3 = filtered(uv + float2(0,  d.y), t, s, c).rgb;
    float3 lo = min(e.rgb, min(min(n0, n1), min(n2, n3))), hi = max(e.rgb, max(max(n0, n1), max(n2, n3)));
    return float4(clamp(e.rgb + (e.rgb - (n0 + n1 + n2 + n3) * 0.25f) * c.box.w, lo, hi), e.a);
}
fragment float4 sharp(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return sharpened(in.uv * c.rect.zw + c.rect.xy, t, s, c); }
// Both spaces use the sRGB transfer curve. Transform primaries in linear light;
// tagging sRGB bytes as Display P3 alone would oversaturate the picture.
static float4 to_p3(float4 v) {
    float3 rgb = max(v.rgb, 0.0f);
    rgb = select(pow((rgb + 0.055f) / 1.055f, float3(2.4f)), rgb / 12.92f, rgb <= 0.04045f);
    rgb = float3(dot(rgb, float3(0.82259287f, 0.17753395f, 0.0f)),
                 dot(rgb, float3(0.03319951f, 0.96678350f, 0.0f)),
                 dot(rgb, float3(0.01708535f, 0.07239572f, 0.91030148f)));
    rgb = select(1.055f * pow(max(rgb, 0.0f), float3(1.0f / 2.4f)) - 0.055f, 12.92f * rgb, rgb <= 0.0031308f);
    return float4(rgb, v.a);
}

fragment float4 fs_p3(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return to_p3(filtered(in.uv * c.rect.zw + c.rect.xy, t, s, c)); }
fragment float4 sharp_p3(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return to_p3(sharpened(in.uv * c.rect.zw + c.rect.xy, t, s, c)); }

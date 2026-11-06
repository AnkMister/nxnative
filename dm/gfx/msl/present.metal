// The present: the frame drawn into the drawable, cropped (nvn_mtl.m present_pipeline)
#include <metal_stdlib>
using namespace metal;
struct V { float4 p [[position]]; float2 uv; };
vertex V vs(uint id [[vertex_id]]) { float2 uv = float2((id << 1) & 2, id & 2); V o; o.p = float4(uv * float2(2, -2) + float2(-1, 1), 0, 1); o.uv = uv; return o; }
struct Crop { float4 rect; float4 edge; };
fragment float4 fs(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return t.sample(s, clamp(in.uv * c.rect.zw + c.rect.xy, c.edge.xy, c.edge.zw)); }
// Both spaces use the sRGB transfer curve. Transform primaries in linear light;
// tagging sRGB bytes as Display P3 alone would oversaturate the picture.
fragment float4 fs_p3(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) {
    float4 v = t.sample(s, clamp(in.uv * c.rect.zw + c.rect.xy, c.edge.xy, c.edge.zw));
    float3 rgb = max(v.rgb, 0.0f);
    rgb = select(pow((rgb + 0.055f) / 1.055f, float3(2.4f)), rgb / 12.92f, rgb <= 0.04045f);
    rgb = float3(dot(rgb, float3(0.82259287f, 0.17753395f, 0.0f)),
                 dot(rgb, float3(0.03319951f, 0.96678350f, 0.0f)),
                 dot(rgb, float3(0.01708535f, 0.07239572f, 0.91030148f)));
    rgb = select(1.055f * pow(max(rgb, 0.0f), float3(1.0f / 2.4f)) - 0.055f, 12.92f * rgb, rgb <= 0.0031308f);
    return float4(rgb, v.a);
}

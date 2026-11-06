// The present: the frame drawn into the drawable, cropped (nvn_mtl.m present_pipeline)
#include <metal_stdlib>
using namespace metal;
struct V { float4 p [[position]]; float2 uv; };
vertex V vs(uint id [[vertex_id]]) { float2 uv = float2((id << 1) & 2, id & 2); V o; o.p = float4(uv * float2(2, -2) + float2(-1, 1), 0, 1); o.uv = uv; return o; }
struct Crop { float4 rect; float4 edge; float4 box; float4 mode; };
// Linear BT.709 and BT.2020 (ITU-R BT.2087; each row sums to 1, so white stays white). Metal's float3x3 takes its columns.
constant float3x3 kRec709To2020 = float3x3(float3(0.627404, 0.069097, 0.016391), float3(0.329283, 0.919540, 0.088013), float3(0.043313, 0.011362, 0.895595));
constant float3x3 kRec2020To709 = float3x3(float3(1.660491, -0.124550, -0.018151), float3(-0.587641, 1.132900, -0.100579), float3(-0.072850, -0.008349, 1.118730));
static inline float3 present_srgb_to_linear(float3 c) {
    float3 lo = c * (1.0 / 12.92);
    float3 hi = pow((c + 0.055) * (1.0 / 1.055), float3(2.4));
    return select(hi, lo, c <= 0.04045);
}
static inline float3 present_linear_to_srgb(float3 l) {
    float3 lo = l * 12.92;
    float3 hi = 1.055 * pow(l, float3(1.0 / 2.4)) - 0.055;
    return select(hi, lo, l <= 0.0031308);
}
// SMPTE ST 2084 EOTF: code value e to absolute luminance (10000 nits = 1.0), divided by the paper white so that 1.0 is the display's SDR white and values above it are headroom
static inline float3 present_pq_to_linear(float3 e, float paper) {
    const float m1 = 0.1593017578125, m2 = 78.84375, c1 = 0.8359375, c2 = 18.8515625, c3 = 18.6875;
    float3 ep = pow(max(e, float3(0.0)), float3(1.0 / m2));
    float3 num = max(ep - c1, float3(0.0));
    float3 den = max(c2 - c3 * ep, float3(1e-6));
    return 10000.0 * pow(num / den, float3(1.0 / m1)) / paper;
}
// SMPTE ST 2084 inverse EOTF: linear light where 1.0 is the paper white, to code values (10000 nits = 1.0). pow() gets a positive base (the library is built with fast math)
static inline float3 present_linear_to_pq(float3 l, float paper) {
    const float m1 = 0.1593017578125, m2 = 78.84375, c1 = 0.8359375, c2 = 18.8515625, c3 = 18.6875;
    float3 ym = pow(max(l * (paper / 10000.0), float3(1e-30)), float3(m1));
    return pow((c1 + c2 * ym) / (1.0 + c3 * ym), float3(m2));
}
// A highlight brought to SDR white as an SDR screen shows it: the largest channel goes to 1.0 and the others scale with it, so the hue holds (a screenshot of an HDR frame)
static inline float3 present_to_sdr_white(float3 c0) {
    float3 c = clamp(c0, -65504.0, 65504.0);   // finite: an infinite channel would give inf * 0 below
    float m = max(max(c.r, c.g), c.b);
    return m > 1.0 ? c * (1.0 / m) : c;
}
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
// Conversion follows the quality filter and sharpening, so every present path uses the same colour contract.
static float4 present_sdr(float4 v, constant Crop& c) {
    if (c.mode.x > 2.5) v.rgb = present_linear_to_pq(kRec709To2020 * present_srgb_to_linear(v.rgb), c.mode.y);
    else if (c.mode.x > 1.5) v.rgb = present_linear_to_srgb(saturate(kRec2020To709 * present_to_sdr_white(present_pq_to_linear(v.rgb, c.mode.y))));
    return v;
}
static float4 present_linear(float4 v, constant Crop& c) {
    if (c.mode.x > 1.5) v.rgb = present_pq_to_linear(v.rgb, c.mode.y);
    else if (c.mode.x > 0.5) v.rgb = kRec709To2020 * present_srgb_to_linear(v.rgb);
    else v.rgb = kRec709To2020 * clamp(v.rgb, -65504.0, 65504.0);
    v.rgb = clamp(v.rgb, -65504.0, 65504.0);
    return v;
}
fragment float4 fs(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) {
    return present_sdr(filtered(in.uv * c.rect.zw + c.rect.xy, t, s, c), c);
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
fragment float4 sharp(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return present_sdr(sharpened(in.uv * c.rect.zw + c.rect.xy, t, s, c), c); }
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

fragment float4 fs_p3(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return to_p3(present_sdr(filtered(in.uv * c.rect.zw + c.rect.xy, t, s, c), c)); }
fragment float4 sharp_p3(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return to_p3(present_sdr(sharpened(in.uv * c.rect.zw + c.rect.xy, t, s, c), c)); }

fragment float4 fs_linear(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return present_linear(filtered(in.uv * c.rect.zw + c.rect.xy, t, s, c), c); }
fragment float4 sharp_linear(V in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], constant Crop& c [[buffer(0)]]) { return present_linear(sharpened(in.uv * c.rect.zw + c.rect.xy, t, s, c), c); }

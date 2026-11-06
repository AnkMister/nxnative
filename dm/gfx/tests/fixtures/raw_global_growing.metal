#pragma clang diagnostic ignored "-Wmissing-prototypes"

#include <metal_stdlib>
#include <simd/simd.h>

using namespace metal;

struct _10
{
    uint _m0;
    uint _m1[8];
    float4 _m2;
    float4 _m3;
    int _m4;
    float _m5[73];
    int4 _m6;
    int _m7;
};

struct _16
{
    float4 _m0[4096];
};

struct _21
{
    uint _m0[1];
};

struct spvDescriptorSetBuffer0
{
    device _21* cp_s0 [[id(0)]];
    device _21* cp_s1 [[id(1)]];
};

static inline __attribute__((always_inline))
int _32(thread const int& _172, thread const int& _173, device _21& cp_s1)
{
    int _176 = _173 << 11;
    uint _179 = uint(int(uint(_172) >> uint(21)));
    int _181 = _176 | int(_179);
    int _183 = _181 & 4095;
    int _185 = _183 * 8;
    int _187 = _185 + 6;
    float _189 = as_type<float>(cp_s1._m0[_187]);
    int _191 = as_type<int>(_189) & 4095;
    bool _193 = _191 != 0;
    uint _195 = uint(int(uint(as_type<int>(_189)) >> uint(12)));
    bool _197 = int(_195) == _181;
    bool _199 = _193 && _197;
    bool _201 = uint(_173) < 512u;
    bool _203 = _199 && _201;
    int _205 = _191;
    if (!_203)
    {
        int _207 = 0;
        int _209 = 0 + 4;
        float _211 = as_type<float>(cp_s1._m0[_209]);
        uint _213 = uint(int(uint(as_type<int>(_211)) >> uint(1)));
        int _215 = int(_213);
        bool _217;
        do
        {
            int _219 = _207 + _215;
            int _221 = _219 * 8;
            int _223 = _221 + 0;
            float _225 = as_type<float>(cp_s1._m0[_223]);
            int _227 = _221 + 1;
            float _229 = as_type<float>(cp_s1._m0[_227]);
            bool _231 = as_type<uint>(_229) < uint(_173);
            bool _233 = as_type<int>(_229) == _173;
            bool _235 = as_type<uint>(_225) <= uint(_172);
            bool _237 = _233 && _235;
            bool _239 = _231 || _237;
            int _241 = _239 ? _219 : _207;
            _207 = _241;
            uint _243 = uint(int(uint(_215) >> uint(1)));
            _215 = int(_243);
            _217 = _215 != 0;
        } while (_217);
        _205 = _207;
    }
    int _245 = _205 * 8;
    int _247 = _245 + 2;
    float _249 = as_type<float>(cp_s1._m0[_247]);
    int _251 = _245 + 3;
    float _253 = as_type<float>(cp_s1._m0[_251]);
    bool _255 = uint(_173) < as_type<uint>(_253);
    bool _257 = _173 == as_type<int>(_253);
    bool _259 = uint(_172) < as_type<uint>(_249);
    bool _261 = _257 && _259;
    bool _263 = _255 || _261;
    if (_263)
    {
        int _265 = _245 + 4;
        float _267 = as_type<float>(cp_s1._m0[_265]);
        int _269 = _172 + as_type<int>(_267);
        bool _271 = uint(_269) < uint(_172);
        int _273 = int(_271);
        int _275 = _245 + 5;
        float _277 = as_type<float>(cp_s1._m0[_275]);
        int _279 = _173 + as_type<int>(_277);
        int _281 = _279 + _273;
        uint _478 = *(reinterpret_cast<device uint*>(as_type<ulong>(uint2(uint(_269), uint(_281)))));
        float _283 = as_type<float>(_478);
        return as_type<int>(_283);
    }
    return 0;
}

kernel void main0(constant spvDescriptorSetBuffer0& spvDescriptorSet0 [[buffer(0)]])
{
    float _36 = as_type<float>((*spvDescriptorSet0.cp_s0)._m0[0]);
    float _38 = as_type<float>((*spvDescriptorSet0.cp_s0)._m0[1]);
    int _40 = as_type<int>(_36) + 4;
    bool _44 = uint(_40) < as_type<uint>(_36);
    int _46 = int(_44);
    int _48 = as_type<int>(_38) + _46;
    int _50 = as_type<int>(_36) + 8;
    bool _52 = uint(_50) < as_type<uint>(_36);
    int _54 = int(_52);
    int _56 = as_type<int>(_38) + _54;
    int _58 = as_type<int>(_36) + 12;
    bool _60 = uint(_58) < as_type<uint>(_36);
    int _62 = int(_60);
    int _64 = as_type<int>(_38) + _62;
    int _66 = as_type<int>(_36);
    int _68 = as_type<int>(_38);
    int _70 = _32(_66, _68, (*spvDescriptorSet0.cp_s1));
    int _72 = _40;
    int _74 = _48;
    int _76 = _32(_72, _74, (*spvDescriptorSet0.cp_s1));
    int _78 = _50;
    int _80 = _56;
    int _82 = _32(_78, _80, (*spvDescriptorSet0.cp_s1));
    int _84 = _58;
    int _86 = _64;
    int _88 = _32(_84, _86, (*spvDescriptorSet0.cp_s1));
    (*spvDescriptorSet0.cp_s0)._m0[4] = uint(_70);
    (*spvDescriptorSet0.cp_s0)._m0[5] = uint(_76);
    (*spvDescriptorSet0.cp_s0)._m0[6] = uint(_82);
    (*spvDescriptorSet0.cp_s0)._m0[7] = uint(_88);
}


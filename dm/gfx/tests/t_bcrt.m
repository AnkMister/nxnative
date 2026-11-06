// NEW work absent from PR #1444. Round-trip a plain BC colour attachment.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", label); } } while (0)
static void finish(void) {
    CHECK(mtl_wait(mtl_sub_commit(), 5000000000ull), "submission completed");
    CHECK(!mtl_last_commit_error(), "no GPU fault"); mtl_drain();
}
static uint8_t expand5(unsigned n) { return (uint8_t)((n << 3) | (n >> 2)); }
static uint8_t expand6(unsigned n) { return (uint8_t)((n << 2) | (n >> 4)); }
// An independent CPU decoder checks every pixel of the actual encoded mip.
static void decode_block(const uint8_t *b, int bc4, uint8_t out[16][4]) {
    if (bc4) {
        unsigned pal[8] = {b[0], b[1]};
        if (b[0] > b[1]) for (int i = 2; i < 8; i++) pal[i] = ((8 - i) * b[0] + (i - 1) * b[1]) / 7;
        else { for (int i = 2; i < 6; i++) pal[i] = ((6 - i) * b[0] + (i - 1) * b[1]) / 5; pal[6] = 0; pal[7] = 255; }
        uint64_t bits = 0; for (int i = 0; i < 6; i++) bits |= (uint64_t)b[i + 2] << (8 * i);
        for (int i = 0; i < 16; i++) { out[i][0] = pal[(bits >> (3 * i)) & 7]; out[i][1] = out[i][2] = 0; out[i][3] = 255; }
    } else {
        unsigned c[2] = {b[0] | b[1] << 8, b[2] | b[3] << 8}; uint8_t pal[4][4] = {{0}};
        for (int i = 0; i < 2; i++) { pal[i][0] = expand5(c[i] >> 11); pal[i][1] = expand6((c[i] >> 5) & 63); pal[i][2] = expand5(c[i] & 31); pal[i][3] = 255; }
        for (int k = 0; k < 3; k++) {
            pal[2][k] = c[0] > c[1] ? (2 * pal[0][k] + pal[1][k]) / 3 : (pal[0][k] + pal[1][k]) / 2;
            pal[3][k] = c[0] > c[1] ? (pal[0][k] + 2 * pal[1][k]) / 3 : 0;
        }
        pal[2][3] = 255; pal[3][3] = c[0] > c[1] ? 255 : 0;
        uint32_t bits; memcpy(&bits, b + 4, 4);
        for (int i = 0; i < 16; i++) memcpy(out[i], pal[(bits >> (2 * i)) & 3], 4);
    }
}
static void encoded_read(id<MTLTexture> base, NSUInteger level, NSUInteger slice, uint8_t *out) {
    NSUInteger w = MAX(base.width >> level, 1u), h = MAX(base.height >> level, 1u), row = ((w + 3) / 4) * 8, bytes = row * ((h + 3) / 4);
    id<MTLBuffer> b = [g_dev newBufferWithLength:bytes options:MTLResourceStorageModeShared]; res_add(b);
    mtl_sub_begin(); enc_b_copy_texture_buffer(blit(), base, slice, level, MTLOriginMake(0,0,0), MTLSizeMake(w,h,1), b, 0, row, bytes); finish();
    memcpy(out, b.contents, bytes); res_remove(b);
}
static void roundtrip(MTLPixelFormat format, int array, NVNformat guest_format) {
    int bc4 = format == MTLPixelFormatBC4_RUnorm;
    MTLTextureDescriptor *d = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:format width:16 height:16 mipmapped:YES];
    d.storageMode = MTLStorageModePrivate; d.usage = MTLTextureUsageShaderRead | MTLTextureUsagePixelFormatView;
    if (array) { d.textureType = MTLTextureType2DArray; d.arrayLength = 2; }
    id<MTLTexture> base = [g_dev newTextureWithDescriptor:d]; CHECK(base != nil, "compressed texture allocated"); if (!base) return;
    res_add(base);
    uint8_t seed[128] = {0}; for (int i = 0; i < 16; i++) { seed[8*i] = bc4 ? 64 : 31; seed[8*i+1] = bc4 ? 64 : 0; }
    id<MTLBuffer> upload = [g_dev newBufferWithBytes:seed length:sizeof seed options:MTLResourceStorageModeShared]; res_add(upload);
    mtl_sub_begin();
    for (NSUInteger slice = 0; slice < base.arrayLength; slice++) for (NSUInteger level = 0; level < base.mipmapLevelCount; level++) {
        NSUInteger w = MAX(base.width >> level,1u), row = ((w + 3) / 4) * 8, bytes = row * ((w + 3) / 4);
        enc_b_copy_buffer_texture(blit(), upload, 0, row, bytes, MTLSizeMake(w,w,1), base, slice, level, MTLOriginMake(0,0,0));
    }
    finish();
    tex_t t = {.magic=MAGIC('T','E','X',0), .serial=nvn_new_serial()};
    t.d = (nvn_texdesc){.target=array ? NVN_TEXTURE_TARGET_2D_ARRAY : NVN_TEXTURE_TARGET_2D, .format=guest_format,
                         .flags=NVN_TEXTURE_FLAGS_COMPRESSIBLE, .width=16, .height=16, .depth=array ? 2 : 1, .levels=5, .samples=1};
    nvn_tex_layout(&t.d,&t.L); mtl_tex_init(&t); tex_put(t.serial,base);
    view_t view = {.set_levels=1, .base_level=1, .nlevels=1, .set_layers=1, .min_layer=array ? 1 : 0, .nlayers=1};
    state_reset(); memset(&R,0,sizeof R); R.has_rt=1; R.rt.n=1; R.rt.color[0]=&t; R.rt.cview[0]=view; R.rt.has_cview[0]=1;
    mtl_sub_begin(); CHECK(rp_begin() != nil, "plain BC mip attaches through a shadow");
    CHECK(g_nbcrt == 1 && g_bcrt[0].encode && g_bcrt[0].level == 1 && g_bcrt[0].slice == (NSUInteger)array, "codec records the requested mip and slice");
    finish();
    uint8_t blocks[128]; encoded_read(base,1,array,blocks);
    uint8_t pixels[16][4]; decode_block(blocks,bc4,pixels);
    CHECK(abs((int)pixels[0][bc4 ? 0 : 2] - (bc4 ? 64 : 255)) <= 4, "Load preserves the seeded encoded mip");
    memset(&R,0,sizeof R); R.has_rt=1; R.rt.n=1; R.rt.color[0]=&t; R.rt.cview[0]=view; R.rt.has_cview[0]=1;
    R.clear_c[0]=1; R.cc[0]=bc4 ? MTLClearColorMake(0.75,0,0,1) : MTLClearColorMake(0,0.25,0,guest_format == NVN_FORMAT_RGB_DXT1 ? 0 : 1);
    mtl_sub_begin(); CHECK(rp_begin() != nil,"clear pass uses the uncompressed shadow"); finish();
    encoded_read(base,1,array,blocks);
    int expected = bc4 ? 191 : format == MTLPixelFormatBC1_RGBA_sRGB ? 137 : 64, same=1;
    for (int block=0;block<4;block++) { decode_block(blocks+block*8,bc4,pixels); for(int i=0;i<16;i++) same &= abs((int)pixels[i][bc4 ? 0 : 1]-expected)<=5 && pixels[i][3]==255; }
    CHECK(same,"every pixel round-trips through encoded BC1/BC4 blocks");
    // Sample the encoded mip on the GPU as well, so a matching CPU encoder/decoder cannot hide invalid blocks.
    mtl_sub_begin(); id<MTLTexture> src=bc_rt_slice(base,1,array,format); id<MTLTexture> shadow=g_bcrt_sh[0];
    CHECK(bc_rt_compute(0,src,shadow,nil,format==MTLPixelFormatBC1_RGBA_sRGB),"GPU decoder accepts encoded mip");
    NSUInteger row=8*(bc4?1:4); id<MTLBuffer> decoded=[g_dev newBufferWithLength:row*8 options:MTLResourceStorageModeShared]; res_add(decoded);
    enc_b_copy_texture_buffer(blit(),shadow,0,0,MTLOriginMake(0,0,0),MTLSizeMake(8,8,1),decoded,0,row,row*8); finish();
    same=1; const uint8_t *bytes=decoded.contents;
    for(int i=0;i<64;i++) same &= abs((int)bytes[i*(bc4?1:4)+(bc4?0:1)]-expected)<=5;
    CHECK(same,"GPU sampling agrees with the encoded mip");
    encoded_read(base,0,0,blocks); CHECK(!memcmp(blocks,seed,128),"other mip remains byte-for-byte unchanged");
    if(array) { encoded_read(base,1,0,blocks); CHECK(!memcmp(blocks,seed,32),"other array slice remains unchanged"); }
    mtl_tex_release(&t); res_remove(decoded); res_remove(upload); res_remove(base);
}
int main(void) { @autoreleasepool {
    unsetenv("DM_NVN_BCRT"); CHECK(!bcrt_on(),"BC redirect is off by default");
    setenv("DM_NVN_BCRT","1",1); mtl_init();
    roundtrip(MTLPixelFormatBC1_RGBA,0,NVN_FORMAT_RGBA_DXT1);
    roundtrip(MTLPixelFormatBC1_RGBA,0,NVN_FORMAT_RGB_DXT1);
    roundtrip(MTLPixelFormatBC1_RGBA_sRGB,0,NVN_FORMAT_RGBA_DXT1_SRGB);
    roundtrip(MTLPixelFormatBC4_RUnorm,1,NVN_FORMAT_RGTC1_UNORM);
    printf("BC render targets: %d checks, %d failed\n",checks,failed); return failed != 0;
} }

#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s (line %d)\n", label, __LINE__); } } while (0)

static void sample_mips(id<MTLSamplerState> sampler) {
    NSError *error = nil;
    id<MTLLibrary> lib = [g_dev newLibraryWithSource:@"#include <metal_stdlib>\nusing namespace metal;\nkernel void k(texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]], device float4 *o [[buffer(0)]]) { o[0]=t.sample(s,float2(0.5),level(0.25)); }" options:nil error:&error];
    CHECK(lib != nil, "mip sampling fixture compiles"); if (!lib) return;
    id<MTLComputePipelineState> pipeline = [g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"k"] error:&error];
    CHECK(pipeline != nil, "mip sampling fixture pipeline builds"); if (!pipeline) return;
    MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA32Float width:4 height:4 mipmapped:YES];
    td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead;
    id<MTLTexture> t = [g_dev newTextureWithDescriptor:td];
    for (int level=0;level<3;level++) {
        float pixels[16*4]; int size=4>>level;
        for (int i=0;i<size*size;i++) { pixels[4*i]=!level; pixels[4*i+1]=0; pixels[4*i+2]=level!=0; pixels[4*i+3]=1; }
        [t replaceRegion:MTLRegionMake2D(0,0,size,size) mipmapLevel:level withBytes:pixels bytesPerRow:size*16];
    }
    id<MTLBuffer> out = [g_dev newBufferWithLength:16 options:MTLResourceStorageModeShared];
    id<MTLCommandBuffer> cb = q_cb(); id<MTLComputeCommandEncoder> ce = [cb computeCommandEncoder];
    [ce setComputePipelineState:pipeline]; [ce setTexture:t atIndex:0]; [ce setSamplerState:sampler atIndex:0]; [ce setBuffer:out offset:0 atIndex:0];
    [ce dispatchThreads:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(1,1,1)]; [ce endEncoding]; [cb commit]; [cb waitUntilCompleted];
    float *v = out.contents; float blue = quality()->trilinear ? 0.25f : 0;
    CHECK(cb.status == MTLCommandBufferStatusCompleted && fabsf(v[0]-(1-blue))<0.01 && fabsf(v[2]-blue)<0.01, "production pool sampler blends mip colours only when enabled");
}
static void samplers(void) {
    for (int min = 0; min < 6; min++) for (int mag = 0; mag < 2; mag++) for (int cmp = 0; cmp < 2; cmp++) for (int red = 0; red < 3; red++) {
        samp_par p = {.minf = min, .magf = mag, .cmp_mode = cmp, .reduction = red};
        MTLSamplerDescriptor *d = [MTLSamplerDescriptor new];
        d.minFilter = (min & 1) ? MTLSamplerMinMagFilterLinear : MTLSamplerMinMagFilterNearest;
        d.magFilter = mag ? MTLSamplerMinMagFilterLinear : MTLSamplerMinMagFilterNearest;
        d.mipFilter = min < 2 ? MTLSamplerMipFilterNotMipmapped : min < 4 ? MTLSamplerMipFilterNearest : MTLSamplerMipFilterLinear;
        d.maxAnisotropy = 1;
        MTLSamplerMipFilter original = d.mipFilter;
        quality_sampler(d, &p);
        int eligible = !cmp && !red && (min & 1) && mag && min >= 2;
        CHECK(d.maxAnisotropy == (eligible ? fmax(1, quality()->aniso) : 1), "anisotropy protects shadows, reductions, nearest and non-mipmapped samplers");
        CHECK(d.mipFilter == (eligible && quality()->trilinear ? MTLSamplerMipFilterLinear : original), "trilinear only upgrades ordinary linear mip samplers");
        d.maxAnisotropy = 16; quality_sampler(d, &p);
        CHECK(d.maxAnisotropy == 16, "anisotropy is a floor and preserves the game's higher value");
    }
    samp_par p = {.minf = 3, .magf = 1, .aniso = 1, .lod_max = 4};
    mtl_reg_samp(91, &p);
    os_unfair_lock_lock(&g_rmu);
    __unsafe_unretained id<MTLBuffer> table = nil;
    uint64_t gpu = pool_gpu(1, 0, 0, 80, &table);
    id<MTLSamplerState> s = samp_by_id(91);
    CHECK(s && gpu == table.gpuAddress, "bindless sampler pool creates the production sampler");
    CHECK(((uint64_t *)((uint8_t *)table.contents + DMSH_POOL_HEAD))[11] == s.gpuResourceID._impl, "pool base and cached sampler resource ID agree");
    id<MTLBuffer> old = table;
    CHECK(pool_gpu(1, 0, 0, 80, &table) == gpu, "unchanged sampler pool reuses its table");
    os_unfair_lock_unlock(&g_rmu);
    sample_mips(s);
    p.minf = 1; mtl_reg_samp(91, &p);
    os_unfair_lock_lock(&g_rmu);
    pool_gpu(1, 0, 0, 80, &table);
    CHECK(table != old && ((uint64_t *)((uint8_t *)table.contents + DMSH_POOL_HEAD))[11] == g_srid[91], "re-registration replaces the sampler in the bindless pool");
    os_unfair_lock_unlock(&g_rmu);
}

static void reduction(void) {
    MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:16 height:16 mipmapped:NO];
    td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead;
    id<MTLTexture> src = [g_dev newTextureWithDescriptor:td]; uint8_t in[16*16*4];
    for (int y=0;y<16;y++) for (int x=0;x<16;x++) { int i=4*(y*16+x); in[i]=in[i+1]=in[i+2]=(x%4==0 ? 255 : 0); in[i+3]=255; }
    [src replaceRegion:MTLRegionMake2D(0,0,16,16) mipmapLevel:0 withBytes:in bytesPerRow:64];
    td.width = td.height = 4; td.usage = MTLTextureUsageRenderTarget;
    id<MTLTexture> dst = [g_dev newTextureWithDescriptor:td]; id<MTLCommandBuffer> cb = q_cb();
    CHECK(present_encode(cb,src,dst,NULL), "reduction pattern encodes"); [cb commit]; [cb waitUntilCompleted];
    uint8_t out[4*4*4]; [dst getBytes:out bytesPerRow:16 fromRegion:MTLRegionMake2D(0,0,4,4) mipmapLevel:0];
    int bad=0, want=quality()->output>1 ? 64 : 0;
    for(int i=0;i<16;i++) bad += abs(out[4*i]-want)>1 || abs(out[4*i+1]-want)>1 || abs(out[4*i+2]-want)>1;
    CHECK(!bad, "the reduction footprint is averaged even with sharpening enabled; default keeps one bilinear sample");
}

static void image_case(int w, int h, int sharp_test, int m4) {
    enum { N = 24 };
    MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm_sRGB width:N height:N mipmapped:NO];
    td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageShaderRead | MTLTextureUsagePixelFormatView;
    id<MTLTexture> src = [g_dev newTextureWithDescriptor:td];
    uint8_t in[N*N*4];
    for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) {
        uint8_t *p = in + 4*(y*N+x); p[0] = 255; p[1] = p[2] = 0; p[3] = 255;
        if (x >= 4 && x < 20 && y >= 4 && y < 20) {
            p[0] = sharp_test ? ((x & 3) == 0 ? 220 : 40) : 128;
            p[1] = sharp_test ? p[0] : 64; p[2] = sharp_test ? p[0] : 200;
        }
    }
    [src replaceRegion:MTLRegionMake2D(0,0,N,N) mipmapLevel:0 withBytes:in bytesPerRow:N*4];
    td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:w height:h mipmapped:NO];
    td.storageMode = MTLStorageModeShared; td.usage = MTLTextureUsageRenderTarget;
    id<MTLTexture> out = [g_dev newTextureWithDescriptor:td];
    const int crop[4] = {4,4,16,16};
    res_add(src); res_commit();
    if (m4) {
        int kind = present_offscreen_wait(src, crop, out);
        CHECK(kind != PRESENT_FAILED, "Metal 4 quality presentation completes");
        if (w == 32 && h == 16) CHECK(kind == (quality()->present && quality()->output > 1 ? PRESENT_METALFX : PRESENT_STANDARD), "supersampled MetalFX reconstructs even at native content size");
    }
    else {
        id<MTLCommandBuffer> cb = q_cb();
        CHECK(present_encode(cb, src, out, crop), "classic quality presentation encodes");
        [cb commit]; [cb waitUntilCompleted];
        CHECK(cb.status == MTLCommandBufferStatusCompleted, "classic quality presentation completes");
    }
    uint8_t *bytes = malloc(w*h*4); [out getBytes:bytes bytesPerRow:w*4 fromRegion:MTLRegionMake2D(0,0,w,h) mipmapLevel:0];
    int bad = 0;
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
        uint8_t *p = bytes + 4*(y*w+x);
        if (x < (w-h)/2 || x >= (w+h)/2) { bad += p[0] || p[1] || p[2]; continue; }
        if (!sharp_test) bad += abs(p[0]-128)>2 || abs(p[1]-64)>2 || abs(p[2]-200)>2;
        else bad += p[0] < 38 || p[0] > 222 || abs(p[0]-p[1])>2 || abs(p[1]-p[2])>2;
    }
    CHECK(!bad, sharp_test ? "sharpening and reduction preserve neutral channels and neighbourhood bounds" : "quality present preserves raw sRGB colour, crop edges and letterboxing");
    free(bytes); res_remove(src);
}

int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 6) return 2;
    const quality_config *c = quality();
    CHECK(c->aniso == atof(argv[1]) && c->trilinear == atoi(argv[2]) && fabs(c->output-atof(argv[3]))<1e-6 && fabs(c->sharpen-atof(argv[4]))<1e-6 && c->present == atoi(argv[5]), "preset defaults and explicit overrides");
    mtl_init(); samplers();
    float uv[12] = {0}; present_quality_constants(uv, 48, 48, 24, 24, (MTLViewport){0,0,16,16,0,1});
    CHECK(uv[8] == (c->output > 1 ? 2 : 1), "fractional reduction covers the footprint only when opted in");
    CHECK(fabsf(uv[9]-1.f/32)<1e-6 && fabsf(uv[10]-1.f/32)<1e-6, "filter spacing follows the crop and destination size");
    reduction(); image_case(32,16,0,0); image_case(8,8,1,0);
    image_case(32,16,0,1); image_case(8,8,1,1);
    mtl_drain();
    printf("t_quality: %d checks, %d failed\n", checks, failed); return failed != 0;
}}

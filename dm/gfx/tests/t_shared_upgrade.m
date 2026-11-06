// Astra review 5: every shared view keeps its interpretation, and every shared
// package descriptor follows backing changes without a CPU write generation.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr,"FAIL: %s\n",label); } } while(0)
static id<MTLComputePipelineState> reader;
static float sample_red(id<MTLTexture> t) {
    id<MTLBuffer> dst=[g_dev newBufferWithLength:16 options:MTLResourceStorageModeShared];
    id<MTLCommandBuffer> cb=q_cb(); id<MTLComputeCommandEncoder> e=[cb computeCommandEncoder];
    [e setComputePipelineState:reader]; [e setTexture:t atIndex:0]; [e setBuffer:dst offset:0 atIndex:0];
    [e dispatchThreads:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(1,1,1)]; [e endEncoding]; [cb commit]; [cb waitUntilCompleted];
    CHECK(cb.status==MTLCommandBufferStatusCompleted,"GPU sample completes"); return ((float *)dst.contents)[0];
}
static tex_t desc(uint64_t serial) {
    tex_t t={.magic=MAGIC('T','E','X',0),.serial=serial};
    t.d=(nvn_texdesc){.target=NVN_TEXTURE_TARGET_2D,.format=NVN_FORMAT_RGBA8,.width=4,.height=4,.depth=1,.levels=1,.samples=1};
    nvn_tex_layout(&t.d,&t.L); return t;
}
static void put(id<MTLTexture> t, NSUInteger level, NSUInteger slice, uint32_t pixel) {
    uint32_t pixels[16]; for(int i=0;i<16;i++) pixels[i]=pixel;
    id<MTLBuffer> b=[g_dev newBufferWithBytes:pixels length:sizeof pixels options:MTLResourceStorageModeShared];
    res_add(b); enc_b_copy_buffer_texture(blit(),b,0,16,sizeof pixels,MTLSizeMake(4,4,1),t,slice,level,MTLOriginMake(0,0,0));
    mtl_sub_commit(); mtl_drain(); CHECK(!mtl_last_commit_error(),"GPU backing write completes");
}
int main(void) { @autoreleasepool {
    setenv("DM_NVN_P1444_TEX","1",1); setenv("DM_NVN_SERIAL_HELD","1",1); setenv("DM_NVN_SERIAL_HELD_CHECK","1",1);
    mtl_init(); NSError *error=nil;
    id<MTLLibrary> lib=[g_dev newLibraryWithSource:@"#include <metal_stdlib>\nusing namespace metal; kernel void read_pixel(texture2d<float, access::read> t [[texture(0)]],device float4 *out [[buffer(0)]]) { out[0]=t.read(uint2(0)); }" options:nil error:&error];
    reader=[g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"read_pixel"] error:&error];
    CHECK(reader!=nil,"GPU read fixture compiles"); if(!reader) return 1;
    MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:8 height:8 mipmapped:YES];
    d.textureType=MTLTextureType2DArray; d.arrayLength=2; d.storageMode=MTLStorageModePrivate;
    d.usage=MTLTextureUsageShaderRead|MTLTextureUsagePixelFormatView;
    id<MTLTexture> raw=[g_dev newTextureWithDescriptor:d]; res_add(raw);
    MTLTextureSwizzleChannels sw=MTLTextureSwizzleChannelsMake(MTLTextureSwizzleBlue,MTLTextureSwizzleGreen,MTLTextureSwizzleRed,MTLTextureSwizzleAlpha);
    id<MTLTexture> view=[raw newTextureViewWithPixelFormat:MTLPixelFormatRGBA8Unorm_sRGB textureType:MTLTextureType2D levels:NSMakeRange(1,1) slices:NSMakeRange(1,1) swizzle:sw];
    tex_t a=desc(994001), b=desc(994002); mtl_tex_init(&a); mtl_tex_init(&b); tex_put(a.serial,view); tex_put(b.serial,view);
    mtl_sub_begin(); id<MTLTexture> changed=tex_upgrade(&a,view,MTLTextureUsageShaderWrite,view.pixelFormat), base=changed;
    while(base.parentTexture) base=base.parentTexture;
    put(base,1,1,0xff804020);  // blue128 becomes red after swizzle, then sRGB decode
    for(int j=0;j<2;j++) {
        id<MTLTexture> v=tex_get(j?b.serial:a.serial);
        CHECK(v.pixelFormat==MTLPixelFormatRGBA8Unorm_sRGB && v.textureType==MTLTextureType2D && v.width==4 && v.height==4 && v.mipmapLevelCount==1,"both serials retain sRGB and selected mip/slice view");
        CHECK(v.swizzle.red==MTLTextureSwizzleBlue,"both serials retain channel swizzle");
        CHECK(fabsf(sample_red(v)-0.21586f)<0.002f,"both serials decode the same GPU-written sRGB pixel");
    }
    // Real packaged aliases, tracked and clean. The upgrade changes no CPU page.
    size_t n=65536; void *mem=NULL; posix_memalign(&mem,getpagesize(),n); memset(mem,0,n);
    pool_t pool={.magic=MAGIC('P','O','O','L'),.mem=mem,.size=n,.flags=NVN_MEMORY_POOL_FLAGS_CPU_UNCACHED|NVN_MEMORY_POOL_FLAGS_GPU_CACHED};
    tex_t p=desc(994010), q=desc(994011); p.has_layout=q.has_layout=1; p.mem=q.mem=mem; p.pool=q.pool=&pool;
    uint32_t seed[16]; for(int i=0;i<16;i++) seed[i]=0xff101010; nvn_swizzle(&p.d,0,0,seed,16,mem);
    mtl_pool_add(mem,n); nvn_dirty_add_range(mem,n); mtl_tex_init(&p); mtl_tex_init(&q);
    mtl_sub_begin(); id<MTLTexture> first=tex_mtl(&p); CHECK(tex_mtl(&q)==first && tex_get(p.serial)==tex_get(q.serial),"two packaged serials share the upstream weak package");
    mtl_reg_tex(401,&p,NULL); mtl_reg_tex(402,&q,NULL);
    os_unfair_lock_lock(&g_rmu); CHECK(tex_by_id(401)==first && tex_by_id(402)==first,"both descriptor families cache original package"); os_unfair_lock_unlock(&g_rmu);
    mtl_sub_commit(); mtl_drain(); uint64_t dirty=nvn_dirty_now();
    mtl_sub_begin(); id<MTLTexture> newer=tex_upgrade(&p,first,MTLTextureUsageShaderWrite,first.pixelFormat); put(newer,0,0,0xff808080);
    CHECK(nvn_dirty_now()==dirty,"GPU-only upgrade/write does not change CPU dirty generation");
    os_unfair_lock_lock(&g_rmu); id<MTLTexture> vp=tex_by_id(401), vq=tex_by_id(402); os_unfair_lock_unlock(&g_rmu);
    CHECK(vp==newer && vq==newer && newer!=first,"both cached descriptors resolve replacement package");
    CHECK(fabsf(sample_red(vp)-128.0f/255)<0.002f && fabsf(sample_red(vq)-128.0f/255)<0.002f,"both descriptor families sample latest GPU write");
    mtl_tex_release(&p); mtl_tex_release(&q); mtl_alias_drop_pool(&pool); nvn_dirty_remove_range(mem); mtl_pool_del(mem); mtl_drain(); free(mem);
    mtl_tex_release(&a); mtl_tex_release(&b);
    printf("shared upgrade regressions: %d checks, %d failed\n",checks,failed); return failed!=0;
} }

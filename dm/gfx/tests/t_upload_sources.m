#include "../tex/nvn_deswizzle_gpu.h"
static int capture_deswizzle(id<MTL4ComputeCommandEncoder>, id<MTL4ArgumentTable>, id<MTLBuffer>, size_t,
                             id<MTLBuffer>, uint64_t, const nvn_texdesc *, unsigned, unsigned, id<MTLBuffer>, uint64_t, size_t);
#define nvn_deswz_gpu_encode_m4 capture_deswizzle
#include "../nvn/nvn_mtl.m"
#undef nvn_deswz_gpu_encode_m4
static id<MTLBuffer> encoded_source;
static int capture_deswizzle(id<MTL4ComputeCommandEncoder> enc, id<MTL4ArgumentTable> table, id<MTLBuffer> params, size_t poff,
                             id<MTLBuffer> src, uint64_t soff, const nvn_texdesc *d, unsigned level, unsigned layer,
                             id<MTLBuffer> dst, uint64_t doff, size_t pitch) {
    encoded_source = src;
    return nvn_deswz_gpu_encode_m4(enc, table, params, poff, src, soff, d, level, layer, dst, doff, pitch);
}
// Expose the pool exactly when up_alloc allocates B's staging, without a
// production test hook or a scheduling race with a guest thread.
@interface UploadSourceDevice : NSObject
@property(strong) id<MTLDevice> device;
@property(copy) void (^onAllocate)(void);
@end
@implementation UploadSourceDevice
- (id)forwardingTargetForSelector:(SEL)sel { return self.device; }
- (id<MTLBuffer>)newBufferWithLength:(NSUInteger)n options:(MTLResourceOptions)options {
    void (^hook)(void) = self.onAllocate; self.onAllocate = nil;
    if (hook) hook();
    return [self.device newBufferWithLength:n options:options];
}
@end
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(label, c) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s (line %d)\n", label, __LINE__); } } while (0)
static int resident(id<MTLBuffer> b) {
    pthread_mutex_lock(&g_res_mu); int yes = [g_res_objects containsObject:b]; pthread_mutex_unlock(&g_res_mu); return yes;
}
static NSUInteger users(id<MTLBuffer> b) {
    pthread_mutex_lock(&g_mu); NSUInteger n = [g_up_src_users countForObject:b]; pthread_mutex_unlock(&g_mu); return n;
}
static id<MTLBuffer> source(uint64_t addr, id<MTLBuffer> dst) {
    up_begin(); uint64_t off = UINT64_MAX;
    id<MTLBuffer> src = up_big_src(addr, 256, &off);
    CHECK("source buffer resolves", src && off < src.length);
    if (src) enc_b_copy_buffer(g_up_ce, src, off, dst, 0, 256);
    return src;
}
static void rollover(void *mem, size_t bytes) {
    mtl_pool_add(mem, bytes);
    tex_t t = {.magic = MAGIC('T','E','X',0), .mem = mem, .has_layout = 1, .serial = 99001};
    t.d = (nvn_texdesc){.target = 1, .format = NVN_FORMAT_RGBA8, .width = 16, .height = 16, .depth = 1, .levels = 1, .samples = 1};
    nvn_tex_layout(&t.d, &t.L);
    CHECK("GPU deswizzle is available", g_nvn_deswz_gpu);
    mtl_sub_begin(); up_begin();
    size_t off; up_alloc(UP_BATCH_BYTES, &off);   // fill A's budget so pkg_upload_ must start B
    uint64_t seq = g_up_seq;
    id<MTLSharedEvent> gate = [g_dev newSharedEvent];
    rec_drain(); [g_q4 waitForEvent:gate value:1];
    UploadSourceDevice *device = [UploadSourceDevice new]; device.device = g_dev;
    __block id<MTLBuffer> carried;
    device.onAllocate = ^{
        carried = g_up_big_src.allValues.lastObject;
        CHECK("A acquired its source before pool exposure", carried && resident(carried) && users(carried) == 1);
        CHECK("staging allocation rolled into B before exposure", g_up_seq == seq + 1 && !g_up_sources.count);
        mtl_pool_addressed(mem, bytes);
    };
    g_dev = (id<MTLDevice>)device;
    id<MTLTexture> image = pkg_upload_(&t, NULL, nil, 0);
    g_dev = device.device;
    CHECK("exposure hook ran during rollover", !device.onAllocate && carried);
    CHECK("pkg_upload_ encoded the carried source into open B", image && g_up_cb && encoded_source == carried);
    uint64_t ignored;
    CHECK("exposed pool refuses upload-only re-acquisition", !up_big_src((uint64_t)(uintptr_t)mem, t.L.size, &ignored));
    CHECK("both batches registered the actual encoded source", users(encoded_source) == 2);
    rec_publish(); gate.signaledValue = 1; up_wait_zero(&g_up_pending, WS_DIAG);
    CHECK("A completed while B is still open", g_up_cb && !atomic_load(&g_up_pending));
    CHECK("carried source stays resident until B completes", resident(encoded_source) && users(encoded_source) == 1);
    // Keep a failing pre-fix run safe: restore residency before submitting B.
    int restore = !resident(encoded_source); if (restore) res_add(encoded_source);
    up_flush(); rec_publish(); up_wait_zero(&g_up_pending, WS_DIAG);
    if (restore) res_remove(encoded_source);
    CHECK("B completion releases the carried source", !resident(encoded_source) && users(encoded_source) == 0);
    CHECK("rendering submission completes", mtl_wait(mtl_sub_commit(), 5000000000ull));
    id<MTLBuffer> pixels = [g_dev newBufferWithLength:16 * 16 * 4 options:MTLResourceStorageModeShared];
    id<MTLCommandBuffer> cb = q_cb(); id<MTLBlitCommandEncoder> blit = [cb blitCommandEncoder];
    [blit copyFromTexture:image sourceSlice:0 sourceLevel:0 sourceOrigin:MTLOriginMake(0, 0, 0) sourceSize:MTLSizeMake(16, 16, 1)
                toBuffer:pixels destinationOffset:0 destinationBytesPerRow:16 * 4 destinationBytesPerImage:16 * 16 * 4];
    [blit endEncoding]; [cb commit]; [cb waitUntilCompleted];
    CHECK("texture readback completes", cb.status == MTLCommandBufferStatusCompleted);
    CHECK("rollover upload preserves every texel", !memcmp(pixels.contents, mem, pixels.length));
    mtl_pool_del(mem);
}
int main(void) { @autoreleasepool {
    setenv("DM_NVN_P1444_STUTTER", "1", 1); mtl_init();
    size_t bytes = 1u << 20;
    uint8_t *mem = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    if (mem == MAP_FAILED) abort();
    memset(mem, 0x5a, bytes); mtl_pool_add(mem, bytes);
    id<MTLBuffer> dst = [g_dev newBufferWithLength:256 options:MTLResourceStorageModeShared]; res_add(dst);
    id<MTLSharedEvent> gate = [g_dev newSharedEvent];
    rec_drain(); [g_q4 waitForEvent:gate value:1];
    id<MTLBuffer> first = source((uint64_t)(uintptr_t)mem, dst);
    CHECK("first batch makes the cached source resident", resident(first) && users(first) == 1);
    CHECK("same-batch reuse returns the wrapper", source((uint64_t)(uintptr_t)mem, dst) == first);
    CHECK("same-batch reuse counts only once", users(first) == 1);
    up_flush(); rec_publish();
    CHECK("second batch reuses the wrapper", source((uint64_t)(uintptr_t)mem, dst) == first);
    CHECK("both batches hold residency", resident(first) && users(first) == 2);
    gate.signaledValue = 1; up_wait_zero(&g_up_pending, WS_DIAG);
    CHECK("first completion leaves the open batch resident", resident(first) && users(first) == 1);
    up_flush(); rec_publish(); up_wait_zero(&g_up_pending, WS_DIAG);
    CHECK("last completion removes residency", !resident(first) && users(first) == 0);
    CHECK("idle CPU cache retains the wrapper", [g_up_big_src.allValues containsObject:first]);
    CHECK("uploaded bytes survive", ((uint8_t *)dst.contents)[0] == 0x5a && ((uint8_t *)dst.contents)[255] == 0x5a);
    CHECK("idle wrapper is reused", source((uint64_t)(uintptr_t)mem, dst) == first);
    CHECK("reuse restores residency", resident(first) && users(first) == 1);
    mtl_pool_del(mem);
    CHECK("pool deletion removes the cached wrapper", ![g_up_big_src.allValues containsObject:first]);
    CHECK("pool deletion leaves the active upload resident", resident(first) && users(first) == 1);
    up_flush(); rec_publish(); up_wait_zero(&g_up_pending, WS_DIAG);
    CHECK("deleted pool source retires at upload completion", !resident(first) && users(first) == 0);
    rollover(mem, bytes);
    CHECK("GPU has no submission error", !mtl_last_commit_error());
    printf("t_upload_sources: %d checks, %d failed\n", checks, failed); return failed != 0;
} }

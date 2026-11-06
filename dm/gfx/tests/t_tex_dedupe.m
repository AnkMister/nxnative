// Existing no-copy Metal buffers must keep naming the restored VM object.
#include "../nvn/nvn_mtl.m"
#include <sys/mman.h>
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
uint64_t now_ns(void) { return bp_now(); }
extern int g_dd_test_lose;
static int checks, failed;
#define CHECK(name, value) do { checks++; if (!(value)) { fprintf(stderr, "FAIL: %s\n", name); failed++; } } while (0)
int main(void) { @autoreleasepool {
    setenv("DM_NVN_TEX_DEDUPE", "1", 1);
    mtl_init();
    CHECK("experiment enabled", dd_on());
    size_t len = 4u << 20;
    uint8_t *mem = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    for (size_t i = 0; i < len; i++) mem[i] = (uint8_t)(i * 13 + 7);
    mtl_pool_add(mem, len); nvn_dirty_add_range(mem, len);
    uint64_t stamp = nvn_dirty_now(); nvn_dirty_protect(mem, len);
    int skip;
    pthread_mutex_lock(&g_mu);
    size_t got = nvn_dirty_release(mem, len, stamp, dd_ok, NULL, &skip);
    pthread_mutex_unlock(&g_mu);
    CHECK("nonresident pool releases all pages", got == len);
    g_dd_test_lose = 1;   // Restore from the file into the shared VM object.
    void *buffer = NULL; uint64_t offset = 0;
    CHECK("pool lookup restores before residency", mtl_addr((uint64_t)mem, len, &buffer, &offset));
    uint64_t gone, released, back, reread, raced, errors, file;
    nvn_dirty_dedupe_stats(&gone, &released, &back, &reread, &raced, &errors, &file);
    CHECK("no pages left released", gone == 0 && back == len / getpagesize());
    id<MTLBuffer> output = [g_dev newBufferWithLength:len options:MTLResourceStorageModeShared];
    id<MTLCommandQueue> queue = [g_dev newCommandQueue];
    id<MTLCommandBuffer> cb = [queue commandBuffer];
    id<MTLBlitCommandEncoder> blit = [cb blitCommandEncoder];
    [blit copyFromBuffer:(__bridge id<MTLBuffer>)buffer sourceOffset:offset toBuffer:output destinationOffset:0 size:len];
    [blit endEncoding]; [cb commit]; [cb waitUntilCompleted];
    CHECK("GPU copy completes", cb.status == MTLCommandBufferStatusCompleted);
    const uint8_t *actual = output.contents; size_t bad = 0;
    for (size_t i = 0; i < len; i++) bad += actual[i] != (uint8_t)(i * 13 + 7);
    CHECK("existing Metal buffer reads every restored byte", bad == 0);
    pthread_mutex_lock(&g_mu);
    got = nvn_dirty_release(mem, len, stamp, dd_ok, NULL, &skip);
    pthread_mutex_unlock(&g_mu);
    CHECK("resident pool cannot release", got == 0 && skip);
    nvn_dirty_remove_range(mem); mtl_pool_del(mem); mtl_drain();
    munmap(mem, len);
    printf("t_tex_dedupe: %d checks, %d failed\n", checks, failed);
    return failed != 0;
} }

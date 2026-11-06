#include "../nvn/nvn_mtl.m"
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
    CHECK("GPU has no submission error", !mtl_last_commit_error());
    printf("t_upload_sources: %d checks, %d failed\n", checks, failed); return failed != 0;
} }

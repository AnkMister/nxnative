// Reuse the offscreen layer, pixel readback and host stubs of the allocator test.
#define main allocator_test_main
#include "t_present_alloc.m"
#undef main

static void finish_present(void) {
    pthread_mutex_lock(&g_pq_mu);
    struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 5;
    while (g_pq_inflight && pthread_cond_timedwait(&g_pq_cv, &g_pq_mu, &ts) != ETIMEDOUT) {}
    CHECK("display GPU work completed", !g_pq_inflight);
    pthread_mutex_unlock(&g_pq_mu);
}
static int show(const tex_t *t, uint64_t ticket, int own) {
    int got = present_now(t, 0, ticket, ticket, NULL, drawable(), 0, atomic_load(&g_eco_work), own);
    finish_present();
    // Offscreen layers do not reach a physical display. Inject only that acknowledgement.
    if (got) atomic_store(&g_eco_displayed, ticket);
    return got;
}
int main(void) { @autoreleasepool {
    alarm(30); setbuf(stdout, NULL);
    setenv("DM_ECO_SAME_FRAME", "1", 1); setenv("DM_PRESENT_HZ", "0", 1);
    mtl_init(); g_test_layer = offscreen_layer(); g_layers = [NSMutableArray new];
    tex_t t = source(92001, 100, 100);
    id<MTLTexture> shared = tex_get(t.serial);
    MTLTextureDescriptor *td = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:8 height:8 mipmapped:NO];
    td.storageMode = MTLStorageModePrivate; td.usage = MTLTextureUsageRenderTarget | MTLTextureUsageShaderRead;
    id<MTLTexture> private = [g_dev newTextureWithDescriptor:td];
    id<MTLCommandBuffer> cb = [g_q commandBuffer]; id<MTLBlitCommandEncoder> be = [cb blitCommandEncoder];
    [be copyFromTexture:shared toTexture:private]; [be endEncoding]; [cb commit]; [cb waitUntilCompleted];
    serial_put(t.serial, private); res_add(private); res_commit();
    pool_t pool = {.flags = NVN_MEMORY_POOL_FLAGS_CPU_NO_ACCESS}; t.pool = &pool;
    CHECK("first present submits display GPU work", show(&t, 1, 1) == 1);
    CHECK("repeat avoids the display command buffer", show(&t, 2, 1) == 0);
    CHECK("repeat records a logical presentation", g_pres[2 % PRING].n == 2 && g_pres[2 % PRING].t > 0);
    CHECK("repeat does not consume an allocator", !g_present_alloc_fence[2]);
    atomic_fetch_add(&g_eco_work, 2);
    CHECK("any intervening guest submission forces rendering", show(&t, 3, 1) == 1);
    nvn_eco_surface_changed();
    CHECK("surface change forces rendering", show(&t, 4, 1) == 1);
    CHECK("external producer is never skipped", show(&t, 5, 0) == 1);
    CHECK("unknown frame invalidates the previous proof", show(&t, 6, 1) == 1);
    pool.flags = 0;
    CHECK("CPU-writable pool is never skipped", show(&t, 7, 1) == 1);
    pool.flags = NVN_MEMORY_POOL_FLAGS_CPU_NO_ACCESS;
    serial_put(t.serial, shared);
    CHECK("shared Metal storage is never skipped", show(&t, 8, 1) == 1);
    serial_put(t.serial, private);
    atomic_fetch_add(&g_eco_work, 1);
    CHECK("in-progress submission is never skipped", show(&t, 9, 1) == 1);
    atomic_fetch_add(&g_eco_work, 1);
    // No periodic callback remains when the queue is empty. Explicit clock demand keeps it awake.
    CAMetalDisplayLink *link = [[CAMetalDisplayLink alloc] initWithMetalLayer:g_test_layer];
    g_dm_present_link = 1;
    NvMetalDisplayLinkDelegate *delegate = [NvMetalDisplayLinkDelegate new];
    FakeLinkUpdate *u = [FakeLinkUpdate new]; u.targetPresentationTimestamp = CACurrentMediaTime();
    [delegate metalDisplayLink:link needsUpdate:(CAMetalDisplayLinkUpdate *)u];
    CHECK("empty queue pauses the display link", link.paused);
    link.paused = NO; g_eco_tick_waiters = 1;
    [delegate metalDisplayLink:link needsUpdate:(CAMetalDisplayLinkUpdate *)u];
    CHECK("clock consumer prevents idle pause", !link.paused);
    g_eco_tick_waiters = 0; link.paused = YES;
    g_link = link; g_link_started = 1; g_link_owns_layer = 1; g_pq_done = 0;
    present_enqueue(&t, 0, NULL, 0);
    CHECK("enqueue wakes a paused link", !link.paused);
    [link invalidate]; g_link = nil;
    printf("eco present: %d checks, %d failed\n", checks, failed);
    return failed != 0;
} }

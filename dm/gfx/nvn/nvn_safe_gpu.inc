// This is a fail-stop safeguard for issue #1326, not a fix for unknown shader or
// driver faults. A kernel call already stuck in the driver may outlive exit.
static _Atomic int g_safe_pending;
static _Atomic uint64_t g_safe_progress, g_safe_wired;
static uint64_t g_safe_limit, g_safe_wired_limit;
static int safe_gpu_on(void) {
    static int on; static dispatch_once_t once;
    dispatch_once(&once, ^{
        const char *e = getenv("DM_SAFE_GPU");
        on = e ? strcmp(e, "0") != 0 : !TARGET_OS_IPHONE && !strcmp(DM_GAME_ID, "0400486024DEC000");
    });
    return on;
}
void dm_host_gpu_stop(void);
__attribute__((weak)) void dm_host_gpu_stop(void) { kill(getpid(), SIGTERM); }
static void safe_gpu_trip(const char *why) {
    if (!safe_gpu_on() || atomic_exchange(&g_safe_stopped, 1)) return;
    MLOG("[RED] DM_SAFE_GPU: %s; GPU submissions stopped permanently; releasing Metal residency and exiting", why);
    dm_host_gpu_stop();   // the host performs cleanup off the Metal callback / submit thread
}
static uint64_t safe_gpu_cap(uint64_t ws) { return ws / 10 * 7; }
static uint64_t safe_gpu_wired_cap(uint64_t ws, uint64_t physical) {
    uint64_t reserve = MAX(ws / 10 * 3, 2ull << 30);
    return physical > reserve ? physical - reserve : 0;
}
static int safe_gpu_budget(uint64_t used, uint64_t wired) {
    return (!g_safe_limit || used < g_safe_limit) && (!g_safe_wired_limit || wired < g_safe_wired_limit);
}
static uint64_t safe_gpu_wired(void) {
    vm_statistics64_data_t vm; mach_msg_type_number_t n = HOST_VM_INFO64_COUNT;
    static mach_port_t host; static dispatch_once_t once; dispatch_once(&once, ^{ host = mach_host_self(); });
    if (host_statistics64(host, HOST_VM_INFO64, (host_info64_t)&vm, &n) != KERN_SUCCESS) return atomic_load(&g_safe_wired);
    return (uint64_t)vm.wire_count * (uint64_t)getpagesize();
}
static int safe_gpu_preflight(void) {
    if (!safe_gpu_on()) return 1;
    if (atomic_load(&g_safe_stopped)) return 0;
    uint64_t used = MAX((uint64_t)g_dev.currentAllocatedSize, MAX(atomic_load(&g_res_bytes), atomic_load(&g_guard_set)));
    uint64_t wired = atomic_load(&g_safe_wired);
    if (safe_gpu_budget(used, wired)) return 1;
    char why[256]; snprintf(why, sizeof why, "memory headroom exhausted (GPU %llu/%llu MiB, system wired %llu/%llu MiB)",
                           (unsigned long long)(used >> 20), (unsigned long long)(g_safe_limit >> 20),
                           (unsigned long long)(wired >> 20), (unsigned long long)(g_safe_wired_limit >> 20));
    safe_gpu_trip(why);
    return 0;
}
static void safe_gpu_feedback(NSError *error) {
    if (!safe_gpu_on()) return;
    atomic_store(&g_safe_progress, clock_gettime_nsec_np(CLOCK_UPTIME_RAW));
    int n = atomic_load(&g_safe_pending);
    while (n > 0 && !atomic_compare_exchange_weak(&g_safe_pending, &n, n - 1)) {}
    // Even an innocent victim means the desktop GPU has faulted. Safe mode
    // deliberately gives up recovery rather than trying more game work.
    if (error) safe_gpu_trip(error.description.UTF8String);
}
static void safe_gpu_started(void) {
    if (!safe_gpu_on()) return;
    if (!atomic_fetch_add(&g_safe_pending, 1)) atomic_store(&g_safe_progress, clock_gettime_nsec_np(CLOCK_UPTIME_RAW));
}
static int safe_gpu_stalled(uint64_t now) {
    uint64_t progress = atomic_load(&g_safe_progress);
    return atomic_load(&g_safe_pending) > 0 && now > progress && now - progress >= 10ull * NSEC_PER_SEC;
}
static void safe_gpu_tick(void) {
    if (!safe_gpu_on()) return;
    atomic_store(&g_safe_wired, safe_gpu_wired());
    if (!safe_gpu_preflight()) return;
    if (safe_gpu_stalled(clock_gettime_nsec_np(CLOCK_UPTIME_RAW))) safe_gpu_trip("no GPU completion feedback for 10 seconds");
}
// Caller holds g_res_mu. Every Metal 4 path, including the encode worker and
// auxiliary queues, checks at the actual kernel submission, not at record time.
static int safe_gpu_commit4_locked(const id<MTL4CommandBuffer> *buffers, NSUInteger count, MTL4CommitOptions *options) {
    if (!safe_gpu_preflight()) return 0;
    MTL4CommitOptions *o = options ?: (safe_gpu_on() ? [MTL4CommitOptions new] : nil);
    if (safe_gpu_on()) {
        [o addFeedbackHandler:^(id<MTL4CommitFeedback> f) { safe_gpu_feedback(f.error); }];
        safe_gpu_started();
    }
    if (o) [g_q4 commit:buffers count:count options:o]; else [g_q4 commit:buffers count:count];
    return 1;
}
static int safe_gpu_commit4(const id<MTL4CommandBuffer> *buffers, NSUInteger count, MTL4CommitOptions *options) {
    pthread_mutex_lock(&g_res_mu);
    int ok = safe_gpu_commit4_locked(buffers, count, options);
    pthread_mutex_unlock(&g_res_mu);
    return ok;
}
static void safe_gpu_commit3(id<MTLCommandBuffer> cb) {
    pthread_mutex_lock(&g_res_mu);
    if (safe_gpu_preflight()) {
        if (safe_gpu_on()) { [cb addCompletedHandler:^(id<MTLCommandBuffer> done) { safe_gpu_feedback(done.error); }]; safe_gpu_started(); }
        [cb commit];
    }
    pthread_mutex_unlock(&g_res_mu);
}
static void safe_gpu_wait3(id<MTLCommandBuffer> cb) { if (!atomic_load(&g_safe_stopped)) [cb waitUntilCompleted]; }
static void safe_gpu_release_extra(void);
void mtl_safe_gpu_release(void) {
    // Never wait for GPU completion after a fault. The host has an independent
    // exit fallback if even removing residency blocks inside Metal.
    int locked = 0;
    for (int i = 0; i < 50 && !locked; i++) { locked = pthread_mutex_trylock(&g_res_mu) == 0; if (!locked) usleep(2000); }
    if (!locked) { MLOG("[RED] DM_SAFE_GPU: residency lock held; cannot release it before exit"); return; }
    [g_q removeResidencySet:g_res]; [g_q4 removeResidencySet:g_res]; [g_res endResidency];
    [g_res removeAllAllocations]; [g_res commit];
    [g_res_objects removeAllObjects]; g_res_dirty = g_res_grew = 0; atomic_store(&g_res_bytes, 0);
    safe_gpu_release_extra();
    pthread_mutex_unlock(&g_res_mu);
    MLOG("DM_SAFE_GPU: Metal residency released; no GPU drain attempted");
}

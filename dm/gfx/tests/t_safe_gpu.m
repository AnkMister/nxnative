// Exercise the production commit gates with fake queues and feedback. No GPU work.
#define nvn_game_fps nvn_game_fps_mtl_default
#include "../nvn/nvn_mtl.m"
#undef nvn_game_fps
#include <assert.h>
uint64_t g_t0_ns;
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static NSError *cbn_test_error(void) { return [NSError errorWithDomain:MTL4CommandQueueErrorDomain code:MTL4CommandQueueErrorTimeout userInfo:nil]; }
static int checks, failed; static volatile sig_atomic_t stops;
#define CHECK(c) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static void stopped(int sig) { (void)sig; stops++; }
@interface FakeDevice : NSObject
@property NSUInteger currentAllocatedSize;
@property id snapshotSet;
@property unsigned newSets, newTextures;
@property int pauseAt;
@property dispatch_semaphore_t entered, resume;
@end
@interface FakeFeedback : NSObject
@property NSError *error;
@end
@implementation FakeFeedback @end
@interface FakeOptions : NSObject
@property NSMutableArray *handlers;
@end
@implementation FakeOptions
- (instancetype)init { if ((self = [super init])) _handlers = [NSMutableArray array]; return self; }
- (void)addFeedbackHandler:(void (^)(id<MTL4CommitFeedback>))handler { [_handlers addObject:[handler copy]]; }
- (void)finish:(NSError *)error { FakeFeedback *f = [FakeFeedback new]; f.error = error; for (void (^handler)(id) in _handlers) handler(f); }
@end
@interface FakeQueue : NSObject
@property unsigned commits, removed, added, signals;
@property dispatch_semaphore_t entered, resume;
@end
@implementation FakeQueue
- (void)commit:(const id *)buffers count:(NSUInteger)n options:(id)o { (void)buffers; (void)n; (void)o; _commits++; }
- (void)commit:(const id *)buffers count:(NSUInteger)n { [self commit:buffers count:n options:nil]; }
- (void)removeResidencySet:(id)set { (void)set; _removed++; }
- (void)signalEvent:(id)event value:(uint64_t)value { (void)event; (void)value; _signals++; }
- (void)addResidencySet:(id)set { (void)set; _added++;
    if (_entered) { dispatch_semaphore_signal(_entered); dispatch_semaphore_wait(_resume, DISPATCH_TIME_FOREVER); } }
@end
@interface FakeSet : NSObject
@property unsigned commits, ends, removed, added, removedOne;
@property NSUInteger allocatedSize;
@end
@implementation FakeSet
- (void)commit { _commits++; }
- (void)endResidency { _ends++; }
- (void)removeAllAllocations { _removed++; }
- (void)addAllocation:(id)a { (void)a; _added++; }
- (void)removeAllocation:(id)a { (void)a; _removedOne++; }
@end
@interface FakeTexture : NSObject
@property NSUInteger width, height;
@property MTLPixelFormat pixelFormat;
@end
@implementation FakeTexture @end
@interface FakeLayer : NSObject
@property id residencySet;
@end
@implementation FakeLayer @end
@implementation FakeDevice
- (void)pause:(int)where {
    if (_pauseAt == where) { dispatch_semaphore_signal(_entered); dispatch_semaphore_wait(_resume, DISPATCH_TIME_FOREVER); }
}
- (id)newSharedEvent { return [NSObject new]; }
- (id)newResidencySetWithDescriptor:(id)desc error:(NSError **)error {
    (void)desc; (void)error; _newSets++; [self pause:1]; return _snapshotSet;
}
- (id)newCommandAllocator { return [NSObject new]; }
- (id)newCommandBuffer { return [NSObject new]; }
- (id)newTextureWithDescriptor:(MTLTextureDescriptor *)d {
    _newTextures++; [self pause:2];
    FakeTexture *t = [FakeTexture new]; t.width = d.width; t.height = d.height; t.pixelFormat = d.pixelFormat; return t;
}
@end
@interface FakeBuffer : NSObject
@property unsigned commits, waits;
@property (copy) void (^finished)(id);
@property NSError *error;
@end
@implementation FakeBuffer
- (void)commit { _commits++; }
- (void)waitUntilCompleted { _waits++; }
- (void)addCompletedHandler:(void (^)(id))handler { self.finished = handler; }
@end
static void auxiliary_stop_test(FakeDevice *device, FakeQueue *queue, FakeSet *mainSet, const char *mode) {
    FakeSet *snapshot = [FakeSet new]; device.snapshotSet = snapshot;
    FakeLayer *layer = [FakeLayer new]; layer.residencySet = [FakeSet new];
    FakeTexture *source = [FakeTexture new]; source.width = source.height = 1; source.pixelFormat = MTLPixelFormatRGBA8Unorm;
    if (!strcmp(mode, "alloc-stop")) {
        CHECK(snap_prepare(0, (id)source) != nil);
        source.width = 2; CHECK(snap_prepare(0, (id)source) != nil);
        source.width = 3; device.pauseAt = 2;
    } else device.pauseAt = 1;
    device.entered = dispatch_semaphore_create(0); device.resume = dispatch_semaphore_create(0);
    if (!strcmp(mode, "attach-stop")) { queue.entered = device.entered; queue.resume = device.resume; }
    dispatch_group_t group = dispatch_group_create();
    dispatch_group_async(group, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        if (!strcmp(mode, "attach-stop")) present_residency_attach((id)layer);
        else snap_prepare(0, (id)source);
    });
    CHECK(!dispatch_semaphore_wait(device.entered, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    safe_gpu_trip("concurrent auxiliary setup"); CHECK(atomic_load(&g_safe_stopped));
    dispatch_semaphore_t stopEntered = dispatch_semaphore_create(0);
    dispatch_group_async(group, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        dispatch_semaphore_signal(stopEntered); mtl_safe_gpu_release();
    });
    CHECK(!dispatch_semaphore_wait(stopEntered, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    CHECK(!mainSet.ends && !snapshot.ends && !queue.removed);
    dispatch_group_async(group, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        // Entries that were waiting for the CPU lock must also observe the stop.
        assert(!present_residency_attach((id)layer)); assert(!snap_prepare(1, (id)source));
    });
    dispatch_semaphore_signal(device.resume);
    CHECK(!dispatch_group_wait(group, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    CHECK(mainSet.ends == 1 && mainSet.removed == 1);
    if (strcmp(mode, "attach-stop")) CHECK(snapshot.ends == 1 && snapshot.removed == 1 && snapshot.added == device.newTextures);
    else CHECK(queue.added == 1 && queue.removed == 3);
    unsigned added = queue.added, sets = device.newSets, textures = device.newTextures, commits = snapshot.commits;
    CHECK(!present_residency_attach((id)layer)); CHECK(!snap_prepare(1, (id)source));
    CHECK(queue.added == added && device.newSets == sets && device.newTextures == textures && snapshot.commits == commits);
    if (!strcmp(mode, "alloc-stop")) CHECK(snapshot.removedOne == 1);
}
int main(int argc, const char **argv) { @autoreleasepool {
    signal(SIGTERM, stopped);
    setenv("DM_GPU_LOST_STOP", "0", 1);   // this fixture isolates safe-mode stop handling
    int off = argc > 1 && (!strcmp(argv[1], "off") || !strcmp(argv[1], "default"));
    if (argc > 1 && !strcmp(argv[1], "default")) unsetenv("DM_SAFE_GPU");
    else if (off) setenv("DM_SAFE_GPU", "0", 1);
    else setenv("DM_SAFE_GPU", "1", 1);   // the safety path is an explicit opt-in
    FakeDevice *device = [FakeDevice new]; g_dev = (id)device;
    FakeQueue *queue = [FakeQueue new]; g_q4 = (id)queue; g_q = (id)queue;
    FakeSet *set = [FakeSet new]; g_res = (id)set;
    g_res_objects = [NSHashTable hashTableWithOptions:NSPointerFunctionsWeakMemory];
    FakeBuffer *buffer = [FakeBuffer new]; id<MTL4CommandBuffer> cb = (id)buffer;
    if (argc > 1 && strstr(argv[1], "-stop")) {
        if (!strcmp(argv[1], "lock-stop")) {
            pthread_mutex_lock(&g_res_mu);
            uint64_t start = bp_now(); mtl_safe_gpu_release();
            CHECK(bp_now() - start < 500ull * NSEC_PER_MSEC); CHECK(atomic_load(&g_safe_stopped)); CHECK(!set.ends && !queue.removed);
            pthread_mutex_unlock(&g_res_mu);
            CHECK(!present_residency_attach((id)[FakeLayer new])); CHECK(!snap_prepare(0, (id)[FakeTexture new]));
        } else auxiliary_stop_test(device, queue, set, argv[1]);
        printf("safe GPU %s: %d checks, %d failed\n", argv[1], checks, failed); return failed != 0;
    }
    if (off) {
        CHECK(!safe_gpu_on()); safe_gpu_feedback(cbn_test_error());
        CHECK(!atomic_load(&g_safe_stopped) && !stops);
        safe_gpu_commit4(&cb, 1, nil); CHECK(queue.commits == 1);
    } else {
        CHECK(safe_gpu_on());
        CHECK(safe_gpu_cap(1000) == 700);
        CHECK(safe_gpu_wired_cap(10ull << 30, 16ull << 30) == 13ull << 30);
        CHECK(!safe_gpu_wired_cap(1, 1));
        g_safe_limit = 700; g_safe_wired_limit = 1000;
        CHECK(safe_gpu_budget(699, 999)); CHECK(!safe_gpu_budget(700, 0)); CHECK(!safe_gpu_budget(0, 1000));
        g_safe_wired_limit = UINT64_MAX;   // synthetic cap, independent of this Mac's load
        FakeOptions *options = [FakeOptions new];
        CHECK(safe_gpu_commit4(&cb, 1, (id)options) && queue.commits == 1);
        CHECK(atomic_load(&g_safe_pending) == 1);
        uint64_t t = atomic_load(&g_safe_progress);
        CHECK(!safe_gpu_stalled(t + 10ull * NSEC_PER_SEC - 1)); CHECK(safe_gpu_stalled(t + 10ull * NSEC_PER_SEC));
        [options finish:nil]; CHECK(!atomic_load(&g_safe_pending) && !atomic_load(&g_safe_stopped));
        safe_gpu_commit3((id)buffer); CHECK(buffer.commits == 1);
        buffer.finished(buffer); CHECK(!atomic_load(&g_safe_pending));
        if (argc > 1 && !strcmp(argv[1], "memory")) {
            atomic_store(&g_res_bytes, 700); g_res_dirty = g_res_grew = 1;
            res_commit(); CHECK(!set.commits);   // pending additions count before a residency commit
        } else if (argc > 1 && !strcmp(argv[1], "set")) {
            set.allocatedSize = 700; g_guard.evict = 600; g_guard.stop = g_guard.wall = 700;
            g_res_dirty = g_res_grew = 1; res_commit(); CHECK(!set.commits);
        } else if (argc > 1 && !strcmp(argv[1], "watchdog")) {
            safe_gpu_started(); atomic_store(&g_safe_progress, clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - 11ull * NSEC_PER_SEC); safe_gpu_tick();
        } else if (argc > 1 && !strcmp(argv[1], "legacy")) {
            buffer.error = [NSError errorWithDomain:MTLCommandBufferErrorDomain code:MTLCommandBufferErrorPageFault userInfo:nil];
            safe_gpu_commit3((id)buffer); buffer.finished(buffer);
        } else if (argc > 1 && !strcmp(argv[1], "hook")) {
            safe_gpu_feedback(cbn_test_error());   // the production completion-error hook
        } else {
            FakeOptions *bad = [FakeOptions new]; safe_gpu_commit4(&cb, 1, (id)bad);
            NSError *error = argc > 1 && !strcmp(argv[1], "ignored")
                ? [NSError errorWithDomain:MTL4CommandQueueErrorDomain code:MTL4CommandQueueErrorAccessRevoked userInfo:nil] : cbn_test_error();
            [bad finish:error];
        }
        CHECK(atomic_load(&g_safe_stopped) && stops == 1);
        unsigned commits = queue.commits, legacy = buffer.commits;
        CHECK(!safe_gpu_commit4(&cb, 1, nil));
        safe_gpu_commit3((id)buffer); safe_gpu_wait3((id)buffer);
        CHECK(queue.commits == commits && buffer.commits == legacy && !buffer.waits);
        rec_t record = {.op = RO_COMMIT_REAL}; record.a[1] = rec_obj(buffer); rec_exec(&record); CFBridgingRelease((void *)(uintptr_t)record.a[1]);
        CHECK(queue.commits == commits);   // queued before the fault, executed afterwards
        rec_t signal = {.op = RO_SIGNAL}; rec_exec(&signal); rec_signal(nil, 1);
        CHECK(!queue.signals);   // a skipped submission must not enqueue its signal afterwards
        safe_gpu_trip("second error"); CHECK(stops == 1);
        mtl_safe_gpu_release();
        CHECK(queue.removed == 2 && set.ends == 1 && set.removed == 1 && set.commits == 1);
        CHECK(!atomic_load(&g_res_bytes));
        g_snap_v = 1; snap_drain();   // would touch the snapshot event or wait for a refused copy without the stop gate
        CHECK(!mtl_snap_acquire_wait());
        CHECK(!mtl_wait_at(100, UINT64_MAX, WS_SYNC)); mtl_drain();
    }
    printf("safe GPU %s: %d checks, %d failed\n", argc > 1 ? argv[1] : "hang", checks, failed);
    return failed != 0;
} }

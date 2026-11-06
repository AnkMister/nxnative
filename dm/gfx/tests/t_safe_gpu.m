// Exercise the production commit gates with fake queues and feedback. No GPU work.
#define nvn_game_fps nvn_game_fps_mtl_default
#include "../nvn/nvn_mtl.m"
#undef nvn_game_fps
uint64_t g_t0_ns;
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed; static volatile sig_atomic_t stops;
#define CHECK(c) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static void stopped(int sig) { (void)sig; stops++; }
@interface FakeDevice : NSObject
@property NSUInteger currentAllocatedSize;
@end
@implementation FakeDevice @end
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
@property unsigned commits, removed;
@end
@implementation FakeQueue
- (void)commit:(const id *)buffers count:(NSUInteger)n options:(id)o { (void)buffers; (void)n; (void)o; _commits++; }
- (void)commit:(const id *)buffers count:(NSUInteger)n { [self commit:buffers count:n options:nil]; }
- (void)removeResidencySet:(id)set { (void)set; _removed++; }
@end
@interface FakeSet : NSObject
@property unsigned commits, ends, removed;
@property NSUInteger allocatedSize;
@end
@implementation FakeSet
- (void)commit { _commits++; }
- (void)endResidency { _ends++; }
- (void)removeAllAllocations { _removed++; }
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
int main(int argc, const char **argv) { @autoreleasepool {
    signal(SIGTERM, stopped);
    if (argc > 1 && !strcmp(argv[1], "off")) setenv("DM_SAFE_GPU", "0", 1);
    else unsetenv("DM_SAFE_GPU");   // the Ocarina build defaults on
    FakeDevice *device = [FakeDevice new]; g_dev = (id)device;
    FakeQueue *queue = [FakeQueue new]; g_q4 = (id)queue; g_q = (id)queue;
    FakeSet *set = [FakeSet new]; g_res = (id)set;
    g_res_objects = [NSHashTable hashTableWithOptions:NSPointerFunctionsWeakMemory];
    FakeBuffer *buffer = [FakeBuffer new]; id<MTL4CommandBuffer> cb = (id)buffer;
    if (argc > 1 && !strcmp(argv[1], "off")) {
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
            cbn_entry e = {.serial = 1}; atomic_store(&g_cbn_test, 1); cbn_failed(&e, nil);
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
        safe_gpu_trip("second error"); CHECK(stops == 1);
        mtl_safe_gpu_release();
        CHECK(queue.removed == 2 && set.ends == 1 && set.removed == 1 && set.commits == 1);
        CHECK(!atomic_load(&g_res_bytes));
        CHECK(!mtl_wait_at(100, UINT64_MAX, WS_SYNC)); mtl_drain();
    }
    printf("safe GPU %s: %d checks, %d failed\n", argc > 1 ? argv[1] : "hang", checks, failed);
    return failed != 0;
} }

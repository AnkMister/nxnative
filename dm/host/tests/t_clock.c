// Real clock state, gate dispatch and assembly entries. No game, renderer or loader required.
#include "../hle_os.c"
#include "../hle.c"
#include <assert.h>
#include <unistd.h>
#include <inttypes.h>

module_t *g_mod; int g_nmod;
struct dm_flags g_flag;
pthread_key_t g_key18;
__thread _Atomic int dm_host_work;
static int ounce;
int dm_sdk_ounce(void) { return ounce; }
void crash_watch_frame(void) {}
void dm_guest_clock_advanced(void) {}
void *guest_sym(const char *s) { (void)s; return NULL; }
void *module_sym(module_t *m, const char *s) { (void)m; (void)s; return NULL; }
void *hlecount_wrap(const char *k, const char *n, void *f) { (void)k; (void)n; return f; }
void thr_svc_enter(uint64_t *r, uint64_t a) { (void)r; (void)a; }
void thr_svc_leave(void) {}
void dm_spin_wait(uint64_t r, uint64_t a) { (void)r; (void)a; }
uint64_t svc_dispatch(int n, uint64_t *r, uint64_t a) { (void)n; (void)r; (void)a; abort(); }
void dm_gate_nested(uint64_t sp) { (void)sp; abort(); }
void dm_thread_returned(void) { abort(); }
extern uint64_t dm_gate_top[], test_gate_ret;
extern const char dm_gate_stubs[], dm_clock_stubs[];
uint64_t test_clock_read(void), test_gate_read(void);
void test_clock_abi(uint64_t *, unsigned char *);
static unsigned char gate_stack[1 << 20] __attribute__((aligned(16)));
static _Atomic int bg_started, bg_finished;
static void *background_read(void *unused) {
    (void)unused;
    atomic_store(&bg_started, 1);
    guest_clock_read_wait();
    atomic_store(&bg_finished, 1);
    return NULL;
}
static uint64_t ns_ticks(uint64_t n) { return ounce ? n / 32 : n * 12 / 625; }
static void abi_check(void) {
    uint64_t r[21], fpsr, fpcr; unsigned char q[512];
    __asm__ volatile("mrs %0, fpsr\n mrs %1, fpcr" : "=r"(fpsr), "=r"(fpcr));
    test_clock_abi(r, q);
    for (int i = 1; i < 18; ++i) assert(r[i] == (unsigned)(100 + i));
    assert(r[18] == 0xa0000000);
    assert(r[19] == fpsr && r[20] == fpcr);
    for (unsigned i = 0; i < sizeof q; ++i) assert(q[i] == 0x5a);
}
static void dispatch_check(void) {
    assert(!pthread_key_create(&g_key18, NULL));
    const char *kinds[] = {"clock_cntpct", "clock_cntvct", "clock_cntfrq"};
    for (unsigned kind = 0; kind < 3; ++kind) for (unsigned n = 0; n < 32; ++n) {
        uint64_t regs[100], original[100], stack[2] = {123, 456};
        for (unsigned i = 0; i < 100; ++i) regs[i] = 1000 + i;
        regs[99] = (uintptr_t)stack; memcpy(original, regs, sizeof regs);
        uint64_t ret = 0x10000 + kind * 256 + n * 4;
        gate_register(ret, kinds[kind], (int)n, 0);
        uint64_t t = gate_dispatch(ret, regs);
        assert(t == (kind == 2 ? (ounce ? 31250000 : 19200000) : guest_ticks()));
        for (unsigned i = 0; i < 100; ++i) assert(regs[i] == (i == n && n < 29 && n != 18 ? t : original[i]));
        assert(stack[0] == (n == 29 ? t : 123));
        assert(stack[1] == (n == 30 ? t : 456));
        if (n == 18) assert((uintptr_t)pthread_getspecific(g_key18) == t);
    }
    pthread_key_delete(g_key18);
}
static void bench(void) {
    volatile uint64_t sink = 0;
    for (int run = 0; run < 10; ++run) {
        uint64_t (*read)(void) = run & 1 ? test_clock_read : test_gate_read;
        uint64_t start = clock_gettime_nsec_np(CLOCK_THREAD_CPUTIME_ID);
        for (int i = 0; i < 200000; ++i) sink = read();
        uint64_t elapsed = clock_gettime_nsec_np(CLOCK_THREAD_CPUTIME_ID) - start;
        printf("bench %s %.3f ns/read calls=200000 sink=%" PRIu64 "\n", run & 1 ? "fast" : "gate", elapsed / 200000., sink);
    }
}
int main(int argc, char **argv) {
    ounce = argc > 1 && !strcmp(argv[1], "ounce");
    assert(dm_clock_stubs - dm_gate_stubs == 16384);
    dm_gate_top[0] = (uintptr_t)(gate_stack + sizeof gate_stack);
    gate_register((uintptr_t)&test_gate_ret, "cntpct", 0, 0);
    // The first opt-in read falls back and prepares the shared state.
    uint64_t a = test_clock_read(), b = test_clock_read(); assert(b >= a);
    int fast_enabled = !getenv("DM_DETCLOCK") && !getenv("DM_CLOCK_STATS");
    assert(atomic_load(&dm_clock_state.enabled) == fast_enabled);
    for (int i = 0; i < 10000; ++i) {
        uint64_t lo = guest_ticks(), t = test_clock_read(), hi = guest_ticks();
        assert(lo <= t && t <= hi);
    }
    uint64_t n = guest_ns(); a = test_clock_read(); usleep(10000); b = test_clock_read();
    uint64_t elapsed = guest_ns() - n;
    assert(b - a > ns_ticks(elapsed) * 9 / 10 && b - a < ns_ticks(elapsed) * 11 / 10);
    abi_check();
    guest_clock_freeze(1);
    assert(!atomic_load(&dm_clock_state.enabled));
    a = test_clock_read(); usleep(3000); assert(test_clock_read() == a); abi_check();
    dispatch_check();
    guest_clock_freeze_for(2, 1); guest_clock_freeze(0);
    assert(test_clock_read() == a); guest_clock_freeze_for(2, 0);
    assert(test_clock_read() >= a && test_clock_read() - a < ns_ticks(1000000));
    guest_clock_freeze_for(1, 1);
    pthread_t th; assert(!pthread_create(&th, NULL, background_read, NULL));
    while (!atomic_load(&bg_started)) sched_yield();
    usleep(3000); assert(!atomic_load(&bg_finished));
    dm_host_work = 1; a = test_clock_read(); assert(test_clock_read() == a); dm_host_work = 0;
    guest_clock_freeze_for(1, 0); pthread_join(th, NULL); assert(atomic_load(&bg_finished));
    if (getenv("DM_DETCLOCK")) {
        dm_guest_frame_tick(); a = test_clock_read(); usleep(2000); assert(test_clock_read() == a);
        dm_guest_frame_tick(); assert(test_clock_read() == ns_ticks(atomic_load(&g_gdet)));
        guest_clock_freeze(1); a = test_clock_read(); dm_guest_frame_tick(); assert(test_clock_read() == a); guest_clock_freeze(0);
    } else if (!getenv("DM_CLOCK_STATS")) bench();
    puts("clock: monotonicity, scaling, freeze/resume, nested reasons, background wait, SIMD/GPR/flags passed");
    return 0;
}

#include "../hle_os.c"
#include <assert.h>
#include <dispatch/dispatch.h>

module_t *g_mod; int g_nmod;
__thread _Atomic int dm_host_work;
int dm_sdk_ounce(void) { return 1; }
void dm_guest_clock_advanced(void) {}
void crash_watch_frame(void) {}
void *module_sym(module_t *m, const char *n) { (void)m; (void)n; return NULL; }
void *guest_sym(const char *n) { (void)n; return NULL; }
static dispatch_semaphore_t entered, returned;
static void *read_clock(void *unused) {
    (void)unused;
    dispatch_semaphore_signal(entered);
    guest_clock_read_wait();
    dispatch_semaphore_signal(returned);
    return NULL;
}
int main(void) {
    unsetenv("DM_DETCLOCK");
    guest_clock_freeze_for(3, 1);
    assert(atomic_load(&g_gfz) && atomic_load(&g_gfz_bg));
    uint64_t frozen = guest_ns();
    entered = dispatch_semaphore_create(0); returned = dispatch_semaphore_create(0);
    pthread_t thread; assert(!pthread_create(&thread, NULL, read_clock, NULL));
    assert(!dispatch_semaphore_wait(entered, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    assert(dispatch_semaphore_wait(returned, dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_MSEC)));
    assert(guest_ns() == frozen);
    // Host GPU draining must still be able to read the frozen clock.
    dm_host_work = 1; guest_clock_read_wait(); dm_host_work = 0;
    guest_clock_freeze_for(1, 1);
    guest_clock_freeze_for(3, 0);
    assert(atomic_load(&g_gfz) && atomic_load(&g_gfz_bg));
    assert(dispatch_semaphore_wait(returned, dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_MSEC)));
    guest_clock_freeze_for(2, 1);
    guest_clock_freeze_for(1, 0);
    assert(!dispatch_semaphore_wait(returned, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    assert(!pthread_join(thread, NULL));
    assert(atomic_load(&g_gfz) && !atomic_load(&g_gfz_bg));
    assert(guest_ns() == frozen);
    guest_clock_freeze_for(2, 0);
    assert(!atomic_load(&g_gfz));
    assert(guest_ns() >= frozen && guest_ns() - frozen < 100000000ull);
    puts("eco clock: hidden pause blocks guest reads; host drain proceeds; background and keyboard freezes compose; resume is continuous PASS");
}

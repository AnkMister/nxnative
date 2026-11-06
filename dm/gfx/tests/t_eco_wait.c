#include "../nvn/nvn_eco.h"
#include <assert.h>
#include <dispatch/dispatch.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static dispatch_semaphore_t entered, returned;
static uint64_t clock_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec;
}
static void *waiter(void *unused) {
    (void)unused;
    uint64_t next = 0;
    if (nvn_eco_hidden_mode() == NVN_ECO_SLOW) nvn_eco_wait(&next);
    dispatch_semaphore_signal(entered);
    nvn_eco_wait(&next);
    dispatch_semaphore_signal(returned);
    return NULL;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    if (strcmp(argv[1], "off")) setenv("DM_ECO_HIDDEN", argv[1], 1);
    else unsetenv("DM_ECO_HIDDEN");
    unsetenv("DM_ECO_SAME_FRAME");
    assert(!nvn_eco_same_on());
    uint64_t generation = nvn_eco_surface();
    nvn_eco_set_hidden(1);
    assert(nvn_eco_surface() != generation);
    entered = dispatch_semaphore_create(0); returned = dispatch_semaphore_create(0);
    pthread_t thread; assert(!pthread_create(&thread, NULL, waiter, NULL));
    assert(!dispatch_semaphore_wait(entered, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    if (nvn_eco_hidden_mode()) {
        assert(dispatch_semaphore_wait(returned, dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_MSEC)));
        nvn_eco_set_hidden(0);
    }
    assert(!dispatch_semaphore_wait(returned, dispatch_time(DISPATCH_TIME_NOW, 2 * NSEC_PER_SEC)));
    assert(!pthread_join(thread, NULL));
    if (nvn_eco_hidden_mode() == NVN_ECO_SLOW) {
        nvn_eco_set_hidden(1);
        uint64_t next = 0; nvn_eco_wait(&next);
        uint64_t t0 = clock_ns(); nvn_eco_wait(&next);
        assert(clock_ns() - t0 >= 120000000ull);
    }
    printf("eco wait %s: blocking, wake on foreground and rate limit PASS\n", argv[1]);
}

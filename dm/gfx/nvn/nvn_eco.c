#include "nvn_eco.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>

static pthread_once_t once = PTHREAD_ONCE_INIT;
static int same_on;
static nvn_eco_mode mode;
static _Atomic int hidden;
static _Atomic uint64_t surface;
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
static void configure(void) {
    const char *s = getenv("DM_ECO_SAME_FRAME");
    same_on = s && !strcmp(s, "1");
    mode = nvn_eco_parse(getenv("DM_ECO_HIDDEN"));
}
int nvn_eco_same_on(void) { pthread_once(&once, configure); return same_on; }
nvn_eco_mode nvn_eco_hidden_mode(void) { pthread_once(&once, configure); return mode; }
int nvn_eco_is_hidden(void) { return atomic_load(&hidden); }
void nvn_eco_surface_changed(void) { atomic_fetch_add(&surface, 1); }
uint64_t nvn_eco_surface(void) { return atomic_load(&surface); }
void nvn_eco_set_hidden(int on) {
    pthread_mutex_lock(&mu);
    atomic_store(&hidden, on != 0);
    nvn_eco_surface_changed();
    pthread_cond_broadcast(&cv);
    pthread_mutex_unlock(&mu);
}
static uint64_t monotonic_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec;
}
void nvn_eco_wait(uint64_t *next) {
    nvn_eco_mode m = nvn_eco_hidden_mode();
    if (!m) return;
    pthread_mutex_lock(&mu);
    while (atomic_load(&hidden) && m == NVN_ECO_PAUSE) pthread_cond_wait(&cv, &mu);
    if (atomic_load(&hidden) && m == NVN_ECO_SLOW) {
        uint64_t now = monotonic_ns();
        while (atomic_load(&hidden) && *next > now) {
            uint64_t ns = *next - now;
            struct timespec dt = {(time_t)(ns / 1000000000ull), (long)(ns % 1000000000ull)};
            // Darwin's relative wait uses a monotonic interval, independent of wall clock changes.
            int err = pthread_cond_timedwait_relative_np(&cv, &mu, &dt);
            if (err && err != ETIMEDOUT) break;
            now = monotonic_ns();
        }
        *next = monotonic_ns() + 125000000ull;
    } else *next = 0;
    pthread_mutex_unlock(&mu);
}

#include <pthread.h>
static int observed_wait(pthread_cond_t *, pthread_mutex_t *);
#define pthread_cond_wait observed_wait
#include "../nvn/nvn_mtl.m"
#undef pthread_cond_wait
#include <assert.h>

static unsigned sleeps;
static pthread_cond_t ready = PTHREAD_COND_INITIALIZER;
static int observed_wait(pthread_cond_t *cv, pthread_mutex_t *mu) {
    if (cv == &g_ubc_done_cv) { sleeps++; pthread_cond_signal(&ready); }
    return pthread_cond_wait(cv, mu);
}

void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }

enum { WORDS = 65536, ROUNDS = 128 };
static uint32_t src[WORDS], dst[WORDS];
static void *consumer(void *p) { ubc_wait((uint64_t)(uintptr_t)p); return NULL; }

int main(void) {
    int expected = getenv("DM_ECO_COPY_WAIT") && !strcmp(getenv("DM_ECO_COPY_WAIT"), "1");
    assert(ubc_sleep_wait() == expected);
    for (unsigned r = 1; r <= ROUNDS; r++) {
        for (unsigned i = 0; i < WORDS; i++) src[i] = r * WORDS + i;
        uint64_t seq = ubc_push(dst, src, sizeof src);
        pthread_t a, b;
        assert(!pthread_create(&a, NULL, consumer, (void *)(uintptr_t)seq));
        assert(!pthread_create(&b, NULL, consumer, (void *)(uintptr_t)seq));
        ubc_wait(seq);
        pthread_join(a, NULL); pthread_join(b, NULL);
        assert(!memcmp(src, dst, sizeof src));
        ubc_wait(seq);   // already completed: no new work or signal is needed
    }

    // Hold completion publication behind the mutex after a real copy. The
    // consumer must sleep through a spurious wake and wake on publication.
    if (expected) {
        pthread_mutex_lock(&g_ubc_mu);
        unsigned before = sleeps;
        uint64_t next = atomic_load(&g_ubc_done) + 1;
        pthread_t a, b;
        assert(!pthread_create(&a, NULL, consumer, (void *)(uintptr_t)next));
        assert(!pthread_create(&b, NULL, consumer, (void *)(uintptr_t)next));
        while (sleeps < before + 2) pthread_cond_wait(&ready, &g_ubc_mu);
        pthread_cond_broadcast(&g_ubc_done_cv);
        while (sleeps < before + 4) pthread_cond_wait(&ready, &g_ubc_mu);
        atomic_store_explicit(&g_ubc_done, next, memory_order_release);
        pthread_cond_broadcast(&g_ubc_done_cv);
        pthread_mutex_unlock(&g_ubc_mu);
        pthread_join(a, NULL); pthread_join(b, NULL);
    }
    printf("t_ubc_wait: %d copy rounds, two concurrent consumers, eco=%d passed\n", ROUNDS, expected);
    return 0;
}

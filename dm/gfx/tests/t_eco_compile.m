#include "../nvn/nvn_mtl.m"
#include <assert.h>

void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }

int main(int argc, char **argv) { @autoreleasepool {
    assert(argc == 2);
    int cap = atoi(argv[1]);
    assert(eco_compile_workers(1) == 1);
    assert(eco_compile_workers(16) == (cap ? cap : 16));
    setenv("DM_PSO_PREPARE_THREADS", "12", 1);
    assert(prepare_workers() == (cap ? cap : 12));

    int pc = 0; size_t sz = sizeof pc;
    if (sysctlbyname("hw.perflevel0.physicalcpu", &pc, &sz, NULL, 0) || pc < 2) pc = 2;
    int n = MIN(pc / 2, 8); if (cap && n > cap) n = cap;
    dispatch_queue_t queues[8] = {0};
    for (int i = 0; i < 16; i++) {
        dispatch_queue_t q = pp_bg_queue();
        assert(dispatch_queue_get_qos_class(q, NULL) == QOS_CLASS_UTILITY);
        if (i < n) {
            for (int j = 0; j < i; j++) assert(q != queues[j]);
            queues[i] = q;
        } else assert(q == queues[i % n]);
    }

    unsigned admitted = 0; uint64_t keys[4] = {1, 2, 3, 4};
    pthread_mutex_lock(&g_pp_mu);
    for (int i = 0; i < 3; i++) {
        pso_key k = {.vs = &keys[i]}; uint32_t gen;
        admitted += pso_pend_slot(&k, 1, &gen) >= 0;
    }
    assert(admitted == (unsigned)(cap == 1 ? 1 : 2));
    pso_key demand = {.vs = &keys[3]}; uint32_t gen;
    assert(pso_pend_slot(&demand, 0, &gen) >= 0);
    pthread_mutex_unlock(&g_pp_mu);
    printf("t_eco_compile: cap=%d, prepare workers, utility queues, speculative admission and demand bypass passed\n", cap);
    return 0;
} }

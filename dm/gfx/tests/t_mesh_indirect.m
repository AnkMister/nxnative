// The NVN mesh argument is produced on the GPU, not in CPU-visible command
// memory at record time. Check the real replay converter's grid and base.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }

int main(void) { @autoreleasepool {
    setenv("DM_NVN_MESH_INDIRECT", "0", 1);
    p_draw disabled = {.prim=DM_PRIM_MESH_TASKS, .ind=16};
    assert(!ixc_wanted(&disabled, NULL));
    setenv("DM_NVN_MESH_INDIRECT", "1", 1);
    assert(ixc_wanted(&disabled, NULL));
    mtl_init(); size_t bytes = (size_t)getpagesize();
    uint32_t *guest = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
    assert(guest != MAP_FAILED); mtl_pool_add(guest, bytes);
    id<MTLBuffer> seed = [g_dev newBufferWithLength:32 options:MTLResourceStorageModeShared];
    const uint32_t input[] = {3, 17, 0, 23, IXC_CAP, 0, IXC_CAP + 1, 0}; memcpy(seed.contents, input, sizeof input); res_add(seed);
    void *buffer; uint64_t offset;
    assert(mtl_addr((uintptr_t)guest, sizeof input, &buffer, &offset));
    mtl_sub_begin();
    enc_b_copy_buffer(blit(), seed, 0, (__bridge id<MTLBuffer>)buffer, offset, sizeof input);
    const p_draw draw_3 = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)guest};
    const p_draw draw_0 = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)(guest + 2)};
    ixc_run(&draw_3, NULL); ixc_run(&draw_0, NULL);
    const ixc_ent *a = ixc_find(&draw_3, NULL), *b = ixc_find(&draw_0, NULL);
    assert(a && a->args && b && b->args && guest[0] == 3);
    id<MTLBuffer> converted = g_cur_arena->buf;
    size_t ao = (size_t)(a->args - converted.gpuAddress), bo = (size_t)(b->args - converted.gpuAddress);
    assert(ao + 20 <= converted.length && bo + 20 <= converted.length);
    // A deferred write to a third argument must be landed before snapshotting
    // the conversion epoch, so the GPU result is still found by the draw.
    const p_draw draw_queued = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)(guest + 4)};
    g_ubd[g_nubd++] = (ubd_ent){draw_queued.ind, draw_queued.ind + 8, seed.gpuAddress, 0, seed};
    ixc_run(&draw_queued, NULL);
    const ixc_ent *queued = ixc_find(&draw_queued, NULL);
    assert(queued && queued->args && !g_nubd);
    size_t qo = (size_t)(queued->args - converted.gpuAddress);
    assert(qo + 20 <= converted.length);
    const p_draw at_cap = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)(guest + 8)};
    const p_draw over_cap = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)(guest + 10)};
    const p_draw wrap = {.prim=DM_PRIM_MESH_TASKS, .ind=(uintptr_t)(guest + 12)};
    guest[8] = IXC_CAP; guest[9] = 0;
    guest[10] = IXC_CAP + 1; guest[11] = 0;
    guest[12] = 2; guest[13] = UINT32_MAX;
    ixc_run(&at_cap, NULL); ixc_run(&over_cap, NULL); ixc_run(&wrap, NULL);
    assert(ixc_find(&at_cap, NULL)->args);
    assert(!ixc_find(&over_cap, NULL)->args && !ixc_find(&wrap, NULL)->args);
    mtl_sub_commit(); mtl_drain();
    const uint32_t expected_3[] = {3, 1, 1, 0, 17}, expected_0[] = {0, 1, 1, 0, 23};
    assert(!memcmp((const uint8_t *)converted.contents + ao, expected_3, sizeof expected_3));
    assert(!memcmp((const uint8_t *)converted.contents + bo, expected_0, sizeof expected_0));
    assert(!memcmp((const uint8_t *)converted.contents + qo, expected_3, sizeof expected_3));
    res_remove(seed); mtl_pool_del(guest); mtl_drain(); munmap(guest, bytes);
    puts("GPU-written mesh arguments: grid, first task and zero-work dispatch, cap and overflow rejection PASS");
} return 0; }

#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(name, value) do { checks++; if (!(value)) { fprintf(stderr, "FAIL: %s\n", name); failed++; } } while (0)
static void upload_edges(id<MTLBuffer> input, id<MTLBuffer> output) {
    up_begin();
    for (unsigned i = 0; i < 2; i++) {
        size_t off; id<MTLBuffer> b = up_alloc(24u << 20, &off);
        enc_b_copy_buffer(g_up_ce, input, i * 256, b, off, 256);
        [g_up_ce barrierAfterEncoderStages:MTLStageBlit beforeEncoderStages:MTLStageBlit visibilityOptions:MTL4VisibilityOptionDevice];
        enc_b_copy_buffer(g_up_ce, b, off, output, i * 256, 256);
    }
    up_flush();
}
int main(void) { @autoreleasepool {
    mtl_init(); mtl_sub_begin();
    id<MTLBuffer> input = [g_dev newBufferWithLength:512 options:MTLResourceStorageModeShared];
    id<MTLBuffer> output = [g_dev newBufferWithLength:512 options:MTLResourceStorageModeShared];
    res_add(input); res_add(output);
    uint8_t expected[512];
    for (unsigned i = 0; i < sizeof expected; i++) expected[i] = (uint8_t)(i * 29 + 3);
    memcpy(input.contents, expected, sizeof expected);
    id<MTLSharedEvent> gate = [g_dev newSharedEvent];
    [g_q4 waitForEvent:gate value:1];
    unsigned slot = g_up_seq % 3;
    @autoreleasepool { upload_edges(input, output); }
    CHECK("both retained blocks allocated", g_up_slot_blk[slot] && g_up_slot_over[slot]);
    CHECK("upload still in flight behind gate", atomic_load(&g_up_alloc_busy[slot]));
    uint64_t last = g_up_slot_last[slot];
    g_sub_serial = last + UP_TRIM_AGE;
    up_trim();
    CHECK("busy slot keeps both blocks despite age", g_up_slot_blk[slot] && g_up_slot_over[slot]);
    gate.signaledValue = 1;
    CHECK("submission completes", mtl_wait(mtl_sub_commit(), 5000000000ull));
    mtl_drain();
    CHECK("GPU completed upload", !atomic_load(&g_up_alloc_busy[slot]));
    CHECK("GPU read correct staging bytes", !memcmp(output.contents, expected, sizeof expected));
    g_sub_serial = last + UP_TRIM_AGE - 1;
    up_trim();
    CHECK("recent idle slot keeps both blocks", g_up_slot_blk[slot] && g_up_slot_over[slot]);
    __weak id<MTLBuffer> primary = g_up_slot_blk[slot], overflow = g_up_slot_over[slot];
    size_t retained = g_up_slot_blk[slot].length + g_up_slot_over[slot].length;
    g_sub_serial++;
    up_trim();
    if (up_trim_on()) {
        CHECK("old idle blocks released", !g_up_slot_blk[slot] && !g_up_slot_over[slot]);
        CHECK("old blocks destroyed after leaving residency", !primary && !overflow);
        CHECK("allocation demand reset", g_up_slot_want[slot] == 0);
        CHECK("reclaimed byte count exact", g_up_trimmed == retained);
    } else {
        CHECK("default-off retains idle staging", g_up_slot_blk[slot] && g_up_slot_over[slot]);
        CHECK("default-off reports no trim", g_up_trimmed == 0);
    }
    // Reuse the trimmed slot, then validate later uploads too.
    g_up_seq += 2;
    mtl_sub_begin();
    memset(output.contents, 0, sizeof expected);
    @autoreleasepool { upload_edges(input, output); }
    CHECK("upload works after idle trim", mtl_wait(mtl_sub_commit(), 5000000000ull));
    mtl_drain();
    CHECK("later upload has exact pixels", !memcmp(output.contents, expected, sizeof expected));
    printf("t_upload_trim: %d checks, %d failed; trim %s, reclaimed %llu MiB\n", checks, failed,
           up_trim_on() ? "on" : "off", (unsigned long long)(g_up_trimmed >> 20));
    return failed != 0;
} }

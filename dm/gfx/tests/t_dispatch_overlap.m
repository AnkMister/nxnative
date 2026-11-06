// The game's dispatches in the copy encoder (dispatch_enc, DM_NVN_DISPATCH_OVERLAP): two with nothing between them and no barrier of the game's run side by side; a game barrier,
// a copy between them or a host dispatch keeps the barrier, as does the switch turned off
#import <Foundation/Foundation.h>
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }

static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s (line %d)\n", label, __LINE__); } } while (0)

@interface MeshRecorderProbe : NSObject
@property uint64_t address;
@property MTLSize objectSize, meshSize;
- (void)drawMeshThreadgroupsWithIndirectBuffer:(uint64_t)address threadsPerObjectThreadgroup:(MTLSize)objectSize threadsPerMeshThreadgroup:(MTLSize)meshSize;
@end
@implementation MeshRecorderProbe
- (void)drawMeshThreadgroupsWithIndirectBuffer:(uint64_t)address threadsPerObjectThreadgroup:(MTLSize)objectSize threadsPerMeshThreadgroup:(MTLSize)meshSize {
    self.address = address; self.objectSize = objectSize; self.meshSize = meshSize;
}
@end
static void mesh_recording(void) {
    rec_blk *saved = g_rb_cur, *block = calloc(1, sizeof *block);
    g_rb_cur = block;
    id encoder = [DmRecEnc new];
    [encoder drawMeshThreadgroupsWithIndirectBuffer:0x12345678ull threadsPerObjectThreadgroup:MTLSizeMake(32, 1, 1) threadsPerMeshThreadgroup:MTLSizeMake(64, 1, 1)];
    CHECK(block->n == 1 && block->r[0].op == RO_R_MESH_IND, "indirect mesh draw records one command");
    MeshRecorderProbe *probe = [MeshRecorderProbe new]; id savedEncoder = g_rx_enc; g_rx_enc = probe;
    rec_exec(&block->r[0]);
    CHECK(probe.address == 0x12345678ull && probe.objectSize.width == 32 && probe.meshSize.width == 64,
          "indirect mesh replay preserves address and threadgroup widths");
    g_rx_enc = savedEncoder; g_rb_cur = saved; free(block);
}

int main(int argc, const char **argv) { @autoreleasepool {
    mesh_recording();
    int on = argc == 1; (void)argv;
    if (on) setenv("DM_NVN_DISPATCH_OVERLAP", "1", 1);
    else unsetenv("DM_NVN_DISPATCH_OVERLAP");
    mtl_init();
    mtl_sub_begin();
    uint64_t b0 = g_blit_barriers;
    dispatch_enc(1);
    CHECK(g_blit_barriers == b0, "the first dispatch in the encoder needs no barrier");
    dispatch_enc(1); dispatch_enc(1);
    CHECK(g_blit_barriers == b0 + (on ? 0 : 2) && g_disp_beside == (on ? 2 : 0), "dispatches with nothing between them run side by side");
    g_cs_gbar = 1; dispatch_enc(1);
    CHECK(g_blit_barriers == b0 + (on ? 1 : 3) && !g_cs_gbar, "a game barrier between them keeps the barrier");
    blit_buf(0, 0, 0x1000, 0x2000); dispatch_enc(1);
    CHECK(g_blit_barriers == b0 + (on ? 3 : 5), "a copy after a dispatch waits for it, and the dispatch after the copy waits for the copy");
    uint64_t b1 = g_blit_barriers; dispatch_enc(0);
    CHECK(g_blit_barriers == b1 + 1, "a host dispatch is ordered as a copy is");
    uint64_t b2 = g_blit_barriers; dispatch_enc(1);
    CHECK(g_blit_barriers == b2 + 1, "a game dispatch after a host dispatch waits for it");
    CHECK(mtl_wait(mtl_sub_commit(), 5000000000ull) && !mtl_last_commit_error(), "the submission completes");
    printf("t_dispatch_overlap: %d checks, %d failed\n", checks, failed);
    return failed != 0;
} }

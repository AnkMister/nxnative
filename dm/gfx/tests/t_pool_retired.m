// A pool table (nvn_mtl.m pool_gpu, for handles traced to no slot) and IDs whose texture the game finalized (retired): with pool_skip_retired such an ID that holds no view gets the
// dummy and no Metal texture is made for it, while a live ID beside it keeps its texture; without the key the retired ID's texture is made again from its storage, as before.
// A retired ID over storage a live texture holds (the sharing table) keeps resolving to that texture with the key: nothing is made for it (Ocarina of Time draws through ~12,000 such IDs).
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(label, c) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s (line %d)\n", label, __LINE__); } } while (0)
enum { LIVE = 7, RETIRED = 8, TARGET = 9, SHARED = 10 };
// The table's entries for the two IDs, from a fresh walk (a registration generation bump makes pool_gpu build it again)
static uint64_t g_shared_e;
static void walk(uint64_t *live, uint64_t *retired, uint64_t *dummy) {
    g_reg_gen++;
    __unsafe_unretained id<MTLBuffer> b = nil;
    mtl_sub_begin();
    CHECK("pool table made", pool_gpu(0, MTLTextureType2D, NVN_DPF_FLOAT, 0, &b) != 0 && b);
    const uint64_t *e = (const uint64_t *)((const uint8_t *)b.contents + DMSH_POOL_HEAD);
    *live = e[LIVE]; *retired = e[RETIRED]; g_shared_e = e[SHARED]; *dummy = g_dummy_tex_rid[MTLTextureType2D % DMY_NT][NVN_DPF_FLOAT & 3];
    CHECK("submission completes", mtl_wait(mtl_sub_commit(), 5000000000ull)); CHECK("GPU has no error", !mtl_last_commit_error());
}
int main(void) { @autoreleasepool {
    mtl_init();
    size_t len = 65536; uint8_t *mem = NULL; if (posix_memalign((void **)&mem, (size_t)getpagesize(), len)) abort(); memset(mem, 0x40, len);
    mtl_pool_add(mem, len);
    pool_t pool = {.magic = MAGIC('P', 'O', 'O', 'L'), .mem = mem, .size = len};
    tex_t a = {.magic = MAGIC('T', 'E', 'X', 0), .has_layout = 1, .serial = 99801, .pool = &pool, .mem = mem};
    a.d = (nvn_texdesc){.target = NVN_TEXTURE_TARGET_2D, .format = NVN_FORMAT_RGBA8, .width = 16, .height = 16, .depth = 1, .levels = 1, .samples = 1}; nvn_tex_layout(&a.d, &a.L);
    tex_t r = a; r.serial++; r.mem = mem + 32768; r.off = 32768;
    // A texture made over its pool storage (not packaged: a render target, as the textures under Ocarina of Time's copied descriptors are) goes into the sharing table, and another
    // object over the same storage and description, finalized, is one of those copied descriptors
    tex_t tg = a; tg.serial += 2; tg.has_layout = 0; tg.mem = mem + 16384; tg.off = 16384;
    tex_t sh = tg; sh.serial++;
    mtl_tex_gpu_written(&pool, tg.mem, tg.L.size);   // the GPU renders into it: its storage is not taken as CPU-written content (tex_cpu_content)
    mtl_tex_init(&a); mtl_tex_init(&r); mtl_tex_init(&tg); mtl_tex_init(&sh);
    mtl_reg_tex(LIVE, &a, NULL); mtl_reg_tex(RETIRED, &r, NULL); mtl_reg_tex(TARGET, &tg, NULL); mtl_reg_tex(SHARED, &sh, NULL);
    mtl_tex_release(&r);   // nvnTextureFinalize: the ID stays registered, its views are dropped
    mtl_tex_release(&sh);
    CHECK("the copied descriptor's ID is retired and holds no view", g_treg[SHARED].retired && !g_treg[SHARED].view);
    CHECK("the finalized texture's ID is retired and holds no view", g_treg[RETIRED].retired && !g_treg[RETIRED].view);
    uint64_t live, ret, dummy;
    g_pool_skip_retired = 0;
    walk(&live, &ret, &dummy);
    CHECK("without the key: the live ID has its texture", live && live != dummy);
    CHECK("without the key: the retired ID's texture is made again", ret && ret != dummy);
    mtl_tex_release(&r);   // a second release changes nothing (its serial is no longer live); drop the view the walk made
    { os_unfair_lock_lock(&g_rmu); treg_drop_views(&g_treg[RETIRED]); treg_drop_views(&g_treg[SHARED]); os_unfair_lock_unlock(&g_rmu); }
    g_pool_skip_retired = 1;
    walk(&live, &ret, &dummy);
    CHECK("with the key: the live ID keeps its texture", live && live != dummy);
    CHECK("with the key: the retired ID gets the dummy", ret == dummy);
    CHECK("with the key: a retired ID over a live texture's storage keeps that texture", g_shared_e && g_shared_e != dummy);
    mtl_tex_release(&a); mtl_tex_release(&tg); mtl_pool_del(mem); mtl_drain(); free(mem);
    printf("t_pool_retired: %d checks, %d failed\n", checks, failed); return failed != 0;
}}

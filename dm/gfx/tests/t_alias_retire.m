// Shared textures no live texture object resolves to are retired when GPU memory runs short (nvn_mtl.m alias_retire_idle): the budget is DM_NVN_WS_MB, set tiny here.
// A texture a live object holds stays, an idle unreferenced one goes, a finalized descriptor over it then resolves to nothing, and a live object over it gets a new texture.
// "./t_alias_retire off" runs with DM_NVN_ALIAS_RETIRE=0: nothing is retired.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", label); } } while (0)

enum { POOL = 16 << 20 };
static tex_t target(pool_t *pool, uint64_t serial, int64_t off, unsigned w) {
    tex_t t = {.magic = MAGIC('T','E','X',0), .serial = serial, .pool = pool, .off = off, .mem = pool->mem + off};
    t.d = (nvn_texdesc){.target = NVN_TEXTURE_TARGET_2D, .format = NVN_FORMAT_RGBA8, .flags = NVN_TEXTURE_FLAGS_COMPRESSIBLE, .width = w, .height = w, .depth = 1, .levels = 1, .samples = 1};
    nvn_tex_layout(&t.d, &t.L); mtl_tex_init(&t); return t;
}
static const tex_t *lookup;
static void submissions(int n) { for (int i = 0; i < n; i++) { if (lookup) (void)tex_mtl(lookup); mtl_sub_commit(); mtl_drain(); mtl_sub_begin(); } dispatch_sync(g_feedback_q, ^{}); defer_drain(); }
static int in_table(id<MTLTexture> t) { pthread_mutex_lock(&g_smu); int r = alias_has(t); pthread_mutex_unlock(&g_smu); return r; }

int main(int argc, char **argv) { @autoreleasepool {
    int off = argc > 1 && !strcmp(argv[1], "off"), release = argc > 1 && !strcmp(argv[1], "release"), def = argc > 1 && !strcmp(argv[1], "default");
    CHECK(alias_budget(1000, 0, 700, 950) == 700, "retirement stays below the safe GPU cap");
    CHECK(alias_budget(1000, 2000, 0, 950) == 950, "a larger override cannot raise the existing guard limit");
    CHECK(alias_budget(1000, 500, 700, 950) == 500, "a smaller simulated working set is respected");
    CHECK(alias_budget(0, 500, 700, 950) == 0, "unknown working set does not permit retirement");
    setenv("DM_NVN_WS_MB", "1", 1);   // any residency set is past 85 % of it
    if (def) unsetenv("DM_NVN_ALIAS_RETIRE"); else setenv("DM_NVN_ALIAS_RETIRE", off ? "0" : "1", 1);
    setenv("DM_TEX_RELEASE", release ? "2" : "0", 1);
    setenv("DM_NVN_POOL_HEAP", "0", 1);   // a pool heap, if the build has one, would hold these textures' memory whatever the retirement does
    mtl_init();
    uint8_t *mem = aligned_alloc(1 << 16, POOL); memset(mem, 0, POOL);
    mtl_pool_add(mem, POOL);
    pool_t pool = {.magic = MAGIC('P','O','O','L'), .flags = NVN_MEMORY_POOL_FLAGS_CPU_NO_ACCESS | NVN_MEMORY_POOL_FLAGS_GPU_CACHED, .mem = mem, .size = POOL};
    @autoreleasepool {
    mtl_sub_begin();
    tex_t kept = target(&pool, 996000, 0, 256), left = target(&pool, 996001, 4 << 20, 256);
    id<MTLTexture> mk = tex_mtl(&kept), ml = tex_mtl(&left);
    CHECK(mk && ml && in_table(mk) && in_table(ml), "both render targets are shared textures");
    id<MTLTexture> view = [mk newTextureViewWithPixelFormat:mk.pixelFormat];
    CHECK(view && view.parentTexture == mk, "fixture has a real texture view");
    serial_put(996010, view); mtl_tex_release(&kept);
    lookup = &left;
    mtl_tex_release(&left);   // finalized: no live object resolves to it any more, as a scene the game left
    submissions(ALIAS_RETIRE + 2 * ALIAS_RETIRE_EVERY);
    CHECK(in_table(mk), "a texture held only through a live view stays");
    if (off || release || def) {
        CHECK(in_table(ml), "disabled retirement or destructive guest release preserves an idle texture");
    } else {
        CHECK(!in_table(ml), "an idle texture no live object resolves to is retired when memory runs short");
        CHECK(g_alias_idle >= 1, "the memory report counts it");
        tex_t stale = left; stale.serial = 996001;   // the finalized descriptor, as a texture pool walk resolves it
        CHECK(tex_mtl(&stale) == nil, "a finalized descriptor over a retired texture resolves to nothing, not a new texture");
        tex_t again = target(&pool, 996002, 4 << 20, 256);   // a live object over the retired storage and description
        id<MTLTexture> ma = tex_mtl(&again);
        CHECK(ma && ma != ml && in_table(ma), "a live object over a retired texture gets a new shared texture");
        mtl_tex_release(&again);
    }
    lookup = NULL; serial_del(996010); view = nil; mk = nil; ml = nil;
    mtl_alias_drop_pool(&pool);
    submissions(2);
    mtl_sub_commit(); mtl_drain();
    }
    free(mem);
    printf("t_alias_retire%s: %d checks, %d failed\n", off ? " (off)" : release ? " (release)" : def ? " (default)" : "", checks, failed); return failed != 0;
} }

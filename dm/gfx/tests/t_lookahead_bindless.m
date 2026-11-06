// The store lookahead (DM_NVN_TBDR=1) on draws whose textures are read through handles: an attachment that only a later
// bindless draw samples (a handle in a uniform buffer, TEXU, or an array of them, TEXA / TEXD, or a shader the reflection calls
// bindless or dynamic) must keep its store, while one that nothing reads before its next full clear
// still drops it. Builds a submission's command list, indexes it with the production mtl_sub_index and asks sdx_decide at the
// end of the first pass. No GPU work, no game shaders or files.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", label); } } while (0)

typedef struct { uint8_t p[4096]; size_t n; } chain;
static void emit(chain *c, unsigned op, const void *a, size_t n) {
    size_t sz = (8 + n + 7) & ~7ull; if (c->n + sz > sizeof c->p) abort();
    op_hdr h = {op, (uint32_t)sz}; memcpy(c->p + c->n, &h, 8);
    if (n) memcpy(c->p + c->n + 8, a, n); c->n += sz;
}
static tex_t target(uint64_t serial) {
    tex_t t = {.magic = MAGIC('T','E','X',0), .serial = serial};
    t.d = (nvn_texdesc){.target = NVN_TEXTURE_TARGET_2D, .format = NVN_FORMAT_RGBA8, .width = 8, .height = 8, .depth = 1, .levels = 1, .samples = 1};
    nvn_tex_layout(&t.d, &t.L); return t;
}
static void set_rt(chain *c, const tex_t *t) { p_set_rt r = {.n = 1}; r.color[0] = t; emit(c, OP_SET_RT, &r, sizeof r); }
static void bind(chain *c, const prog_t *p) { p_bind_program b = {p, 3}; emit(c, OP_BIND_PROGRAM, &b, sizeof b); }
static void tri(chain *c) { p_draw d = {.prim = NVN_DRAW_PRIMITIVE_TRIANGLES, .count = 3, .instances = 1}; emit(c, OP_DRAW, &d, sizeof d); }
static void clear(chain *c) { p_clear_color cl = {.index = 0, .mask = 0xf}; emit(c, OP_CLEAR_COLOR, &cl, sizeof cl); }

// A program whose fragment shader has one binding of the given kind (0: none); flag 1 = reflection bindless, 2 = dynamic
static void program(prog_t *pg, uint64_t serial, int kind, int flag) {
    pg->serial = serial;
    NvProg *p = [NvProg new]; p->sh[0] = [NvShader new]; p->sh[1] = [NvShader new];
    p->sh[0]->stage = 0; p->sh[1]->stage = 1;
    if (kind) { p->sh[1]->rf.nb = 1; p->sh[1]->rf.b[0] = (nvn_rbind){.kind = kind, .reg = 0}; }
    p->sh[1]->rf.bindless = flag == 1; p->sh[1]->rf.dyn = flag == 2;
    serial_put(serial, p);
}

// pass 1 draws A; pass 2 (target B) draws with `reader`; then A is attached again and cleared in full. The store decision of A at
// the end of pass 1: 2 = redundant (dropped), anything else = kept.
static int decide(const prog_t *reader, int dispatch, int clear_case) {
    static uint64_t ser = 600000; tex_t a = target(++ser), b = target(++ser);
    prog_t plain; program(&plain, ++ser, 0, 0);
    chain c = {0};
    set_rt(&c, &a); bind(&c, &plain); tri(&c);         // seq 0 1 2
    set_rt(&c, &b); p_bind_program bp = {reader, dispatch ? 32 : 3}; emit(&c, OP_BIND_PROGRAM, &bp, sizeof bp);
    if (dispatch) { p_dispatch d = {0}; emit(&c, OP_DISPATCH, &d, sizeof d); } else tri(&c); // seq 3 4 5
    set_rt(&c, &a);
    if (clear_case == 1 || clear_case == 5) { p_scissor sc = {0, 0, 4, 8}; emit(&c, OP_SCISSOR, &sc, sizeof sc); }
    if (clear_case == 2 || clear_case == 3 || clear_case == 4 || clear_case == 6) {
        p_render_cond rc = {.mode = clear_case == 3 ? 3 : 0}; emit(&c, OP_RENDER_COND, &rc, sizeof rc);
        if (clear_case == 4) { rc.mode = 2; emit(&c, OP_RENDER_COND, &rc, sizeof rc); }
    }
    if (clear_case >= 5) {
        p_set_rt r = {.depth = &a}; emit(&c, OP_SET_RT, &r, sizeof r);
        p_clear_ds ds = {.depth_mask = 1}; emit(&c, OP_CLEAR_DS, &ds, sizeof ds);
    } else clear(&c);
    tri(&c);                // seq 6 7 8
    emit(&c, OP_END, NULL, 0);
    state_reset(); memset(&R, 0, sizeof R);
    uint64_t h = (uint64_t)c.p; mtl_sub_index(&h, 1);
    CHECK(g_sdx_ok, "the index is available");
    g_exec_cur = g_sdx_op[3]; g_exec_seq = 4;
    g_nsd = 1; g_sd[0] = (sd_att){.ser = a.serial, .idx = 0, .depth = clear_case >= 5 ? 1 : 0};
    uint8_t st[SD_ATT_MAX] = {0};
    CHECK(sdx_decide(st), "the decision is made from the index");
    g_exec_cur = NULL; g_exec_seq = 0; g_nsd = 0;
    return st[0];
}

int main(void) {
    @autoreleasepool {
        setenv("DM_NVN_TBDR", "1", 1);
        CHECK(tbdr_on(), "lookahead on");
        prog_t none; program(&none, 700001, 0, 0);
        CHECK(!xv_on(), "unseen submissions retain stores by default");
        CHECK(decide(&none, 0, 0) == 2, "nothing reads A before its full clear: its store is dropped");
        prog_t slot; program(&slot, 700002, NVN_RB_TEX, 0);   // reads slot 0, which holds nothing: not A
        CHECK(decide(&slot, 0, 0) == 2, "a slot read of another texture leaves the store dropped");
        CHECK(decide(&none, 0, 1) == 8, "a partial scissor clear retains the earlier color store");
        CHECK(decide(&none, 0, 2) == 8, "a conditional clear cannot prove an overwrite");
        CHECK(decide(&none, 0, 3) == 8, "a disabled clear cannot prove an overwrite");
        CHECK(decide(&none, 0, 4) == 2, "unconditional enable restores the full-clear proof");
        CHECK(decide(&none, 0, 5) == 8, "a partial scissor clear retains the earlier depth store");
        CHECK(decide(&none, 0, 6) == 8, "Ocarina's conditional depth clear retains the earlier depth store");
        const int kinds[] = {NVN_RB_TEXU, NVN_RB_TEXA, NVN_RB_TEXD};
        const char *names[] = {"a handle in a uniform buffer (TEXU) keeps the store", "an array of handles (TEXA) keeps the store",
                               "a dynamic handle array (TEXD) keeps the store"};
        for (int i = 0; i < 3; i++) { prog_t p; program(&p, 700010 + i, kinds[i], 0); CHECK(decide(&p, 0, 0) == 4, names[i]); }
        prog_t bl; program(&bl, 700020, 0, 1); CHECK(decide(&bl, 0, 0) == 4, "a shader the reflection calls bindless keeps the store");
        prog_t dy; program(&dy, 700021, 0, 2); CHECK(decide(&dy, 0, 0) == 4, "a dynamic shader keeps the store");
        CHECK(decide(NULL, 0, 0) == 4, "an unknown draw program keeps the store");
        const char *pkinds[] = {"tex_pool", "img_ubo", "tbuf_ubo"};
        for (int i = 0; i < 3; i++) {
            prog_t pg; program(&pg, 700030 + i, 0, 0); NvProg *p = serial_get(pg.serial);
            NSDictionary *j = @{@"route": @"B", @"stage": @"ps", @"bindings": @[@{@"kind": @(pkinds[i]), @"msl_name": @"t", @"msl_type": @"texture2d<float>", @"elem": @"texture2d<float>", @"reg": @0, @"arg_id": @0}]};
            char err[160]; CHECK(!nvn_refl_from_json(j, &p->sh[1]->rf, err, sizeof err), "pool / UBO reflection converts");
            CHECK(decide(&pg, 0, 0) == 4, "parsed bindless reflection keeps every candidate stored");
            p->sh[5] = p->sh[1]; p->sh[1] = nil;
            CHECK(decide(&pg, 1, 0) == 4, "bindless compute reader keeps every candidate stored");
        }
    }
    printf("LOOKAHEAD_BINDLESS %d checks, %d failed\n", checks, failed);
    return failed != 0;
}

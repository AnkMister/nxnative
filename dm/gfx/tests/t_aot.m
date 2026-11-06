// Synthetic archives only. The Python test supplies libraries, exact descriptors
// and a small metal-tt archive. No game, guest code or rendering loop is run.
#include "../nvn/nvn_mtl.m"
uint64_t g_t0_ns;
int dm_guest_as_contains(uintptr_t address) { (void)address; return 0; }
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "AOT fixture failed line %d: %s\n", __LINE__, #x); return 1; } } while (0)
int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 4) { fprintf(stderr, "usage: t_aot <libraries> <archive> <seen>\n"); return 2; }
    setenv("DM_AOT", "1", 1); setenv("DM_AOT_STRICT", "1", 1); setenv("DM_PSO_BUNDLE", argv[2], 1);
    setenv("DM_PSO_ARCHIVE", "off", 1); setenv("DM_PSO_SEEN", argv[3], 1);
    setenv("DM_SHARPEN", "0.2", 1);
    g_dev = MTLCreateSystemDefaultDevice(); CHECK(g_dev); g_msl_dir = @(argv[1]); pso4_init(); CHECK(g_arch_bundle);
    // Exact keys must distinguish depth/stencil state; replay must restore it.
    MTLRenderPipelineDescriptor *ds = [MTLRenderPipelineDescriptor new];
    ds.vertexFunction = aot_function(lib_from_file([g_msl_dir stringByAppendingPathComponent:@"v_b.metallib"], nil), @"main0");
    NSDictionary *no_depth = aot_render_row(ds, 0);
    ds.depthAttachmentPixelFormat = MTLPixelFormatDepth32Float;
    ds.stencilAttachmentPixelFormat = MTLPixelFormatStencil8;
    NSDictionary *with_depth = aot_render_row(ds, 0);
    CHECK(![aot_bytes(no_depth) isEqual:aot_bytes(with_depth)]);
    MTL4RenderPipelineDescriptor *roundtrip = (id)aot_descriptor(with_depth);
    // Metal 4 pipelines keep depth/stencil attachment formats out of the compiler descriptor.
    CHECK(roundtrip != nil);
    uint64_t before = dm_aot_compiler_count(0); aot_prewarm(); CHECK(dm_aot_compiler_count(0) == before);
    NSData *data = [NSData dataWithContentsOfFile:[@(argv[2]) stringByAppendingPathComponent:@"aot.json"]];
    NSArray *rows = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil]; CHECK(rows.count >= 3);
    dm_aot_gameplay();
    for (NSDictionary *row in rows) { CHECK(aot_lookup(row, 0, nil)); aot_record(row); }
    CHECK(dm_aot_compiler_count(1) == 0);
    // The real helper descriptors, including HDR and sharpening, hit the
    // inventory loaded at startup without entering a compiler during gameplay.
    const MTLPixelFormat present_formats[] = {MTLPixelFormatRGBA8Unorm, MTLPixelFormatBGRA8Unorm, MTLPixelFormatRGB10A2Unorm, MTLPixelFormatRGBA16Float};
    for (unsigned i = 0; i < sizeof present_formats / sizeof *present_formats; i++) {
        present_pipeline(present_formats[i]); CHECK(g_blit_pso && g_sharp_pso);
    }
    CHECK(dm_aot_compiler_count(1) == 0);
    // Actual host library bytes must match the standalone helper compiler's bytes.
    NSError *e = nil; id<MTLLibrary> helper = host_lib("ixc", &e); CHECK(helper);
    CHECK(host_msl_compute(g_dev, helper, @"ixc_arrays", &e)); CHECK(dm_aot_compiler_count(1) == 0);
    // Recreate a learned render descriptor from ordinary functions: exact hit,
    // no base specialization. Changing color format produces a visible miss.
    MTLRenderPipelineDescriptor *d = [MTLRenderPipelineDescriptor new];
    d.vertexFunction = aot_function(lib_from_file([g_msl_dir stringByAppendingPathComponent:@"v_b.metallib"], &e), @"main0");
    d.fragmentFunction = aot_function(lib_from_file([g_msl_dir stringByAppendingPathComponent:@"f_b.metallib"], &e), @"main0");
    d.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA8Unorm; d.vertexDescriptor = [MTLVertexDescriptor new];
    CHECK(aot_lookup(aot_render_row(d, 0), 0, nil));
    d.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA16Float;
    CHECK(!aot_lookup(aot_render_row(d, 0), 0, nil));
    CHECK(aot_lookup(aot_render_row(d, 0), 1, &e)); CHECK(dm_aot_compiler_count(1) == 1);
    // New final state is learned even when it was not in the input inventory.
    aot_record(aot_render_row(d, 0));
    fprintf(stderr, "t_aot: archive-only startup, exact render/compute/mesh/helper hits; strict miss counted\n");
    return 0;
} }

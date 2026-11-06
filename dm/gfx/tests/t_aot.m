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
@interface MeshBaseFixture : NSObject { @public MTL4PipelineDescriptor *desc; } @end
@implementation MeshBaseFixture
- (MTL4PipelineDescriptor *)newRenderPipelineDescriptorForSpecialization { return desc; }
@end
int main(int argc, char **argv) { @autoreleasepool {
    int tool = mtl_pso_aot_tool(); if (tool) return tool < 0;
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
    // Produce the real native TSV ABI for build-time import, including the
    // mesh/object relationship. The importer must use the live producers.
    NSString *tsv = [@(argv[3]) stringByAppendingString:@".tsv"];
    FILE *manifest = fopen(tsv.fileSystemRepresentation, "w"); CHECK(manifest);
    NvShader *vkey = [NvShader new], *fkey = [NvShader new]; strcpy(vkey->key, "v_b"); strcpy(fkey->key, "f_b"); fkey->stage = 1;
    pso_key native = {0}; native.cfmt[0] = MTLPixelFormatRGBA8Unorm; native.samples = 1; native.chmask = 15;
    pso_skey sk; char hex[sizeof sk * 2 + 1]; pso_skey_from(&native, vkey, fkey, 0, NULL, &sk); pso_skey_hex(&sk, hex);
    fprintf(manifest, "R\t%s\nC\tc_b\n", hex);
    strcpy(vkey->key, "m_b"); vkey->stage = 4; pso_skey_from(&native, vkey, fkey, 0, NULL, &sk); pso_skey_hex(&sk, hex);
    fprintf(manifest, "M\tt_b\t%s\n", hex); CHECK(!fclose(manifest));
    // The real helper descriptors, including HDR and sharpening, hit the
    // inventory loaded at startup without entering a compiler during gameplay.
    const MTLPixelFormat present_formats[] = {MTLPixelFormatRGBA8Unorm, MTLPixelFormatBGRA8Unorm, MTLPixelFormatRGB10A2Unorm, MTLPixelFormatRGBA16Float};
    for (unsigned i = 0; i < sizeof present_formats / sizeof *present_formats; i++) {
        present_pipeline(present_formats[i]); CHECK(g_blit_pso && g_sharp_pso);
    }
    CHECK(dm_aot_compiler_count(1) == 0);

    // Constants are part of the portable identity; an archive lookup cannot
    // silently substitute another value or enter a synchronous compiler.
    id<MTLLibrary> qlib = lib_from_file([g_msl_dir stringByAppendingPathComponent:@"q_b.metallib"], nil);
    MTLFunctionConstantValues *cv = [MTLFunctionConstantValues new]; int value = 7; bool enabled = true;
    [cv setConstantValue:&value type:MTLDataTypeInt atIndex:0]; [cv setConstantValue:&enabled type:MTLDataTypeBool atIndex:32];
    MTLRenderPipelineDescriptor *qd = [MTLRenderPipelineDescriptor new]; qd.vertexFunction = ds.vertexFunction;
    qd.fragmentFunction = fn4_values(fn_spec(qlib, @"main0", cv, nil), @[@[@0,@"int",@7], @[@32,@"bool",@YES]]);
    qd.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA8Unorm; qd.vertexDescriptor = [MTLVertexDescriptor new];
    CHECK(aot_lookup(aot_render_row(qd, 0), 0, nil));
    fn4_values(qd.fragmentFunction, @[@[@0,@"int",@8], @[@32,@"bool",@YES]]);
    CHECK(!aot_lookup(aot_render_row(qd, 0), 1, nil)); CHECK(dm_aot_compiler_count(1) == 0);

    MTLMeshRenderPipelineDescriptor *mesh = [MTLMeshRenderPipelineDescriptor new];
    id<MTLLibrary> ml = lib_from_file([g_msl_dir stringByAppendingPathComponent:@"m_b.metallib"], nil);
    id<MTLLibrary> tl = lib_from_file([g_msl_dir stringByAppendingPathComponent:@"t_b.metallib"], nil);
    mesh.meshFunction = aot_function(ml, @"main0"); mesh.objectFunction = aot_function(tl, @"main0");
    mesh.fragmentFunction = aot_function(lib_from_file([g_msl_dir stringByAppendingPathComponent:@"f_b.metallib"], nil), @"main0");
    mesh.maxTotalThreadsPerMeshThreadgroup = mesh.maxTotalThreadsPerObjectThreadgroup = 1; mesh.payloadMemoryLength = 16;
    mesh.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA8Unorm;
    CHECK(!fn4_of(mesh.meshFunction)); CHECK(!fn4_of(mesh.objectFunction));
    CHECK(!pre_fn(ml, @"main0")); CHECK(!pre_fn(tl, @"main0"));
    CHECK([aot_ref(mesh.meshFunction)[0] isEqual:@"m_b"]);
    CHECK(aot_mesh(mesh, nil)); CHECK(dm_aot_compiler_count(1) == 0);
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
    // Even a legacy compile=1 caller must never compile inside exact lookup.
    CHECK(!aot_lookup(aot_render_row(d, 0), 1, &e)); CHECK(dm_aot_compiler_count(1) == 0);
    CHECK(aot_render(d, &e)); CHECK(dm_aot_compiler_count(1) == 1);
    // A mesh or stripped descriptor from a base must never enter vertex specialization.
    d.colorAttachments[0].pixelFormat = MTLPixelFormatRG8Unorm;
    pbase_key key; pbase_key_of(d, &key);
    MeshBaseFixture *base = [MeshBaseFixture new];
    MTL4MeshRenderPipelineDescriptor *md = [MTL4MeshRenderPipelineDescriptor new];
    for (int i = 0; i < 8; i++) pso_col4(md.colorAttachments[i], d.colorAttachments[i]);
    base->desc = md; hm_put_id(&g_pbase, &key, base);
    uint64_t counted = dm_aot_compiler_count(1);
    CHECK(pso_build_ex(d, nil, 0) == (id)base);
    md.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA8Unorm;
    CHECK(!pso_build_ex(d, nil, 0)); CHECK(dm_aot_compiler_count(1) == counted);
    MTL4RenderPipelineDescriptor *stripped = [MTL4RenderPipelineDescriptor new];
    for (int i = 0; i < 8; i++) pso_col4(stripped.colorAttachments[i], d.colorAttachments[i]);
    base->desc = stripped; CHECK(pso_build_ex(d, nil, 0) == (id)base);
    hm_del_id(&g_pbase, &key);
    // New final state is learned even when it was not in the input inventory.
    aot_record(aot_render_row(d, 0));
    fprintf(stderr, "t_aot: archive-only startup, exact render/compute/mesh/helper hits; strict miss counted\n");
    return 0;
} }

// NEW host work, absent from PR #1444. Plain BC1/BC4 colour attachments are
// decoded to a shadow and compressed back after the pass. Compression is lossy.
static int bcrt_on(void) { const char *e = getenv("DM_NVN_BCRT"); return e && !strcmp(e, "1"); }
static MTLPixelFormat bc_rt_format(id<MTLTexture> base, const view_t *v, int has_v) {
    if (!bcrt_on() || !base || base.sampleCount != 1 || base.textureType == MTLTextureType3D) return MTLPixelFormatInvalid;
    MTLPixelFormat pf = base.pixelFormat;
    if (has_v && v->set_format) {
        uint32_t fmt; uint8_t swz[4];
        if (!nvn_fmt_to_mtl(v->format, &fmt, swz) || tex_need_pfv(pf, (MTLPixelFormat)fmt)) return MTLPixelFormatInvalid;
        pf = (MTLPixelFormat)fmt;
    }
    if (pf == MTLPixelFormatBC1_RGBA) return MTLPixelFormatRGBA8Unorm;
    if (pf == MTLPixelFormatBC1_RGBA_sRGB) return MTLPixelFormatRGBA8Unorm_sRGB;
    if (pf == MTLPixelFormatBC4_RUnorm) return MTLPixelFormatR8Unorm;
    return MTLPixelFormatInvalid;
}
static id<MTLComputePipelineState> g_bc_ps[3]; static id<MTL4ArgumentTable> g_bc_at;
static int bc_rt_ready(void) {
    if (g_bc_at) return 1;
    NSError *error = nil; id<MTLLibrary> lib = host_lib("bc_encode", &error);
    NSString *names[] = {@"bc_decode", @"bc_encode_bc1", @"bc_encode_bc4"};
    for (int i = 0; i < 3; i++) {
        id<MTLFunction> f = lib ? aot_function(lib, names[i]) : nil;
        g_bc_ps[i] = f ? aot_compute(f, &error) : nil;
        if (!g_bc_ps[i]) { RED_ONCE(153, "BC render-target codec unavailable: %s", error.localizedDescription.UTF8String); return 0; }
    }
    MTL4ArgumentTableDescriptor *d = [MTL4ArgumentTableDescriptor new]; d.maxTextureBindCount = 2; d.maxBufferBindCount = 2;
    g_bc_at = rec_table([g_dev newArgumentTableWithDescriptor:d error:&error]);
    return g_bc_at != nil;
}
static int bc_rt_compute(int kind, id<MTLTexture> src, id<MTLTexture> dst, id<MTLBuffer> blocks, int srgb) {
    if (!bc_rt_ready() || !src || (!kind && !dst) || (kind && !blocks)) return 0;
    if (g_blit) { enc_b_end(g_blit); g_blit = nil; }
    id<MTLBuffer> params; size_t offset = arena_alloc(16, &params);
    *(uint32_t *)((uint8_t *)params.contents + offset) = (uint32_t)srgb;
    [g_bc_at setAddress:params.gpuAddress + offset atIndex:1];
    if (blocks) [g_bc_at setAddress:blocks.gpuAddress atIndex:0];
    [g_bc_at setTexture:src.gpuResourceID atIndex:0];
    if (dst) [g_bc_at setTexture:dst.gpuResourceID atIndex:1];
    id<MTL4ComputeCommandEncoder> ce = enc_c_begin(NULL); [ce setArgumentTable:g_bc_at]; [ce setComputePipelineState:g_bc_ps[kind]];
    NSUInteger w = kind ? (src.width + 3) / 4 : dst.width, h = kind ? (src.height + 3) / 4 : dst.height;
    [ce dispatchThreadgroups:MTLSizeMake((w + 7) / 8, (h + 7) / 8, 1) threadsPerThreadgroup:MTLSizeMake(8, 8, 1)];
    enc_c_end(ce); args_dirty_all();
    return 1;
}
// Attach exactly one mip and slice, including a cube face. Array-layer rendering
// is refused in rp_begin_ex_ because this shadow has only one layer.
static id<MTLTexture> bc_rt_slice(id<MTLTexture> base, NSUInteger level, NSUInteger slice, MTLPixelFormat pf) {
    id<MTLTexture> view = [base newTextureViewWithPixelFormat:pf textureType:MTLTextureType2D levels:NSMakeRange(level, 1) slices:NSMakeRange(slice, 1)];
    if (view) defer_obj_unref(view);
    return view;
}

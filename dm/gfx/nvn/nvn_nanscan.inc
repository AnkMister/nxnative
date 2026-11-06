// Scan in the submitting command buffer, between the store and the next pass.
// A separate queue/command buffer would observe later writes to the same target.
static int nan_on(void) {
    static int on = -1;
    if (on < 0) { const char *e = getenv("DM_NVN_NANSCAN"); on = e && atoi(e) == 1;
        if (on) MLOG("[nanscan] enabled; counts RGBA non-finite pixels after stored render passes; shader keys are candidates, not per-draw attribution"); }
    return on;
}
static void nan_note(MTL4RenderPassDescriptor *pd) {
    if (!nan_on()) return;
    static uint64_t every;
    if (!every) { const char *e = getenv("DM_NVN_NANSCAN_EVERY"); every = e ? MAX(atoll(e), 1ll) : 1; }
    if (atomic_load(&g_cur_frame) % every) return;
    g_nan_pd = pd; g_nan_keys = [NSMutableOrderedSet orderedSet];
}
static void nan_after(void) {
    MTL4RenderPassDescriptor *pd = g_nan_pd; if (!pd) return;
    g_nan_pd = nil;
    NSString *keys = [g_nan_keys.array componentsJoinedByString:@","]; g_nan_keys = nil;
    uint64_t frame = atomic_load(&g_cur_frame), pass = g_stat_pass;
    static id<MTLComputePipelineState> ps[2]; static id<MTL4ArgumentTable> at; static int failed;
    if (failed) return;
    if (!ps[0]) {
        NSError *e = nil; id<MTLLibrary> lib = host_lib("nanscan", &e);
        ps[0] = [g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"scan"] error:&e];
        ps[1] = [g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"scan_ms"] error:&e];
        MTL4ArgumentTableDescriptor *ad = [MTL4ArgumentTableDescriptor new]; ad.maxTextureBindCount = 1; ad.maxBufferBindCount = 1;
        at = rec_table([g_dev newArgumentTableWithDescriptor:ad error:&e]);
        if (!ps[0] || !ps[1] || !at) { failed = 1; MLOG("[RED] nanscan pipeline: %s", e.localizedDescription.UTF8String); return; }
    }
    for (int i = 0; i < 8; i++) {
        MTLRenderPassColorAttachmentDescriptor *a = pd.colorAttachments[i]; id<MTLTexture> t = a.texture;
        if (!t || !pf_is_float(t.pixelFormat)) continue; // Normalized/integer storage cannot hold NaN or Inf.
        uint64_t ser = R.rt.color[i] ? R.rt.color[i]->serial : 0;
        int ms = t.sampleCount > 1; MTLTextureType type = ms ? MTLTextureType2DMultisample : MTLTextureType2D;
        if (!(t.usage & MTLTextureUsageShaderRead) || t.storageMode == MTLStorageModeMemoryless ||
            t.textureType == MTLTextureType3D || a.storeAction == MTLStoreActionDontCare || a.storeAction == MTLStoreActionMultisampleResolve) {
            MLOG("[nanscan] skip frame=%llu pass=%llu c=%d ser=%llu reason=unreadable-or-discarded-target", frame, pass, i, ser); continue;
        }
        NSUInteger layers = MAX(pd.renderTargetArrayLength, 1ul);
        for (NSUInteger layer = a.slice; layer < a.slice + layers; layer++) {
            id<MTLTexture> v = t;
            if (t.textureType != type || a.level || layer)
                v = [t newTextureViewWithPixelFormat:t.pixelFormat textureType:type levels:NSMakeRange(a.level, 1) slices:NSMakeRange(layer, 1)];
            if (!v) { MLOG("[RED] nanscan view frame=%llu pass=%llu c=%d ser=%llu layer=%lu", frame, pass, i, ser, (unsigned long)layer); continue; }
            NSUInteger tx = (v.width + 15) / 16, ty = (v.height + 15) / 16, n = tx * ty, pixels = v.width * v.height;
            id<MTLBuffer> b = [g_dev newBufferWithLength:n * sizeof(uint32_t) options:MTLResourceStorageModeShared];
            if (!b) { MLOG("[RED] nanscan count allocation failed"); continue; }
            memset(b.contents, 0xff, b.length);
            res_add(b);
            if (g_blit) { enc_b_end(g_blit); g_blit = nil; }
            id<MTL4ComputeCommandEncoder> ce = (id<MTL4ComputeCommandEncoder>)enc_c_begin(NULL);
            [ce setArgumentTable:at]; [at setTexture:v.gpuResourceID atIndex:0]; [at setAddress:b.gpuAddress atIndex:0];
            enc_c_pso(ce, ps[ms]); enc_c_dispatch(ce, MTLSizeMake(tx, ty, 1), MTLSizeMake(16, 16, 1)); enc_c_end(ce);
            args_dirty_all();
            NSUInteger lv = a.level;
            [g_commit_blocks addObject:^{
                const uint32_t *counts = b.contents; uint64_t bad = 0;
                for (NSUInteger k = 0; k < n; k++) {
                    if (counts[k] > 256) { MLOG("[RED] nanscan incomplete readback frame=%llu pass=%llu c=%d", frame, pass, i); return; }
                    bad += counts[k];
                }
                MLOG("[nanscan] frame=%llu pass=%llu c=%d ser=%llu lv=%lu layer=%lu nonfinite=%llu pixels=%lu keys=%s",
                     frame, pass, i, ser, (unsigned long)lv, (unsigned long)layer, bad, (unsigned long)pixels, keys.length ? keys.UTF8String : "-");
            }];
            defer_obj_release(b);
            if (v != t) defer_obj_unref(v);
        }
    }
}

// Exact, portable descriptors shared by the offline planner and startup loader.
// Default off. Unknown function constants/diagnostic source stay on the old path.
static os_unfair_lock g_aot_lock = OS_UNFAIR_LOCK_INIT;
static NSMutableDictionary<NSData *, id> *g_aot_ps;
static NSMutableSet<NSData *> *g_aot_seen;
static NSData *aot_bytes(NSDictionary *j) { return [NSJSONSerialization dataWithJSONObject:j options:NSJSONWritingSortedKeys error:nil]; }
static NSArray *aot_ref(id<MTLFunction> fn) {
    MTL4FunctionDescriptor *fd = fn4_of(fn);
    if (![fd isKindOfClass:MTL4LibraryFunctionDescriptor.class]) return nil;
    MTL4LibraryFunctionDescriptor *f = (id)fd;
    if (!f.library.label.length || fn.functionConstantsDictionary.count) return nil;
    return @[f.library.label, f.name];
}
static NSDictionary *aot_compute_row(id<MTLFunction> fn) {
    NSArray *f = aot_ref(fn); return f ? @{@"version": @1, @"chain": @(DMSH_CHAIN), @"class": @"compute", @"compute": f} : nil;
}
static NSDictionary *aot_render_row(id d, int mesh) {
    NSArray *v = aot_ref(mesh ? [d meshFunction] : [d vertexFunction]), *f = aot_ref([d fragmentFunction]);
    if (!v || ([d fragmentFunction] && !f)) return nil;
    NSMutableDictionary *j = [@{@"version": @1, @"chain": @(DMSH_CHAIN), @"class": mesh ? @"mesh" : @"render",
        mesh ? @"mesh" : @"vertex": v, @"samples": @([d rasterSampleCount]), @"a2c": @([d isAlphaToCoverageEnabled]), @"raster": @([d isRasterizationEnabled])} mutableCopy];
    if (f) j[@"fragment"] = f;
    NSMutableArray *colors = [NSMutableArray array];
    for (int i = 0; i < 8; i++) { MTLRenderPipelineColorAttachmentDescriptor *c = mesh ? ((MTLMeshRenderPipelineDescriptor *)d).colorAttachments[i] : ((MTLRenderPipelineDescriptor *)d).colorAttachments[i];
        [colors addObject:@[@(c.pixelFormat), @(c.writeMask), @(c.blendingEnabled), @(c.sourceRGBBlendFactor), @(c.destinationRGBBlendFactor),
            @(c.rgbBlendOperation), @(c.sourceAlphaBlendFactor), @(c.destinationAlphaBlendFactor), @(c.alphaBlendOperation)]]; }
    j[@"colors"] = colors;
    if (mesh) {
        MTLMeshRenderPipelineDescriptor *m = d; NSArray *t = aot_ref(m.objectFunction);
        if (m.objectFunction && !t) return nil; if (t) j[@"object"] = t;
        j[@"mesh_threads"] = @(m.maxTotalThreadsPerMeshThreadgroup); j[@"object_threads"] = @(m.maxTotalThreadsPerObjectThreadgroup);
        j[@"payload"] = @(m.payloadMemoryLength); j[@"mesh_grid"] = @(m.maxTotalThreadgroupsPerMeshGrid);
        j[@"mesh_multiple"] = @(m.meshThreadgroupSizeIsMultipleOfThreadExecutionWidth); j[@"object_multiple"] = @(m.objectThreadgroupSizeIsMultipleOfThreadExecutionWidth);
    } else {
        MTLRenderPipelineDescriptor *r = d; j[@"topology"] = @(r.inputPrimitiveTopology); j[@"amp"] = @(r.maxVertexAmplificationCount);
        NSMutableArray *attrs = [NSMutableArray array], *layouts = [NSMutableArray array];
        for (int i = 0; r.vertexDescriptor && i < 31; i++) { MTLVertexAttributeDescriptor *a = r.vertexDescriptor.attributes[i]; MTLVertexBufferLayoutDescriptor *l = r.vertexDescriptor.layouts[i];
            [attrs addObject:@[@(a.format), @(a.offset), @(a.bufferIndex)]]; [layouts addObject:@[@(l.stride), @(l.stepFunction), @(l.stepRate)]]; }
        j[@"attrs"] = attrs; j[@"layouts"] = layouts;
    }
    return j;
}
static MTL4FunctionDescriptor *aot_load_ref(NSArray *ref) {
    if (ref.count != 2 || ![ref[0] isKindOfClass:NSString.class] || ![ref[1] isKindOfClass:NSString.class]) return nil;
    NSString *name = ref[0]; if ([name containsString:@"/"] || [name containsString:@".."] || !name.length) return nil;
    id<MTLLibrary> lib = [name hasPrefix:@"host:"] ? host_lib([name substringFromIndex:5].UTF8String, nil) : lib_from_file([g_msl_dir stringByAppendingPathComponent:[name stringByAppendingPathExtension:@"metallib"]], nil);
    if (!lib) return nil;
    MTL4LibraryFunctionDescriptor *f = [MTL4LibraryFunctionDescriptor new]; f.library = lib; f.name = ref[1]; return f;
}
static MTL4PipelineDescriptor *aot_descriptor(NSDictionary *j) {
    if ([j[@"version"] intValue] != 1 || ![j[@"chain"] isEqual:@(DMSH_CHAIN)]) return nil;
    NSString *kind = j[@"class"];
    if ([kind isEqual:@"compute"]) { MTL4ComputePipelineDescriptor *d = [MTL4ComputePipelineDescriptor new]; d.computeFunctionDescriptor = aot_load_ref(j[@"compute"]); return d.computeFunctionDescriptor ? d : nil; }
    int mesh = [kind isEqual:@"mesh"]; if (!mesh && ![kind isEqual:@"render"]) return nil;
    id d = mesh ? [MTL4MeshRenderPipelineDescriptor new] : [MTL4RenderPipelineDescriptor new];
    MTL4FunctionDescriptor *v = aot_load_ref(j[mesh ? @"mesh" : @"vertex"]), *f = j[@"fragment"] ? aot_load_ref(j[@"fragment"]) : nil;
    if (!v || (j[@"fragment"] && !f)) return nil;
    if (mesh) { MTL4MeshRenderPipelineDescriptor *m = d; m.meshFunctionDescriptor = v; m.fragmentFunctionDescriptor = f;
        if (j[@"object"] && !(m.objectFunctionDescriptor = aot_load_ref(j[@"object"]))) return nil;
        m.maxTotalThreadsPerMeshThreadgroup = [j[@"mesh_threads"] unsignedIntegerValue]; m.maxTotalThreadsPerObjectThreadgroup = [j[@"object_threads"] unsignedIntegerValue];
        m.payloadMemoryLength = [j[@"payload"] unsignedIntegerValue]; m.maxTotalThreadgroupsPerMeshGrid = [j[@"mesh_grid"] unsignedIntegerValue];
        m.meshThreadgroupSizeIsMultipleOfThreadExecutionWidth = [j[@"mesh_multiple"] boolValue]; m.objectThreadgroupSizeIsMultipleOfThreadExecutionWidth = [j[@"object_multiple"] boolValue];
    } else { MTL4RenderPipelineDescriptor *r = d; r.vertexFunctionDescriptor = v; r.fragmentFunctionDescriptor = f;
        r.inputPrimitiveTopology = [j[@"topology"] unsignedIntegerValue]; r.maxVertexAmplificationCount = [j[@"amp"] unsignedIntegerValue];
        NSArray *attrs = j[@"attrs"], *layouts = j[@"layouts"]; if (attrs.count != layouts.count || attrs.count > 31) return nil;
        if (attrs.count) { MTLVertexDescriptor *vd = [MTLVertexDescriptor new];
            for (NSUInteger i = 0; i < attrs.count; i++) { NSArray *a = attrs[i], *l = layouts[i]; if (a.count != 3 || l.count != 3) return nil;
                vd.attributes[i].format = [a[0] unsignedIntegerValue]; vd.attributes[i].offset = [a[1] unsignedIntegerValue]; vd.attributes[i].bufferIndex = [a[2] unsignedIntegerValue];
                vd.layouts[i].stride = [l[0] unsignedIntegerValue]; vd.layouts[i].stepFunction = [l[1] unsignedIntegerValue]; vd.layouts[i].stepRate = [l[2] unsignedIntegerValue]; }
            r.vertexDescriptor = vd; }
    }
    [d setRasterSampleCount:[j[@"samples"] unsignedIntegerValue]]; [d setRasterizationEnabled:[j[@"raster"] boolValue]];
    [d setAlphaToCoverageState:[j[@"a2c"] boolValue] ? MTL4AlphaToCoverageStateEnabled : MTL4AlphaToCoverageStateDisabled];
    NSArray *colors = j[@"colors"]; if (colors.count != 8) return nil;
    for (int i = 0; i < 8; i++) { NSArray *c = colors[i]; if (c.count != 9) return nil; MTL4RenderPipelineColorAttachmentDescriptor *a = mesh ? ((MTL4MeshRenderPipelineDescriptor *)d).colorAttachments[i] : ((MTL4RenderPipelineDescriptor *)d).colorAttachments[i];
        if ([c[0] intValue] == -1) { a.pixelFormat = MTLPixelFormatUnspecialized; a.writeMask = MTLColorWriteMaskUnspecialized; a.blendingState = MTL4BlendStateUnspecialized;
            a.sourceRGBBlendFactor = a.destinationRGBBlendFactor = a.sourceAlphaBlendFactor = a.destinationAlphaBlendFactor = MTLBlendFactorUnspecialized;
            a.rgbBlendOperation = a.alphaBlendOperation = MTLBlendOperationUnspecialized; continue; }
        a.pixelFormat = [c[0] unsignedIntegerValue]; a.writeMask = [c[1] unsignedIntegerValue]; a.blendingState = [c[2] boolValue] ? MTL4BlendStateEnabled : MTL4BlendStateDisabled;
        a.sourceRGBBlendFactor = [c[3] unsignedIntegerValue]; a.destinationRGBBlendFactor = [c[4] unsignedIntegerValue]; a.rgbBlendOperation = [c[5] unsignedIntegerValue];
        a.sourceAlphaBlendFactor = [c[6] unsignedIntegerValue]; a.destinationAlphaBlendFactor = [c[7] unsignedIntegerValue]; a.alphaBlendOperation = [c[8] unsignedIntegerValue]; }
    return d;
}
static id aot_lookup(NSDictionary *j, int compile, NSError **error) {
    if (!j) return nil;
    NSData *key = aot_bytes(j); os_unfair_lock_lock(&g_aot_lock); id ps = g_aot_ps[key]; os_unfair_lock_unlock(&g_aot_lock); if (ps) return ps;
    MTL4PipelineDescriptor *d = aot_descriptor(j); if (!d) return nil;
    int cs = [j[@"class"] isEqual:@"compute"];
    for (id<MTL4Archive> a in [g_arch4p arrayByAddingObjectsFromArray:g_arch4 ?: @[]]) {
        dm_aot_event([j[@"class"] UTF8String], nil, "archive lookup", 0);
        if (cs) ps = [a newComputePipelineStateWithDescriptor:(id)d error:nil]; else ps = [a newRenderPipelineStateWithDescriptor:d error:nil];
        if (ps) break;
    }
    if (!ps && compile && g_comp4) {
        dm_aot_event([j[@"class"] UTF8String], [[NSString alloc] initWithData:key encoding:NSUTF8StringEncoding], "exact archive miss", 1);
        if (cs) ps = [g_comp4 newComputePipelineStateWithDescriptor:(id)d compilerTaskOptions:nil error:error]; else ps = [g_comp4 newRenderPipelineStateWithDescriptor:d compilerTaskOptions:nil error:error];
    }
    if (ps) { os_unfair_lock_lock(&g_aot_lock); if (!g_aot_ps) g_aot_ps = [NSMutableDictionary dictionary]; g_aot_ps[key] = ps; os_unfair_lock_unlock(&g_aot_lock); }
    return ps;
}
static void aot_record(NSDictionary *j) {
    if (!dm_aot_on() || !j || [j[@"base"] boolValue]) return;
    NSData *key = aot_bytes(j); os_unfair_lock_lock(&g_aot_lock);
    const char *e = getenv("DM_PSO_SEEN"); NSString *user = pso_user_path(); NSString *path = e && *e ? @(e) : user ? [user.stringByDeletingLastPathComponent stringByAppendingPathComponent:@"pso_seen.jsonl"] : nil;
    if (!g_aot_seen) {
        g_aot_seen = [NSMutableSet set];
        NSString *text = path ? [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:nil] : nil;
        for (NSString *line in [text componentsSeparatedByString:@"\n"]) {
            NSData *data = [line dataUsingEncoding:NSUTF8StringEncoding];
            NSDictionary *old = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
            if ([old isKindOfClass:NSDictionary.class]) [g_aot_seen addObject:aot_bytes(old)];
        }
        if (!path) MLOG("[RED] AOT descriptor learning needs DM_PSO_SEEN or the per-game save directory");
    }
    if (![g_aot_seen containsObject:key]) {
        if (path) { FILE *f = fopen(path.fileSystemRepresentation, "a");
            if (f) { int ok = fwrite(key.bytes, 1, key.length, f) == key.length && fputc('\n', f) != EOF; if (fclose(f)) ok = 0; if (ok) [g_aot_seen addObject:key]; else MLOG("[RED] AOT descriptor write failed"); }
            else MLOG("[RED] AOT cannot open descriptor census %s", path.UTF8String); }
    }
    os_unfair_lock_unlock(&g_aot_lock);
}
static void aot_prewarm(void) {
    if (!dm_aot_on()) return;
    pso4_init();
    NSString *path = [g_bundle_dir stringByAppendingPathComponent:@"aot.json"];
    NSData *data = path ? [NSData dataWithContentsOfFile:path] : nil;
    NSArray *rows = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
    if (![rows isKindOfClass:NSArray.class]) { MLOG("[RED] AOT no packed descriptor inventory; gameplay coverage unknown"); return; }
    __block _Atomic unsigned misses = 0; __block _Atomic NSUInteger next = 0;
    dispatch_group_t group = dispatch_group_create();
    for (int i = 0; i < 4; i++) dispatch_group_async(group, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{ @autoreleasepool {
        for (;;) { NSUInteger n = atomic_fetch_add(&next, 1); if (n >= rows.count) break; if (!aot_lookup(rows[n], 0, nil)) atomic_fetch_add(&misses, 1); }
    } });
    dispatch_group_wait(group, DISPATCH_TIME_FOREVER);
    MLOG("%sAOT startup archive-only prewarm: %lu descriptors, %u misses (no compiler fallback)", misses ? "[RED] " : "", (unsigned long)rows.count, (unsigned)misses);
}
static id<MTLComputePipelineState> aot_compute(id<MTLFunction> f, NSError **e) {
    NSDictionary *j = aot_compute_row(f); if (dm_aot_on()) { pso4_init(); aot_record(j); id ps = aot_lookup(j, 1, e); if (ps) return ps; }
    dm_aot_event("compute/helper", j ? [[NSString alloc] initWithData:aot_bytes(j) encoding:NSUTF8StringEncoding] : f.description, "device fallback", 1);
    return [g_dev newComputePipelineStateWithFunction:f error:e];
}
static id<MTLRenderPipelineState> aot_render(MTLRenderPipelineDescriptor *d, NSError **e) {
    NSDictionary *j = aot_render_row(d, 0); if (dm_aot_on()) { pso4_init(); aot_record(j); id ps = aot_lookup(j, 1, e); if (ps) return ps; }
    dm_aot_event("render/helper", j ? [[NSString alloc] initWithData:aot_bytes(j) encoding:NSUTF8StringEncoding] : d.description, "device fallback", 1);
    return [g_dev newRenderPipelineStateWithDescriptor:d error:e];
}
static id<MTLRenderPipelineState> aot_mesh(MTLMeshRenderPipelineDescriptor *d, NSError **e) {
    NSDictionary *j = aot_render_row(d, 1); if (dm_aot_on()) { pso4_init(); aot_record(j); id ps = aot_lookup(j, 1, e); if (ps) return ps; }
    dm_aot_event("mesh", j ? [[NSString alloc] initWithData:aot_bytes(j) encoding:NSUTF8StringEncoding] : d.description, "device fallback", 1);
    return [g_dev newRenderPipelineStateWithMeshDescriptor:d options:MTLPipelineOptionNone reflection:nil error:e];
}

// Used by the early deswizzle initialization as well as the regular prewarm.
id<MTLComputePipelineState> dm_aot_helper_compute(id<MTLDevice> dev, id<MTLLibrary> lib, NSString *entry) {
    if (dev != g_dev) return nil;
    pso4_init(); id<MTLFunction> f = aot_function(lib, entry);
    NSDictionary *j = aot_compute_row(f); aot_record(j); return aot_lookup(j, 0, nil);
}

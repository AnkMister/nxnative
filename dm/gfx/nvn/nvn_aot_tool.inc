// Build-time only. Reuse the live key decoder and descriptor producers rather
// than reproducing the native TSV ABI, blend conversion or function constants.
static int aot_import_stale(NSArray<NSString *> *c) {
    if (([c[0] isEqual:@"C"] || [c[0] isEqual:@"S"]) && c.count >= 2) return !warm_map_stage(c[1]);
    int mesh = [c[0] isEqual:@"M"]; pso_skey sk;
    if (mesh ? c.count != 3 || pso_mesh_skey_parse(c[2].UTF8String, &sk) : c.count != 2 || ![c[0] isEqual:@"R"] || pso_skey_parse(c[1].UTF8String, &sk)) return 0;
    NSString *vk = warm_key(sk.vs, sizeof sk.vs), *fk = warm_key(sk.fs, sizeof sk.fs);
    return !warm_map_stage(vk) || (fk.length && !warm_map_stage(fk)) || (mesh && ![c[1] isEqual:@"-"] && !warm_map_stage(c[1]));
}
static NSDictionary *aot_import_row(NSArray<NSString *> *c) {
    if ([c[0] isEqual:@"C"] && c.count == 2) {
        if (![warm_map_stage(c[1]) isEqual:@"compute"]) return nil;
        NvShader *cs = warm_shader(c[1], 5); return cs ? aot_compute_row(cs->fn) : nil;
    }
    int mesh = [c[0] isEqual:@"M"];
    if ((!mesh && (![c[0] isEqual:@"R"] || c.count != 2)) || (mesh && c.count != 3)) return nil;
    pso_skey sk;
    if (mesh ? pso_mesh_skey_parse(c[2].UTF8String, &sk) : pso_skey_parse(c[1].UTF8String, &sk)) return nil;
    NSString *vk = warm_key(sk.vs, sizeof sk.vs), *fk = warm_key(sk.fs, sizeof sk.fs);
    if (!vk.length || !warm_map_stage(vk) || (fk.length && !warm_map_stage(fk))) return nil;
    if (![warm_map_stage(vk) isEqual:mesh ? @"mesh" : @"vertex"] || (fk.length && ![warm_map_stage(fk) isEqual:@"pixel"])) return nil;
    NvShader *vs = warm_shader(vk, sk.vs_stage), *fs = fk.length ? warm_shader(fk, sk.fs_stage) : nil;
    if (!vs || (fk.length && !fs)) return nil;
    if (mesh) {
        NvShader *ts = [c[1] isEqual:@"-"] ? nil : warm_shader(c[1], 3);
        if (![c[1] isEqual:@"-"] && (!ts || ![warm_map_stage(c[1]) isEqual:@"task"])) return nil;
        if (vs->stage != 4 || vs->mesh_kind != 2 || (fs && fs->stage != 1) ||
            (ts ? (ts->stage != 3 || ts->mesh_kind != 1 || vs->mesh_notask) : !vs->mesh_notask)) return nil;
        return aot_render_row(mtk_desc(&sk.k, ts, vs, fs), 1);
    }
    if (vs->stage != 0 || (fs && fs->stage != 1)) return nil;
    id<MTLFunction> fn = nil;
    if (sk.fz) {
        if (sk.fz_desc.kind != 1 || !fs) return nil;
        int fx[32]; for (int i = 0; i < 32; i++) fx[i] = sk.fz_desc.fx[i];
        fn = bf_fn(fs, fx, sk.fz_desc.fbmask, sk.k.lmap); if (!fn) return nil;
    }
    pso_key k = sk.k; k.vs = (__bridge void *)vs; k.fs = (__bridge void *)fs; k.fsfn = (__bridge void *)fn;
    return aot_render_row(pso_desc(&k, vs, fs, fn, sk.merged), 0);
}

int mtl_pso_aot_tool(void) { @autoreleasepool {
    const char *mode = getenv("DM_AOT_TOOL"); if (!mode) return 0;
    const char *input = getenv("DM_AOT_INPUT"), *output = getenv("DM_AOT_OUTPUT");
    if (!input || !output || (strcmp(mode, "import") && strcmp(mode, "compile"))) { MLOG("[RED] AOT tool: import/compile requires input and output"); return -1; }
    // This entry runs before host_preload: never open guest modules or a game.
    setenv("DM_PSO_ARCHIVE", "off", 1); setenv("DM_PSO_BUNDLE", "off", 1); setenv("DM_PSO_MANIFEST", "off", 1);
    if (!dm_aot_on()) { MLOG("[RED] AOT tool needs DM_AOT=1"); return -1; }
    const char *chain = getenv("DM_AOT_CHAIN");
    if (!chain || strcmp(chain, DMSH_CHAIN)) { MLOG("[RED] AOT tool chain mismatch: planner %s / host %s", chain ?: "unset", DMSH_CHAIN); return -1; }
    g_dev = MTLCreateSystemDefaultDevice(); if (!g_dev) return -1;
    const char *arch = getenv("DM_AOT_ARCH");
    if (arch && strcmp(arch, g_dev.architecture.name.UTF8String)) { MLOG("[RED] native AOT compiler cannot target %s on %s", arch, g_dev.architecture.name.UTF8String); return -1; }
    shmap_read_once(); pso4_init();
    if (!strcmp(mode, "import")) {
        const char *zero = getenv("DM_PSO_PREBUILD_DEPTH"); atomic_store(&g_depth_zero, zero && !strcmp(zero, "zero"));
        NSString *text = [NSString stringWithContentsOfFile:@(input) encoding:NSUTF8StringEncoding error:nil]; if (!text) return -1;
        warm_load_begin(); NSMutableData *data = [NSMutableData data]; NSMutableSet *seen = [NSMutableSet set];
        unsigned n = 0, shaders = 0, line_no = 0;
        NSMutableArray *refused = [NSMutableArray array]; NSMutableString *accepted = [NSMutableString string];
        for (NSString *line in [text componentsSeparatedByString:@"\n"]) { @autoreleasepool {
            line_no++; if (!line.length || [line hasPrefix:@"#"]) continue;
            NSArray<NSString *> *c = [line componentsSeparatedByString:@"\t"];
            if (aot_import_stale(c)) { [refused addObject:@{@"line": @(line_no), @"kind": c[0], @"reason": @"shader key absent from current map", @"stale": @YES}]; continue; }
            const char *const stages[] = {"vertex", "pixel", "geometry", "task", "mesh", "compute"};
            if ([c[0] isEqual:@"S"] && c.count == 3 && c[2].length == 1 && [c[2] characterAtIndex:0] >= '0' && [c[2] characterAtIndex:0] <= '5'
                && [warm_map_stage(c[1]) isEqual:@(stages[[c[2] intValue]])]) { shaders++; [accepted appendFormat:@"%@\n", line]; continue; }
            NSDictionary *row = aot_import_row(c); NSData *key = row ? aot_bytes(row) : nil;
            if (!key) { [refused addObject:@{@"line": @(line_no), @"kind": c[0], @"reason": @"unsupported or invalid native state", @"stale": @NO}]; MLOG("[RED] AOT import cannot replay line %u (%s)", line_no, [c[0] UTF8String]); continue; }
            if (![seen containsObject:key]) { [data appendData:key]; [data appendBytes:"\n" length:1]; [seen addObject:key]; }
            n++;
            [accepted appendFormat:@"%@\n", line];
        } }
        MLOG("AOT import: %u pipeline rows, %lu unique descriptors, %u shader-only rows, %lu refused (see sidecar)", n, (unsigned long)seen.count, shaders, (unsigned long)refused.count);
        NSData *audit = [NSJSONSerialization dataWithJSONObject:refused options:NSJSONWritingSortedKeys error:nil];
        return [data writeToFile:@(output) atomically:YES] && [accepted writeToFile:[@(output) stringByAppendingString:@".manifest.tsv"] atomically:YES encoding:NSUTF8StringEncoding error:nil]
            && [audit writeToFile:[@(output) stringByAppendingString:@".refused.json"] atomically:YES] ? 1 : -1;
    }
    NSData *data = [NSData dataWithContentsOfFile:@(input)];
    NSArray *rows = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
    if (![rows isKindOfClass:NSArray.class] || !rows.count) return -1;
    MTL4PipelineDataSetSerializerDescriptor *sd = [MTL4PipelineDataSetSerializerDescriptor new]; sd.configuration = MTL4PipelineDataSetSerializerConfigurationCaptureBinaries;
    id<MTL4PipelineDataSetSerializer> serializer = [g_dev newPipelineDataSetSerializerWithDescriptor:sd];
    MTL4CompilerDescriptor *cd = [MTL4CompilerDescriptor new]; cd.pipelineDataSetSerializer = serializer;
    NSError *error = nil; id<MTL4Compiler> compiler = serializer ? [g_dev newCompilerWithDescriptor:cd error:&error] : nil;
    if (!compiler) return -1;
    for (NSDictionary *row in rows) { @autoreleasepool {
        MTL4PipelineDescriptor *d = aot_descriptor(row); id ps = nil;
        if (d) ps = [row[@"class"] isEqual:@"compute"] ? [compiler newComputePipelineStateWithDescriptor:(id)d compilerTaskOptions:nil error:&error]
            : [compiler newRenderPipelineStateWithDescriptor:d compilerTaskOptions:nil error:&error];
        if (!ps) {
            NSString *why = error.localizedDescription ?: @"invalid portable descriptor or function constants";
            NSData *audit = [NSJSONSerialization dataWithJSONObject:@{@"descriptor": row, @"error": why} options:NSJSONWritingSortedKeys error:nil];
            [audit writeToFile:[@(output) stringByAppendingString:@".refused.json"] atomically:YES];
            MLOG("[RED] AOT offline descriptor refused: %s (%s)", [[NSString alloc] initWithData:aot_bytes(row) encoding:NSUTF8StringEncoding].UTF8String, why.UTF8String); return -2;
        }
    } }
    if (![serializer serializeAsArchiveAndFlushToURL:[NSURL fileURLWithPath:@(output)] error:&error]) { MLOG("[RED] AOT offline archive write: %s", error.localizedDescription.UTF8String); return -1; }
    MLOG("AOT offline archive: %lu exact descriptors", (unsigned long)rows.count); return 1;
} }

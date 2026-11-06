#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
int main(int argc, char **argv) { @autoreleasepool {
    (void)argv;
    if (argc > 1) unsetenv("DM_NVN_NANSCAN"); else setenv("DM_NVN_NANSCAN","1",1); mtl_init(); mtl_set_frame(1); mtl_sub_begin();
    MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA16Float width:16 height:16 mipmapped:NO];
    d.storageMode=MTLStorageModePrivate;d.usage=MTLTextureUsageRenderTarget|MTLTextureUsageShaderRead;
    id<MTLTexture> t=[g_dev newTextureWithDescriptor:d];res_add(t);
    for(int i=0;i<2;i++) {
        MTL4RenderPassDescriptor *pd=[MTL4RenderPassDescriptor new];pd.colorAttachments[0].texture=t;
        pd.colorAttachments[0].loadAction=MTLLoadActionClear;pd.colorAttachments[0].storeAction=MTLStoreActionStore;
        pd.colorAttachments[0].clearColor=MTLClearColorMake(i ? 0 : INFINITY,0,0,1);
        nan_note(pd);g_stat_pass=i+1;
        enc_r_end(enc_r_begin(pd));nan_after();
    }
    dispatch_semaphore_t done=dispatch_semaphore_create(0);
    [g_commit_blocks addObject:^{ dispatch_semaphore_signal(done); }];
    uint64_t fence=mtl_sub_commit();int ok=mtl_wait(fence,5000000000ull);
    ok &= dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC)) == 0;
    // The log must contain pass 1 nonfinite=256 and pass 2 nonfinite=0 even
    // though the very same texture has been overwritten before completion.
    printf("nanscan pass timeline completed: %d\n",ok);return !ok;
} }

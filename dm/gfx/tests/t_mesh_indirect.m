// The upstream MDX GPU snapshot keeps NVN's count/first layout. The optional
// mesh validation refuses an excessive count or wrapping first+count on GPU.
#import <Metal/Metal.h>
#include <stdint.h>
#include <stdio.h>
#include "../nvn/host_msl.h"

typedef struct { uint64_t rec, cnt, out; uint32_t i, words; } Job;
int main(void) { @autoreleasepool {
    id<MTLDevice> dev = MTLCreateSystemDefaultDevice(); NSError *error = nil;
    id<MTLLibrary> lib = host_msl_lib(dev, nil, "mdx", &error);
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"mdx_mask"] error:&error];
    if (!ps) { fprintf(stderr, "mdx: %s\n", error.localizedDescription.UTF8String); return 1; }
    const uint32_t cases[][4] = {{0,0,1,0}, {1,17,1,1}, {49152,19,1,49152}, {49153,0,1,0},
        {2,UINT32_MAX,1,0}, {0,UINT32_MAX,1,0}, {UINT32_MAX,0,0,UINT32_MAX}};
    unsigned checks = 0, failed = 0;
    for (unsigned n = 0; n < sizeof cases / sizeof *cases; n++) {
        id<MTLBuffer> data = [dev newBufferWithLength:64 options:MTLResourceStorageModeShared];
        uint32_t *p = data.contents; p[0] = cases[n][0]; p[1] = cases[n][1];
        p[7] = 0xdeadbeef; Job job = {data.gpuAddress, data.gpuAddress, data.gpuAddress+16, cases[n][2], 0};
        id<MTLCommandQueue> queue = [dev newCommandQueue]; id<MTLCommandBuffer> cb = [queue commandBuffer];
        id<MTLComputeCommandEncoder> ce = [cb computeCommandEncoder]; [ce setComputePipelineState:ps];
        [ce setBytes:&job length:sizeof job atIndex:0]; [ce useResource:data usage:MTLResourceUsageRead|MTLResourceUsageWrite];
        [ce dispatchThreads:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(1,1,1)]; [ce endEncoding]; [cb commit]; [cb waitUntilCompleted];
#define CHECK(C) do { checks++; if (!(C)) { failed++; fprintf(stderr,"case %u failed: %s\n",n,#C); } } while(0)
        CHECK(cb.status == MTLCommandBufferStatusCompleted); CHECK(p[4] == cases[n][3]); CHECK(p[5] == 1 && p[6] == 1);
        CHECK(p[7] == 0xdeadbeef); CHECK(p[0] == cases[n][0] && p[1] == cases[n][1]);
#undef CHECK
    }
    printf("t_mesh_indirect: %u checks, %u failed\n", checks, failed); return failed != 0;
} }

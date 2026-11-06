#import <Metal/Metal.h>
#include <math.h>
#include <stdio.h>
#include "../nvn/host_msl.h"
static int checks, failed;
#define CHECK(c, msg) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", msg); } } while (0)
static void scan(id<MTLDevice> dev, id<MTLCommandQueue> q, id<MTLLibrary> lib, id<MTLTexture> t, unsigned want) {
    NSError *error = nil;
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:t.sampleCount > 1 ? @"scan_ms" : @"scan"] error:&error];
    CHECK(ps != nil, "production scan pipeline compiles"); if (!ps) return;
    NSUInteger tx=(t.width+15)/16, ty=(t.height+15)/16;
    id<MTLBuffer> b=[dev newBufferWithLength:tx*ty*4 options:MTLResourceStorageModeShared]; memset(b.contents,0xcd,b.length);
    id<MTLCommandBuffer> cb=[q commandBuffer]; id<MTLComputeCommandEncoder> ce=[cb computeCommandEncoder];
    [ce setComputePipelineState:ps]; [ce setTexture:t atIndex:0]; [ce setBuffer:b offset:0 atIndex:0];
    [ce dispatchThreadgroups:MTLSizeMake(tx,ty,1) threadsPerThreadgroup:MTLSizeMake(16,16,1)]; [ce endEncoding]; [cb commit]; [cb waitUntilCompleted];
    CHECK(cb.status == MTLCommandBufferStatusCompleted, "scan completes on GPU");
    unsigned sum=0; for (NSUInteger i=0;i<tx*ty;i++) sum+=((uint32_t*)b.contents)[i];
    CHECK(sum == want, "counts non-finite pixels once across channels and samples, including edge tiles");
}
int main(void) { @autoreleasepool {
    id<MTLDevice> dev=MTLCreateSystemDefaultDevice(); if (!dev) return 77;
    id<MTLCommandQueue> q=[dev newCommandQueue]; NSError *error=nil;
    id<MTLLibrary> lib=host_msl_lib(dev,nil,"nanscan",&error); CHECK(lib != nil,"loads production kernel"); if(!lib) return 1;
    MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA32Float width:19 height:17 mipmapped:NO];
    d.storageMode=MTLStorageModeShared;d.usage=MTLTextureUsageShaderRead;
    id<MTLTexture> t=[dev newTextureWithDescriptor:d]; float px[19*17*4];
    for (unsigned i=0;i<19*17*4;i++) px[i]=i%4 == 3 ? 1.f : -0.5f;
    [t replaceRegion:MTLRegionMake2D(0,0,19,17) mipmapLevel:0 withBytes:px bytesPerRow:19*16]; scan(dev,q,lib,t,0);
    px[0]=NAN; px[1]=INFINITY; px[4]=-INFINITY; px[(19*17-1)*4+3]=NAN;
    px[8]=__FLT_MAX__; px[12]=__FLT_MIN__; // finite extreme values must not count
    [t replaceRegion:MTLRegionMake2D(0,0,19,17) mipmapLevel:0 withBytes:px bytesPerRow:19*16]; scan(dev,q,lib,t,3);
    d.textureType=MTLTextureType2DArray;d.arrayLength=2;d.mipmapLevelCount=2;
    id<MTLTexture> a=[dev newTextureWithDescriptor:d];
    [a replaceRegion:MTLRegionMake2D(0,0,9,8) mipmapLevel:1 slice:1 withBytes:px bytesPerRow:9*16 bytesPerImage:9*8*16];
    id<MTLTexture> v=[a newTextureViewWithPixelFormat:d.pixelFormat textureType:MTLTextureType2D levels:NSMakeRange(1,1) slices:NSMakeRange(1,1)];
    scan(dev,q,lib,v,2);
    d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA16Float width:16 height:16 mipmapped:NO];
    d.textureType=MTLTextureType2DMultisample;d.sampleCount=4;d.storageMode=MTLStorageModePrivate;d.usage=MTLTextureUsageRenderTarget|MTLTextureUsageShaderRead;
    id<MTLTexture> ms=[dev newTextureWithDescriptor:d]; CHECK(ms != nil,"multisample test target allocated");
    MTLRenderPassDescriptor *rp=[MTLRenderPassDescriptor new];rp.colorAttachments[0].texture=ms;rp.colorAttachments[0].loadAction=MTLLoadActionClear;
    rp.colorAttachments[0].storeAction=MTLStoreActionStore;rp.colorAttachments[0].clearColor=MTLClearColorMake(INFINITY,0,0,1);
    id<MTLCommandBuffer> cb=[q commandBuffer];[[cb renderCommandEncoderWithDescriptor:rp] endEncoding];[cb commit];[cb waitUntilCompleted];
    scan(dev,q,lib,ms,256);
    printf("nanscan: %d checks, %d failed\n",checks,failed);return failed != 0;
} }

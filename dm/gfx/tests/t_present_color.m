#import <Metal/Metal.h>
#import <CoreGraphics/CoreGraphics.h>
#include <stdio.h>
#include "../nvn/host_msl.h"
static int checks, failed;
#define CHECK(c, msg) do { checks++; if (!(c)) { failed++; fprintf(stderr,"FAIL: %s\n",msg); } } while(0)
int main(void) { @autoreleasepool {
    id<MTLDevice> dev=MTLCreateSystemDefaultDevice();if(!dev) return 77;
    id<MTLCommandQueue> q=[dev newCommandQueue];NSError *error=nil;
    id<MTLLibrary> lib=host_msl_lib(dev,nil,"present",&error);
    MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:8 height:1 mipmapped:NO];
    d.storageMode=MTLStorageModeShared;d.usage=MTLTextureUsageShaderRead|MTLTextureUsageRenderTarget;
    id<MTLTexture> src=[dev newTextureWithDescriptor:d],out=[dev newTextureWithDescriptor:d];
    uint8_t bytes[32]={0,0,0,255,255,255,255,255,255,0,0,255,0,255,0,255,0,0,255,255,128,128,128,255,128,64,200,255,1,10,11,255};
    [src replaceRegion:MTLRegionMake2D(0,0,8,1) mipmapLevel:0 withBytes:bytes bytesPerRow:32];
    CGColorSpaceRef srgb=CGColorSpaceCreateWithName(kCGColorSpaceSRGB),p3=CGColorSpaceCreateWithName(kCGColorSpaceDisplayP3);
    for(int variant=0;variant<3;variant++) {
        MTLRenderPipelineDescriptor *pd=[MTLRenderPipelineDescriptor new];pd.vertexFunction=[lib newFunctionWithName:@"vs"];
        pd.fragmentFunction=[lib newFunctionWithName:variant == 2 ? @"sharp_p3" : variant ? @"fs_p3" : @"fs"];pd.colorAttachments[0].pixelFormat=d.pixelFormat;
        id<MTLRenderPipelineState> ps=[dev newRenderPipelineStateWithDescriptor:pd error:&error];CHECK(ps != nil,"present pipeline compiles");if(!ps) return 1;
        MTLRenderPassDescriptor *rp=[MTLRenderPassDescriptor new];rp.colorAttachments[0].texture=out;
        rp.colorAttachments[0].loadAction=MTLLoadActionDontCare;rp.colorAttachments[0].storeAction=MTLStoreActionStore;
        id<MTLCommandBuffer> cb=[q commandBuffer];id<MTLRenderCommandEncoder> e=[cb renderCommandEncoderWithDescriptor:rp];
        MTLSamplerDescriptor *sd=[MTLSamplerDescriptor new];id<MTLSamplerState> samp=[dev newSamplerStateWithDescriptor:sd];
        float crop[16]={0,0,1,1,.0625,.5,.9375,.5,1,0.125,1,0};
        [e setRenderPipelineState:ps];[e setFragmentTexture:src atIndex:0];[e setFragmentSamplerState:samp atIndex:0];[e setFragmentBytes:crop length:sizeof crop atIndex:0];
        [e drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:3];[e endEncoding];[cb commit];[cb waitUntilCompleted];
        CHECK(cb.status == MTLCommandBufferStatusCompleted,"present executes on GPU");
        uint8_t got[32];[out getBytes:got bytesPerRow:32 fromRegion:MTLRegionMake2D(0,0,8,1) mipmapLevel:0];
        for(int i=0;i<8;i++) {
            CGFloat components[4]={bytes[4*i]/255.,bytes[4*i+1]/255.,bytes[4*i+2]/255.,1};
            CGColorRef c=CGColorCreate(srgb,components),ref=CGColorCreateCopyByMatchingToColorSpace(variant?p3:srgb,kCGRenderingIntentRelativeColorimetric,c,NULL);
            CHECK(ref != nil,"ColorSync reference available");const CGFloat *v=CGColorGetComponents(ref);
            for(int k=0;k<3;k++) CHECK(abs((int)got[4*i+k]-(int)lround(v[k]*255))<=2,"GPU result matches independent ColorSync conversion within two code values");
            CHECK(got[4*i+3]==255,"opaque alpha unchanged");CGColorRelease(c);CGColorRelease(ref);
        }
    }
    CGColorSpaceRelease(srgb);CGColorSpaceRelease(p3);
    printf("present colour: %d checks, %d failed\n",checks,failed);return failed != 0;
} }

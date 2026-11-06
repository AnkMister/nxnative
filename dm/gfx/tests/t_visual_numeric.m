// Runs a translated numeric fixture without the host or game.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <stdio.h>
int main(int argc, char **argv) { @autoreleasepool {
    if (argc != 4) return 2;
    id<MTLDevice> dev = MTLCreateSystemDefaultDevice(); NSError *error = nil;
    id<MTLLibrary> lib = [dev newLibraryWithURL:[NSURL fileURLWithPath:@(argv[1])] error:&error];
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"main0"] error:&error];
    if (!ps) { fprintf(stderr, "%s\n", error.localizedDescription.UTF8String); return 1; }
    NSData *initial = [NSData dataWithContentsOfFile:@(argv[2])];
    id<MTLBuffer> output = [dev newBufferWithBytes:initial.bytes length:initial.length options:MTLResourceStorageModeShared];
    uint64_t address = output.gpuAddress;
    id<MTLBuffer> args = [dev newBufferWithBytes:&address length:8 options:MTLResourceStorageModeShared];
    id<MTLCommandQueue> q = [dev newCommandQueue]; id<MTLCommandBuffer> cb = [q commandBuffer];
    id<MTLComputeCommandEncoder> ce = [cb computeCommandEncoder]; [ce setComputePipelineState:ps];
    [ce setBuffer:args offset:0 atIndex:0]; [ce setBuffer:output offset:0 atIndex:30];
    [ce useResource:output usage:MTLResourceUsageRead | MTLResourceUsageWrite];
    [ce dispatchThreadgroups:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(strtoul(argv[3],NULL,10),1,1)];
    [ce endEncoding]; [cb commit]; [cb waitUntilCompleted];
    if (cb.status != MTLCommandBufferStatusCompleted) { fprintf(stderr,"%s\n",cb.error.localizedDescription.UTF8String); return 1; }
    fwrite(output.contents,1,initial.length,stdout);
    return 0;
} }

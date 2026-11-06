// Synthetic guest pool table for scalar/grouped shader comparisons. No host or game.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int main(int argc, const char **argv) { @autoreleasepool {
    if (argc != 3) return 2;
    id<MTLDevice> dev = MTLCreateSystemDefaultDevice();
    NSError *error = nil;
    id<MTLLibrary> lib = [dev newLibraryWithURL:[NSURL fileURLWithPath:@(argv[1])] error:&error];
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"main0"] error:&error];
    if (!ps) { fprintf(stderr, "%s\n", error.localizedDescription.UTF8String); return 1; }
    NSData *input = [NSData dataWithContentsOfFile:@(argv[2])];
    if (input.length < 24 || input.length % 8) return 2;
    const uint64_t *words = input.bytes;
    unsigned count = (unsigned)words[1];
    if (count > 4095 || input.length != (2 + 3 * count) * 8) return 2;
    id<MTLBuffer> table = [dev newBufferWithLength:4096*32 options:MTLResourceStorageModeShared];
    id<MTLBuffer> data = [dev newBufferWithLength:256 options:MTLResourceStorageModeShared];
    id<MTLBuffer> output = [dev newBufferWithLength:32 options:MTLResourceStorageModeShared];
    memset(table.contents, 0, table.length);
    uint64_t *rows = table.contents;
    for (unsigned i = 1; i <= count; i++) {
        rows[4*i] = words[2+3*(i-1)];
        rows[4*i+1] = words[3+3*(i-1)];
        rows[4*i+2] = data.gpuAddress + words[4+3*(i-1)] - rows[4*i];
    }
    for (unsigned i = count+1; i < 4096; i++) rows[4*i] = UINT64_MAX;
    for (unsigned i = 0; i < 64; i++) ((uint32_t*)data.contents)[i] = 0x81000000u + i;
    memcpy(output.contents, words, 8);
    uint64_t address = table.gpuAddress;
    id<MTLBuffer> args = [dev newBufferWithBytes:&address length:8 options:MTLResourceStorageModeShared];
    id<MTLCommandQueue> q = [dev newCommandQueue];
    id<MTLCommandBuffer> cb = [q commandBuffer];
    id<MTLComputeCommandEncoder> ce = [cb computeCommandEncoder];
    [ce setComputePipelineState:ps]; [ce setBuffer:args offset:0 atIndex:0]; [ce setBuffer:output offset:0 atIndex:30];
    [ce useResource:table usage:MTLResourceUsageRead]; [ce useResource:data usage:MTLResourceUsageRead];
    [ce dispatchThreadgroups:MTLSizeMake(1,1,1) threadsPerThreadgroup:MTLSizeMake(1,1,1)];
    [ce endEncoding]; [cb commit]; [cb waitUntilCompleted];
    if (cb.status != MTLCommandBufferStatusCompleted) { fprintf(stderr,"%s\n",cb.error.localizedDescription.UTF8String); return 1; }
    fwrite((uint32_t*)output.contents+4, 4, 4, stdout);
    return 0;
} }

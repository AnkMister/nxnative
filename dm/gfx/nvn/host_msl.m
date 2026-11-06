#import "host_msl.h"
#include "host_msl_gen.h"
#include <os/lock.h>
#include <string.h>
#include <time.h>
#include <stdatomic.h>
#include <stdlib.h>

#define HLOG(...) do { fprintf(stderr, "[dm] [msl] " __VA_ARGS__); fputc('\n', stderr); } while (0)

id<MTLLibrary> host_msl_lib(id<MTLDevice> dev, id<MTL4Compiler> comp, const char *name, NSError **e) {
    static os_unfair_lock lk = OS_UNFAIR_LOCK_INIT; static NSMutableDictionary<NSString *, id<MTLLibrary>> *libs; static int said;
    if (!dev || !name) return nil;
    NSString *key = [NSString stringWithFormat:@"%p/%s", (__bridge void *)dev, name];
    os_unfair_lock_lock(&lk);
    if (!libs) libs = [NSMutableDictionary dictionary];
    id<MTLLibrary> lib = libs[key];
    if (!said++) HLOG("host shader libraries: %lu, compiled for %s by %s", sizeof k_host_msl / sizeof *k_host_msl, HOST_MSL_SDK, HOST_MSL_COMPILER);
    os_unfair_lock_unlock(&lk);
    if (lib) return lib;
    int i = 0, n = (int)(sizeof k_host_msl / sizeof *k_host_msl);
    while (i < n && strcmp(k_host_msl[i].name, name)) i++;
    if (i == n) { HLOG("[RED] no host shader library %s (dm/gfx/msl/%s.metal)", name, name); return nil; }
    NSError *le = nil;
    if (k_host_msl[i].lib_len) {
        dispatch_data_t d = dispatch_data_create(k_host_msl[i].lib, k_host_msl[i].lib_len, NULL, ^{});   // static bytes: nothing to free
        lib = [dev newLibraryWithData:d error:&le];
    }
    if (!lib) {   // the build had no Metal compiler, or this system does not take the library: compile its source (through the MTLDevice, also from MTL4Compiler)
        uint64_t t0 = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
        NSString *src = @(k_host_msl[i].src);
        dm_aot_event("library-source", @(name), "host library fallback", 1);
        if (comp) { MTL4LibraryDescriptor *ld = [MTL4LibraryDescriptor new]; ld.source = src; lib = [comp newLibraryWithDescriptor:ld error:e]; }
        else lib = [dev newLibraryWithSource:src options:nil error:e];
        HLOG("[RED] host shader library %s %s: compiled from its source in %.1f ms%s", name,
             k_host_msl[i].lib_len ? [NSString stringWithFormat:@"did not load (%@)", le.localizedDescription].UTF8String : "was not compiled when the host was built (no Metal toolchain)",
             (clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - t0) / 1e6, lib ? "" : " and failed");
        if (!lib) return nil;
    }
    lib.label = [@"host:" stringByAppendingString:@(name)];
    os_unfair_lock_lock(&lk);
    id<MTLLibrary> had = libs[key]; if (had) lib = had; else libs[key] = lib;   // another thread made it meanwhile: one library per name
    os_unfair_lock_unlock(&lk);
    return lib;
}

static _Atomic int aot_play;
static _Atomic uint64_t aot_count[2][2], aot_dirty;
static uint64_t aot_last;
int dm_aot_on(void) { const char *s = getenv("DM_AOT"); return s && !strcmp(s, "1"); }
void dm_aot_summary(void) {
    static os_unfair_lock lock = OS_UNFAIR_LOCK_INIT;
    if (!atomic_load(&aot_dirty)) return;
    uint64_t now = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    os_unfair_lock_lock(&lock);
    const char *s = getenv("DM_AOT_LOG_SECONDS"); double sec = s ? atof(s) : 5;
    if (now - aot_last >= (uint64_t)((sec > 0 ? sec : 5) * 1e9) && atomic_exchange(&aot_dirty, 0)) {
        aot_last = now;
        HLOG("AOT totals startup compiler=%llu archive=%llu gameplay compiler=%llu archive=%llu (API entries)",
             (unsigned long long)atomic_load(&aot_count[0][1]), (unsigned long long)atomic_load(&aot_count[0][0]),
             (unsigned long long)atomic_load(&aot_count[1][1]), (unsigned long long)atomic_load(&aot_count[1][0]));
    }
    os_unfair_lock_unlock(&lock);
}
void dm_aot_event(const char *kind, NSString *identity, const char *reason, int compiler) {
    int play = atomic_load(&aot_play); atomic_fetch_add(&aot_count[play][!!compiler], 1); atomic_store(&aot_dirty, 1);
    if (!compiler) return;   // archive loads never invoke the compiler; summarize without a line per load
    // Hash stable UTF-8 identity bytes, never Objective-C pointer hashes.
    const unsigned char *p = (const unsigned char *)(identity.UTF8String ?: "unknown"); uint64_t h = 14695981039346656037ull;
    for (; *p; p++) { h ^= *p; h *= 1099511628211ull; }
    const char *strict = getenv("DM_AOT_STRICT");
    HLOG("%sAOT phase=%s class=%s descriptor=%016llx reason=%s identity=%s",
         play && compiler && strict && !strcmp(strict, "1") ? "[RED] " : "", play ? "gameplay" : "startup", kind,
         (unsigned long long)h, reason, identity.UTF8String ?: "unknown");
    dm_aot_summary();
}
void dm_aot_gameplay(void) { if (!atomic_exchange(&aot_play, 1)) { HLOG("AOT phase=gameplay (first game present; includes title/loading screens)"); } dm_aot_summary(); }
uint64_t dm_aot_compiler_count(int gameplay) { return atomic_load(&aot_count[!!gameplay][1]); }
// Standalone users of host_msl have no NVN archive. The NVN host overrides this
// hook and uses its validated archive loader, including malformed-file checks.
__attribute__((weak)) id<MTLComputePipelineState> dm_aot_helper_compute(id<MTLDevice> dev, id<MTLLibrary> lib, NSString *entry) { (void)dev; (void)lib; (void)entry; return nil; }
id<MTLComputePipelineState> host_msl_compute(id<MTLDevice> dev, id<MTLLibrary> lib, NSString *entry, NSError **e) {
    NSString *identity = [NSString stringWithFormat:@"%@/%@", lib.label, entry];
    if (dm_aot_on()) { id<MTLComputePipelineState> ps = dm_aot_helper_compute(dev, lib, entry); if (ps) return ps; }
    dm_aot_event("compute/helper", identity, "host archive miss/device fallback", 1);
    return [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:entry] error:e];
}

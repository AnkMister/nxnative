// Released texture pages (DM_NVN_TEX_DEDUPE, nvn_dirty.c nvn_dirty_release): a protected, unwritten page's bytes go to the dedupe file and its memory back to the system; any later
// access must see the same bytes as before. Expected values come from the bytes written before the release and from what the dirty tracker reported before it: a read leaves the
// texture clean, a write makes it dirty, a page written after the upload's stamp is not released, a refused release changes nothing, and a pool going away gets its bytes back first.
// g_dd_test_lose plays the kernel taking the released pages (their bytes then come back from the file); otherwise they come back from the same physical pages
#include "../nvn/nvn_dirty.h"
#include "../../host/dm.h"
#include <sys/mman.h>
#include <mach/mach.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>

module_t *g_mod;
int g_nmod;
module_t *module_of(const void *p) { (void)p; return NULL; }
void crash_install(void);
static int test_madvise(void *, size_t, int);
static ssize_t test_pread(int, void *, size_t, off_t);
#define madvise test_madvise
#define pread test_pread
#include "../nvn/nvn_dirty.c"
#undef pread
#undef madvise

static int g_fail;
#define EXPECT(name, want, got) do { \
    long long want_ = (long long)(want), got_ = (long long)(got); \
    printf("%-64s expected %-8lld → got %-8lld %s\n", name, want_, got_, want_ == got_ ? "✓" : "✗"); \
    if (want_ != got_) g_fail++; \
} while (0)

enum { NP = 64 };
static size_t g_pg;
static uint8_t byte_at(size_t i, unsigned salt) { return (uint8_t)((i * 2654435761u) >> 13) ^ (uint8_t)salt; }
static void fill(uint8_t *m, size_t n, unsigned salt) { for (size_t i = 0; i < n; i++) m[i] = byte_at(i, salt); }
static uint8_t *g_m;   // the range: bytes are checked against their offset in it
static size_t bad_bytes(const volatile uint8_t *m, size_t n, unsigned salt) { size_t b = 0, o = (size_t)(m - g_m); for (size_t i = 0; i < n; i++) b += m[i] != byte_at(o + i, salt); return b; }
static uint64_t gone_bytes(void) { uint64_t g, a, b, c, d, e, f; nvn_dirty_dedupe_stats(&g, &a, &b, &c, &d, &e, &f); return g; }
static uint64_t reread_pages(void) { uint64_t g, a, b, c, d, e, f; nvn_dirty_dedupe_stats(&g, &a, &b, &c, &d, &e, &f); return c; }
static int prot_of(void *p) {   // the page's current protection
    vm_address_t a = (vm_address_t)p; vm_size_t s = 0; vm_region_basic_info_data_64_t info; mach_msg_type_number_t cnt = VM_REGION_BASIC_INFO_COUNT_64; mach_port_t obj = MACH_PORT_NULL;
    if (vm_region_64(mach_task_self(), &a, &s, VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &cnt, &obj) != KERN_SUCCESS) return -1;
    return info.protection;
}
static int release_checks, restore_checks;
static int test_madvise(void *addr, size_t len, int advice) {
    if (advice == MADV_FREE_REUSABLE && g_m) {
        range_t *r = find_span((uintptr_t)g_m, 1);
        if (r && (uintptr_t)addr >= r->alias && (uintptr_t)addr < r->alias + r->end - r->base) {
            if (prot_of((void *)(r->base + (uintptr_t)addr - r->alias)) != VM_PROT_NONE) EXPECT("release leaves the guest inaccessible", VM_PROT_NONE, prot_of((void *)(r->base + (uintptr_t)addr - r->alias)));
            release_checks++;
        }
    }
    return madvise(addr, len, advice);
}
static _Atomic int read_hold, read_entered;
static ssize_t test_pread(int fd, void *dst, size_t len, off_t off) {
    range_t *r = find_span((uintptr_t)g_m, 1);
    if (r && (uintptr_t)dst >= r->alias && (uintptr_t)dst < r->alias + r->end - r->base) {
        if (prot_of((void *)((r->base + (uintptr_t)dst - r->alias) & ~(g_pg - 1))) != VM_PROT_NONE) EXPECT("restore leaves the guest inaccessible", VM_PROT_NONE, prot_of((void *)((r->base + (uintptr_t)dst - r->alias) & ~(g_pg - 1))));
        restore_checks++;
    }
    if (atomic_load(&read_hold)) { atomic_store(&read_entered, 1); while (atomic_load(&read_hold)) sched_yield(); }
    return pread(fd, dst, len, off);
}
static uint64_t footprint(void) {
    task_vm_info_data_t vi; mach_msg_type_number_t n = TASK_VM_INFO_COUNT;
    if (task_info(mach_task_self(), TASK_VM_INFO, (task_info_t)&vi, &n)) abort();
    return vi.phys_footprint;
}
static int refuse(void *ctx, uintptr_t lo, uintptr_t hi) { (void)lo; (void)hi; ++*(int *)ctx; return 0; }
static int allow(void *ctx, uintptr_t lo, uintptr_t hi) { (void)lo; (void)hi; ++*(int *)ctx; return 1; }

static uint8_t *g_rd; static _Atomic int g_rd_bad;
static void *reader(void *arg) { (void)arg; for (int k = 0; k < NP; k++) if (bad_bytes(g_rd + (size_t)k * g_pg, g_pg, 1)) atomic_fetch_add(&g_rd_bad, 1); return NULL; }

static _Atomic int gpu_entered, gpu_access, kernel_released;
static void *gpu_consumer(void *p) {
    atomic_store(&gpu_entered, 1);
    nvn_dirty_require(p, g_pg);   // the same gate used before pool/raw-map residency
    atomic_store(&gpu_access, 1);
    return NULL;
}
static void *kernel_releaser(void *p) {
    for (int i = 0; i < 256; i++) {
        int skip; size_t n = nvn_dirty_release(p, NP * g_pg, nvn_dirty_now(), NULL, NULL, &skip);
        if (n) atomic_fetch_add(&kernel_released, 1);
    }
    return NULL;
}
static void *restore_thread(void *p) { nvn_dirty_require(p, g_pg); return NULL; }

int main(void) {
    crash_install(); setvbuf(stdout, NULL, _IONBF, 0);
    g_pg = (size_t)getpagesize();
    const char *tmp = getenv("TMPDIR");
    EXPECT("dedupe file opened", 0, nvn_dirty_dedupe_open(tmp));
    size_t n = NP * g_pg;
    uint8_t *m = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (m == MAP_FAILED) { perror("mmap"); return 2; }
    fill(m, n, 1); g_m = m;
    nvn_dirty_add_range(m, n);
    uint64_t stamp = nvn_dirty_now();
    nvn_dirty_protect(m, n);
    m[2 * g_pg + 5] = byte_at(2 * g_pg + 5, 1);   // a write after the stamp (same byte): page 2 must stay
    int calls = 0, skip = 0;

    EXPECT("refused by the pool check: bytes released", 0, nvn_dirty_release(m, n, stamp, refuse, &calls, &skip));
    EXPECT("refused: the check was asked", 1, calls);
    EXPECT("refused: the span counts as skipped", 1, skip);
    EXPECT("refused: page 4 still read-only (a write is still tracked)", VM_PROT_READ, prot_of(m + 4 * g_pg));

    calls = 0;
    size_t got = nvn_dirty_release(m, n, stamp, allow, &calls, &skip);
    EXPECT("released: every page but the one written after the stamp", (NP - 1) * g_pg, got);
    EXPECT("released: pages counted as gone", (NP - 1) * g_pg, gone_bytes());
    EXPECT("released: page 4 inaccessible", VM_PROT_NONE, prot_of(m + 4 * g_pg));
    EXPECT("written after the stamp: page 2 kept (writable)", VM_PROT_READ | VM_PROT_WRITE, prot_of(m + 2 * g_pg));

    EXPECT("read of a released page: its bytes", 0, bad_bytes(m + 3 * g_pg, g_pg, 1));
    EXPECT("read: page 3 read-only again (still write-tracked)", VM_PROT_READ, prot_of(m + 3 * g_pg));
    uint64_t s2 = nvn_dirty_now();
    EXPECT("read: no page written since the read", 0, nvn_dirty_since(m + 3 * g_pg, g_pg, s2));
    EXPECT("read: one page fewer gone", (NP - 2) * g_pg, gone_bytes());

    uint64_t before_w = nvn_dirty_now();
    m[5 * g_pg + 100] ^= 0xff;   // a write into a released page: bytes back first, then the write
    EXPECT("write into a released page: the dirty tracker sees it", 1, nvn_dirty_since(m + 5 * g_pg, g_pg, before_w));
    m[5 * g_pg + 100] ^= 0xff;
    EXPECT("write: the rest of the page kept its bytes", 0, bad_bytes(m + 5 * g_pg, g_pg, 1));
    EXPECT("write: page 5 writable", VM_PROT_READ | VM_PROT_WRITE, prot_of(m + 5 * g_pg));

    g_dd_test_lose = 1;   // the kernel took the pages: bytes from the file
    uint64_t rr = reread_pages();
    EXPECT("taken page: its bytes back from the file", 0, bad_bytes(m + 7 * g_pg, g_pg, 1));
    EXPECT("taken page: read back from the file", rr + 1, reread_pages());
    dm_guest_write_prepare(m + 9 * g_pg + 10, 20);   // a host system call about to write there
    EXPECT("host pre-write: page 9 writable", VM_PROT_READ | VM_PROT_WRITE, prot_of(m + 9 * g_pg));
    EXPECT("host pre-write: page 9 kept its bytes", 0, bad_bytes(m + 9 * g_pg, g_pg, 1));

    g_rd = m; pthread_t th[4];   // four threads reading the released pages at once
    for (int i = 0; i < 4; i++) pthread_create(&th[i], NULL, reader, NULL);
    for (int i = 0; i < 4; i++) pthread_join(th[i], NULL);
    EXPECT("four threads reading every released page: wrong pages", 0, atomic_load(&g_rd_bad));
    EXPECT("after the readers: nothing gone", 0, gone_bytes());

    // released again, then put back for the GPU (nvn_dirty_restore), then released and the pool goes away
    uint64_t st3 = nvn_dirty_now(); nvn_dirty_protect(m, n);
    got = nvn_dirty_release(m, n, st3, NULL, NULL, &skip);
    EXPECT("released again (every page re-protected)", n, got);
    nvn_dirty_restore(m + g_pg, 4 * g_pg);
    EXPECT("restore of 4 pages: those come back", n - 4 * g_pg, gone_bytes());
    EXPECT("restore: page 1 read-only, not dirty", VM_PROT_READ, prot_of(m + g_pg));
    EXPECT("restore: bytes", 0, bad_bytes(m + g_pg, 4 * g_pg, 1));
    nvn_dirty_remove_range(m);
    EXPECT("pool gone: nothing left released", 0, gone_bytes());
    EXPECT("pool gone: page 30 writable", VM_PROT_READ | VM_PROT_WRITE, prot_of(m + 30 * g_pg));
    EXPECT("pool gone: every byte", 0, bad_bytes(m, n, 1));
    g_dd_test_lose = 0;

    // two ranges over the same pages (pools sharing memory): nothing is released
    nvn_dirty_add_range(m, n); nvn_dirty_add_range(m + g_pg, 8 * g_pg);
    uint64_t st4 = nvn_dirty_now(); nvn_dirty_protect(m, n);
    got = nvn_dirty_release(m, n, st4, NULL, NULL, &skip);
    EXPECT("span shared with another range: bytes released", 0, got);
    nvn_dirty_remove_range(m + g_pg); nvn_dirty_remove_range(m);

    EXPECT("release protection checks ran", 1, release_checks > 0);
    EXPECT("restore protection checks ran", 1, restore_checks > 0);
    munmap(m, n);

    // Exercise the actual kernel ledger, then verify every restored byte.
    size_t large = 64u << 20;
    m = mmap(NULL, large, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    g_m = m; fill(m, large, 7); nvn_dirty_add_range(m, large);
    uint64_t st5 = nvn_dirty_now(); nvn_dirty_protect(m, large);
    uint64_t before = footprint();
    EXPECT("64 MiB guest copy released", large, nvn_dirty_release(m, large, st5, NULL, NULL, &skip));
    uint64_t after = footprint();
    printf("64 MiB probe: footprint before %.2f MiB, after %.2f MiB\n", before / 1048576., after / 1048576.);
    EXPECT("release reduces footprint by at least 48 MiB", 1, before > after && before - after >= (48u << 20));
    g_dd_test_lose = 1;
    EXPECT("64 MiB restored from disk: every byte", 0, bad_bytes(m, large, 7));
    nvn_dirty_remove_range(m); munmap(m, large);

    m = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    g_m = m; fill(m, n, 1); nvn_dirty_add_range(m, n);
    uint64_t st6 = nvn_dirty_now(); nvn_dirty_protect(m, n);
    EXPECT("new pool after retirement can release again", n, nvn_dirty_release(m, n, st6, NULL, NULL, &skip));
    pid_t child = fork();
    if (!child) { close(g_dd_fd); volatile uint8_t v = m[0]; (void)v; _exit(1); }
    int status = 0; waitpid(child, &status, 0);
    EXPECT("unreadable backup stops instead of returning corrupt bytes", 88, WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    nvn_dirty_remove_range(m); munmap(m, n);

    m = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    g_m = m; fill(m, n, 1); nvn_dirty_add_range(m, n);
    uint64_t st7 = nvn_dirty_now(); nvn_dirty_protect(m, n);
    EXPECT("kernel source released", n, nvn_dirty_release(m, n, st7, NULL, NULL, &skip));
    char file[1200]; snprintf(file, sizeof file, "%s/kernel-source.XXXXXX", tmp);
    int fd = mkstemp(file); unlink(file);
    EXPECT("unprepared kernel copy-in reproduces EFAULT", -1, pwrite(fd, m, g_pg, 0));
    EXPECT("copy-in errno", EFAULT, errno);
    dm_guest_read_prepare(m, g_pg);
    EXPECT("prepared file write from released texture page", g_pg, pwrite(fd, m, g_pg, 0));
    uint8_t *check = malloc(g_pg);
    EXPECT("read file bytes", g_pg, pread(fd, check, g_pg, 0));
    EXPECT("file matches released texture bytes", 0, memcmp(check, m, g_pg));
    EXPECT("kernel-visible range cannot be re-released", 0, nvn_dirty_release(m, n, st7, NULL, NULL, &skip));
    EXPECT("second file write remains accessible", g_pg, pwrite(fd, m, g_pg, 0));
    pthread_t releaser; pthread_create(&releaser, NULL, kernel_releaser, m);
    for (int i = 0; i < 64; i++) EXPECT("concurrent kernel write", g_pg, pwrite(fd, m, g_pg, 0));
    pthread_join(releaser, NULL);
    EXPECT("concurrent release cannot reclaim kernel-visible range", 0, atomic_load(&kernel_released));
    free(check); close(fd); nvn_dirty_remove_range(m); munmap(m, n);

    m = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    g_m = m; fill(m, n, 1); nvn_dirty_add_range(m, n);
    uint64_t st8 = nvn_dirty_now(); nvn_dirty_protect(m, n);
    EXPECT("delayed restore source released", n, nvn_dirty_release(m, n, st8, NULL, NULL, &skip));
    g_dd_test_lose = 1; atomic_store(&read_hold, 1); atomic_store(&read_entered, 0);
    pthread_t restorer; pthread_create(&restorer, NULL, restore_thread, m);
    while (!atomic_load(&read_entered)) sched_yield();
    pthread_t consumer; pthread_create(&consumer, NULL, gpu_consumer, m);
    while (!atomic_load(&gpu_entered)) sched_yield();
    EXPECT("timeout cannot authorize a GPU consumer", 0, nvn_dirty_restore(m, g_pg));
    EXPECT("unfinished bytes remain inaccessible", VM_PROT_NONE, prot_of(m));
    EXPECT("residency consumer cannot pass incomplete bytes", 0, atomic_load(&gpu_access));
    atomic_store(&read_hold, 0); pthread_join(restorer, NULL); pthread_join(consumer, NULL);
    EXPECT("residency consumer proceeds only after restoration", 1, atomic_load(&gpu_access));
    EXPECT("completed restoration authorizes access", 1, nvn_dirty_restore(m, g_pg));
    EXPECT("completed bytes match texture", 0, bad_bytes(m, g_pg, 1));
    EXPECT("restore timeout disables future release (keep guest copy)", 0, nvn_dirty_release(m, n, st8, NULL, NULL, &skip));
    nvn_dirty_remove_range(m); munmap(m, n);

    printf("%s\n", g_fail ? "FAILED" : "all passed");
    return g_fail != 0;
}

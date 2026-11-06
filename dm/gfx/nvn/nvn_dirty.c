// Write-protect dirty-page tracking for guest memory: pool pages of packaged textures (CPU writes, GPU reads) are set read-only after upload, and as soon as the game writes it faults -> mark dirty, unprotect;
// before use, check the write generation of the covered pages and re-upload if newer than at upload time. NVN semantics: a texture descriptor points to pool memory, and the GPU reads the current content every time
// (measured: the game writes streamed assets into texture storage that is still being sampled, without re-registering).
// Signal handler constraint: the page-fault path uses only atomic operations and mprotect, no allocation, no locks.
#include "nvn_dirty.h"
#include "../../host/dm.h"
#include <stdatomic.h>
#include <pthread.h>
#include <sys/mman.h>
#include <unistd.h>
#include <mach/mach_time.h>
#include <sched.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Order of page state and mprotect: the side changing protection first sets the state to BUSY and sets the final state only after mprotect has landed; other threads wait when they see BUSY.
//   set read-only: NONE -> BUSY -> mprotect(read-only) -> PROT; unprotect: PROT -> BUSY -> mprotect(writable) -> NONE.
// Invariant: a page whose state is NONE is always writable, one whose state is PROT is always read-only. Setting read-only used to be "record PROT, then mprotect"; in between, another thread's unprotect-before-write
// (the movie decoder thread writing a frame into texture storage, a disk read into a guest buffer) could set the state back to NONE, then the mprotect landed => the page read-only with state NONE: a game thread writing it got only
// "re-execute" from the fault handler and spun forever; a host system call reading into it saw NONE in prep_write, skipped, and failed with EFAULT (reproduced by t_dirty_race).
// BUSY lasts at most one mprotect (plus a few atomic writes when setting read-only). The wait is capped at BUSY_WAIT_MS and reports red beyond it: in the fault handler it then returns "not our page" so the crash handler reports truthfully
enum { PG_NONE = 0, PG_PROT = 1, PG_BUSY = 2, PG_GONE = 3 };
// PG_GONE (DM_NVN_TEX_DEDUPE, nvn_dirty_release): the page's bytes are in the dedupe file and its memory was given back (madvise MADV_FREE_REUSABLE, the same VM object, so a pool's
// no-copy buffer over it stays coherent); the page is PROT_NONE. Any access faults and puts the bytes back first (dd_take): a read leaves it PROT (still write-tracked), a write NONE
// with a new generation, as a write to a PROT page does. Leaving GONE: GONE -> BUSY -> mprotect(read-write) -> bytes back -> PROT / NONE
enum { BUSY_WAIT_MS = 2000 };
// Tracked ranges = the memory pools (registered by MemoryPoolInitialize). After a pool is destroyed its live=0 slot is reused; the signal handler scans without locks.
// The table grows in blocks of 1,024 slots, up to 262,144; a block is never moved or freed, so the signal handler reads it without locks. A pool past the end goes untracked: its textures count
// as dirty and are re-uploaded at every use. The table was a fixed 256 slots (Zelda has about 300 pools at the title), then a fixed 4,096, and Breath of the Wild reaches 4,006 pools in its first
// shrine. The scans only cover slots in use, so the capacity itself costs nothing
enum { BLK_SHIFT = 10, BLK = 1 << BLK_SHIFT, NBLK = 256, MAX_RANGE = BLK * NBLK };
// Ranges are rounded to host pages (16 KB) but guest memory pools are only 4 KB aligned: adjacent pools share their first / last pages, so one address can fall in several registered ranges.
// So: "is this texture tracked" looks for a range that holds its whole span; a fault / host pre-write unprotects and stamps every range covering that page; pool destruction identifies its range by the pool's exact start mem.
// (Previously the first range containing the address was always taken: two SMBW ASTC 6x5 textures whose pool's first page is shared with a small preceding pool were judged untracked and re-uploaded on every use, about 6 MB per frame)
typedef struct { uintptr_t base, end, mem; _Atomic uint8_t *state; _Atomic uint64_t *gen; _Atomic(_Atomic uint8_t *) sparse; size_t cap; _Atomic int live;
                 _Atomic(_Atomic uint32_t *) slot; uintptr_t alias; } range_t;   // sparse: per page, protected for a placement sparse tile (nvn_dirty_protect_sparse)
// slot: per-page file offset + 1, allocated on first release. alias: the same
// backing VM object mapped at a host-only address until the pool retires.
static _Atomic(range_t *) g_blk[NBLK];
static inline range_t *rg(int i) { return &atomic_load_explicit(&g_blk[i >> BLK_SHIFT], memory_order_acquire)[i & (BLK - 1)]; }
static _Atomic int g_nr;
static uintptr_t g_pg, g_shift;
static _Atomic uint64_t g_now = 1;
static _Atomic uint64_t g_faults, g_preps;
static _Atomic uint64_t g_adds_total;
static _Atomic int g_live, g_live_peak;   // number of registered pools and peak (for the memory readout line)
void nvn_dirty_stat(int *live, int *peak, int *cap) { *live = atomic_load(&g_live); *peak = atomic_load(&g_live_peak); *cap = MAX_RANGE; }
static _Atomic int g_overflow_logged;
static pthread_mutex_t g_slot_mu = PTHREAD_MUTEX_INITIALIZER;   // Pool creation, retirement and protection serialize descriptor lifetime; the page-fault path does not touch this mutex
static _Atomic uint64_t g_mp_calls, g_mp_pages, g_mp_ticks;   // This module's mprotect: call count, pages covered, time spent (mach timebase, safe in the page-fault path too)
static void mp(uintptr_t a, size_t len, int prot) {
    uint64_t t = mach_absolute_time(); mprotect((void *)a, len, prot);
    atomic_fetch_add(&g_mp_ticks, mach_absolute_time() - t); atomic_fetch_add(&g_mp_calls, 1); atomic_fetch_add(&g_mp_pages, len >> g_shift);
}

static mach_timebase_info_data_t g_tb;   // obtained when the first pool is registered (the fault path only multiplies and divides)
static _Atomic int g_busy_red;
// Wait for this page to leave BUSY. Returns 1 = it has left; 0 = waited past the limit (reported red once). Usable in a signal handler: only atomic reads, mach_absolute_time and sched_yield
static int busy_wait(range_t *r, uintptr_t p) {
    uint64_t t0 = 0;
    for (unsigned n = 1; atomic_load(&r->state[p]) == PG_BUSY; n++) {
        if (n & 0x3ff) continue;
        uint64_t now = mach_absolute_time(); if (!t0) t0 = now;
        if ((now - t0) * g_tb.numer / g_tb.denom > (uint64_t)BUSY_WAIT_MS * 1000000ull) {
            if (!atomic_exchange(&g_busy_red, 1)) LOG("[RED] dirty-page tracking: page %p stuck 'busy' for over %d ms (the thread changing its protection has not finished), no longer waiting", (void *)(r->base + (p << g_shift)), BUSY_WAIT_MS);
            return 0; }
        sched_yield();
    }
    return 1;
}
static int live_at(int i) { return atomic_load_explicit(&rg(i)->live, memory_order_acquire); }
// The registered range that holds all of [a, a+len) (used for a texture's tracking / protection / dirty check)
static _Atomic int g_span_last;   // the last range found: looks come in runs over one pool, and a scan of Mario Kart World's 5,000 pools per look took a quarter of its submit thread's time
static range_t *find_span(uintptr_t a, size_t len) {
    int n = atomic_load(&g_nr), k = atomic_load_explicit(&g_span_last, memory_order_relaxed);
    if (k < n) { range_t *r = rg(k); if (live_at(k) && a >= r->base && a + len <= r->end) return r; }
    for (int i = 0; i < n; i++) { range_t *r = rg(i); if (live_at(i) && a >= r->base && a + len <= r->end) { atomic_store_explicit(&g_span_last, i, memory_order_relaxed); return r; } }
    return NULL;
}
static void stamp_page(range_t *r, uintptr_t p) {
    atomic_store(&r->gen[p], atomic_fetch_add(&g_now, 1) + 1);
    // Publish completion after the generation: a checker may have cached "clean" using the incremented clock before the generation store. Both fault and host-write paths
    // must invalidate that cached clock, as the page stays writable until the next upload protects it again.
    atomic_fetch_add(&g_now, 1);
}
static _Atomic uint64_t g_sparse_writes;   // writes to pages protected for a placement sparse tile (nvn_dirty_sparse_writes)
static void sparse_note(range_t *r, uintptr_t p) { _Atomic uint8_t *sp = atomic_load(&r->sparse); if (sp && atomic_exchange(&sp[p], 0)) atomic_fetch_add(&g_sparse_writes, 1); }
static void unprotect_page(range_t *r, uintptr_t p) {   // The caller has already changed the state from PROT to BUSY
    mp(r->base + (p << g_shift), g_pg, PROT_READ | PROT_WRITE);
    stamp_page(r, p); sparse_note(r, p);
    atomic_store(&r->state[p], PG_NONE);
}
// Released textures keep their file backup until the pool retires. A private
// host alias names the same VM object as guest memory and existing Metal buffers.
// Only that alias becomes writable during release/restore. The guest stays
// inaccessible until its bytes are complete, so concurrent readers and writers
// cannot see zeros or lose a write in a temporary read-write window.
static int g_dd_fd = -1;
static pthread_mutex_t g_dd_mu = PTHREAD_MUTEX_INITIALIZER;   // the file's slot allocator (never taken in the page-fault path)
static uint32_t *g_dd_free, g_dd_nfree, g_dd_freecap, g_dd_next = 1;
static _Atomic int64_t g_dd_gone;                              // pages released now
static _Atomic uint64_t g_dd_released, g_dd_back, g_dd_reread, g_dd_raced, g_dd_failed, g_dd_slots_hi;
int g_dd_test_lose;   // test switch (t_dirty_dedupe): every page counts as taken by the kernel, so its bytes come back from the file
int nvn_dirty_dedupe_open(const char *dir) {
    if (g_dd_fd >= 0) return 0;
    if (!g_pg) { g_pg = (uintptr_t)getpagesize(); g_shift = __builtin_ctzl(g_pg); }
    if (!dir || !*dir) { errno = EINVAL; return -1; }
    char path[1024];
    if (snprintf(path, sizeof path, "%s/dm-texdedupe-%d.XXXXXX", dir, (int)getpid()) >= (int)sizeof path) { errno = ENAMETOOLONG; return -1; }
    int fd = mkstemp(path);
    if (fd < 0) return -1;
    if (unlink(path)) { int e = errno; close(fd); errno = e; return -1; }
    fcntl(fd, F_SETFD, FD_CLOEXEC);
    g_dd_fd = fd;
    return 0;
}
int nvn_dirty_dedupe_on(void) { return g_dd_fd >= 0; }
static uint32_t dd_slot_new(void) {
    pthread_mutex_lock(&g_dd_mu);
    uint32_t s = g_dd_nfree ? g_dd_free[--g_dd_nfree] : g_dd_next++;
    pthread_mutex_unlock(&g_dd_mu);
    if (s > atomic_load(&g_dd_slots_hi)) atomic_store(&g_dd_slots_hi, s);
    return s;
}
static void dd_slots_free(range_t *r, size_t np) {   // a range going: its slots back to the allocator (normal context)
    _Atomic uint32_t *sl = atomic_load(&r->slot); if (!sl) return;
    pthread_mutex_lock(&g_dd_mu);
    for (size_t i = 0; i < np; i++) { uint32_t s = atomic_exchange(&sl[i], 0); if (!s) continue;
        if (g_dd_nfree == g_dd_freecap) { g_dd_freecap = g_dd_freecap ? g_dd_freecap * 2 : 4096; uint32_t *f = realloc(g_dd_free, g_dd_freecap * sizeof *f); if (!f) die("dedupe slot list"); g_dd_free = f; }
        g_dd_free[g_dd_nfree++] = s; }
    pthread_mutex_unlock(&g_dd_mu);
}
// The original page stays PROT_NONE throughout. Cancelling reuse prevents the
// kernel from taking the alias's bytes while we inspect or restore them.
static int dd_fill(range_t *r, uintptr_t p) {
    uint8_t *a = (uint8_t *)(r->alias + (p << g_shift)); char in = 0;
    if (madvise(a, g_pg, MADV_FREE_REUSE)) _exit(88);
    if (!g_dd_test_lose && !mincore(a, g_pg, &in) && (in & MINCORE_INCORE)) return 0;
    uint32_t sl = atomic_load(&atomic_load(&r->slot)[p]);
    off_t off = (off_t)(sl - 1) << g_shift;
    size_t got = 0;
    while (got < g_pg) {
        ssize_t n = pread(g_dd_fd, a + got, g_pg - got, off + (off_t)got);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) _exit(88);   // Never resume the game with missing backup bytes.
        got += (size_t)n;
    }
    atomic_fetch_add(&g_dd_reread, 1); return 1;
}
static void dd_back(range_t *r, uintptr_t p, int write) {   // GONE -> BUSY done by the caller; the count of released pages drops only once the page is final, so a reader that faulted on it still finds it ours
    uintptr_t a = r->base + (p << g_shift);
    dd_fill(r, p);
    atomic_fetch_add(&g_dd_back, 1);
    if (write) { mp(a, g_pg, PROT_READ | PROT_WRITE); stamp_page(r, p); sparse_note(r, p); atomic_store(&r->state[p], PG_NONE); }
    else {
        mp(a, g_pg, PROT_READ);
        atomic_store(&r->state[p], PG_PROT);
    }
    atomic_fetch_sub(&g_dd_gone, 1);
}
// Bring page p of r back if it is released (waiting out a release or restore in progress). Returns 1 when the page is accessible now and was ever released here (the access runs again)
static int dd_take(range_t *r, uintptr_t p, int write) {
    for (;;) {
        uint8_t st = PG_GONE;
        if (atomic_compare_exchange_strong(&r->state[p], &st, PG_BUSY)) { dd_back(r, p, write); return 1; }
        if (st == PG_BUSY) { if (!busy_wait(r, p)) return 0; continue; }
        _Atomic uint32_t *sl = atomic_load(&r->slot);
        return sl && atomic_load(&sl[p]) != 0;
    }
}
// Unprotect one page of a range: if protected, unprotect and stamp it; if another thread is changing its protection, wait for it to finish and look again -- if the other side was setting read-only, the page is PROT after the wait and still has to be unprotected
// (an unprotect-before-write never reaches the fault handler, so it must be done here). Returns 1 = this page is managed by this module; 0 = it is not, or the wait on BUSY timed out
static int release_page(range_t *r, uintptr_t p, _Atomic uint64_t *count) {
    for (;;) {
        uint8_t st = PG_PROT;
        if (atomic_compare_exchange_strong(&r->state[p], &st, PG_BUSY)) { unprotect_page(r, p); if (count) atomic_fetch_add(count, 1); return 1; }
        if (st == PG_GONE) { st = PG_GONE; if (atomic_compare_exchange_strong(&r->state[p], &st, PG_BUSY)) { dd_back(r, p, 1); if (count) atomic_fetch_add(count, 1); return 1; } continue; }   // released (DM_NVN_TEX_DEDUPE): bytes back, then writable
        if (st != PG_BUSY) return atomic_load(&r->gen[p]) != 0;   // already NONE: just unprotected by another thread (the fault happened before the unprotect) -> re-execute; pages never protected are not ours
        if (!busy_wait(r, p)) return 0;
    }
}
static int on_fault(void *addr, int is_write, void *uc) {
    (void)uc;
    uintptr_t a = (uintptr_t)addr; int ours = 0, n = atomic_load(&g_nr), e = errno;   // errno kept for the interrupted code (pread, mprotect)
    for (int i = 0; i < n; i++)   // Every range sharing the page must be released: releasing only one leaves the other range's state at "protected", and later writes no longer fault and are missed
        { range_t *r = rg(i); if (live_at(i) && a >= r->base && a < r->end) ours |= is_write ? release_page(r, (a - r->base) >> g_shift, &g_faults) : dd_take(r, (a - r->base) >> g_shift, 0); }   // a read: only a released page is ours
    errno = e;
    return ours;
}
// Unprotect pages p..q of a range with one mprotect per run of protected pages (a host write over a whole texture, e.g. WriteTexels, used to make one system call per 16 KB page:
// Link's Awakening, about 275 a frame). Pages another thread is changing are handled one by one after the run so far is finished, so no BUSY page is held while waiting
static void release_pages(range_t *r, uintptr_t p, uintptr_t q, _Atomic uint64_t *count) {
    uintptr_t run = 0; int open = 0;
    for (uintptr_t i = p; i <= q + 1; i++) {
        uint8_t st = PG_PROT; int took = i <= q && atomic_compare_exchange_strong(&r->state[i], &st, PG_BUSY);
        if (took) { if (!open) { run = i; open = 1; } continue; }
        if (open) {
            mp(r->base + (run << g_shift), (i - run) << g_shift, PROT_READ | PROT_WRITE);
            for (uintptr_t k = run; k < i; k++) { stamp_page(r, k); sparse_note(r, k); atomic_store(&r->state[k], PG_NONE); }
            if (count) atomic_fetch_add(count, i - run);
            open = 0;
        }
        if (i <= q && (st == PG_BUSY || st == PG_GONE)) release_page(r, i, count);   // another thread is changing it: wait, then unprotect it if it ended up protected; a released page: bytes back first
    }
}
static void prep_write(void *addr, size_t len) {
    uintptr_t a = (uintptr_t)addr, e = a + len; int n = atomic_load(&g_nr);
    if (!len) return;
    for (int i = 0; i < n; i++) {
        range_t *r = rg(i);
        if (!live_at(i) || e <= r->base || a >= r->end) continue;
        uintptr_t lo = a > r->base ? a : r->base, hi = e < r->end ? e : r->end;
        release_pages(r, (lo - r->base) >> g_shift, (hi - 1 - r->base) >> g_shift, &g_preps);
    }
}

void nvn_dirty_add_range(const void *mem, size_t size) {
    static int inited;
    if (!inited) { inited = 1; g_pg = (uintptr_t)getpagesize(); g_shift = __builtin_ctzl(g_pg); mach_timebase_info(&g_tb); dm_fault_hook_register(on_fault); dm_guest_write_prep_register(prep_write); }
    atomic_fetch_add(&g_adds_total, 1);
    pthread_mutex_lock(&g_slot_mu);
    int n = atomic_load(&g_nr);
    int slot = -1;
    for (int i = 0; i < n; i++) if (!live_at(i)) { slot = i; break; }
    if (slot < 0) {
        if (n >= MAX_RANGE) {
            int expected = 0;
            if (atomic_compare_exchange_strong(&g_overflow_logged, &expected, 1)) LOG("[RED] dirty-page tracking ranges are full (%d), pool %p not tracked", MAX_RANGE, mem);
            pthread_mutex_unlock(&g_slot_mu); return;
        }
        slot = n;
        if (!atomic_load_explicit(&g_blk[n >> BLK_SHIFT], memory_order_acquire)) {   // published before g_nr counts the slot (the scans read g_nr first)
            range_t *b = calloc(BLK, sizeof *b); if (!b) die("dirty-page tracking range table allocation failed (block %d)", n >> BLK_SHIFT);
            atomic_store_explicit(&g_blk[n >> BLK_SHIFT], b, memory_order_release);
        }
    }
    { int lv = atomic_fetch_add(&g_live, 1) + 1, pk = atomic_load(&g_live_peak); while (lv > pk && !atomic_compare_exchange_weak(&g_live_peak, &pk, lv)) {} }
    range_t *r = rg(slot);
    uintptr_t base = (uintptr_t)mem & ~(g_pg - 1), end = ((uintptr_t)mem + size + g_pg - 1) & ~(g_pg - 1);
    size_t np = (end - base) >> g_shift;
    _Atomic uint8_t *state = r->state;
    _Atomic uint64_t *gen = r->gen;
    if (r->cap < np) {
        state = calloc(np, 1); gen = calloc(np, sizeof *gen);
        if (!state || !gen) die("dirty-page table allocation failed (%zu pages)", np);
        // The old array is not freed: the signal handler may still have a very brief stale reader; leak = 9 bytes per page.
        atomic_store(&r->sparse, NULL);   // sized for the old cap, not freed for the same reason
        atomic_store(&r->slot, NULL); r->alias = 0;   // the same (their slots went back when the range went, dd_slots_free)
        r->cap = np;
    } else {
        memset((void *)state, 0, np); memset((void *)gen, 0, np * sizeof *gen);
        _Atomic uint8_t *sp = atomic_load(&r->sparse); if (sp) memset((void *)sp, 0, np);
    }
    r->base = base; r->end = end; r->mem = (uintptr_t)mem; r->state = state; r->gen = gen;
    if (slot == n) atomic_store(&g_nr, n + 1);
    atomic_store_explicit(&r->live, 1, memory_order_release);
    pthread_mutex_unlock(&g_slot_mu);
}
// Pool destruction: first restore still-protected pages to writable (the pool memory may be reused for something else once returned to the game), then mark invalid
void nvn_dirty_remove_range(const void *mem) {
    pthread_mutex_lock(&g_slot_mu);
    range_t *r = NULL; int n = atomic_load(&g_nr);
    for (int i = 0; i < n && !r; i++) if (live_at(i) && rg(i)->mem == (uintptr_t)mem) r = rg(i);   // Match by the pool's exact start: an adjacent pool sharing a page may have the same rounded base
    if (r) { prep_write((void *)r->base, r->end - r->base); dd_slots_free(r, (r->end - r->base) >> g_shift); if (r->alias) { mach_vm_deallocate(mach_task_self(), r->alias, r->end - r->base); r->alias = 0; } atomic_store_explicit(&r->live, 0, memory_order_release); atomic_fetch_sub(&g_live, 1); }   // released pages come back first (prep_write)
    pthread_mutex_unlock(&g_slot_mu);
}
int nvn_dirty_tracked(const void *addr, size_t len) {
    return find_span((uintptr_t)addr, len) != NULL;
}
// The tracked range holding [addr, addr+len), as a handle a caller keeps (packaged textures: the scan over every range ran twice per texture lookup). NULL = untracked
const void *nvn_dirty_span(const void *addr, size_t len) { return len ? find_span((uintptr_t)addr, len) : NULL; }
// Set read-only: mark the pages BUSY first and mark them PROT only after mprotect has landed (for the order and the invariant see the state notes at the top of the file)
void nvn_dirty_protect(const void *addr, size_t len) {
    // Keep this descriptor live through the last mprotect. Retirement restores
    // RW under this same mutex; it must not finish between lookup and PG_BUSY.
    pthread_mutex_lock(&g_slot_mu);
    range_t *r = len ? find_span((uintptr_t)addr, len) : NULL;
    if (!r) { pthread_mutex_unlock(&g_slot_mu); return; }
    uintptr_t a = (uintptr_t)addr, p = (a - r->base) >> g_shift, q = (a + len - 1 - r->base) >> g_shift;
    // Consecutive pages are merged into one mprotect (per-page calls reach thousands per frame on the first upload of large textures; character select page startup frame 5: 4888 calls).
    // Pages already PROT / BUSY break the consecutive run: do not protect again, and do not touch pages another thread is changing.
    // A BUSY page is waited out (the run so far is protected first, so none of ours is BUSY meanwhile) and looked at again: an unprotect in progress leaves the page writable
    // with a generation the caller's stamp may cover, so skipped, its later writes never faulted and the texture stayed stale (MacNativeGames a166602)
    uintptr_t run = 0; int open = 0;
    for (uintptr_t i = p; i <= q + 1; i++) {
        uint8_t st = PG_NONE;
        int took = i <= q && atomic_compare_exchange_strong(&r->state[i], &st, PG_BUSY);
        if (took && !open) { run = i; open = 1; }
        if (!took && open) { mp(r->base + (run << g_shift), (i - run) << g_shift, PROT_READ); for (uintptr_t k = run; k < i; k++) atomic_store(&r->state[k], PG_PROT); open = 0; }
        if (!took && i <= q && st == PG_BUSY && busy_wait(r, i)) i--;   // this page again
    }
    pthread_mutex_unlock(&g_slot_mu);
}
// As nvn_dirty_protect, for the pages behind a placement sparse tile: a write to one of them moves nvn_dirty_sparse_writes, which nothing else moves, so its textures need no look at their tiles
// until one is written (the page table's walk per look is what this replaces; nvn_mtl.m sparse_look)
void nvn_dirty_protect_sparse(const void *addr, size_t len) {
    nvn_dirty_protect(addr, len);
    pthread_mutex_lock(&g_slot_mu);
    range_t *r = len ? find_span((uintptr_t)addr, len) : NULL;
    if (r) {
        _Atomic uint8_t *sp = atomic_load(&r->sparse);
        if (!sp) { sp = calloc(r->cap, 1); atomic_store(&r->sparse, sp); }
        if (sp) for (uintptr_t i = ((uintptr_t)addr - r->base) >> g_shift, q = ((uintptr_t)addr + len - 1 - r->base) >> g_shift; i <= q; i++) atomic_store(&sp[i], 1);
    }
    pthread_mutex_unlock(&g_slot_mu);
}
uint64_t nvn_dirty_sparse_writes(void) { return atomic_load(&g_sparse_writes); }
uint64_t nvn_dirty_now(void) { return atomic_load(&g_now); }
// As nvn_dirty_since, with the caller's last range kept in *span (rechecked, scanned again only if it no longer holds the span; a slot reused by another pool over the same memory is as
// good): a packaged texture keeps its handle (the scan over every range ran twice per texture lookup), and a sparse texture's page-table walk (hle_nvn.c vpt_walk) asks once per run of
// physical pages, which mostly lie in one pool, where find_span scans every registered range (about 4,300 in a Mario Kart World race)
int nvn_dirty_since_cached(const void **span, const void *addr, size_t len, uint64_t stamp) {
    if (!len) return 0;
    range_t *r = (range_t *)*span; uintptr_t a = (uintptr_t)addr;
    if (!r || !atomic_load_explicit(&r->live, memory_order_acquire) || a < r->base || a + len > r->end) { r = find_span(a, len); *span = r; }
    if (!r) return 1;   // When untracked, conservatively treat as dirty: better to upload more than to show stale content
    uintptr_t p = (a - r->base) >> g_shift, q = (a + len - 1 - r->base) >> g_shift;
    for (uintptr_t i = p; i <= q; i++) if (atomic_load(&r->gen[i]) > stamp) return 1;   // The generation of the last write before upload is <= the stamp; any later write must be > the stamp
    return 0;
}
int nvn_dirty_since_span(const void *span, const void *addr, size_t len, uint64_t stamp) { return nvn_dirty_since_cached(&span, addr, len, stamp); }
int nvn_dirty_since(const void *addr, size_t len, uint64_t stamp) { return nvn_dirty_since_span(NULL, addr, len, stamp); }
void nvn_dirty_slot_stats(int *live, int *used_slots, uint64_t *adds_total) {
    int n = atomic_load(&g_nr), active = 0;
    for (int i = 0; i < n; i++) active += live_at(i) != 0;
    *live = active; *used_slots = n; *adds_total = atomic_load(&g_adds_total);
}
void nvn_dirty_stats(uint64_t *faults, uint64_t *preps) { *faults = atomic_load(&g_faults); *preps = atomic_load(&g_preps); }
void nvn_dirty_mp_stats(uint64_t *calls, uint64_t *pages, uint64_t *ns) {
    static mach_timebase_info_data_t tb; if (!tb.denom) mach_timebase_info(&tb);
    *calls = atomic_load(&g_mp_calls); *pages = atomic_load(&g_mp_pages); *ns = atomic_load(&g_mp_ticks) * tb.numer / tb.denom;
}
// Release the whole host pages inside [addr, addr + len) that are protected and unwritten since stamp (DM_NVN_TEX_DEDUPE; see "Released texture pages" above), in batches of at most
// DD_BATCH pages: each batch is taken BUSY under the slot lock, then ok(ctx, lo, hi) decides (nvn_mtl.m: the pool is out of the residency set, under its lock; whoever makes it resident
// later waits out the BUSY pages and puts them back, nvn_dirty_restore), then the bytes go to the file and the memory goes. Only a span one range alone covers is released (adjacent
// pools share pages). Returns the bytes released; *skip is set when the span cannot be released at all (untracked, shared, refused by ok)
enum { DD_BATCH = 256 };   // 4 MB of 16 KB pages: a waiter on BUSY pages (busy_wait's 2 s limit) waits for one batch's writes at most
size_t nvn_dirty_release(const void *addr, size_t len, uint64_t stamp, int (*ok)(void *ctx, uintptr_t lo, uintptr_t hi), void *ctx, int *skip) {
    *skip = 0;
    if (g_dd_fd < 0 || !len || !g_pg) { *skip = 1; return 0; }
    uintptr_t a = (uintptr_t)addr, ia = (a + g_pg - 1) & ~(g_pg - 1), ie = (a + len) & ~(g_pg - 1);
    if (ie <= ia) { *skip = 1; return 0; }
    size_t done = 0;
    for (uintptr_t lo = ia; lo < ie; ) {
        uintptr_t hi = lo + ((uintptr_t)DD_BATCH << g_shift); if (hi > ie) hi = ie; uint32_t pages[DD_BATCH]; int np = 0;
        pthread_mutex_lock(&g_slot_mu);
        range_t *r = find_span(a, len); int n = atomic_load(&g_nr), shared = 0;
        if (r) for (int i = 0; i < n && !shared; i++) { range_t *o = rg(i); shared = live_at(i) && o != r && lo < o->end && hi > o->base; }
        if (!r || shared) { pthread_mutex_unlock(&g_slot_mu); *skip = !done; return done; }
        if (!atomic_load(&r->slot)) {   // first release in this range
            _Atomic uint32_t *sl = calloc(r->cap, sizeof *sl);
            if (!sl) die("dedupe page tables (%zu pages)", r->cap);
            atomic_store(&r->slot, sl);
        }
        if (!r->alias) {
            mach_vm_address_t alias = 0; vm_prot_t cur, max;
            kern_return_t kr = mach_vm_remap(mach_task_self(), &alias, r->end - r->base, 0, VM_FLAGS_ANYWHERE,
                                             mach_task_self(), r->base, FALSE, &cur, &max, VM_INHERIT_NONE);
            if (kr != KERN_SUCCESS || mprotect((void *)alias, r->end - r->base, PROT_READ | PROT_WRITE)) {
                if (kr == KERN_SUCCESS) mach_vm_deallocate(mach_task_self(), alias, r->end - r->base);
                pthread_mutex_unlock(&g_slot_mu); *skip = 1; return done;
            }
            r->alias = alias;
        }
        for (uintptr_t p = (lo - r->base) >> g_shift, q = (hi - r->base) >> g_shift; p < q; p++) {
            uint8_t st = PG_PROT;
            if (atomic_load(&r->gen[p]) <= stamp && atomic_compare_exchange_strong(&r->state[p], &st, PG_BUSY)) {
                if (atomic_load(&r->gen[p]) <= stamp) pages[np++] = (uint32_t)p;
                else atomic_store(&r->state[p], PG_PROT);
            }
        }
        pthread_mutex_unlock(&g_slot_mu);
        if (np && ok && !ok(ctx, lo, hi)) { for (int k = 0; k < np; k++) atomic_store(&r->state[pages[k]], PG_PROT); *skip = !done; return done; }
        _Atomic uint32_t *sl = atomic_load(&r->slot);
        int nk = 0;
        for (int k = 0; k < np; k++) {   // the bytes into the file, while the page is still read-only (a write faults and waits on BUSY)
            uintptr_t p = pages[k]; const uint8_t *pa = (const uint8_t *)(r->base + (p << g_shift));
            uint32_t s = atomic_load(&sl[p]); if (!s) { s = dd_slot_new(); atomic_store(&sl[p], s); }
            size_t put = 0; off_t off = (off_t)(s - 1) << g_shift;
            while (put < g_pg) { ssize_t w = pwrite(g_dd_fd, pa + put, g_pg - put, off + (off_t)put); if (w < 0 && errno == EINTR) continue; if (w <= 0) break; put += (size_t)w; }
            if (put < g_pg) { atomic_fetch_add(&g_dd_failed, 1); atomic_store(&r->state[p], PG_PROT); continue; }   // no room on the disk: the page stays as it is
            pages[nk++] = (uint32_t)p;
        }
        for (int k = 0; k < nk; ) {   // runs of consecutive pages: inaccessible, then given back through the alias
            int e = k + 1; while (e < nk && pages[e] == pages[e - 1] + 1) e++;
            uintptr_t ra = r->base + ((uintptr_t)pages[k] << g_shift); size_t rl = (size_t)(e - k) << g_shift;
            if (mprotect((void *)ra, rl, PROT_NONE)) _exit(88);
            int bad = madvise((void *)(r->alias + (ra - r->base)), rl, MADV_FREE_REUSABLE);
            if (bad) mp(ra, rl, PROT_READ);
            if (!bad) atomic_fetch_add(&g_dd_gone, e - k);
            for (int j = k; j < e; j++) atomic_store(&r->state[pages[j]], bad ? PG_PROT : PG_GONE);
            if (bad) atomic_fetch_add(&g_dd_failed, 1);
            else { atomic_fetch_add(&g_dd_released, (uint64_t)(e - k)); done += rl; }
            k = e;
        }
        lo = hi;
    }
    return done;
}
// Put back every released page in [addr, addr + len) before the GPU may read it (a no-copy buffer over it going into the residency set, an upload reading it); waits out a release in progress
void nvn_dirty_restore(const void *addr, size_t len) {
    if (!len || g_dd_fd < 0) return;
    uintptr_t a = (uintptr_t)addr, e = a + len; int n = atomic_load(&g_nr);
    for (int i = 0; i < n; i++) {
        range_t *r = rg(i);
        if (!live_at(i) || !atomic_load(&r->slot) || e <= r->base || a >= r->end) continue;
        uintptr_t lo = a > r->base ? a : r->base, hi = e < r->end ? e : r->end;
        for (uintptr_t p = (lo - r->base) >> g_shift, q = (hi - 1 - r->base) >> g_shift; p <= q; p++) {
            uint8_t st = atomic_load(&r->state[p]);
            if (st == PG_GONE || st == PG_BUSY) dd_take(r, p, 0);
        }
    }
}
// Released pages now (bytes), pages released / put back / read back from the file / kept with a write that raced the release / failed, in total, and the file's high-water mark (bytes)
void nvn_dirty_dedupe_stats(uint64_t *gone, uint64_t *released, uint64_t *back, uint64_t *reread, uint64_t *raced, uint64_t *failed, uint64_t *file) {
    int64_t g = atomic_load(&g_dd_gone); *gone = g > 0 ? (uint64_t)g << g_shift : 0;
    *released = atomic_load(&g_dd_released); *back = atomic_load(&g_dd_back); *reread = atomic_load(&g_dd_reread); *raced = atomic_load(&g_dd_raced); *failed = atomic_load(&g_dd_failed);
    *file = atomic_load(&g_dd_slots_hi) << g_shift;
}

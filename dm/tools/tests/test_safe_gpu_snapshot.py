"""Review Astra 2's interleaving probe, using the production watchdog functions."""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


def function(source, name):
    match = re.search(r'^static [^\n]*\b' + name + r'\([^\n]*?\{', source, re.M)
    start = match.start()
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


PREFIX = r'''
#import <Foundation/Foundation.h>
#include <assert.h>
#include <errno.h>
#include <pthread.h>
#include <stdatomic.h>
static _Atomic int g_safe_pending;
static _Atomic uint64_t g_safe_progress;
static pthread_mutex_t g_safe_mu = PTHREAD_MUTEX_INITIALIZER;
static uint64_t fake_now = 20000000000ull;
static int safe_gpu_on(void) { return 1; }
static void safe_gpu_trip(const char *why) { (void)why; abort(); }
#define clock_gettime_nsec_np(x) fake_now
static void inject_after_load(void);
static int inject;
#undef atomic_load
#define atomic_load(p) ({ __auto_type value = __c11_atomic_load(p, __ATOMIC_SEQ_CST); if ((void *)(p) == (void *)&g_safe_progress && inject) inject_after_load(); value; })
'''

PROBE = r'''
static pthread_t injected;
static dispatch_semaphore_t attempted;
static void *start_during_snapshot(void *unused) {
    (void)unused;
    int locked = pthread_mutex_trylock(&g_safe_mu) == 0;
    if (locked) pthread_mutex_unlock(&g_safe_mu);
    // A locked snapshot defers the writer. The old unlocked code lets it finish.
    if (!locked) dispatch_semaphore_signal(attempted);
    safe_gpu_started();
    if (locked) dispatch_semaphore_signal(attempted);
    return NULL;
}
static void inject_after_load(void) {
    inject = 0;
    assert(!pthread_create(&injected, NULL, start_during_snapshot, NULL));
    assert(!dispatch_semaphore_wait(attempted, dispatch_time(DISPATCH_TIME_NOW, NSEC_PER_SEC)));
}
static void *feedback(void *unused) {
    (void)unused;
    for (int i = 0; i < 10000; i++) safe_gpu_feedback(nil);
    return NULL;
}
static void *start_and_finish(void *unused) {
    (void)unused;
    for (int i = 0; i < 10000; i++) { safe_gpu_started(); safe_gpu_feedback(nil); }
    return NULL;
}
int main(int argc, const char **argv) { @autoreleasepool {
    assert(argc == 2);
    atomic_store(&g_safe_progress, 1000000000ull);
    if (!strcmp(argv[1], "idle")) {
        attempted = dispatch_semaphore_create(0); inject = 1;
        int stalled = safe_gpu_stalled(fake_now);
        assert(!pthread_join(injected, NULL));
        printf("review interleaving: stalled=%d pending=%d progress=%llu\n", stalled, atomic_load(&g_safe_pending), (unsigned long long)atomic_load(&g_safe_progress));
        assert(!stalled && atomic_load(&g_safe_pending) == 1 && atomic_load(&g_safe_progress) == fake_now);
        safe_gpu_feedback(nil);
        safe_gpu_started(); assert(!safe_gpu_stalled(fake_now));
        safe_gpu_feedback(nil); assert(!safe_gpu_stalled(fake_now + 20ull * NSEC_PER_SEC));
    } else if (!strcmp(argv[1], "feedback")) {
        atomic_store(&g_safe_pending, 20000);
        safe_gpu_feedback(nil); safe_gpu_started();
        assert(!safe_gpu_stalled(fake_now));
        pthread_t a, b;
        assert(!pthread_create(&a, NULL, feedback, NULL)); assert(!pthread_create(&b, NULL, feedback, NULL));
        assert(!pthread_join(a, NULL)); assert(!pthread_join(b, NULL));
        assert(!atomic_load(&g_safe_pending)); safe_gpu_feedback(nil); assert(!atomic_load(&g_safe_pending));
    } else {
        pthread_t a, b;
        assert(!pthread_create(&a, NULL, start_and_finish, NULL)); assert(!pthread_create(&b, NULL, start_and_finish, NULL));
        for (int i = 0; i < 20000; i++) assert(!safe_gpu_stalled(fake_now));
        assert(!pthread_join(a, NULL)); assert(!pthread_join(b, NULL)); assert(!atomic_load(&g_safe_pending));
        safe_gpu_started();
        assert(!safe_gpu_stalled(fake_now + 10ull * NSEC_PER_SEC - 1));
        assert(safe_gpu_stalled(fake_now + 10ull * NSEC_PER_SEC));
        pthread_mutex_lock(&g_safe_mu); assert(!safe_gpu_stalled(fake_now + 20ull * NSEC_PER_SEC)); pthread_mutex_unlock(&g_safe_mu);
    }
    puts("watchdog snapshot PASS"); return 0;
} }
'''


@unittest.skipUnless(sys.platform == 'darwin' and shutil.which('clang'), 'needs Apple clang and Foundation')
class SafeGpuSnapshot(unittest.TestCase):
    source = (pathlib.Path(__file__).resolve().parents[2] / 'gfx/nvn/nvn_safe_gpu.inc').read_text()

    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.work.cleanup)
        root = pathlib.Path(cls.work.name)
        src = root / 'snapshot.m'
        src.write_text(PREFIX + '\n'.join(function(cls.source, name) for name in ('safe_gpu_feedback', 'safe_gpu_started', 'safe_gpu_stalled')) + PROBE)
        cls.runner = root / 'snapshot'
        subprocess.run(['clang', '-O1', '-fobjc-arc', str(src), '-framework', 'Foundation', '-o', str(cls.runner)], check=True, capture_output=True, text=True)

    def run_probe(self, mode):
        result = subprocess.run([str(self.runner), mode], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_idle_to_active_interleaving(self):
        self.run_probe('idle')

    def test_concurrent_feedback(self):
        self.run_probe('feedback')

    def test_concurrent_start_feedback_and_watchdog(self):
        self.run_probe('concurrent')


if __name__ == '__main__':
    unittest.main()

// Test the real host handoff in a child process, without Metal or a game.
#include "../hle_lifecycle.c"
#include <assert.h>
#include <sys/wait.h>
#include <time.h>
static int out_fd, blocked;
static void note(char c) { assert(write(out_fd, &c, 1) == 1); }
uint64_t now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec; }
void mtl_safe_gpu_release(void) {
    note('R');
    if (blocked) { dispatch_semaphore_t sem = dispatch_semaphore_create(0); dispatch_semaphore_wait(sem, DISPATCH_TIME_FOREVER); }
}
void hlecount_flush(void) { note('H'); }
void dm_rec_finish(void) { note('C'); }
void dm_cheats_exit(void) { note('E'); }
void dm_audio_suspend(int on) { assert(on); note('A'); }
void dm_gfx_suspend(int on) { (void)on; note('G'); abort(); }
int main(void) {
    for (int mode = 0; mode < 2; mode++) {
        int fds[2]; assert(!pipe(fds)); pid_t pid = fork(); assert(pid >= 0);
        if (!pid) {
            close(fds[0]); out_fd = fds[1]; blocked = mode;
            dm_host_gpu_stop(); dm_host_gpu_stop();
            dispatch_main();
        }
        close(fds[1]); char text[32] = {0}; size_t n = 0; ssize_t got;
        while ((got = read(fds[0], text + n, sizeof text - n - 1)) > 0) n += (size_t)got;
        close(fds[0]); int status; assert(waitpid(pid, &status, 0) == pid);
        assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
        assert(!strcmp(text, mode ? "R" : "RHCEA"));
    }
    puts("GPU stop: cleanup order, once-only handoff, no drain, and blocked-cleanup exit PASS");
}

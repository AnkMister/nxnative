// Exercise the production gate callbacks with the audited parameter layouts.
#include "../hle_oot_resolution.c"
#include <assert.h>
#include <sys/wait.h>
#include <unistd.h>

static module_t modules[1];
module_t *g_mod = modules;
int g_nmod = 1;
static unsigned present;
static void (*callbacks[OBS_MAX])(uint64_t *, int);
static int writes, checks;
void dm_guest_write_prepare(void *p, size_t n) { assert(p && n); writes++; }
int gate_obs_present(int id) { return !!(present & (1u << (id - OBS_OOT_RES_PARAM))); }
void gate_obs_set(int id, void (*fn)(uint64_t *, int)) { assert(id >= OBS_OOT_RES_PARAM && id <= OBS_OOT_RES_FINAL); callbacks[id] = fn; }
#define CHECK(x) do { assert(x); checks++; } while (0)

static void check(const char *env, int valid_build, unsigned gates, int expected) {
    strcpy(modules[0].name, "main");
    strcpy(modules[0].build_id, valid_build ? "e0f3ccfaf50065ae4ea01eb5aeb13b1a" : "01234567890123456789012345678901");
    if (env) setenv("DM_OOT_RENDER_RES", env, 1); else unsetenv("DM_OOT_RENDER_RES");
    present = gates;
    dm_oot_resolution_install();
    CHECK(writes == 0);
    for (int i = OBS_OOT_RES_PARAM; i <= OBS_OOT_RES_FINAL; i++) CHECK(!!callbacks[i] == !!expected);
    if (!expected) return;

    uint8_t obj[0x60], want[sizeof obj];
    memset(obj, 0xa4, sizeof obj); memcpy(want, obj, sizeof obj);
    int32_t dims[4] = {expected * 16 / 9, expected, expected * 16 / 9, expected};
    memcpy(want + 0x38, dims, sizeof dims); want[0x4c] |= 1; want[0x4d] |= 1;
    uint64_t regs[30] = {0}, before[30]; regs[20] = (uintptr_t)obj; memcpy(before, regs, sizeof regs);
    callbacks[OBS_OOT_RES_PARAM](regs, 0);
    CHECK(!memcmp(obj, want, sizeof obj)); CHECK(!memcmp(regs, before, sizeof regs));
    callbacks[OBS_OOT_RES_PARAM](regs, 0);
    CHECK(!memcmp(obj, want, sizeof obj));

    // Real stock priorities vary from 0.75 to 0.33334. Every level must stay at the requested size.
    float stock[] = {.75f, .71112f, .66667f, .62223f, .58334f, .53334f, .5f, .4445f, .37223f, .33334f};
    for (unsigned i = 0; i < sizeof stock / sizeof *stock; i++) {
        memset(obj, 0x24, sizeof obj); memcpy(obj + 0x3c, &stock[i], 4); memcpy(want, obj, sizeof obj);
        float scale = 1; memcpy(want + 0x3c, &scale, 4); want[0x40] |= 1;
        callbacks[OBS_OOT_RES_LEVEL](regs, 0);
        CHECK(!memcmp(obj, want, sizeof obj)); CHECK(!memcmp(regs, before, sizeof regs));
    }

    // Both the framework clamp and the game's fixed-1080p branch arrive at the same commit gate.
    for (int fallback = 0; fallback < 2; fallback++) {
        uint8_t scene[0xe70], scene_want[sizeof scene];
        memset(scene, 0x38, sizeof scene); float old[2] = {fallback ? 1920 : 2560, fallback ? 1080 : 1440};
        memcpy(scene + 0xe54, old, sizeof old); memcpy(scene_want, scene, sizeof scene);
        float final[2] = {dims[0], dims[1]}; memcpy(scene_want + 0xe54, final, sizeof final);
        regs[19] = (uintptr_t)scene; regs[21] = 1080; memcpy(before, regs, sizeof regs); before[21] = expected;
        callbacks[OBS_OOT_RES_FINAL](regs, 0);
        CHECK(!memcmp(scene, scene_want, sizeof scene)); CHECK(!memcmp(regs, before, sizeof regs));
        // The displaced instruction and subsequent store consume the new height.
        float height = (int32_t)regs[21]; CHECK(height == expected);
    }
    CHECK(writes == 14);
}

int main(void) {
    const char *values[] = {NULL, "", "0", "off", "1440", "2160", "1080", "1440p", " 1440", "2160 ", "nan", "1440", "1440", "1440", "1440"};
    int total = 0;
    for (unsigned i = 0; i < sizeof values / sizeof *values; i++) {
        // pipe the count back, keeping every case's startup state independent.
        int fd[2]; assert(!pipe(fd)); pid_t pid = fork(); assert(pid >= 0);
        if (!pid) {
            close(fd[0]); check(values[i], i != 11, i >= 12 ? 7u ^ (1u << (i - 12)) : 7u, i == 4 ? 1440 : i == 5 ? 2160 : 0);
            assert(write(fd[1], &checks, sizeof checks) == sizeof checks); _exit(0);
        }
        close(fd[1]); int n = 0; assert(read(fd[0], &n, sizeof n) == sizeof n); close(fd[0]);
        int status; assert(waitpid(pid, &status, 0) == pid && WIFEXITED(status) && WEXITSTATUS(status) == 0); total += n;
    }
    printf("Ocarina engine resolution: 15 startup cases, %d checks passed\n", total);
}

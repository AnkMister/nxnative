// Ocarina's engine parameters, before it allocates targets and calculates effect constants.
// The build-bound gates are in its patches.py. No NVN dimensions or shader uniforms are guessed here.
#include "hle.h"
#include <TargetConditionals.h>
#include <stdatomic.h>

static int g_oot_res;
static atomic_flag g_oot_res_logged = ATOMIC_FLAG_INIT;

static void oot_resolution_param(uint64_t *regs, int param) {
    (void)param;
    uint8_t *p = (uint8_t *)(uintptr_t)regs[20];
    int32_t size[4] = {g_oot_res * 16 / 9, g_oot_res, g_oot_res * 16 / 9, g_oot_res};
    dm_guest_write_prepare(p + 0x38, 0x16);
    memcpy(p + 0x38, size, sizeof size);
    p[0x4c] |= 1; p[0x4d] |= 1;   // Use this entry rather than an inherited value.
}

static void oot_resolution_level(uint64_t *regs, int param) {
    (void)param;
    uint8_t *p = (uint8_t *)(uintptr_t)regs[20];
    float scale = 1;
    dm_guest_write_prepare(p + 0x3c, 5);
    memcpy(p + 0x3c, &scale, sizeof scale);
    p[0x40] |= 1;   // Every priority has the same size, including inherited palettes.
}

static void oot_resolution_final(uint64_t *regs, int param) {
    (void)param;
    uint8_t *p = (uint8_t *)(uintptr_t)regs[19];
    float size[2] = {g_oot_res * 16 / 9, g_oot_res};
    dm_guest_write_prepare(p + 0xe54, sizeof size);
    memcpy(p + 0xe54, size, sizeof size);
    // The displaced scvtf converts w21 to s0 and the game stores it at +0xe50.
    regs[21] = (uint32_t)g_oot_res;
    if (!atomic_flag_test_and_set(&g_oot_res_logged)) LOG("Ocarina engine final resolution %dx%d, scene palette 1:1 (DM_OOT_RENDER_RES); visual acceptance open", g_oot_res * 16 / 9, g_oot_res);
}

void dm_oot_resolution_install(void) {
    const char *e = getenv("DM_OOT_RENDER_RES");
    if (!e || !*e || !strcmp(e, "off") || !strcmp(e, "0")) return;
    int res = !strcmp(e, "1440") ? 1440 : !strcmp(e, "2160") ? 2160 : 0;
    if (!res) { LOG("[RED] DM_OOT_RENDER_RES=%s: use 1440, 2160 or off; keeping the game's resolution", e); return; }
    if (TARGET_OS_IPHONE || strcmp(dm_main_build(), "e0f3ccfaf50065ae4ea01eb5aeb13b1a")) {
        LOG("[RED] DM_OOT_RENDER_RES: requires the audited Ocarina v131072 main on Mac; keeping the game's resolution"); return;
    }
    if (!gate_obs_present(OBS_OOT_RES_PARAM) || !gate_obs_present(OBS_OOT_RES_LEVEL) || !gate_obs_present(OBS_OOT_RES_FINAL)) {
        LOG("[RED] DM_OOT_RENDER_RES: missing engine resolution gates; rewrite main with the current Ocarina profile, then restart; keeping the game's resolution"); return;
    }
    g_oot_res = res;
    gate_obs_set(OBS_OOT_RES_PARAM, oot_resolution_param);
    gate_obs_set(OBS_OOT_RES_LEVEL, oot_resolution_level);
    gate_obs_set(OBS_OOT_RES_FINAL, oot_resolution_final);
    LOG("Ocarina internal resolution requested %dx%d (DM_OOT_RENDER_RES); dynamic reduction disabled; awaiting engine size selection", res * 16 / 9, res);
}

"""Ocarina v131072's build-checked render ceiling and optional frame controller.

The engine stores its final scale after dynamic and fixed-mode selection.
State +0x10 holds the existing host DM_RENDER_SCALE setting.
"""
from nso_asm import ADRP, B


def render_scale(ctx):
    site = 0x31d3f48
    ctx.site(site, '805e0ebd')  # str s0,[x20,#0xe5c]
    start = ctx.here()
    ctx.emit(0xadbf7ffe)  # stp q30,q31,[sp,#-32]!
    ctx.emit(0xa9bf47f0)  # stp x16,x17,[sp,#-16]!
    ctx.emit(ADRP(16, ctx.here(), ctx.state))
    for word in (
        0xd53b4211,  # mrs x17,nzcv: the original store leaves flags intact
        0xbd40121e,  # ldr s30,[x16,#0x10]: host scale ceiling
        0x1e2023c8,  # fcmp s30,#0
        0x540000ed,  # b.le original: an unset state keeps the game
        0x1e2e101f,  # fmov s31,#1
        0x1e3f23c0,  # fcmp s30,s31
        0x5400008a,  # b.ge original: 1.0 keeps the original bits
        0x1e3e581f,  # fmin s31,s0,s30: the game can still choose a lower scale
        0xbd0e5e9f,  # str s31,[x20,#0xe5c]: leave s0 as the original store did
        0x14000002,  # b restore
        0xbd0e5e80,  # original: str s0,[x20,#0xe5c]
        0xd51b4211,  # restore: msr nzcv,x17
        0xa8c147f0,  # ldp x16,x17,[sp],#16
        0xacc17ffe,  # ldp q30,q31,[sp],#32
    ):
        ctx.emit(word)
    ctx.emit(B(ctx.here(), site + 4))
    ctx.put(site, [B(site, start)], 'dynamic resolution capped by the host render scale (1.0 = original)')
    ctx.render_scale = 1


# v131072 main: the frame step (patch_nso.py "Frame step in whole vsyncs"). The game has its own frame-rate controller (main+0x3b4ef60, called once a frame with x20 = its
# config): from the measured frame time it picks a vsync interval between config +0x0 and +0x4 (with hysteresis, +0x50 / +0x54), stores it at +0x48 and fps = 60 / interval
# at +0x58, then at main+0x3b4f074 (where its paths meet) calls main+0x3b4f160, which hands +0x58 to setFrameRate (main+0x4dc0f0), and the framework's setInterval
# (main+0x346c5c0) with +0x48, which sets the window's present interval (main+0xf49970) and the framework's fps (+0xfc = 60 / interval). So 30 fps (interval 2) is the game's
# own mode, with its game time stepping by the interval. The stub at main+0x3b4f074 replaces the interval and fps with the host's step (state page +0x20, 1 = 60 fps, 2 = 30) while
# a target fps is set (state +0x0, the launcher's Frame rate / DM_FPS_TARGET; 0 = the game's own choice), and counts the vsyncs stepped (+0x30) for the host's speed check
def frame_step(ctx):
    here, emit, fs_site, fs_put, FS_STATE_OFF = ctx.here, ctx.emit, ctx.site, ctx.put, ctx.state
    site = 0x3b4f074
    fs_site(site, 'e00314aa')   # mov x0,x20
    start = here()
    emit(0xa9bf47f0)  # preserve x16,x17
    emit(0xa9bf7fe9)  # preserve x9 (and stack alignment)
    emit(ADRP(16, here(), FS_STATE_OFF))
    for w in (0xb9400211,   # ldr w17,[x16]           target fps (float bits; 0 = off)
              0x34000151,   # cbz w17,restore (+10)
              0xb9402211,   # ldr w17,[x16,#0x20]     step in vsyncs
              0x34000111,   # cbz w17,restore (+8)       not decided yet
              0xb9004a91,   # str w17,[x20,#0x48]     the controller's interval
              0x52800789,   # mov w9,#60
              0x1ad10929,   # udiv w9,w9,w17
              0xb9005a89,   # str w9,[x20,#0x58]      its fps, which setFrameRate takes
              0xf9401a09,   # ldr x9,[x16,#0x30]
              0x8b314129,   # add x9,x9,w17,uxtw
              0xf9001a09,   # str x9,[x16,#0x30]      vsyncs stepped
              0xa8c17fe9,   # restore x9
              0xa8c147f0,   # restore x16,x17
              0xaa1403e0):  # orig: mov x0,x20
        emit(w)
    emit(B(here(), site + 4))
    fs_put(site, [B(site, start)], "frame step: the frame-rate controller's interval and fps follow the host's vsyncs (state page target fps; 0 = the game's own choice)")


def apply(ctx):
    render_scale(ctx)
    frame_step(ctx)  # target 0 preserves the game's controller; opt in with DM_FPS_TARGET=30/60


FRAME_STEP = {'e0f3ccfaf50065ae4ea01eb5aeb13b1a': apply}

BINDING = [
    {'what': 'frame controller interval and fps follow the host step', 'now': 'build', 'goal': 'game', 'purpose': 'frame rate',
     'why': 'the controller hands its interval to presentation and its fps to game time',
     'blocked': 'frame-step stubs have no function-matched form; local game-speed acceptance remains open',
     'checked': 'cheemu21 v131072 site guard; synthetic ARM64 execution only on this branch'},
    {'what': 'dynamic-resolution ceiling', 'now': 'build', 'goal': 'game', 'purpose': 'rendering',
     'why': "the game's final scale store follows its dynamic and fixed-mode choices",
     'blocked': 'the store and its role are verified for this main build only',
     'checked': 'v131072 main E0F3CCFAF50065AE4EA01EB5AEB13B1A, original store and surrounding code, 2026-11-06'},
]

    .text
    .globl _test_clock_read
_test_clock_read:
    stp x29, x30, [sp, #-16]!
    bl _dm_clock_stubs
    mov x0, x29
    ldp x29, x30, [sp], #16
    ret
    ldp x29, x30, [sp], #16
    b _test_gate_read

    .globl _test_gate_read
_test_gate_read:
    stp x29, x30, [sp, #-16]!
    bl _dm_gate_stubs
    .globl _test_gate_ret
_test_gate_ret:
    ldp x29, x30, [sp], #16
    ret

// Probe the instruction ABI, including full SIMD registers and flags, not merely the C ABI.
    .globl _test_clock_abi
_test_clock_abi:
    stp x29, x30, [sp, #-96]!
    stp x19, x20, [sp, #16]
    stp d8, d9, [sp, #32]
    stp d10, d11, [sp, #48]
    stp d12, d13, [sp, #64]
    stp d14, d15, [sp, #80]
    mov x19, x0
    mov x20, x1
    mov x1, #101
    mov x2, #102
    mov x3, #103
    mov x4, #104
    mov x5, #105
    mov x6, #106
    mov x7, #107
    mov x8, #108
    mov x9, #109
    mov x10, #110
    mov x11, #111
    mov x12, #112
    mov x13, #113
    mov x14, #114
    mov x15, #115
    mov x16, #116
    mov x17, #117
    .set k, 0
    .rept 32
    // Encode movi vK.16b,#0x5a without depending on assembler macro register substitution.
    .long (0x4f02e740 + k)
    .set k, k+1
    .endr
    mov x0, #0xa0000000
    msr nzcv, x0
    bl _test_clock_read
    stp x0, x1, [x19]
    stp x2, x3, [x19, #16]
    stp x4, x5, [x19, #32]
    stp x6, x7, [x19, #48]
    stp x8, x9, [x19, #64]
    stp x10, x11, [x19, #80]
    stp x12, x13, [x19, #96]
    stp x14, x15, [x19, #112]
    stp x16, x17, [x19, #128]
    mrs x0, nzcv
    str x0, [x19, #144]
    mrs x0, fpsr
    str x0, [x19, #152]
    mrs x0, fpcr
    str x0, [x19, #160]
    .set k, 0
    .rept 32
    // str qK,[x20,#16*K]
    .long (0x3d800280 + (k << 10) + k)
    .set k, k+1
    .endr
    ldp x19, x20, [sp, #16]
    ldp d8, d9, [sp, #32]
    ldp d10, d11, [sp, #48]
    ldp d12, d13, [sp, #64]
    ldp d14, d15, [sp, #80]
    ldp x29, x30, [sp], #96
    ret

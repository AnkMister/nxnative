// Integer-only clock entry ABI (entry.S). All mutable fields are atomic for the snapshot reader.
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>
typedef struct {
    _Atomic uint64_t seq, enabled, numer, denom, lag, ounce;
} dm_clock_state_t;
_Static_assert(sizeof(dm_clock_state_t) == 48 && offsetof(dm_clock_state_t, ounce) == 40, "clock assembly layout");
extern dm_clock_state_t dm_clock_state;
void dm_clock_prepare(void);
void dm_clock_count(int kind);

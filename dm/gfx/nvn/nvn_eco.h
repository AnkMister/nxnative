// Conservative repeat scan-out proof. Equality never licenses skipping guest commands.
#pragma once
#include <stdint.h>
#include <string.h>

typedef enum { NVN_ECO_OFF, NVN_ECO_PAUSE, NVN_ECO_SLOW } nvn_eco_mode;
static inline nvn_eco_mode nvn_eco_parse(const char *s) {
    return s && !strcmp(s, "pause") ? NVN_ECO_PAUSE : s && !strcmp(s, "slow") ? NVN_ECO_SLOW : NVN_ECO_OFF;
}
static inline int nvn_eco_hidden(int active, int key, int visible, int mini, int text_box) {
    return mini || !visible || !active || (!key && !text_box);
}

typedef struct {
    uint64_t serial, resource, work, surface;
    uint64_t width, height, format, origin;
    int crop[4];
} nvn_eco_image;
typedef struct { nvn_eco_image image; int valid; } nvn_eco_detector;
static inline int nvn_eco_same(const nvn_eco_detector *d, const nvn_eco_image *i, int known) {
    return known && d->valid && i->serial && !(i->work & 1) &&
        !memcmp(&d->image, i, sizeof *i);
}
static inline void nvn_eco_record(nvn_eco_detector *d, const nvn_eco_image *i, int known) {
    d->valid = known && i->serial && !(i->work & 1);
    d->image = *i;
}

int nvn_eco_same_on(void);
nvn_eco_mode nvn_eco_hidden_mode(void);
void nvn_eco_set_hidden(int hidden);
int nvn_eco_is_hidden(void);
// Each caller owns its next deadline. Foreground transitions interrupt a slow wait.
void nvn_eco_wait(uint64_t *next);
void nvn_eco_surface_changed(void);
uint64_t nvn_eco_surface(void);

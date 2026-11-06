#include "../nvn/nvn_eco.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    nvn_eco_detector d = {0};
    nvn_eco_image a = {.serial = 1, .resource = 2, .work = 4, .surface = 6,
        .width = 1280, .height = 720, .format = 80, .origin = 1, .crop = {0, 0, 1280, 720}};
    assert(!nvn_eco_same(&d, &a, 1));
    nvn_eco_record(&d, &a, 1);
    assert(nvn_eco_same(&d, &a, 1));
    assert(!nvn_eco_same(&d, &a, 0));
    // Every byte represents an input to scan-out, with no lossy hash equality.
    for (size_t k = 0; k < sizeof a; k++) {
        nvn_eco_image b = a;
        ((unsigned char *)&b)[k] ^= 1;
        assert(!nvn_eco_same(&d, &b, 1));
    }
    nvn_eco_image b = a; b.work = 5;
    nvn_eco_record(&d, &b, 1);
    assert(!nvn_eco_same(&d, &b, 1));
    nvn_eco_record(&d, &a, 0);
    assert(!nvn_eco_same(&d, &a, 1));
    b = a; b.serial = 0;
    nvn_eco_record(&d, &b, 1);
    assert(!nvn_eco_same(&d, &b, 1));
    assert(nvn_eco_parse(NULL) == NVN_ECO_OFF);
    assert(nvn_eco_parse("0") == NVN_ECO_OFF);
    assert(nvn_eco_parse("bad") == NVN_ECO_OFF);
    assert(nvn_eco_parse("pause") == NVN_ECO_PAUSE);
    assert(nvn_eco_parse("slow") == NVN_ECO_SLOW);
    for (int active = 0; active < 2; active++)
    for (int key = 0; key < 2; key++)
    for (int visible = 0; visible < 2; visible++)
    for (int mini = 0; mini < 2; mini++)
    for (int box = 0; box < 2; box++) {
        int watched = active && visible && !mini && (key || box);
        assert(nvn_eco_hidden(active, key, visible, mini, box) == !watched);
    }
    puts("eco: first/repeat/unknown, every image input, in-flight work, modes and 32 visibility combinations PASS");
}

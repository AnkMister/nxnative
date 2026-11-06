#include "../front_screen.h"
#include <assert.h>
#include <stdio.h>

int main(void) { @autoreleasepool {
    NSArray<NSString *> *names = @[@"Built-in Retina Display", @"Acer CB342CK C", @"Acer ET322QU"];
    assert(front_screen_index(names, NULL) == NSNotFound);
    assert(front_screen_index(names, "") == NSNotFound);
    assert(front_screen_index(names, "missing") == NSNotFound);
    assert(front_screen_index(@[], "Acer") == NSNotFound);
    assert(front_screen_index(names, "Built-in Retina Display") == 0);
    assert(front_screen_index(names, "cb342ck") == 1);
    assert(front_screen_index(names, "ET322") == 2);
    assert(front_screen_index(names, "acer") == 1);
    assert(front_screen_index(names, "\xff") == NSNotFound);
    puts("front screen: 9 checks passed");
    return 0;
} }

#pragma once
#import <Foundation/Foundation.h>

static inline NSUInteger front_screen_index(NSArray<NSString *> *names, const char *part) {
    if (!part || !*part) return NSNotFound;
    NSString *query = [NSString stringWithUTF8String:part];
    if (!query) return NSNotFound;
    for (NSUInteger i = 0; i < names.count; i++)
        if ([names[i] rangeOfString:query options:NSCaseInsensitiveSearch].location != NSNotFound) return i;
    return NSNotFound;
}

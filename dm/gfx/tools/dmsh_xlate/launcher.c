// Source-built universal launcher for the adjacent AnyCPU translator.
// Build: clang -O2 -arch arm64 -arch x86_64 launcher.c -o ../dmsh_xlate_bin/dmsh_xlate
#include <mach-o/dyld.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    char executable[PATH_MAX], resolved[PATH_MAX], library[PATH_MAX], runtime[PATH_MAX];
    uint32_t size = sizeof executable;
    if (_NSGetExecutablePath(executable, &size) || !realpath(executable, resolved)) {
        perror("translator launcher path"); return 1;
    }
    char *slash = strrchr(resolved, '/');
    if (!slash) return 1;
    *slash = 0;
    if (snprintf(library, sizeof library, "%s/dmsh_xlate.dll", resolved) >= sizeof library) return 1;
    const char *root = getenv("DOTNET_ROOT");
    const char *command = "dotnet";
    if (root && *root) {
        if (snprintf(runtime, sizeof runtime, "%s/dotnet", root) >= sizeof runtime) return 1;
        command = runtime;
    }
    char **args = calloc((size_t)argc + 2, sizeof *args);
    if (!args) return 1;
    args[0] = (char *)command; args[1] = library;
    for (int i = 1; i < argc; i++) args[i + 1] = argv[i];
    execvp(command, args);
    perror("translator: install .NET 10 or set DOTNET_ROOT");
    free(args); return 1;
}

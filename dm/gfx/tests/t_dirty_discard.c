#include "../nvn/nvn_dirty.h"
#include "../../host/dm.h"
#include <sys/mman.h>
#include <unistd.h>
module_t *g_mod; int g_nmod;
void crash_install(void);
module_t *module_of(const void *p) { (void)p; return NULL; }
static int checks, failed;
#define CHECK(c) do { checks++; if (!(c)) { failed++; fprintf(stderr,"discard assertion line%d failed\n",__LINE__); } } while(0)
int main(void) {
    crash_install(); size_t pg=getpagesize(), size=pg*4;
    unsigned char *mem=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0); CHECK(mem!=MAP_FAILED);
    memset(mem,0x4c,size);
    CHECK(nvn_dirty_discard(mem+pg-1,pg+2,0,0)==pg);
    CHECK(mem[0]==0x4c && mem[size-1]==0x4c);
    CHECK(nvn_dirty_discard(mem,pg,1,0)==0);
    nvn_dirty_add_range(mem,size); nvn_dirty_protect(mem,size);
    CHECK(nvn_dirty_discard(mem,pg,0,0)==0); // an overlapping tracked pool must survive even if caller says untracked
    CHECK(nvn_dirty_discard(mem,size,1,1)==0);
    nvn_dirty_remove_range(mem); munmap(mem,size);
    CHECK(nvn_dirty_discard((void *)(UINTPTR_MAX-3),16,0,0)==0);
    printf("dirty discard: %d checks, %d failed\n",checks,failed); return failed!=0;
}

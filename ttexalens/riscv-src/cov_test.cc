#include "ttgcov-runtime.h"

int main(void)
{
    uint32_t* ptr = (uint32_t*) 160000;
    if(*ptr == 0xdeadbeef) {
        ptr[1] = 0xdeadc0de;
    }
    else ptr[1] = 0x00ffffff;
    gcov_dump();
}

// brxy 0,0 100864 1
// wxy 0,0 160000 0xdeadbeef
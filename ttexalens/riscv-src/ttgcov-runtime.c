#include "ttgcov-runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

void write_data(const void* data, unsigned int length, void* arg)
{
    static uint32_t l1_written = 0;
    uint8_t* new_gcov_data = (uint8_t*) data;
    uint8_t volatile* l1_cov_base = (uint8_t volatile*) __coverage_start;
    
    for(unsigned int i = 0; i < length; i++) {
        l1_cov_base[l1_written++] = new_gcov_data[i];
    }
}

void write_fname(const char* fname, void* arg)
{
    __gcov_filename_to_gcfn(fname, write_data, NULL);
}

void* alloc(unsigned int size, void* arg)
{
    static uint8_t* heap_ptr = &__bss_free;
    size = (size + 3) & ~3; // ensure it's 4 byte aligned
    if((heap_ptr + size) >= &__bss_end) return NULL;

    void* allocated = heap_ptr;
    heap_ptr += size;
    return allocated;
}

void gcov_dump(void)
{
    __asm__ volatile("ebreak");
    const volatile struct gcov_info* const volatile* info = __gcov_info_start;
    const volatile struct gcov_info* const volatile* end = __gcov_info_end;
    __asm__ volatile ("" : "+r" (info)); // prevent optimizations

    while(info != end) {
        __gcov_info_to_gcda(*((const struct gcov_info* const*) info), write_fname, write_data, alloc, NULL);
        info++;
    }
}

#ifdef __cplusplus
}
#endif

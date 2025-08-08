#include "ttgcov-runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

#define COV_OVERFLOW 0xDEADBEEF
#define ever ;;

void __wrap__exit(int status)
{
    (void) status;
    gcov_dump();
    for(ever);
}

size_t strlen(const char* s)
{
    size_t i = 0;
    for(; s[i]; i++);
    return i;
}

// This variable indexes into the coverage segment.
// The first value in it is the total bytes written.
// Hence, skip the first 4 bytes when dumping the segment.
uint32_t written = 4;

void write_data(const void* _data, unsigned int length, void* arg)
{
    uint8_t* data = (uint8_t*) _data;

    if(__coverage_start + written + length >= __coverage_end) {
        // Not enough space in the segment.
        // Write overflow sentinel and return.
        *(uint32_t*) __coverage_start = COV_OVERFLOW;
        return;
    }
    
    for(unsigned int i = 0; i < length; i++) {
        __coverage_start[written++] = data[i];
    }
}

void fname_nop(const char* fname, void* arg)
{
    return;
}

void* alloc(unsigned int size, void* arg)
{
    // The heap starts from the unused part of bss and spans to the end of the segment.
    // The linker ensures it's 4-byte aligned.
    static uint8_t* heap_ptr = &__bss_free;
    size = (size + 3) & ~3; // Ensure the heap pointer remains aligned after bumping.
    if((heap_ptr + size) >= &__bss_end) return NULL;

    void* allocated = heap_ptr;
    heap_ptr += size;
    return allocated;
}

void gcov_dump(void)
{
    // Mind that this function extracts coverage info of only one TU.
    // This was built with LLK tests in mind.

    const struct gcov_info* const* info = __gcov_info_start;
    __asm__ volatile("" : "+r" (info)); // Prevent optimizations.
    __gcov_info_to_gcda(*info, fname_nop, write_data, alloc, NULL);

    // The total number of bytes written is stored at the start of the segment.
    // If an overflow took place while writing, avoid clobbering the sentinel.
    if(*(uint32_t*) __coverage_start != COV_OVERFLOW) 
        *(uint32_t*) __coverage_start = written;
}

#ifdef __cplusplus
}
#endif

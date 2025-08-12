#include "ttgcov-runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

#define COV_OVERFLOW 0xDEADBEEF

// This variable indexes into the coverage segment. The first value in the
// segment is the number of bytes written. Note, in gcov_dump, that it gets
// set to 4 - that is to accomodate for this value itself.
// The covdump.py script uses this to know how much data to extract.
uint32_t written;

void write_data(const void* _data, unsigned int length, void* arg)
{
    uint8_t* data = (uint8_t*) _data;

    if(__coverage_start + written + length >= __coverage_end) {
        // Not enough space in the segment, write overflow sentinel and return.
        *(uint32_t*) __coverage_start = COV_OVERFLOW;
        return;
    }
    
    for(unsigned int i = 0; i < length; i++) {
        __coverage_start[written++] = data[i];
    }
}

void fname_nop(const char* fname, void* arg)
{
    // As we're only extracting data for one TU, writing the filename is not
    // necessary, and in fact would complicate things.
    // One could call __gcov_filename_to_gcfn from gcc/libgcc/libgcov-driver.c
    // (also found in tt-gcov.c) should it be necessary to merge data from
    // multiple TUs, in which case gcov-tool's merge-stream subcommand would 
    // be used to facilitate that. However, that's a considerably more complex
    // approach; this is preferred as serializing the data into gcda format is 
    // fairly straightforward if only one TU is relevant.

    return;
}

void* alloc(unsigned int size, void* arg)
{
    // The heap starts from the unused part of bss and spans to the end of
    // the segment. The linker ensures it's 4-byte aligned.
    
    static uint8_t* heap_ptr = &__bss_free;
    // Ensure the heap pointer remains aligned after bumping.
    size = (size + 3) & ~3;
    if((heap_ptr + size) >= &__bss_end) return NULL;

    void* allocated = heap_ptr;
    heap_ptr += size;
    return allocated;
}

void gcov_dump(void)
{
    // Mind that this function extracts coverage info of only one TU, as this
    // was built with LLK tests in mind. It is possible to extend this to
    // multiple TUs by iterating from __gcov_info_start to __gcov_info_end
    // and calling __gcov_info_to_gcda on each of them with an implemented
    // filename callback; refer to the comment in fname_nop.

    // Memory must be zeroed here. Cheaping out on this caused arcane issues
    // which I don't want anyone else to have to deal with.
    for(int* p = (int*) __coverage_start; p != (int*) __coverage_end; p++)
        *p = 0;

    // First 4 bytes are reserved for written itself, start writing past that.
    written = 4;

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

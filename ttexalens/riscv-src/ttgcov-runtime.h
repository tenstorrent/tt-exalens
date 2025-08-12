#ifndef TTGCOV_RUNTIME_H
#define TTGCOV_RUNTIME_H

#include <stdint.h>
#include <stddef.h>
#include "tt-gcov.h"

#ifdef __cplusplus
extern "C" {
#endif

// Symbols pointing to per-TU coverage data from -fprofile-info-section.
// Only __gcov_info_start is used currently.
extern const struct gcov_info* __gcov_info_start[];
extern const struct gcov_info* __gcov_info_end[];

// Start address and region length of per-RISC REGION_GCOV.
// This region stores the actual gcda, and the host reads it
// and dumps it into a file.
extern uint8_t __coverage_start[];
extern uint8_t __coverage_end[];

// The remaining portion of bss is currently used as a makeshift heap.
// This is needed for __gcov_info_to_gcda, as it may allocate. 
// I may get rid of this upon testing if it turns out to be unnecessary.
extern uint8_t __bss_free;
extern uint8_t __bss_end;

// Write length bytes of data into the coverage region in L1.
void write_data(const void* data, unsigned int length, void* arg);

// Simple bump allocator using bss memory.
void* alloc(unsigned int size, void* arg);

// Run this at the end of a kernel if you wish to do coverage analysis.
void gcov_dump(void);

#ifdef __cplusplus
}
#endif

#endif // TTGCOV_RUNTIME_H

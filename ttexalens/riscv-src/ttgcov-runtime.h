#ifndef TTGCOV_RUNTIME_H
#define TTGCOV_RUNTIME_H

#include <stdint.h>
#include <stddef.h>
#include "tt-gcov.h"

#ifdef __cplusplus
extern "C" {
#endif

// Symbols pointing to per-TU coverage data from -fprofile-info-section.
extern const volatile struct gcov_info* const volatile __gcov_info_start[];
extern const volatile struct gcov_info* const volatile __gcov_info_end[];

// Start address and region length of per-RISC REGION_GCOV.
// Data in the gcda format is written into this region from the raw per-TU counters.
extern const uint8_t __coverage_start[];
extern const uint32_t __coverage_length;

// The remaining portion of bss is currently used as a makeshift heap.
// This is needed for __gcov_info_to_gcda, as it may allocate. 
// I may get rid of this upon testing if it turns out to be unnecessary.
extern uint8_t __bss_free;
extern uint8_t __bss_end;

// Write the given data with the given length into the coverage region in L1. Called repeatedly per TU.
void write_data(const void* data, unsigned int length, void* arg);

// Write a filename for the purpose of the gcda format. Called once per TU.
void write_fname(const char* fname, void* arg);

// Simple bump allocator. Not thread-safe.
void* alloc(unsigned int size, void* arg);

// Run this at the end of a kernel if you wish to enable profiling and coverage analysis.
void gcov_dump(void);

#ifdef __cplusplus
}
#endif

#endif // TTGCOV_RUNTIME_H

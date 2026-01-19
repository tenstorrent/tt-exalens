// SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

#include "gcov.h"

#define COVERAGE_OVERFLOW 0xDEADBEEF

// Symbols pointing to per-TU coverage data from -fprofile-info-section.
extern const struct gcov_info* __gcov_info_start[];
extern const struct gcov_info* __gcov_info_end[];

// Start address and region length of per-RISC REGION_GCOV.
// This region stores the actual gcda, and the host reads it
// and dumps it into a file.
extern uint8_t __coverage_start[];
extern uint8_t __coverage_end[];

const uint32_t COVERAGE_MAGIC_NUMBER = 0xC0B384B3;  // 0xC0V3R4G3

typedef struct _CoverageHeader {
    uint32_t bytes_written;
    uint32_t magic_number;
    const char* filename;
    uint32_t filename_length;
} CoverageHeader;
CoverageHeader* coverage_header = (CoverageHeader*)__coverage_start;

// The first value in the coverage segment is the number of bytes written.
// Note, in gcov_dump, that it gets set to 4 - that is to accomodate for the
// value itself. The covdump.py script uses it to know how much data to
// extract.

static void write_data(const void* _data, unsigned int length, void* arg) {
    uint8_t* data = (uint8_t*)_data;
    uint32_t* written = (uint32_t*)__coverage_start;
    if (*written == COVERAGE_OVERFLOW) return;

    uint8_t* mem = __coverage_start + *written;  // Start writing from here.
    if (mem + length >= __coverage_end) {
        // Not enough space in the segment, write overflow sentinel and return.
        *written = COVERAGE_OVERFLOW;
        return;
    }

    for (unsigned int i = 0; i < length; i++) {
        mem[i] = data[i];
    }
    *written += length;
}

static size_t strlen(const char* s) {
    size_t n;
    for (n = 0; s[n]; n++);
    return n;
}

// This callback is called once at the beginning of the data for each TU.
static void filename(const char* fname, void* arg) {
    // Write filename into header
    CoverageHeader* header = (CoverageHeader*)__coverage_start;
    header->filename = fname;
    header->filename_length = strlen(fname);
}

void gcov_init(void) {
    // First part is reserved for header
    coverage_header->magic_number = COVERAGE_MAGIC_NUMBER;
    coverage_header->bytes_written = 8;  // We wrote 8 bytes so far (first two fields of header).
}

void gcov_dump(void) {
    // First part is reserved for header
    CoverageHeader* header = (CoverageHeader*)__coverage_start;
    header->bytes_written = sizeof(CoverageHeader);
    header->magic_number = COVERAGE_MAGIC_NUMBER;

    const struct gcov_info* const* info = __gcov_info_start;
    __asm__ volatile("" : "+r"(info));  // Prevent optimizations.
    __gcov_info_to_gcda(*info, filename, write_data, NULL, NULL);
}

#ifdef __cplusplus
}
#endif

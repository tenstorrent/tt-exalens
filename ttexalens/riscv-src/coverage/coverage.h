#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#ifdef COVERAGE
#include <stdint.h>

// Symbols pointing to per-TU coverage data from -fprofile-info-section.
// Only __gcov_info_start is used currently.
extern const struct gcov_info* __gcov_info_start[];
extern const struct gcov_info* __gcov_info_end[];

// Start address and region length of per-RISC REGION_GCOV.
// This region stores the actual gcda, and the host reads it
// and dumps it into a file.
extern uint8_t __coverage_start[];
extern uint8_t __coverage_end[];

// Run this at the end of a kernel if you wish to do coverage analysis.
void gcov_dump(void);

#else // !COVERAGE
[[gnu::always_inline]]
static inline void gcov_dump(void) {}
#endif // COVERAGE

#ifdef __cplusplus
}
#endif

#ifndef TT_GCOV_H
#define TT_GCOV_H

#ifdef __cplusplus
extern "C" {
#endif

// This header provides the interface to libgcov's routines which were pulled
// out of GCC. That was necessary since linking against the default libgcov
// would cause the binary to become severely bloated for reasons yet unclear.
// Note that __gcov_filename_to_gcfn is commented out. The reason for that is
// laid out in ttgcov-runtime.c.

void
__gcov_info_to_gcda (const struct gcov_info *gi_ptr,
                     void (*filename_fn) (const char *, void *),
                     void (*dump_fn) (const void *, unsigned, void *),
                     void *(*allocate_fn) (unsigned, void *),
                     void *arg);

// void
// __gcov_filename_to_gcfn (const char *filename,
//			                void (*dump_fn) (const void *, unsigned, void *),
//			                void *arg);

#ifdef __cplusplus
}
#endif

#endif

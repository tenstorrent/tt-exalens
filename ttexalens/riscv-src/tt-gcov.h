#ifndef TT_GCOV_H
#define TT_GCOV_H

#ifdef __cplusplus
extern "C" {
#endif
void
__gcov_info_to_gcda (const struct gcov_info *gi_ptr,
                     void (*filename_fn) (const char *, void *),
                     void (*dump_fn) (const void *, unsigned, void *),
                     void *(*allocate_fn) (unsigned, void *),
                     void *arg);

void
__gcov_filename_to_gcfn (const char *filename,
			             void (*dump_fn) (const void *, unsigned, void *),
			             void *arg);

#ifdef __cplusplus
}
#endif

#endif

/*
 * SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
 *
 * SPDX-License-Identifier: Apache-2.0
 */
MEMORY
{
    BRISC_LOCAL_DATA_MEM : ORIGIN = 0xFFB00000, LENGTH = (4 * 1024) - 1024
    TRISC0_LOCAL_DATA_MEM : ORIGIN = 0xFFB00000, LENGTH = (2 * 1024) - 256
    TRISC1_LOCAL_DATA_MEM : ORIGIN = 0xFFB00000, LENGTH = (2 * 1024) - 256
    TRISC2_LOCAL_DATA_MEM : ORIGIN = 0xFFB00000, LENGTH = (2 * 1024) - 768
    NCRISC_LOCAL_DATA_MEM : ORIGIN = 0xFFB00000, LENGTH = (4 * 1024) - 1024
    BRISC_STACK_MEM : ORIGIN = (0xFFB00000 + (4 * 1024) - 1024), LENGTH = 1024
    TRISC0_STACK_MEM : ORIGIN = (0xFFB00000 + (2 * 1024) - 256), LENGTH = 256
    TRISC1_STACK_MEM : ORIGIN = (0xFFB00000 + (2 * 1024) - 256), LENGTH = 256
    TRISC2_STACK_MEM : ORIGIN = (0xFFB00000 + (2 * 1024) - 768), LENGTH = 768
    NCRISC_STACK_MEM : ORIGIN = (0xFFB00000 + (4 * 1024) - 1024), LENGTH = 1024
    BRISC_CODE : ORIGIN = (2048 + 512), LENGTH = (16 * 1024)
    TRISC0_CODE : ORIGIN = ((2048 + 512) + (16 * 1024)), LENGTH = (16 * 1024)
    TRISC1_CODE : ORIGIN = (((2048 + 512) + (16 * 1024)) + (16 * 1024)), LENGTH = (16 * 1024)
    TRISC2_CODE : ORIGIN = ((((2048 + 512) + (16 * 1024)) + (16 * 1024)) + (16 * 1024)), LENGTH = (16 * 1024)
    NCRISC_CODE : ORIGIN = 0xFFC00000, LENGTH = (16 * 1024)
    BRISC_LOADER_INIT_MEM : ORIGIN = 68096, LENGTH = 4 * 1024
    NCRISC_LOADER_INIT_MEM : ORIGIN = (68096 + (4 * 1024)), LENGTH = (4 * 1024)
    TRISC0_LOADER_INIT_MEM : ORIGIN = (68096 + (4 * 1024) + (4 * 1024)), LENGTH = (2 * 1024)
    TRISC1_LOADER_INIT_MEM : ORIGIN = (68096 + (4 * 1024) + (4 * 1024) + (2 * 1024)), LENGTH = (2 * 1024)
    TRISC2_LOADER_INIT_MEM : ORIGIN = (68096 + (4 * 1024) + (4 * 1024) + (2 * 1024) + (2 * 1024)), LENGTH = (2 * 1024)
    BRISC_LOADER_CODE_MEM : ORIGIN = 82432, LENGTH = 0 * 1024
    NCRISC_LOADER_CODE_MEM : ORIGIN = (82432 + (0 * 1024)), LENGTH = (16 * 1024)
    TRISC0_LOADER_CODE_MEM : ORIGIN = (82432 + (0 * 1024) + (16 * 1024)), LENGTH = (0 * 1024)
    TRISC1_LOADER_CODE_MEM : ORIGIN = (82432 + (0 * 1024) + (16 * 1024) + (0 * 1024)), LENGTH = (0 * 1024)
    TRISC2_LOADER_CODE_MEM : ORIGIN = (82432 + (0 * 1024) + (16 * 1024) + (0 * 1024) + (0 * 1024)), LENGTH = (0 * 1024)

    /* This region holds the coverage data in gcda format.
     * An unreasonably large amount of memory is allocated here;
     * the size of this region could very well be trimmed by an order of magnitude,
     * so adapt it to the particular tests that will run on the device. */
    BRISC_GCOV_MEM : ORIGIN = 92672, LENGTH = 8192
    TRISC0_GCOV_MEM : ORIGIN = 92672 + 8192, LENGTH = 8192
    TRISC1_GCOV_MEM : ORIGIN = 92672 + 8192 + 8192, LENGTH = 8192
    TRISC2_GCOV_MEM : ORIGIN = 92672 + 8192 + 8192 + 8192, LENGTH = 8192
    NCRISC_GCOV_MEM : ORIGIN = 92672 + 8192 + 8192 + 8192 + 8192, LENGTH = 8192

    /* This region holds the per-TU pointers to raw coverage data.
     * As the coverage runtime support library was written with just one TU in mind,
     * this is set to four bytes so the build will fail if more than one is attempted to be instrumented. */
    BRISC_GCOV_INFO : ORIGIN = 133632, LENGTH = 4
    TRISC0_GCOV_INFO : ORIGIN = 133632 + 4, LENGTH = 4
    TRISC1_GCOV_INFO : ORIGIN = 133632 + 4 + 4, LENGTH = 4
    TRISC2_GCOV_INFO : ORIGIN = 133632 + 4 + 4 + 4, LENGTH = 4
    NCRISC_GCOV_INFO : ORIGIN = 133632 + 4 + 4 + 4 + 4, LENGTH = 4

    /* This region holds newlib's reentrancy machinery, a couple of kilobytes in size in total (in code + data).
     * The stuff in here just makes things like errno thread-safe, so it is absolutely inane that it is even linked.
     * Something in the exalens linker scripts makes errno be pulled in, which in turn pulls in all of this;
     * I would suggest checking the objdump of a kernel compiled with your linker scripts for instances of
     * __errno or _impure_ptr and adjusting said scripts to kick all of that out, as it's a complete waste of space. */
    BRISC_IMPURE_DATA : ORIGIN = 133712, LENGTH = 1280
    TRISC0_IMPURE_DATA : ORIGIN = 133712 + 1280, LENGTH = 1280
    TRISC1_IMPURE_DATA : ORIGIN = 133712 + 1280 + 1280, LENGTH = 1280
    TRISC2_IMPURE_DATA : ORIGIN = 133712 + 1280 + 1280 + 1280, LENGTH = 1280
    NCRISC_IMPURE_DATA : ORIGIN = 133712 + 1280 + 1280 + 1280 + 1280, LENGTH = 1280

    /* Some of the coverage-related data goes into .bss, particularly the arc counters.
     * Some metadata (GCC's struct gcov_info) goes into .data. 
     * I've found merely extracting .bss from private memory makes sufficient room. */
    BRISC_BSS : ORIGIN = 140112, LENGTH = 1024
    TRISC0_BSS : ORIGIN = 140112 + 2048, LENGTH = 1024
    TRISC1_BSS : ORIGIN = 140112 + 2048 + 2048, LENGTH = 1024
    TRISC2_BSS : ORIGIN = 140112 + 2048 + 2048 + 2048, LENGTH = 1024
    NCRISC_BSS : ORIGIN = 140112 + 2048 + 2048 + 2048 + 2048, LENGTH = 1024
}

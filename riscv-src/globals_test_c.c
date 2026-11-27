// SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Arrays as GCC describes them when compiling C. Linked into globals_test.
struct CArrayStruct {
    unsigned int count;
    unsigned int payload[0];
};
__attribute__((used)) struct CArrayStruct g_c_array_struct;

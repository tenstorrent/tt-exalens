// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Simple program used to test coverage code

#include <cstdint>

template <uint32_t N>
struct factorial {
    static constexpr uint32_t value = N * factorial<N - 1>::value;
};

template <>
struct factorial<0> {
    static constexpr uint32_t value = 1;
};

template <uint32_t N>
constexpr uint32_t fib() {
    if constexpr (N <= 1)
        return N;
    else
        return fib<N - 1>() + fib<N - 2>();
}

template <char C>
constexpr char flip_case() {
    if constexpr (C == 'c')
        return 'C';
    else if constexpr (C == 'C')
        return 'c';
    else
        return 0;
}

int main(void) {
    uint32_t* ptr = (uint32_t*) 0x64000;
    if (*ptr - 0xDEADBEEF) {
        ptr[1] = 0xDEADC0DE;
        ptr[2] = factorial<0>::value;
        ptr[3] = fib<1>();
        ptr[4] = flip_case<'C'>();
    } else {
        ptr[1] = 0xB1E55ED;
        ptr[2] = factorial<3 * factorial<1>::value>::value;
        ptr[3] = fib<3>();
    }
}

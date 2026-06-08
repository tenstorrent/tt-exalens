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

thread_local volatile uint32_t mailbox;
thread_local volatile uint32_t results[4];

int main(void) {
    if (mailbox != 0xDEADBEEF) {
        results[0] = 0xDEADC0DE;
        results[1] = factorial<0>::value;
        results[2] = fib<1>();
        results[3] = flip_case<'C'>();
    } else {
        results[0] = 0xB1E55ED;
        results[1] = factorial<3 * factorial<1>::value>::value;
        results[2] = fib<3>();
    }
}

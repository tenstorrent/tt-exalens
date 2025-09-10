// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/vector.h>

namespace tt::exalens {
class ttexalens_implementation;
}

extern "C" void __attribute__((visibility("default"))) set_ttexalens_implementation(
    std::unique_ptr<tt::exalens::ttexalens_implementation> imp);

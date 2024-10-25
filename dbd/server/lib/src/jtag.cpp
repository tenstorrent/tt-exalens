// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "dbdserver/jtag.h"

#include <dlfcn.h>
#include <stdint.h>

#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

Jtag::Jtag(const char* libName) {
    handle = dlopen(libName, RTLD_LAZY);
    if (!handle) {
        throw std::runtime_error("Failed to load library");
    }
}

Jtag::~Jtag() {
    if (handle) {
        dlclose(handle);
    }
}

void Jtag::loadFunction(const char* name) {
    if (funcMap.find(name) == funcMap.end()) {
        void* funcPtr = dlsym(handle, name);
        const char* dlsym_error = dlerror();
        if (dlsym_error) {
            std::cerr << "Cannot load symbol: " << dlsym_error << '\n';
            throw std::runtime_error("Failed to load function");
        }
        funcMap[name] = funcPtr;
    }
}
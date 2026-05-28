// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace ttexalens::native_elf {

class MemoryAccess {
   public:
    // Access to memory
    virtual void read(uint64_t address, std::span<std::byte> buffer) const = 0;
    virtual void write(uint64_t address, std::span<const std::byte> buffer) = 0;

    // Access to registers
    virtual uint64_t read_register(uint16_t register_index) const = 0;
    virtual void write_register(uint16_t register_index, uint64_t value) = 0;

    // Helper functions
    std::optional<uint64_t> try_read_word(uint64_t address, uint8_t pointer_size) const {
        // Zero-initialized so the unread high bytes stay 0 when pointer_size < 8.
        uint64_t result = 0;
        try {
            read(address, std::span<std::byte>(reinterpret_cast<std::byte*>(&result), pointer_size));
        } catch (...) {
            // TODO: Consider rethrowing on timeouts or other non-recoverable errors instead of swallowing all
            // exceptions.
            return std::nullopt;
        }
        return result;
    }
};

}  // namespace ttexalens::native_elf

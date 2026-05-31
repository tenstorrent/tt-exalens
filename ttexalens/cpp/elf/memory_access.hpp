// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <utility>
#include <vector>

namespace ttexalens::native_elf {

class MemoryAccess {
   public:
    // Access to memory
    virtual void read(uint64_t address, std::span<std::byte> buffer) const = 0;
    virtual void write(uint64_t address, std::span<const std::byte> buffer) = 0;

    // Access to registers
    virtual uint64_t read_register(uint16_t register_index) const = 0;
    virtual void write_register(uint16_t register_index, uint64_t value) = 0;

    virtual ~MemoryAccess() = default;

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

// Serves reads from a snapshot byte range when the requested address falls
// inside [cached_address, cached_address + cached_data.size()); otherwise
// delegates to `base`. Writes and register access always pass through to
// `base`. Used by NativeElfVariable::read() to freeze a variable's bytes so
// later member/dereference walks don't re-hit live memory.
class CachedReadMemoryAccess : public MemoryAccess {
   public:
    CachedReadMemoryAccess(uint64_t cached_address, std::vector<std::byte> cached_data,
                           std::shared_ptr<MemoryAccess> base)
        : cached_address_(cached_address), cached_data_(std::move(cached_data)), base_(std::move(base)) {}

    void read(uint64_t address, std::span<std::byte> buffer) const override {
        if (address >= cached_address_ && address + buffer.size() <= cached_address_ + cached_data_.size()) {
            const size_t offset = static_cast<size_t>(address - cached_address_);
            std::memcpy(buffer.data(), cached_data_.data() + offset, buffer.size());
            return;
        }
        base_->read(address, buffer);
    }
    void write(uint64_t address, std::span<const std::byte> buffer) override { base_->write(address, buffer); }
    uint64_t read_register(uint16_t register_index) const override { return base_->read_register(register_index); }
    void write_register(uint16_t register_index, uint64_t value) override {
        base_->write_register(register_index, value);
    }

   private:
    uint64_t cached_address_;
    std::vector<std::byte> cached_data_;
    std::shared_ptr<MemoryAccess> base_;
};

// Singleton MemoryAccess that raises on every operation. Used as the base of
// CachedReadMemoryAccess for synthesized (non-addressable) ElfVariable values
// where all reads should hit the cache; any out-of-range read or any
// write/register access is a programming error that must surface.
class NoMemoryAccess : public MemoryAccess {
   public:
    void read(uint64_t /*address*/, std::span<std::byte> /*buffer*/) const override {
        throw std::runtime_error("read called on NoMemoryAccess");
    }
    void write(uint64_t /*address*/, std::span<const std::byte> /*buffer*/) override {
        throw std::runtime_error("write called on NoMemoryAccess");
    }
    uint64_t read_register(uint16_t /*register_index*/) const override {
        throw std::runtime_error("read_register called on NoMemoryAccess");
    }
    void write_register(uint16_t /*register_index*/, uint64_t /*value*/) override {
        throw std::runtime_error("write_register called on NoMemoryAccess");
    }

    // Shared singleton — there's no per-instance state.
    static std::shared_ptr<MemoryAccess> instance() {
        static std::shared_ptr<MemoryAccess> inst = std::make_shared<NoMemoryAccess>();
        return inst;
    }
};

}  // namespace ttexalens::native_elf

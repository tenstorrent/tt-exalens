// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <variant>
#include <vector>

#include "memory_access.hpp"

namespace ttexalens::native_elf {

// Forward declarations
class DwarfDie;
using DwarfDiePtr = std::shared_ptr<DwarfDie>;

class SymbolNotFoundException : public std::runtime_error {
   public:
    explicit SymbolNotFoundException(std::string member_path)
        : std::runtime_error("Cannot find member: " + member_path), member_path_(std::move(member_path)) {}
    const std::string& member_path() const { return member_path_; }

   private:
    std::string member_path_;
};

class TypeMismatchException : public std::runtime_error {
   public:
    TypeMismatchException(std::string operation, std::string actual_type)
        : std::runtime_error("Cannot perform '" + operation + "' on type '" + actual_type + "'"),
          operation_(std::move(operation)),
          actual_type_(std::move(actual_type)) {}
    const std::string& operation() const { return operation_; }
    const std::string& actual_type() const { return actual_type_; }

   private:
    std::string operation_;
    std::string actual_type_;
};

class InvalidArrayAccessException : public std::runtime_error {
   public:
    InvalidArrayAccessException(int64_t index, std::optional<uint64_t> length)
        : std::runtime_error("Array index " + std::to_string(index) + " out of bounds"),
          index_(index),
          length_(length) {}
    int64_t index() const { return index_; }
    std::optional<uint64_t> length() const { return length_; }

   private:
    int64_t index_;
    std::optional<uint64_t> length_;
};

class DataLossException : public std::runtime_error {
   public:
    DataLossException(std::string value_repr, std::string type_name)
        : std::runtime_error("Data loss writing " + value_repr + " to " + type_name),
          value_repr_(std::move(value_repr)),
          type_name_(std::move(type_name)) {}
    const std::string& value_repr() const { return value_repr_; }
    const std::string& type_name() const { return type_name_; }

   private:
    std::string value_repr_;
    std::string type_name_;
};

// In-memory view of a variable located by DWARF.
class ElfVariable {
   public:
    // Variant returned by read_value / accepted by write_value.
    using Value = std::variant<bool, int64_t, uint64_t, float, double, std::string>;

    ElfVariable(DwarfDiePtr type_die, uint64_t address, std::shared_ptr<MemoryAccess> memory_access);
    ~ElfVariable();
    ElfVariable(const ElfVariable&);
    ElfVariable(ElfVariable&&) noexcept;
    ElfVariable& operator=(const ElfVariable&);
    ElfVariable& operator=(ElfVariable&&) noexcept;

    const DwarfDiePtr& get_type_die() const { return type_die; }
    uint64_t get_address() const { return address; }
    const std::shared_ptr<MemoryAccess>& get_memory_access() const { return memory_access; }

    // Size in bytes of this variable's resolved type. Throws if the type DIE
    // doesn't expose a size.
    uint64_t get_size() const;

    // Walks struct/union/inheritance members to find `member_name`.
    ElfVariable get_member(std::string_view member_name) const;

    // Dereferences a pointer variable. Reads the pointer bytes from live
    // memory and returns a ElfVariable for the pointee.
    ElfVariable dereference() const;

    // Indexes into an array or pointer variable.
    ElfVariable get_index(int64_t i) const;

    // Number of elements in the first array dimension.
    uint64_t get_length() const;

    // Reads `get_size()` bytes from the live address.
    std::vector<std::byte> read_bytes() const;
    void read_bytes(std::span<std::byte> buffer) const;

    // Reads the variable's value as a scalar. Supported tags: base_type,
    // pointer_type, enumeration_type. Anything else throws
    // TypeMismatchException.
    Value read_value() const;

    // Writes a scalar value. `check_data_loss` triggers DataLossException
    // when the round-trip changes the value (e.g. assigning 1.5 to int).
    void write_value(Value value, bool check_data_loss = true);

    // Snapshots the variable's bytes and returns a new ElfVariable
    // backed by a CachedReadMemoryAccess. Subsequent member / dereference /
    // index walks served from the cache instead of re-hitting live memory.
    // For pointer variables, dereferences first and then snapshots.
    ElfVariable read() const;

    // Convert read Value to string.
    static std::string value_to_string(const Value& v);

   private:
    DwarfDiePtr type_die;
    uint64_t address;
    std::shared_ptr<MemoryAccess> memory_access;
};

}  // namespace ttexalens::native_elf

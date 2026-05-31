// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "variable.hpp"

#include <cstring>

#include "dwarf_attribute.hpp"
#include "dwarf_die.hpp"

using namespace std::literals;

namespace ttexalens::native_elf {

namespace {

// Walks the unnamed struct/union members of `type_die` looking for a child
// named `member_name`. Returns {offset_into_type_die, member_die} on hit or
// {nullopt, nullptr} on miss. Mirrors ElfVariable._resolve_unnamed_struct_union_member.
std::pair<std::optional<uint64_t>, NativeDwarfDiePtr> resolve_unnamed_struct_union_member(
    const NativeDwarfDie& type_die, std::string_view name) {
    for (auto child = type_die.get_first_child(); child; child = child->get_next_sibling()) {
        if (!child->get_name().empty() || child->get_tag() != NativeDwarfDieTag::member) {
            continue;
        }
        auto struct_union_type = child->get_resolved_type();
        if (!struct_union_type) {
            continue;
        }
        if (auto member = struct_union_type->find_child_by_name(name)) {
            return {child->get_address(), member};
        }
        auto [nested_offset, nested_member] = resolve_unnamed_struct_union_member(*struct_union_type, name);
        if (nested_member && nested_offset.has_value()) {
            auto child_address = child->get_address();
            if (!child_address.has_value()) {
                continue;
            }
            return {*nested_offset + *child_address, nested_member};
        }
    }
    return {std::nullopt, nullptr};
}

// Recursively walks DW_TAG_inheritance children of `type_die`. Mirrors
// ElfVariable._resolve_inheritance_member.
std::pair<std::optional<uint64_t>, NativeDwarfDiePtr> resolve_inheritance_member(const NativeDwarfDie& type_die,
                                                                                 std::string_view name,
                                                                                 uint64_t offset = 0) {
    for (auto child = type_die.get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_tag() != NativeDwarfDieTag::inheritance) {
            continue;
        }
        auto child_address = child->get_address();
        if (!child_address.has_value()) {
            continue;
        }
        uint64_t data_member_location = offset + *child_address;
        auto child_type = child->get_resolved_type();
        if (!child_type) {
            continue;
        }
        if (auto member = child_type->find_child_by_name(name)) {
            return {data_member_location, member};
        }
        auto [inherited_offset, inherited_member] = resolve_inheritance_member(*child_type, name, data_member_location);
        if (inherited_member && inherited_offset.has_value()) {
            return {inherited_offset, inherited_member};
        }
        auto [unnamed_offset, unnamed_member] = resolve_unnamed_struct_union_member(*child_type, name);
        if (unnamed_member && unnamed_offset.has_value()) {
            return {data_member_location + *unnamed_offset, unnamed_member};
        }
    }
    return {std::nullopt, nullptr};
}

// Peels typedef/const/volatile wrappers off an enum so we can ask the
// underlying base type for size/signedness during read/write_value.
NativeDwarfDiePtr resolve_enum_base(NativeDwarfDiePtr type_die) {
    while (type_die && type_die->get_tag() == NativeDwarfDieTag::enumeration_type) {
        auto resolved = type_die->get_resolved_type();
        if (!resolved || resolved.get() == type_die.get()) {
            break;
        }
        type_die = resolved;
    }
    return type_die;
}

// Little-endian load of `size` bytes (1..8) as an unsigned 64-bit integer.
uint64_t load_uint_le(const std::vector<std::byte>& bytes, size_t size) {
    uint64_t value = 0;
    for (size_t i = 0; i < size && i < bytes.size(); ++i) {
        value |= static_cast<uint64_t>(bytes[i]) << (8 * i);
    }
    return value;
}

// Sign-extends an LE-loaded value at the given byte width.
int64_t sign_extend(uint64_t raw, size_t size) {
    if (size == 0 || size >= 8) {
        return static_cast<int64_t>(raw);
    }
    const uint64_t sign_bit = uint64_t{1} << (8 * size - 1);
    if (raw & sign_bit) {
        const uint64_t mask = ~((uint64_t{1} << (8 * size)) - 1);
        raw |= mask;
    }
    return static_cast<int64_t>(raw);
}

// Stores the low `size` bytes of `value` in LE order into `out`.
void store_uint_le(std::vector<std::byte>& out, uint64_t value, size_t size) {
    out.resize(size);
    for (size_t i = 0; i < size; ++i) {
        out[i] = static_cast<std::byte>((value >> (8 * i)) & 0xFF);
    }
}

// Returns the variant's value as double for data-loss round-trip checks.
double value_as_double(const NativeElfVariable::Value& v) {
    return std::visit(
        [](auto&& x) -> double {
            using T = std::decay_t<decltype(x)>;
            if constexpr (std::is_same_v<T, bool>) {
                return x ? 1.0 : 0.0;
            } else {
                return static_cast<double>(x);
            }
        },
        v);
}

}  // namespace

NativeElfVariable::NativeElfVariable(NativeDwarfDiePtr type_die, uint64_t address,
                                     std::shared_ptr<MemoryAccess> memory_access)
    : type_die(std::move(type_die)), address(address), memory_access(std::move(memory_access)) {}

NativeElfVariable::~NativeElfVariable() = default;
NativeElfVariable::NativeElfVariable(const NativeElfVariable&) = default;
NativeElfVariable::NativeElfVariable(NativeElfVariable&&) noexcept = default;
NativeElfVariable& NativeElfVariable::operator=(const NativeElfVariable&) = default;
NativeElfVariable& NativeElfVariable::operator=(NativeElfVariable&&) noexcept = default;

uint64_t NativeElfVariable::get_size() const {
    auto size = type_die->get_size();
    if (!size.has_value()) {
        throw TypeMismatchException("get_size", type_die->get_path());
    }
    return *size;
}

NativeElfVariable NativeElfVariable::get_member(std::string_view member_name) const {
    if (type_die->get_tag() == NativeDwarfDieTag::pointer_type) {
        return dereference().get_member(member_name);
    }

    uint64_t offset = 0;
    NativeDwarfDiePtr child_die = type_die->find_child_by_name(member_name);
    if (!child_die) {
        auto [resolved_offset, resolved_child] = resolve_unnamed_struct_union_member(*type_die, member_name);
        if (resolved_child && resolved_offset.has_value()) {
            offset = *resolved_offset;
            child_die = resolved_child;
        }
    }
    if (!child_die) {
        auto [resolved_offset, resolved_child] = resolve_inheritance_member(*type_die, member_name);
        if (resolved_child && resolved_offset.has_value()) {
            offset = *resolved_offset;
            child_die = resolved_child;
        }
    }
    if (!child_die) {
        std::string path = type_die->get_path();
        path += "::";
        path += member_name;
        throw SymbolNotFoundException(std::move(path));
    }
    auto child_address = child_die->get_address();
    if (!child_address.has_value()) {
        std::string path = type_die->get_path();
        path += "::";
        path += member_name;
        throw SymbolNotFoundException(std::move(path));
    }
    auto resolved_type = child_die->get_resolved_type();
    return NativeElfVariable(std::move(resolved_type), address + *child_address + offset, memory_access);
}

NativeElfVariable NativeElfVariable::dereference() const {
    if (type_die->get_tag() != NativeDwarfDieTag::pointer_type) {
        throw TypeMismatchException("dereference", type_die->get_path());
    }
    auto ptr_size = type_die->get_size();
    if (!ptr_size.has_value()) {
        throw TypeMismatchException("dereference", type_die->get_path());
    }
    auto deref_type = type_die->get_dereference_type();
    if (!deref_type) {
        throw TypeMismatchException("dereference", type_die->get_path());
    }
    std::vector<std::byte> bytes(*ptr_size);
    memory_access->read(address, bytes);
    uint64_t pointee = load_uint_le(bytes, *ptr_size);
    return NativeElfVariable(std::move(deref_type), pointee, memory_access);
}

NativeElfVariable NativeElfVariable::get_index(int64_t i) const {
    const auto tag = type_die->get_tag();
    if (tag != NativeDwarfDieTag::array_type && tag != NativeDwarfDieTag::pointer_type) {
        throw TypeMismatchException("index", type_die->get_path());
    }

    NativeDwarfDiePtr element_type;
    uint64_t base_address = address;
    if (tag == NativeDwarfDieTag::pointer_type) {
        element_type = type_die->get_dereference_type();
        base_address = dereference().get_address();
    } else {
        element_type = type_die->get_array_element_type();
    }
    if (!element_type) {
        throw TypeMismatchException("index", type_die->get_path());
    }
    auto elem_size = element_type->get_size();
    if (!elem_size.has_value()) {
        throw TypeMismatchException("index", type_die->get_path());
    }
    uint64_t new_address = base_address + static_cast<uint64_t>(i) * *elem_size;
    return NativeElfVariable(std::move(element_type), new_address, memory_access);
}

uint64_t NativeElfVariable::get_length() const {
    if (type_die->get_tag() != NativeDwarfDieTag::array_type) {
        throw TypeMismatchException("len", type_die->get_path());
    }
    for (auto child = type_die->get_first_child(); child; child = child->get_next_sibling()) {
        auto upper_bound = child->get_attribute(NativeDwarfAttributeTag::upper_bound);
        if (upper_bound == nullptr) {
            continue;
        }
        const auto& value = upper_bound->get_value();
        if (auto* signed_val = std::get_if<int64_t>(&value)) {
            return static_cast<uint64_t>(*signed_val) + 1;
        }
        if (auto* unsigned_val = std::get_if<uint64_t>(&value)) {
            return *unsigned_val + 1;
        }
    }
    throw InvalidArrayAccessException(0, std::nullopt);
}

void NativeElfVariable::read_bytes(std::span<std::byte> buffer) const {
    auto size = get_size();
    if (buffer.size() < size) {
        throw std::invalid_argument("Buffer too small for variable size");
    }
    if (buffer.size() > size) {
        buffer = buffer.first(size);
    }
    memory_access->read(address, buffer);
}

std::vector<std::byte> NativeElfVariable::read_bytes() const {
    std::vector<std::byte> bytes(get_size());
    read_bytes(bytes);
    return bytes;
}

NativeElfVariable::Value NativeElfVariable::read_value() const {
    auto type = type_die;
    const auto tag = type->get_tag();
    if (tag != NativeDwarfDieTag::base_type && tag != NativeDwarfDieTag::pointer_type &&
        tag != NativeDwarfDieTag::enumeration_type) {
        throw TypeMismatchException("read_value", type->get_path());
    }
    if (tag == NativeDwarfDieTag::enumeration_type) {
        type = resolve_enum_base(type);
    }

    auto type_size_opt = type->get_size();
    if (!type_size_opt.has_value()) {
        throw TypeMismatchException("read_value", type->get_path());
    }
    const size_t type_size = static_cast<size_t>(*type_size_opt);

    std::vector<std::byte> bytes(type_size);
    memory_access->read(address, bytes);

    if (type->get_tag() == NativeDwarfDieTag::pointer_type) {
        // Match Python: pointer.read_value() returns the dereferenced address.
        return static_cast<uint64_t>(load_uint_le(bytes, type_size));
    }

    const auto name = type->get_name();
    if (name == "float"sv && type_size >= sizeof(float)) {
        float f = 0.0f;
        std::memcpy(&f, bytes.data(), sizeof(float));
        return f;
    }
    if (name == "double"sv && type_size >= sizeof(double)) {
        double d = 0.0;
        std::memcpy(&d, bytes.data(), sizeof(double));
        return d;
    }
    if (name == "bool"sv) {
        return load_uint_le(bytes, type_size) != 0;
    }
    const uint64_t raw = load_uint_le(bytes, type_size);
    if (type->is_signed_type()) {
        return sign_extend(raw, type_size);
    }
    return raw;
}

void NativeElfVariable::write_value(Value value, bool check_data_loss) {
    auto type = type_die;
    const auto tag = type->get_tag();
    if (tag != NativeDwarfDieTag::base_type && tag != NativeDwarfDieTag::enumeration_type) {
        throw TypeMismatchException("write_value", type->get_path());
    }
    if (tag == NativeDwarfDieTag::enumeration_type) {
        type = resolve_enum_base(type);
    }

    auto type_size_opt = type->get_size();
    if (!type_size_opt.has_value()) {
        throw TypeMismatchException("write_value", type->get_path());
    }
    const size_t type_size = static_cast<size_t>(*type_size_opt);
    const std::string_view name(type->get_name());
    std::vector<std::byte> bytes;

    if (name == "float"sv || name == "double"sv) {
        // Encode the floating-point value to bytes.
        double d = value_as_double(value);
        if (name == "float"sv) {
            float f = static_cast<float>(d);
            bytes.resize(type_size);
            std::memcpy(bytes.data(), &f, std::min(sizeof(float), bytes.size()));
        } else {
            bytes.resize(type_size);
            std::memcpy(bytes.data(), &d, std::min(sizeof(double), bytes.size()));
        }
        if (check_data_loss) {
            // Round-trip the encoded value back to a double and compare. For
            // integer sources we additionally verify the int value round-
            // trips exactly through the chosen float type — `double` only has
            // 53 bits of mantissa, so a 64-bit integer near the extremes
            // can't be represented losslessly.
            double rt = 0.0;
            if (name == "float"sv) {
                float rt_f = 0.0f;
                std::memcpy(&rt_f, bytes.data(), std::min(sizeof(float), bytes.size()));
                rt = static_cast<double>(rt_f);
            } else {
                std::memcpy(&rt, bytes.data(), std::min(sizeof(double), bytes.size()));
            }
            bool ok = std::visit(
                [&](auto&& x) -> bool {
                    using T = std::decay_t<decltype(x)>;
                    if constexpr (std::is_same_v<T, bool>) {
                        return rt == (x ? 1.0 : 0.0);
                    } else if constexpr (std::is_same_v<T, int64_t>) {
                        return static_cast<int64_t>(rt) == x && static_cast<double>(static_cast<int64_t>(rt)) == rt;
                    } else if constexpr (std::is_same_v<T, uint64_t>) {
                        return static_cast<uint64_t>(rt) == x && static_cast<double>(static_cast<uint64_t>(rt)) == rt;
                    } else {
                        return rt == static_cast<double>(x);
                    }
                },
                value);
            if (!ok) {
                throw DataLossException(value_to_string(value), std::string(name));
            }
        }
    } else if (name == "bool"sv) {
        const bool truthy = std::visit(
            [](auto&& x) -> bool {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, bool>) {
                    return x;
                } else {
                    return x != T{0};
                }
            },
            value);
        store_uint_le(bytes, truthy ? 1u : 0u, type_size);
    } else {
        // Integer base type. Take the value as int64_t when signed, uint64_t
        // when unsigned. For floats we round-trip and verify on data loss.
        const bool signed_dest = type->is_signed_type();
        int64_t signed_val = 0;
        uint64_t unsigned_val = 0;
        bool came_from_float = false;
        double float_input = 0.0;

        std::visit(
            [&](auto&& x) {
                using T = std::decay_t<decltype(x)>;
                if constexpr (std::is_same_v<T, bool>) {
                    signed_val = x ? 1 : 0;
                    unsigned_val = x ? 1 : 0;
                } else if constexpr (std::is_same_v<T, int64_t>) {
                    signed_val = x;
                    unsigned_val = static_cast<uint64_t>(x);
                } else if constexpr (std::is_same_v<T, uint64_t>) {
                    signed_val = static_cast<int64_t>(x);
                    unsigned_val = x;
                } else if constexpr (std::is_same_v<T, float> || std::is_same_v<T, double>) {
                    came_from_float = true;
                    float_input = static_cast<double>(x);
                    signed_val = static_cast<int64_t>(x);
                    unsigned_val = static_cast<uint64_t>(static_cast<int64_t>(x));
                }
            },
            value);

        const uint64_t raw = signed_dest ? static_cast<uint64_t>(signed_val) : unsigned_val;
        store_uint_le(bytes, raw, type_size);

        if (check_data_loss) {
            const uint64_t loaded = load_uint_le(bytes, type_size);
            const int64_t loaded_signed = sign_extend(loaded, type_size);
            bool ok;
            if (came_from_float) {
                ok = static_cast<double>(signed_dest ? loaded_signed : static_cast<int64_t>(loaded)) == float_input;
            } else if (signed_dest) {
                ok = loaded_signed == signed_val;
            } else {
                ok = loaded == unsigned_val;
            }
            if (!ok) {
                throw DataLossException(value_to_string(value), std::string(name));
            }
        }
    }

    memory_access->write(address,
                         std::span<const std::byte>(reinterpret_cast<const std::byte*>(bytes.data()), bytes.size()));
}

NativeElfVariable NativeElfVariable::read() const {
    if (type_die->get_tag() == NativeDwarfDieTag::pointer_type) {
        return dereference().read();
    }
    auto data = read_bytes();
    auto cached = std::make_shared<CachedReadMemoryAccess>(address, std::move(data), memory_access);
    return NativeElfVariable(type_die, address, std::move(cached));
}

std::string NativeElfVariable::value_to_string(const Value& v) {
    return std::visit(
        [](auto&& x) -> std::string {
            using T = std::decay_t<decltype(x)>;
            if constexpr (std::is_same_v<T, bool>) {
                return x ? "true" : "false";
            } else {
                return std::to_string(x);
            }
        },
        v);
}

}  // namespace ttexalens::native_elf

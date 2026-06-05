// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include <cstdint>
#include <cstdio>
#include <string>
#include <variant>

#include "bindings.hpp"
#include "dwarf_die.hpp"
#include "memory_access.hpp"
#include "variable.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

namespace {

// Helpers for ElfVariable dunders: reduce a C++ TypeMismatchException
// (raised when read_value is called on a non-base/pointer/enum type) to
// Python's NotImplemented so the arithmetic/comparison operators degrade
// gracefully, matching the Python ElfVariable contract.
nb::object var_value_obj(const ElfVariable& self) { return nb::cast(self.read_value()); }

template <typename Op>
nb::object try_binop(const ElfVariable& self, nb::handle other, Op&& op) {
    try {
        return op(var_value_obj(self), other);
    } catch (const TypeMismatchException&) {
        return nb::borrow(Py_NotImplemented);
    } catch (const nb::python_error& e) {
        if (e.matches(PyExc_TypeError)) {
            return nb::borrow(Py_NotImplemented);
        }
        throw;
    }
}

}  // namespace

void bind_variable(nb::module_& m) {
    // Live view of a variable located by DWARF. Mirrors
    // ttexalens.elf.variable.ElfVariable: structural methods on the C++ side,
    // Python dunders wired here so call sites can keep doing `var.x.y[i] + 1`.
    nb::class_<ElfVariable>(m, "ElfVariable")
        .def(nb::init<ttexalens::native_elf::DwarfDiePtr, uint64_t, std::shared_ptr<MemoryAccess>>(),
             nb::arg("type_die"), nb::arg("address"), nb::arg("memory_access"))
        // Core structural / value methods.
        .def("get_member", &ElfVariable::get_member, nb::arg("member_name"))
        .def("dereference", &ElfVariable::dereference)
        .def("get_address", &ElfVariable::get_address)
        .def("get_size", &ElfVariable::get_size)
        .def("read_bytes",
             [](const ElfVariable& self) {
                 auto v = self.read_bytes();
                 return nb::bytes(reinterpret_cast<const char*>(v.data()), v.size());
             })
        .def("read_value", &ElfVariable::read_value)
        .def("write_value", &ElfVariable::write_value, nb::arg("value"), nb::arg("check_data_loss") = true)
        // Snapshots the variable's bytes; subsequent member/index walks read
        // from the cache instead of re-hitting live memory.
        .def("read", &ElfVariable::read)
        // Array helpers — materialize all elements eagerly.
        .def("as_list",
             [](const ElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list out;
                 for (uint64_t i = 0; i < n; ++i) {
                     out.append(nb::cast(self.get_index(static_cast<int64_t>(i))));
                 }
                 return out;
             })
        .def("as_value_list",
             [](const ElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list out;
                 for (uint64_t i = 0; i < n; ++i) {
                     out.append(nb::cast(self.get_index(static_cast<int64_t>(i)).read_value()));
                 }
                 return out;
             })
        // __getitem__ handles both struct member access (string keys) and
        // array/pointer indexing (integer keys). Mirrors ElfVariable.__getitem__.
        .def("__getitem__",
             [](const ElfVariable& self, nb::handle key) -> ElfVariable {
                 if (nb::isinstance<nb::str>(key)) {
                     return self.get_member(nb::cast<std::string>(key));
                 }
                 if (nb::isinstance<nb::int_>(key)) {
                     return self.get_index(nb::cast<int64_t>(key));
                 }
                 // Fall back to int conversion (mirrors Python: int(key)).
                 try {
                     return self.get_index(nb::cast<int64_t>(key));
                 } catch (const nb::cast_error&) {
                     throw nb::type_error("ElfVariable indices must be integers or strings");
                 }
             })
        // __getattr__ is only invoked when normal attribute lookup fails, so
        // bound C++ methods take precedence over struct members of the same
        // name (matching the Python implementation).
        .def("__getattr__", [](const ElfVariable& self, std::string_view name) { return self.get_member(name); })
        .def("__len__", &ElfVariable::get_length)
        .def("__iter__",
             [](const ElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list elements;
                 for (uint64_t i = 0; i < n; ++i) {
                     elements.append(nb::cast(self.get_index(static_cast<int64_t>(i))));
                 }
                 return nb::iter(elements);
             })
        // Comparison: equal/less-than/etc. fall back to NotImplemented on a
        // type mismatch, matching the Python ElfVariable contract. Array
        // variables compare element-by-element with any other indexable
        // sequence.
        .def(
            "__eq__",
            [](const ElfVariable& self, nb::handle other) -> nb::object {
                if (self.get_type_die()->get_tag() == DwarfDieTag::array_type) {
                    if (nb::isinstance<nb::str>(other)) {
                        return try_binop(self, other,
                                         [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.equal(b)); });
                    }
                    if (!PyObject_HasAttrString(other.ptr(), "__len__") ||
                        !PyObject_HasAttrString(other.ptr(), "__getitem__")) {
                        return nb::cast(false);
                    }
                    try {
                        const uint64_t n = self.get_length();
                        if (n != nb::cast<uint64_t>(nb::module_::import_("builtins").attr("len")(other))) {
                            return nb::cast(false);
                        }
                        for (uint64_t i = 0; i < n; ++i) {
                            nb::object lhs = nb::cast(self.get_index(static_cast<int64_t>(i)));
                            nb::object rhs = other[i];
                            if (!lhs.equal(rhs)) {
                                return nb::cast(false);
                            }
                        }
                        return nb::cast(true);
                    } catch (...) {
                        return nb::cast(false);
                    }
                }
                return try_binop(self, other,
                                 [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.equal(b)); });
            },
            nb::sig("def __eq__(self, other: object, /) -> bool"))
        .def(
            "__ne__",
            [](const ElfVariable& self, nb::handle other) {
                return try_binop(self, other,
                                 [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.not_equal(b)); });
            },
            nb::sig("def __ne__(self, other: object, /) -> bool"))
        .def("__lt__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a < b); });
             })
        .def("__le__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a <= b); });
             })
        .def("__gt__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a > b); });
             })
        .def("__ge__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a >= b); });
             })
        // Arithmetic — read_value() + Python's native operator dispatch.
        .def("__add__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a + b; });
             })
        .def("__radd__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b + a; });
             })
        .def("__sub__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a - b; });
             })
        .def("__rsub__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b - a; });
             })
        .def("__mul__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a * b; });
             })
        .def("__rmul__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b * a; });
             })
        .def("__truediv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a / b; });
             })
        .def("__rtruediv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b / a; });
             })
        .def("__floordiv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a.floor_div(b); });
             })
        .def("__rfloordiv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b.floor_div(a); });
             })
        .def("__mod__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a % b; });
             })
        .def("__rmod__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b % a; });
             })
        // ** doesn't have an overloaded operator on nb::object, so go through
        // PyNumber_Power which mirrors Python's natural fallback to
        // NotImplemented when either operand doesn't support the operation.
        .def("__pow__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) -> nb::object {
                     PyObject* r = PyNumber_Power(a.ptr(), b.ptr(), Py_None);
                     if (r == nullptr) {
                         throw nb::python_error();
                     }
                     return nb::steal<nb::object>(r);
                 });
             })
        .def("__rpow__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) -> nb::object {
                     PyObject* r = PyNumber_Power(b.ptr(), a.ptr(), Py_None);
                     if (r == nullptr) {
                         throw nb::python_error();
                     }
                     return nb::steal<nb::object>(r);
                 });
             })
        // Bitwise.
        .def("__and__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a & b; });
             })
        .def("__rand__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b & a; });
             })
        .def("__or__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a | b; });
             })
        .def("__ror__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b | a; });
             })
        .def("__xor__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a ^ b; });
             })
        .def("__rxor__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b ^ a; });
             })
        .def("__lshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a << b; });
             })
        .def("__rlshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b << a; });
             })
        .def("__rshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a >> b; });
             })
        .def("__rrshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b >> a; });
             })
        // Unary. Return is int | float at runtime — annotate the stubs so
        // call sites like `abs(-var.x)` typecheck.
        .def(
            "__neg__", [](const ElfVariable& self) { return -var_value_obj(self); },
            nb::sig("def __neg__(self) -> int | float"))
        .def(
            "__pos__",
            [](const ElfVariable& self) {
                // Python's unary + on int/float is a no-op; on bool it promotes to int.
                // Call PyNumber_Positive to mirror that exactly.
                nb::object val = var_value_obj(self);
                PyObject* r = PyNumber_Positive(val.ptr());
                if (r == nullptr) {
                    throw nb::python_error();
                }
                return nb::steal<nb::object>(r);
            },
            nb::sig("def __pos__(self) -> int | float"))
        .def(
            "__abs__",
            [](const ElfVariable& self) { return nb::module_::import_("builtins").attr("abs")(var_value_obj(self)); },
            nb::sig("def __abs__(self) -> int | float"))
        .def(
            "__invert__", [](const ElfVariable& self) { return ~var_value_obj(self); },
            nb::sig("def __invert__(self) -> int"))
        // Truthiness — arrays are truthy when non-empty; scalars use the
        // underlying value (via Python's PyObject_IsTrue so int/float/bool
        // all work). Falls back to TypeMismatchException for composite types
        // (struct/union) that can't be read as a single value.
        .def("__bool__",
             [](const ElfVariable& self) {
                 if (self.get_type_die()->get_tag() == DwarfDieTag::array_type) {
                     return self.get_length() > 0;
                 }
                 nb::object val = var_value_obj(self);
                 int r = PyObject_IsTrue(val.ptr());
                 if (r < 0) {
                     throw nb::python_error();
                 }
                 return r != 0;
             })
        // Index conversion (so var can be used directly as a list index).
        .def("__index__",
             [](const ElfVariable& self) {
                 nb::object val = var_value_obj(self);
                 if (nb::isinstance<nb::int_>(val) || nb::isinstance<nb::bool_>(val)) {
                     return nb::cast<int64_t>(val);
                 }
                 if (nb::isinstance<nb::float_>(val)) {
                     double d = nb::cast<double>(val);
                     if (d == static_cast<int64_t>(d)) {
                         return static_cast<int64_t>(d);
                     }
                 }
                 throw nb::type_error("ElfVariable cannot be used as an index");
             })
        // Hashing — value-based when scalar, identity-based for composites.
        .def("__hash__",
             [](const ElfVariable& self) -> Py_hash_t {
                 try {
                     return PyObject_Hash(var_value_obj(self).ptr());
                 } catch (const TypeMismatchException&) {
                     auto tuple = nb::make_tuple(self.get_type_die()->get_offset(), self.get_address());
                     return PyObject_Hash(tuple.ptr());
                 }
             })
        // Formatting hooks. __str__ tries read_value() and renders enum
        // values as their qualified name; falls back to __repr__ on failure.
        .def("__str__",
             [](const ElfVariable& self) -> std::string {
                 try {
                     nb::object val = var_value_obj(self);
                     if (self.get_type_die()->get_tag() == DwarfDieTag::enumeration_type) {
                         for (auto child = self.get_type_die()->get_first_child(); child;
                              child = child->get_next_sibling()) {
                             auto cv = child->get_constant_value();
                             if (auto* iv = std::get_if<int64_t>(&cv)) {
                                 if (nb::cast<int64_t>(val) == *iv) {
                                     return child->get_path();
                                 }
                             } else if (auto* uv = std::get_if<uint64_t>(&cv)) {
                                 if (nb::cast<uint64_t>(val) == *uv) {
                                     return child->get_path();
                                 }
                             }
                         }
                     }
                     return nb::cast<std::string>(nb::str(val));
                 } catch (const TypeMismatchException&) {
                     // repr fallback when read_value is unsupported. Memory
                     // errors (Timeout/RiscHalt/Restricted) propagate.
                     return nb::cast<std::string>(nb::module_::import_("builtins").attr("repr")(nb::cast(self)));
                 }
             })
        .def("__repr__",
             [](const ElfVariable& self) {
                 std::string type_name(self.get_type_die()->get_name());
                 if (type_name.empty()) {
                     type_name = "Unknown";
                 }
                 std::string value_info;
                 try {
                     value_info = ", value=" + nb::cast<std::string>(nb::repr(var_value_obj(self)));
                 } catch (const TypeMismatchException&) {
                 }
                 std::string length_info;
                 try {
                     length_info = ", length=" + std::to_string(self.get_length());
                 } catch (const TypeMismatchException&) {
                 } catch (const InvalidArrayAccessException&) {
                 }
                 char addr_buf[32];
                 std::snprintf(addr_buf, sizeof(addr_buf), "0x%lx", static_cast<unsigned long>(self.get_address()));
                 return "ElfVariable(type_name='" + type_name + "', address=" + std::string(addr_buf) + value_info +
                        length_info + ")";
             })
        .def("__format__", [](const ElfVariable& self, std::string_view spec) {
            try {
                return nb::module_::import_("builtins")
                    .attr("format")(var_value_obj(self), nb::cast(std::string(spec)));
            } catch (const TypeMismatchException&) {
                return nb::module_::import_("builtins").attr("str")(nb::cast(self));
            }
        });
}

}  // namespace ttexalens::native_elf::bindings

// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/trampoline.h>

#include <cstddef>
#include <span>
#include <utility>
#include <vector>

#include "bindings.hpp"
#include "memory_access.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

namespace {

// Trampoline so Python can subclass MemoryAccess and provide implementations.
class MemoryAccessTrampoline : public MemoryAccess {
   public:
    NB_TRAMPOLINE(MemoryAccess, 4);

    void read(uint64_t address, std::span<std::byte> buffer) const override {
        nb::gil_scoped_acquire gil;
        nanobind::detail::ticket nb_ticket(nb_trampoline, "read", /*pure=*/true);
        // Hand Python a writable memoryview over our buffer — zero-copy on
        // the C++ to Python boundary. Python writes directly into it.
        PyObject* mv = PyMemoryView_FromMemory(reinterpret_cast<char*>(buffer.data()),
                                               static_cast<Py_ssize_t>(buffer.size()), PyBUF_WRITE);
        if (mv == nullptr) {
            throw nb::python_error();
        }
        nb::object py_buf = nb::steal<nb::object>(mv);
        nb_trampoline.base().attr(nb_ticket.key)(address, py_buf);
    }

    void write(uint64_t address, std::span<const std::byte> buffer) override {
        nb::gil_scoped_acquire gil;
        nanobind::detail::ticket nb_ticket(nb_trampoline, "write", /*pure=*/true);
        // Hand Python a read-only memoryview over our buffer — zero-copy on
        // the C++ to Python boundary.
        PyObject* mv = PyMemoryView_FromMemory(const_cast<char*>(reinterpret_cast<const char*>(buffer.data())),
                                               static_cast<Py_ssize_t>(buffer.size()), PyBUF_READ);
        if (mv == nullptr) {
            throw nb::python_error();
        }
        nb::object data = nb::steal<nb::object>(mv);
        nb_trampoline.base().attr(nb_ticket.key)(address, data);
    }

    uint64_t read_register(uint16_t register_index) const override { NB_OVERRIDE_PURE(read_register, register_index); }

    void write_register(uint16_t register_index, uint64_t value) override {
        NB_OVERRIDE_PURE(write_register, register_index, value);
    }
};

}  // namespace

void bind_memory_access(nb::module_& m) {
    nb::class_<MemoryAccess, MemoryAccessTrampoline>(m, "MemoryAccess")
        .def(nb::init<>())
        .def(
            "read",
            [](const MemoryAccess& self, uint64_t address, nb::handle buffer) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(buffer.ptr(), &buf, PyBUF_WRITABLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                self.read(address,
                          std::span<std::byte>(static_cast<std::byte*>(buf.buf), static_cast<size_t>(buf.len)));
            },
            nb::arg("address"), nb::arg("buffer"),
            nb::sig("def read(self, address: int, buffer: memoryview | bytearray) -> None"))
        .def(
            "write",
            [](MemoryAccess& self, uint64_t address, nb::handle data) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(data.ptr(), &buf, PyBUF_SIMPLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                self.write(address, std::span<const std::byte>(static_cast<const std::byte*>(buf.buf),
                                                               static_cast<size_t>(buf.len)));
            },
            nb::arg("address"), nb::arg("data"),
            nb::sig("def write(self, address: int, data: bytes | bytearray | memoryview) -> None"))
        .def("read_register", &MemoryAccess::read_register, nb::arg("register_index"))
        .def("write_register", &MemoryAccess::write_register, nb::arg("register_index"), nb::arg("value"));

    // MemoryAccess that raises on every operation. There's no per-instance
    // state, so a single process-wide shared_ptr (NoMemoryAccess.instance())
    // is what callers should use whenever a MemoryAccess is required but no
    // live target is available.
    nb::class_<NoMemoryAccess, MemoryAccess>(m, "NoMemoryAccess")
        .def(nb::init<>())
        .def_static("instance", &NoMemoryAccess::instance);

    // Concrete MemoryAccess that serves reads from a byte snapshot when the
    // address falls in the cached range, otherwise delegates to `base`. Used
    // by ElfVariable::read() but exposed here so Python can also
    // construct one directly.
    nb::class_<CachedReadMemoryAccess, MemoryAccess>(m, "CachedReadMemoryAccess")
        .def(
            "__init__",
            [](CachedReadMemoryAccess* self, uint64_t cached_address, nb::handle cached_data,
               std::shared_ptr<MemoryAccess> base) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(cached_data.ptr(), &buf, PyBUF_SIMPLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                std::vector<std::byte> data(static_cast<const std::byte*>(buf.buf),
                                            static_cast<const std::byte*>(buf.buf) + buf.len);
                new (self) CachedReadMemoryAccess(cached_address, std::move(data), std::move(base));
            },
            nb::arg("cached_address"), nb::arg("cached_data"), nb::arg("base"),
            nb::sig("def __init__(self, cached_address: int, cached_data: bytes | bytearray | memoryview, base: "
                    "MemoryAccess) -> None"));
}

}  // namespace ttexalens::native_elf::bindings

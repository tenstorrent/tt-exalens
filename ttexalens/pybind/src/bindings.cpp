// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include "bindings.h"

#include <ttexalensserver/jtag_implementation.h>
#include <ttexalensserver/open_implementation.h>
#include <ttexalensserver/umd_implementation.h>

#include <fstream>
#include <optional>

static std::unique_ptr<tt::exalens::ttexalens_implementation> ttexalens_implementation;

class scoped_null_stdout {
   private:
    std::streambuf *original_stdout;
    std::ofstream null_stream;

   public:
    scoped_null_stdout() {
        original_stdout = std::cout.rdbuf();
        null_stream.open("/dev/null");
        std::cout.rdbuf(null_stream.rdbuf());
    }

    ~scoped_null_stdout() { std::cout.rdbuf(original_stdout); }
};

void set_ttexalens_implementation(std::unique_ptr<tt::exalens::ttexalens_implementation> imp) {
    ttexalens_implementation = std::move(imp);
}

bool open_device(const std::string &binary_directory, const std::vector<uint8_t> &wanted_devices, bool init_jtag,
                 bool initialize_with_noc1) {
    try {
        // Since tt::umd::Cluster is printing some output and we don't want to see it in python, we disable std::cout
        scoped_null_stdout null_stdout;

        if (init_jtag) {
            ttexalens_implementation = tt::exalens::open_implementation<tt::exalens::jtag_implementation>::open(
                binary_directory, wanted_devices, initialize_with_noc1);
        } else {
            ttexalens_implementation = tt::exalens::open_implementation<tt::exalens::umd_implementation>::open(
                binary_directory, wanted_devices, initialize_with_noc1);
        }
        if (!ttexalens_implementation) {
            return false;
        }
    } catch (std::runtime_error &error) {
        std::cerr << "Cannot open device: " << error.what() << std::endl;
        return false;
    }
    return true;
}

std::optional<uint32_t> pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->pci_read32(noc_id, chip_id, noc_x, noc_y, address);
    }
    return {};
}

std::optional<uint32_t> pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->pci_write32(noc_id, chip_id, noc_x, noc_y, address, data);
    }
    return {};
}

std::optional<pybind11::object> pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                         uint64_t address, uint32_t size) {
    if (ttexalens_implementation) {
        auto data = ttexalens_implementation->pci_read(noc_id, chip_id, noc_x, noc_y, address, size);

        if (data) {
            // This is a hacky way to create a bytes object for Python so that we avoid multiple
            // copying. Pyobject is created manually and then passed to pybind11::reinterpret_steal
            // to prevent memory leak.
            // See https://github.com/pybind/pybind11/issues/1236
            PyBytesObject *bytesObject = nullptr;

            bytesObject = (PyBytesObject *)PyObject_Malloc(offsetof(PyBytesObject, ob_sval) + size + 1);

            PyObject_INIT_VAR(bytesObject, &PyBytes_Type, size);
            bytesObject->ob_shash = -1;
            bytesObject->ob_sval[size] = '\0';

            for (size_t i = 0; i < size; i++) {
                bytesObject->ob_sval[i] = data.value()[i];
            }

            return pybind11::reinterpret_steal<pybind11::object>((PyObject *)bytesObject);
        }
    }
    return {};
}

std::optional<uint32_t> pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                  pybind11::buffer data, uint32_t size) {
    if (ttexalens_implementation) {
        pybind11::buffer_info info = data.request();
        uint8_t *data_ptr = static_cast<uint8_t *>(info.ptr);

        return ttexalens_implementation->pci_write(noc_id, chip_id, noc_x, noc_y, address, data_ptr, size);
    }
    return {};
}

std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->pci_read32_raw(chip_id, address);
    }
    return {};
}

std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->pci_write32_raw(chip_id, address, data);
    }
    return {};
}

std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->dma_buffer_read32(chip_id, address, channel);
    }
    return {};
}

std::optional<std::string> pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                         uint64_t address, uint32_t size, uint8_t data_format) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->pci_read_tile(noc_id, chip_id, noc_x, noc_y, address, size, data_format);
    }
    return {};
}

std::optional<uint32_t> jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->jtag_read32(noc_id, chip_id, noc_x, noc_y, address);
    }
    return {};
}

std::optional<uint32_t> jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                     uint32_t data) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->jtag_write32(noc_id, chip_id, noc_x, noc_y, address, data);
    }
    return {};
}

std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->jtag_read32_axi(chip_id, address);
    }
    return {};
}

std::optional<uint32_t> jtag_write32_axi(uint8_t chip_id, uint64_t address, uint32_t data) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->jtag_write32_axi(chip_id, address, data);
    }
    return {};
}

std::optional<std::string> get_cluster_description() {
    if (ttexalens_implementation) {
        return ttexalens_implementation->get_cluster_description();
    }
    return {};
}

std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                              const std::string &core_type,
                                                              const std::string &coord_system) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system);
    }
    return {};
}

std::optional<std::vector<uint8_t>> get_device_ids() {
    if (ttexalens_implementation) {
        return ttexalens_implementation->get_device_ids();
    }
    return {};
}

std::optional<std::string> get_device_arch(uint8_t chip_id) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->get_device_arch(chip_id);
    }
    return {};
}

std::optional<std::string> get_device_soc_description(uint8_t chip_id) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->get_device_soc_description(chip_id);
    }
    return {};
}

std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t noc_id, uint8_t chip_id, uint32_t msg_code,
                                                           bool wait_for_done, uint32_t arg0, uint32_t arg1,
                                                           int timeout) {
    if (ttexalens_implementation) {
        return ttexalens_implementation->arc_msg(noc_id, chip_id, msg_code, wait_for_done, arg0, arg1, timeout);
    }
    return {};
}

PYBIND11_MODULE(ttexalens_pybind, m) {
    m.def("open_device", &open_device, "Opens tt device. Prints error message if failed.",
          pybind11::arg("binary_directory"), pybind11::arg_v("wanted_devices", std::vector<uint8_t>(), "[]"),
          pybind11::arg("init_jtag"), pybind11::arg("initialize_with_noc1"));
    m.def("pci_read32", &pci_read32, "Reads 4 bytes from PCI address", pybind11::arg("noc_id"),
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"));
    m.def("pci_write32", &pci_write32, "Writes 4 bytes to PCI address", pybind11::arg("noc_id"),
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"),
          pybind11::arg("data"));
    m.def("pci_read", &pci_read, "Reads data from PCI address", pybind11::arg("noc_id"), pybind11::arg("chip_id"),
          pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"), pybind11::arg("size"));
    m.def("pci_write", &pci_write, "Writes data to PCI address", pybind11::arg("noc_id"), pybind11::arg("chip_id"),
          pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"), pybind11::arg("data"),
          pybind11::arg("size"));
    m.def("pci_read32_raw", &pci_read32_raw, "Reads 4 bytes from PCI address", pybind11::arg("chip_id"),
          pybind11::arg("address"));
    m.def("pci_write32_raw", &pci_write32_raw, "Writes 4 bytes to PCI address", pybind11::arg("chip_id"),
          pybind11::arg("address"), pybind11::arg("data"));
    m.def("dma_buffer_read32", &dma_buffer_read32, "Reads 4 bytes from DMA buffer", pybind11::arg("chip_id"),
          pybind11::arg("address"), pybind11::arg("channel"));
    m.def("pci_read_tile", &pci_read_tile, "Reads tile from PCI address", pybind11::arg("noc_id"),
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"),
          pybind11::arg("size"), pybind11::arg("data_format"));
    m.def("get_cluster_description", &get_cluster_description, "Returns cluster description");
    m.def("convert_from_noc0", &convert_from_noc0, "Convert noc0 coordinate into specified coordinate system",
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("core_type"),
          pybind11::arg("coord_system"));
    m.def("get_device_ids", &get_device_ids, "Returns device ids");
    m.def("get_device_arch", &get_device_arch, "Returns device architecture", pybind11::arg("chip_id"));
    m.def("get_device_soc_description", &get_device_soc_description, "Returns device SoC description",
          pybind11::arg("chip_id"));
    m.def("jtag_read32", &jtag_read32, "Reads 4 bytes from NOC address using JTAG", pybind11::arg("noc_id"),
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"));
    m.def("jtag_write32", &jtag_write32, "Writes 4 bytes to NOC address using JTAG", pybind11::arg("noc_id"),
          pybind11::arg("chip_id"), pybind11::arg("noc_x"), pybind11::arg("noc_y"), pybind11::arg("address"),
          pybind11::arg("data"));
    m.def("jtag_read32_axi", &jtag_read32_axi, "Reads 4 bytes from AXI address using JTAG", pybind11::arg("chip_id"),
          pybind11::arg("address"));
    m.def("jtag_write32_axi", &jtag_write32_axi, "Writes 4 bytes to AXI address using JTAG", pybind11::arg("chip_id"),
          pybind11::arg("address"), pybind11::arg("data"));

    // Bind arc_msg with explicit lambda to ensure type resolution
    m.def("arc_msg", &arc_msg, "Send ARC message", pybind11::arg("noc_id"), pybind11::arg("chip_id"),
          pybind11::arg("msg_code"), pybind11::arg("wait_for_done"), pybind11::arg("arg0"), pybind11::arg("arg1"),
          pybind11::arg("timeout"));
}

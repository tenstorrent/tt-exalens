// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <jtag_implementation.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/vector.h>
#include <open_implementation.h>
#include <umd_implementation.h>

#include <optional>

using namespace nanobind::literals;

// Wrapper class that encapsulates the ttexalens_implementation
class TTExaLensImplementation {
   private:
    std::unique_ptr<tt::exalens::ttexalens_implementation> implementation;

   public:
    TTExaLensImplementation(std::unique_ptr<tt::exalens::ttexalens_implementation> impl)
        : implementation(std::move(impl)) {
        if (!implementation) {
            throw std::runtime_error("TTExaLens implementation not provided");
        }
    }

    template <typename T>
    T _check_result(const std::optional<T> &result) {
        if (!result.has_value()) {
            throw std::runtime_error("TTExaLens implementation not implemented");
        }
        return result.value();
    }

    uint32_t pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) {
        return _check_result(implementation->pci_read32(noc_id, chip_id, noc_x, noc_y, address));
    }

    uint32_t pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                         uint32_t data) {
        return _check_result(implementation->pci_write32(noc_id, chip_id, noc_x, noc_y, address, data));
    }

    nanobind::bytes pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                             uint32_t size) {
        auto data = implementation->pci_read(noc_id, chip_id, noc_x, noc_y, address, size);
        if (data) {
            // For nanobind, we can use nanobind::bytes directly
            return nanobind::bytes(reinterpret_cast<const char *>(data.value().data()), size);
        }
        throw std::runtime_error("TTExaLens implementation not implemented");
    }

    uint32_t pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                       nanobind::bytes data) {
        const char *data_ptr = data.c_str();
        return _check_result(implementation->pci_write(noc_id, chip_id, noc_x, noc_y, address,
                                                       reinterpret_cast<const uint8_t *>(data_ptr), data.size()));
    }

    uint32_t pci_read32_raw(uint8_t chip_id, uint64_t address) {
        return _check_result(implementation->pci_read32_raw(chip_id, address));
    }

    uint32_t pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
        return _check_result(implementation->pci_write32_raw(chip_id, address, data));
    }

    uint32_t dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
        return _check_result(implementation->dma_buffer_read32(chip_id, address, channel));
    }

    std::string pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                              uint32_t size, uint8_t data_format) {
        return _check_result(implementation->pci_read_tile(noc_id, chip_id, noc_x, noc_y, address, size, data_format));
    }

    std::string get_cluster_description() { return _check_result(implementation->get_cluster_description()); }

    std::tuple<uint8_t, uint8_t> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                   const std::string &core_type, const std::string &coord_system) {
        return _check_result(implementation->convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system));
    }

    std::vector<uint8_t> get_device_ids() { return _check_result(implementation->get_device_ids()); }

    std::string get_device_arch(uint8_t chip_id) { return _check_result(implementation->get_device_arch(chip_id)); }

    std::string get_device_soc_description(uint8_t chip_id) {
        return _check_result(implementation->get_device_soc_description(chip_id));
    }

    uint32_t jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) {
        if (address % 4 != 0) {
            throw std::runtime_error("Unaligned access in jtag_read32");
        }
        return _check_result(implementation->jtag_read32(noc_id, chip_id, noc_x, noc_y, address));
    }

    uint32_t jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                          uint32_t data) {
        if (address % 4 != 0) {
            throw std::runtime_error("Unaligned access in jtag_write32");
        }
        return _check_result(implementation->jtag_write32(noc_id, chip_id, noc_x, noc_y, address, data));
    }

    uint32_t jtag_read32_axi(uint8_t chip_id, uint32_t address) {
        if (address % 4 != 0) {
            throw std::runtime_error("Unaligned access in jtag_read32_axi");
        }
        return _check_result(implementation->jtag_read32_axi(chip_id, address));
    }

    uint32_t jtag_write32_axi(uint8_t chip_id, uint64_t address, uint32_t data) {
        if (address % 4 != 0) {
            throw std::runtime_error("Unaligned access in jtag_write32_axi");
        }
        return _check_result(implementation->jtag_write32_axi(chip_id, address, data));
    }

    std::tuple<int, uint32_t, uint32_t> arc_msg(uint8_t noc_id, uint8_t chip_id, uint32_t msg_code, bool wait_for_done,
                                                uint32_t arg0, uint32_t arg1, int timeout) {
        return _check_result(implementation->arc_msg(noc_id, chip_id, msg_code, wait_for_done, arg0, arg1, timeout));
    }

    uint64_t read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag) {
        return _check_result(implementation->read_arc_telemetry_entry(chip_id, telemetry_tag));
    }
};

std::unique_ptr<TTExaLensImplementation> open_device(const std::string &binary_directory,
                                                     const std::vector<uint8_t> &wanted_devices, bool init_jtag,
                                                     bool initialize_with_noc1) {
    std::unique_ptr<tt::exalens::ttexalens_implementation> impl;
    if (init_jtag) {
        impl = tt::exalens::open_implementation<tt::exalens::jtag_implementation>::open(
            binary_directory, wanted_devices, initialize_with_noc1);
    } else {
        impl = tt::exalens::open_implementation<tt::exalens::umd_implementation>::open(binary_directory, wanted_devices,
                                                                                       initialize_with_noc1);
    }
    if (!impl) {
        return nullptr;
    }
    return std::make_unique<TTExaLensImplementation>(std::move(impl));
}

std::unique_ptr<TTExaLensImplementation> open_simulation(const std::string &simulation_directory) {
    auto impl =
        tt::exalens::open_implementation<tt::exalens::umd_implementation>::open_simulation(simulation_directory);
    if (!impl) {
        return nullptr;
    }
    return std::make_unique<TTExaLensImplementation>(std::move(impl));
}

NB_MODULE(ttexalens_pybind, m) {
    // Disable nanobind leak warnings
    // We are creating single instance of ttexalens_pybind.TTExaLensImplementation, but nanobind thinks it is a leak
    // because we are not explicitly deleting it. However, we want to keep it alive for the entire program duration.
    nanobind::set_leak_warnings(false);

    // Bind the TTExaLensImplementation class
    nanobind::class_<TTExaLensImplementation>(m, "TTExaLensImplementation")
        .def("pci_read32", &TTExaLensImplementation::pci_read32, "Reads 4 bytes from PCI address", "noc_id"_a,
             "chip_id"_a, "noc_x"_a, "noc_y"_a, "address"_a)
        .def("pci_write32", &TTExaLensImplementation::pci_write32, "Writes 4 bytes to PCI address", "noc_id"_a,
             "chip_id"_a, "noc_x"_a, "noc_y"_a, "address"_a, "data"_a)
        .def("pci_read", &TTExaLensImplementation::pci_read, "Reads data from PCI address", "noc_id"_a, "chip_id"_a,
             "noc_x"_a, "noc_y"_a, "address"_a, "size"_a)
        .def("pci_write", &TTExaLensImplementation::pci_write, "Writes data to PCI address", "noc_id"_a, "chip_id"_a,
             "noc_x"_a, "noc_y"_a, "address"_a, "data"_a)
        .def("pci_read32_raw", &TTExaLensImplementation::pci_read32_raw, "Reads 4 bytes from PCI address", "chip_id"_a,
             "address"_a)
        .def("pci_write32_raw", &TTExaLensImplementation::pci_write32_raw, "Writes 4 bytes to PCI address", "chip_id"_a,
             "address"_a, "data"_a)
        .def("dma_buffer_read32", &TTExaLensImplementation::dma_buffer_read32, "Reads 4 bytes from DMA buffer",
             "chip_id"_a, "address"_a, "channel"_a)
        .def("pci_read_tile", &TTExaLensImplementation::pci_read_tile, "Reads tile from PCI address", "noc_id"_a,
             "chip_id"_a, "noc_x"_a, "noc_y"_a, "address"_a, "size"_a, "data_format"_a)
        .def("get_cluster_description", &TTExaLensImplementation::get_cluster_description,
             "Returns cluster description")
        .def("convert_from_noc0", &TTExaLensImplementation::convert_from_noc0,
             "Convert noc0 coordinate into specified coordinate system", "chip_id"_a, "noc_x"_a, "noc_y"_a,
             "core_type"_a, "coord_system"_a)
        .def("get_device_ids", &TTExaLensImplementation::get_device_ids, "Returns device ids")
        .def("get_device_arch", &TTExaLensImplementation::get_device_arch, "Returns device architecture", "chip_id"_a)
        .def("get_device_soc_description", &TTExaLensImplementation::get_device_soc_description,
             "Returns device SoC description", "chip_id"_a)
        .def("jtag_read32", &TTExaLensImplementation::jtag_read32, "Reads 4 bytes from NOC address using JTAG",
             "noc_id"_a, "chip_id"_a, "noc_x"_a, "noc_y"_a, "address"_a)
        .def("jtag_write32", &TTExaLensImplementation::jtag_write32, "Writes 4 bytes to NOC address using JTAG",
             "noc_id"_a, "chip_id"_a, "noc_x"_a, "noc_y"_a, "address"_a, "data"_a)
        .def("jtag_read32_axi", &TTExaLensImplementation::jtag_read32_axi, "Reads 4 bytes from AXI address using JTAG",
             "chip_id"_a, "address"_a)
        .def("jtag_write32_axi", &TTExaLensImplementation::jtag_write32_axi, "Writes 4 bytes to AXI address using JTAG",
             "chip_id"_a, "address"_a, "data"_a)
        .def("arc_msg", &TTExaLensImplementation::arc_msg, "Send ARC message", "noc_id"_a, "chip_id"_a, "msg_code"_a,
             "wait_for_done"_a, "arg0"_a, "arg1"_a, "timeout"_a)
        .def("read_arc_telemetry_entry", &TTExaLensImplementation::read_arc_telemetry_entry, "Read ARC telemetry entry",
             "chip_id"_a, "telemetry_tag"_a);

    // Bind factory functions
    m.def("open_device", &open_device, "Opens tt device. Returns TTExaLensImplementation object or None if failed.",
          "binary_directory"_a, "wanted_devices"_a = std::vector<uint8_t>(), "init_jtag"_a = false,
          "initialize_with_noc1"_a = false);
    m.def("open_simulation", &open_simulation,
          "Opens tt device simulation. Returns TTExaLensImplementation object or None if failed.",
          "simulation_directory"_a);
}

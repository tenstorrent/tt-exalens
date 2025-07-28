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

bool open_device(const std::string& binary_directory, const std::vector<uint8_t>& wanted_devices = {},
                 bool init_jtag = false, bool initialize_with_noc1 = false);
void set_ttexalens_implementation(std::unique_ptr<tt::exalens::ttexalens_implementation> imp);

std::optional<uint32_t> pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address);
std::optional<uint32_t> pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data);

std::optional<nanobind::object> pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                         uint64_t address, uint32_t size);
std::optional<uint32_t> pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                  nanobind::bytes data, uint32_t size);

std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address);
std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data);

std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel);
std::optional<std::string> pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                         uint64_t address, uint32_t size, uint8_t data_format);

std::optional<std::string> get_cluster_description();
std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                              const std::string& core_type,
                                                              const std::string& coord_system);
std::optional<std::vector<uint8_t>> get_device_ids();
std::optional<std::string> get_device_arch(uint8_t chip_id);
std::optional<std::string> get_device_soc_description(uint8_t chip_id);

std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t noc_id, uint8_t chip_id, uint32_t msg_code,
                                                           bool wait_for_done, uint32_t arg0, uint32_t arg1,
                                                           int timeout);
std::optional<uint32_t> read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag);

std::optional<uint32_t> jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address);
std::optional<uint32_t> jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                     uint32_t data);
std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address);
std::optional<uint32_t> jtag_write32_axi(uint8_t chip_id, uint64_t address, uint32_t data);

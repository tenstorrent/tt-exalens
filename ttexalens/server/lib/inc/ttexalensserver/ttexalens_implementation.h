// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <tuple>
#include <vector>

namespace tt::exalens {

// Interface that should be implemented for TTExaLens server to process requests.
class ttexalens_implementation {
   public:
    virtual ~ttexalens_implementation() = default;

    virtual std::optional<uint32_t> pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                               uint64_t address) {
        return {};
    }
    virtual std::optional<uint32_t> pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                uint64_t address, uint32_t data) {
        return {};
    }
    virtual std::optional<std::vector<uint8_t>> pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                         uint64_t address, uint32_t size) {
        return {};
    }
    virtual std::optional<uint32_t> pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                              uint64_t address, const uint8_t* data, uint32_t size) {
        return {};
    }
    virtual std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) { return {}; }
    virtual std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) { return {}; }
    virtual std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
        return {};
    }

    virtual std::optional<std::string> pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                     uint64_t address, uint32_t size, uint8_t data_format) {
        return {};
    }
    virtual std::optional<std::string> get_cluster_description() { return {}; }
    virtual std::optional<std::vector<uint8_t>> get_device_ids() { return {}; }
    virtual std::optional<std::string> get_device_arch(uint8_t chip_id) { return {}; }
    virtual std::optional<std::string> get_device_soc_description(uint8_t chip_id) { return {}; }
    virtual std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                          const std::string& core_type,
                                                                          const std::string& coord_system) {
        return {};
    }

    virtual std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t noc_id, uint8_t chip_id,
                                                                       uint32_t msg_code, bool wait_for_done,
                                                                       uint32_t arg0, uint32_t arg1, int timeout) {
        return {};
    }
    virtual std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) { return {}; }
    virtual std::optional<int> jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                            uint64_t address, uint32_t data) {
        return {};
    }
    virtual std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) { return {}; }
    virtual std::optional<uint32_t> jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                uint64_t address) {
        return {};
    }
};

}  // namespace tt::exalens

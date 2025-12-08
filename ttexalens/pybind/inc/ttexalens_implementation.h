// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <chrono>
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

    virtual std::optional<uint32_t> read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                           uint64_t address, bool use_4B_mode) {
        return {};
    }
    virtual std::optional<uint32_t> write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                            uint64_t address, uint32_t data, bool use_4B_mode) {
        return {};
    }
    virtual std::optional<std::vector<uint8_t>> read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                     uint64_t address, uint32_t size, bool use_4B_mode) {
        return {};
    }
    virtual std::optional<uint32_t> write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                          uint64_t address, const uint8_t* data, uint32_t size, bool use_4B_mode) {
        return {};
    }
    virtual std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) { return {}; }
    virtual std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) { return {}; }
    virtual std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
        return {};
    }

    virtual std::optional<std::string> read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
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
                                                                       const std::vector<uint32_t>& args,
                                                                       std::chrono::milliseconds timeout) {
        return {};
    }
    virtual std::optional<uint32_t> read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag) { return {}; }
    virtual std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> get_firmware_version(uint8_t chip_id) { return {}; }
    virtual std::optional<uint64_t> get_device_unique_id(uint8_t chip_id) { return {}; }
    virtual void warm_reset(bool is_galaxy_configuration = false) { return; }
    virtual std::optional<std::tuple<uint8_t, uint8_t>> get_remote_transfer_eth_core(uint8_t chip_id) { return {}; }
};

}  // namespace tt::exalens

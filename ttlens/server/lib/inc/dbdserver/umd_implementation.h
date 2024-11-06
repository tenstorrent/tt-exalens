// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <optional>

#include "debuda_implementation.h"
#include "device/cluster.h"

namespace tt::umd {
class Cluster;
}

class JtagDevice;

namespace tt::dbd {

class umd_implementation : public debuda_implementation {
   public:
    umd_implementation(tt::umd::Cluster* device, JtagDevice* jtag_device);

   protected:
    std::optional<uint32_t> pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override;
    std::optional<uint32_t> pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                        uint32_t data) override;
    std::optional<std::vector<uint8_t>> pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                 uint32_t size) override;
    std::optional<uint32_t> pci_write(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                      const uint8_t* data, uint32_t size) override;
    std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) override;
    std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) override;
    std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) override;

    std::optional<std::string> pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                             uint32_t size, uint8_t data_format) override;

    std::optional<std::string> get_harvester_coordinate_translation(uint8_t chip_id) override;
    std::optional<std::string> get_device_arch(uint8_t chip_id) override;

    virtual std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t chip_id, uint32_t msg_code,
                                                                       bool wait_for_done, uint32_t arg0, uint32_t arg1,
                                                                       int timeout) override;

    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override;
    std::optional<int> jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override;
    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override;
    std::optional<uint32_t> jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override;

   private:
    bool is_chip_mmio_capable(uint8_t chip_id);

    tt::umd::Cluster* device = nullptr;
    JtagDevice* jtag_device = nullptr;
    std::string cluster_descriptor_path;
};

}  // namespace tt::dbd

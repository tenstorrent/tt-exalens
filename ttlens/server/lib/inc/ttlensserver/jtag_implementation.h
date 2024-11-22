// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <optional>

#include "ttlens_implementation.h"

class JtagDevice;

namespace tt::lens {

class jtag_implementation : public ttlens_implementation {
   public:
    jtag_implementation(JtagDevice* device);

   protected:
    std::optional<std::string> get_harvester_coordinate_translation(uint8_t chip_id) override;
    std::optional<std::string> get_device_arch(uint8_t chip_id) override;

    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override;
    std::optional<int> jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override;
    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override;
    std::optional<uint32_t> jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override;

   private:
    JtagDevice* jtag_device = nullptr;
};

}  // namespace tt::lens

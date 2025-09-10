// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <optional>

#include "ttexalens_implementation.h"
#include "umd/device/jtag/jtag_device.h"

namespace tt::exalens {

class jtag_implementation : public ttexalens_implementation {
   public:
    typedef JtagDevice DeviceType;
    jtag_implementation(JtagDevice* device);

   protected:
    std::optional<std::string> get_device_arch(uint8_t chip_id) override;

    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override;
    std::optional<int> jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override;
    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override;
    std::optional<uint32_t> jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                        uint64_t address) override;

   private:
    JtagDevice* jtag_device = nullptr;
};

}  // namespace tt::exalens

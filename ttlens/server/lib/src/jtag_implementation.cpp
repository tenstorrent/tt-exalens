// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttlensserver/jtag_implementation.h"

#include "ttlensserver/jtag_device.h"
#include "umd/device/tt_soc_descriptor.h"
#include "umd/device/types/arch.h"

namespace tt::lens {

jtag_implementation::jtag_implementation(JtagDevice* device) : jtag_device(device) {}

std::optional<std::string> jtag_implementation::get_harvester_coordinate_translation(uint8_t chip_id) {
    return jtag_device->get_jtag_harvester_coordinate_translation(chip_id);
}

std::optional<std::string> jtag_implementation::get_device_arch(uint8_t chip_id) {
    auto x = jtag_device->get_jtag_arch(chip_id);
    if (x) {
        return tt::arch_to_str(*x);
    }
    return {};
}

std::optional<int> jtag_implementation::jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) {
    return jtag_device->write32_axi(chip_id, address, data);
}
std::optional<int> jtag_implementation::jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                     uint32_t data) {
    return jtag_device->write32(chip_id, noc_x, noc_y, address, data);
}
std::optional<uint32_t> jtag_implementation::jtag_read32_axi(uint8_t chip_id, uint32_t address) {
    return jtag_device->read32_axi(chip_id, address);
}
std::optional<uint32_t> jtag_implementation::jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                         uint64_t address) {
    return jtag_device->read32(chip_id, noc_x, noc_y, address);
}

}  // namespace tt::lens

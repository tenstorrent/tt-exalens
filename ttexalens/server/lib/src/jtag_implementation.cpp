// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttexalensserver/jtag_implementation.h"

#include "umd/device/tt_soc_descriptor.h"
#include "umd/device/types/arch.h"

namespace tt::exalens {

jtag_implementation::jtag_implementation(JtagDevice* device) : jtag_device(device) {}

std::optional<std::string> jtag_implementation::get_device_arch(uint8_t chip_id) {
    tt::ARCH arch = jtag_device->get_jtag_arch(chip_id);
    return tt::arch_to_str(arch);
}

std::optional<int> jtag_implementation::jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) {
    jtag_device->write32_axi(chip_id, address, data);
    return sizeof(uint32_t);
}
std::optional<int> jtag_implementation::jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                     uint64_t address, uint32_t data) {
    // TODO: Update JTAG library to use noc_id
    jtag_device->write32(chip_id, noc_x, noc_y, address, data);
    return sizeof(uint32_t);
}
std::optional<uint32_t> jtag_implementation::jtag_read32_axi(uint8_t chip_id, uint32_t address) {
    return jtag_device->read32_axi(chip_id, address);
}
std::optional<uint32_t> jtag_implementation::jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                         uint64_t address) {
    // TODO: Update JTAG library to use noc_id
    return jtag_device->read32(chip_id, noc_x, noc_y, address);
}

}  // namespace tt::exalens

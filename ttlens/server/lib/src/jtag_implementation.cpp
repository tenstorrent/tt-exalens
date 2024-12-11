// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttlensserver/jtag_implementation.h"

#include "ttlensserver/jtag_device.h"
#include "umd/device/tt_soc_descriptor.h"
#include "umd/device/types/arch.h"

namespace tt::lens {

jtag_implementation::jtag_implementation(JtagDevice* device) : jtag_device(device) {}

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

std::optional<std::vector<uint32_t>> jtag_implementation::dbus_memdump(uint8_t chip_id, const char* client_name,
                                                                       const char* mem, const char* thread_id_name,
                                                                       const char* start_addr, const char* end_addr) {
    return jtag_device->dbus_memdump(chip_id, client_name, mem, thread_id_name, start_addr, end_addr);
}
std::optional<std::vector<uint32_t>> jtag_implementation::dbus_sigdump(uint8_t chip_id, const char* client_name,
                                                                       uint32_t dbg_client_id,
                                                                       uint32_t dbg_signal_sel_start,
                                                                       uint32_t dbg_signal_sel_end) {
    return jtag_device->dbus_sigdump(chip_id, client_name, dbg_client_id, dbg_signal_sel_start, dbg_signal_sel_end);
}

}  // namespace tt::lens

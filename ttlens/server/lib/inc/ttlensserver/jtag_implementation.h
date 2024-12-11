// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <optional>

#include "ttlensserver/jtag_device.h"
#include "ttlensserver/ttlens_implementation.h"

namespace tt::lens {

class jtag_implementation : public ttlens_implementation {
   public:
    typedef JtagDevice DeviceType;
    jtag_implementation(JtagDevice* device);

   protected:
    std::optional<std::string> get_device_arch(uint8_t chip_id) override;

    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override;
    std::optional<int> jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override;
    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override;
    std::optional<uint32_t> jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override;

    std::optional<std::vector<uint32_t>> dbus_memdump(uint8_t chip_id, const char* client_name, const char* mem,
                                                      const char* thread_id_name, const char* start_addr,
                                                      const char* end_addr);
    std::optional<std::vector<uint32_t>> dbus_sigdump(uint8_t chip_id, const char* client_name, uint32_t dbg_client_id,
                                                      uint32_t dbg_signal_sel_start, uint32_t dbg_signal_sel_end);

   private:
    JtagDevice* jtag_device = nullptr;
};

}  // namespace tt::lens

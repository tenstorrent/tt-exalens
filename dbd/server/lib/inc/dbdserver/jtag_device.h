// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#ifndef JTAG_IMPLEMENTATION_H
#define JTAG_IMPLEMENTATION_H

#include <cstdint>
#include <memory>
#include <stdexcept>
#include <unordered_map>
#include <vector>

#include "dbdserver/jtag.h"

class JtagDevice {
   public:
    explicit JtagDevice(std::unique_ptr<Jtag> jtag_device);
    ~JtagDevice();

    std::optional<uint32_t> get_device_cnt();
    std::optional<int> open_jlink_by_serial_wrapper(uint32_t chip_id, unsigned int serial_number);
    std::optional<int> open_jlink_wrapper(uint32_t chip_id);
    std::optional<uint32_t> read_tdr(uint32_t chip_id, const char* client, uint32_t reg_offset);
    std::optional<uint32_t> readmon_tdr(uint32_t chip_id, const char* client, uint32_t id, uint32_t reg_offset);
    std::optional<int> writemon_tdr(uint32_t chip_id, const char* client, uint32_t id, uint32_t reg_offset,
                                    uint32_t data);
    std::optional<int> write_tdr(uint32_t chip_id, const char* client, uint32_t reg_offset, uint32_t data);
    std::optional<int> dbus_memdump(uint32_t chip_id, const char* client_name, const char* mem,
                                    const char* thread_id_name, const char* start_addr, const char* end_addr);
    std::optional<int> dbus_sigdump(uint32_t chip_id, const char* client_name, uint32_t dbg_client_id,
                                    uint32_t dbg_signal_sel_start, uint32_t dbg_signal_sel_end);
    std::optional<int> write_axi(uint32_t chip_id, uint32_t reg_addr, uint32_t data);
    std::optional<int> write_noc_xy(uint32_t chip_id, uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr,
                                    uint32_t noc_data);
    std::optional<uint32_t> read_axi(uint32_t chip_id, uint32_t reg_addr);
    std::optional<uint32_t> read_noc_xy(uint32_t chip_id, uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr);
    std::optional<std::vector<uint32_t>> enumerate_jlink(uint32_t chip_id);
    std::optional<int> close_jlink(uint32_t chip_id);
    std::optional<uint32_t> read_id_raw(uint32_t chip_id);
    std::optional<uint32_t> read_id(uint32_t chip_id);

   private:
    std::unique_ptr<Jtag> jtag;
    std::vector<uint32_t> jlink_devices;
    std::vector<std::vector<uint32_t>> harvesting;
    uint32_t curr_device_idx = -1;
    uint32_t curr_device_chip_id = -1;

    std::vector<uint32_t> get_harvesting_from_efuse(uint32_t efuse_harvesting);
};

#endif

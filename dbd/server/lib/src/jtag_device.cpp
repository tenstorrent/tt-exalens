// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "dbdserver/jtag_device.h"

#include <dlfcn.h>
#include <stdint.h>

#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

#include "dbdserver/jtag.h"

#define ROW_LEN 12
#define WORMHOLE_ID 0x138a5
#define WORMHOLE_ARC_EFUSE_BOX1 0x80042000
#define WORMHOLE_ARC_EFUSE_HARVESTING (WORMHOLE_ARC_EFUSE_BOX1 + 0x25C)

JtagDevice::JtagDevice(std::unique_ptr<Jtag> jtag_device) : jtag(std::move(jtag_device)) {
    std::vector<uint32_t> potential_devices = jtag->tt_enumerate_jlink();
    if (potential_devices.empty()) {
        throw std::runtime_error("There are no devices");
    }

    for (int jlink_id : potential_devices) {
        uint32_t status = jtag->tt_open_jlink_by_serial_wrapper(jlink_id);
        if (status != 0) {
            continue;
        }
        uint32_t id = jtag->tt_read_id();
        if (id != WORMHOLE_ID) {
            std::cerr << "Only supporting WORMHOLE for now" << std::endl;
            jtag->tt_close_jlink();
            continue;
        }

        jlink_devices.push_back(jlink_id);
        uint32_t efuse = jtag->tt_read_axi(WORMHOLE_ARC_EFUSE_HARVESTING);
        harvesting.push_back(get_harvesting_from_efuse(efuse));

        jtag->tt_close_jlink();
    }
    if (jlink_devices.empty()) {
        throw std::runtime_error("There are no supported devices");
    }

    curr_device_idx = 0;
    curr_device_chip_id = 0;
    jtag->tt_open_jlink_by_serial_wrapper(jlink_devices[curr_device_idx]);
}

JtagDevice::~JtagDevice() {}

std::optional<uint32_t> JtagDevice::get_device_cnt() { return jlink_devices.size(); }

std::vector<uint32_t> JtagDevice::get_harvesting_from_efuse(uint32_t efuse_harvesting) {
    uint32_t bad_mem_bits = efuse_harvesting & 0x3FF;
    uint32_t bad_logic_bits = (efuse_harvesting >> 10) & 0x3FF;
    uint32_t bad_row_bits = (bad_mem_bits | bad_logic_bits) << 1;

    uint32_t mapping_idx[ROW_LEN] = {0, 2, 4, 6, 8, 10, 11, 9, 7, 5, 3, 1};
    uint32_t harvesting_rows[ROW_LEN - 2] = {0};
    bad_row_bits |= 1 << mapping_idx[6];
    int cnt = 1;

    for (int i = 1; i < ROW_LEN; i++) {
        if (i == 6) {
            harvesting_rows[i] = i;
            continue;
        }

        while ((1 << mapping_idx[cnt]) & bad_row_bits) {
            cnt++;
        }
        harvesting_rows[i] = cnt++;
    }

    return std::vector<uint32_t>(harvesting_rows, harvesting_rows + ROW_LEN - 2);
}

std::optional<int> JtagDevice::open_jlink_by_serial_wrapper(uint8_t chip_id, unsigned int serial_number) {
    return jtag->tt_open_jlink_by_serial_wrapper(serial_number);
}

std::optional<int> JtagDevice::open_jlink_wrapper(uint8_t chip_id) { return jtag->tt_open_jlink_wrapper(); }

std::optional<uint32_t> JtagDevice::read_tdr(uint8_t chip_id, const char* client, uint32_t reg_offset) {
    return jtag->tt_read_tdr(client, reg_offset);
}

std::optional<uint32_t> JtagDevice::readmon_tdr(uint8_t chip_id, const char* client, uint32_t id, uint32_t reg_offset) {
    return jtag->tt_readmon_tdr(client, id, reg_offset);
}

std::optional<int> JtagDevice::writemon_tdr(uint8_t chip_id, const char* client, uint32_t id, uint32_t reg_offset,
                                            uint32_t data) {
    jtag->tt_writemon_tdr(client, id, reg_offset, data);
    return 0;
}

std::optional<int> JtagDevice::write_tdr(uint8_t chip_id, const char* client, uint32_t reg_offset, uint32_t data) {
    jtag->tt_write_tdr(client, reg_offset, data);
    return 0;
}

std::optional<int> JtagDevice::dbus_memdump(uint8_t chip_id, const char* client_name, const char* mem,
                                            const char* thread_id_name, const char* start_addr, const char* end_addr) {
    jtag->tt_dbus_memdump(client_name, mem, thread_id_name, start_addr, end_addr);
    return 0;
}

std::optional<int> JtagDevice::dbus_sigdump(uint8_t chip_id, const char* client_name, uint32_t dbg_client_id,
                                            uint32_t dbg_signal_sel_start, uint32_t dbg_signal_sel_end) {
    jtag->tt_dbus_sigdump(client_name, dbg_client_id, dbg_signal_sel_start, dbg_signal_sel_end);
    return 0;
}

std::optional<int> JtagDevice::write_axi(uint8_t chip_id, uint32_t address, uint32_t data) {
    if (chip_id >= jlink_devices.size()) {
        return {};
    }
    if (curr_device_chip_id != chip_id) {
        curr_device_idx = chip_id;
        curr_device_chip_id = chip_id;
        jtag->tt_close_jlink();
        jtag->tt_open_jlink_by_serial_wrapper(jlink_devices[curr_device_idx]);
    }

    jtag->tt_write_axi(address, data);
    return 0;
}

std::optional<int> JtagDevice::write_noc_xy(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                            uint32_t data) {
    if (chip_id >= jlink_devices.size()) {
        return {};
    }
    if (curr_device_chip_id != chip_id) {
        curr_device_idx = chip_id;
        curr_device_chip_id = chip_id;
        jtag->tt_close_jlink();
        jtag->tt_open_jlink_by_serial_wrapper(jlink_devices[curr_device_idx]);
    }

    uint32_t nocvirt_y = harvesting[curr_device_idx][noc_y];
    jtag->tt_write_noc_xy(noc_x, nocvirt_y, address, data);
    return 0;
}

std::optional<uint32_t> JtagDevice::read_axi(uint8_t chip_id, uint32_t address) {
    if (chip_id >= jlink_devices.size()) {
        return {};
    }
    if (curr_device_chip_id != chip_id) {
        curr_device_idx = chip_id;
        curr_device_chip_id = chip_id;
        jtag->tt_close_jlink();
        jtag->tt_open_jlink_by_serial_wrapper(jlink_devices[curr_device_idx]);
    }

    return jtag->tt_read_axi(address);
}

std::optional<uint32_t> JtagDevice::read_noc_xy(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) {
    if (chip_id >= jlink_devices.size()) {
        return {};
    }
    if (curr_device_chip_id != chip_id) {
        curr_device_idx = chip_id;
        curr_device_chip_id = chip_id;
        jtag->tt_close_jlink();
        jtag->tt_open_jlink_by_serial_wrapper(jlink_devices[curr_device_idx]);
    }

    uint32_t nocvirt_y = harvesting[curr_device_idx][noc_y];
    return jtag->tt_read_noc_xy(noc_x, nocvirt_y, address);
}

std::optional<std::vector<uint32_t>> JtagDevice::enumerate_jlink(uint8_t chip_id) { return jtag->tt_enumerate_jlink(); }

std::optional<int> JtagDevice::close_jlink(uint8_t chip_id) {
    jtag->tt_close_jlink();
    return 0;
}

std::optional<uint32_t> JtagDevice::read_id_raw(uint8_t chip_id) { return jtag->tt_read_id_raw(); }

std::optional<uint32_t> JtagDevice::read_id(uint8_t chip_id) { return jtag->tt_read_id(); }

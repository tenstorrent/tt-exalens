// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "dbdserver/jtag.h"

#include <dlfcn.h>
#include <stdint.h>

#include <iostream>
#include <vector>

Jtag::Jtag(const char* libName) {
    handle = dlopen(libName, RTLD_LAZY);
    if (!handle) {
        // std::cerr << "Cannot open library: " << dlerror() << '\n';
        throw std::runtime_error("Failed to load library");
    }
}

Jtag::~Jtag() {
    if (handle) {
        dlclose(handle);
    }
}

int Jtag::tt_open_jlink_by_serial_wrapper(unsigned int serial_number) {
    loadFunction(tt_open_jlink_by_serial_wrapper_handle, (const char*)"tt_open_jlink_by_serial_wrapper");
    return tt_open_jlink_by_serial_wrapper_handle(serial_number);
}

int Jtag::tt_open_jlink_wrapper() {
    loadFunction(tt_open_jlink_wrapper_handle, (const char*)"tt_open_jlink_wrapper");
    return tt_open_jlink_wrapper_handle();
}

uint32_t Jtag::tt_read_tdr(const char* client, uint32_t reg_offset) {
    loadFunction(tt_read_tdr_handle, (const char*)"tt_read_tdr");
    return tt_read_tdr_handle(client, reg_offset);
}

uint32_t Jtag::tt_readmon_tdr(const char* client, uint32_t id, uint32_t reg_offset) {
    loadFunction(tt_readmon_tdr_handle, (const char*)"tt_readmon_tdr");
    return tt_readmon_tdr_handle(client, id, reg_offset);
}

void Jtag::tt_writemon_tdr(const char* client, uint32_t id, uint32_t reg_offset, uint32_t data) {
    loadFunction(tt_writemon_tdr_handle, (const char*)"tt_writemon_tdr");
    tt_writemon_tdr_handle(client, id, reg_offset, data);
}

void Jtag::tt_write_tdr(const char* client, uint32_t reg_offset, uint32_t data) {
    loadFunction(tt_write_tdr_handle, (const char*)"tt_write_tdr");
    tt_write_tdr_handle(client, reg_offset, data);
}

void Jtag::tt_dbus_memdump(const char* client_name, const char* mem, const char* thread_id_name, const char* start_addr,
                           const char* end_addr) {
    loadFunction(tt_dbus_memdump_handle, (const char*)"tt_dbus_memdump");
    tt_dbus_memdump_handle(client_name, mem, thread_id_name, start_addr, end_addr);
}

void Jtag::tt_dbus_sigdump(const char* client_name, uint32_t dbg_client_id, uint32_t dbg_signal_sel_start,
                           uint32_t dbg_signal_sel_end) {
    loadFunction(tt_dbus_sigdump_handle, (const char*)"tt_dbus_sigdump");
    tt_dbus_sigdump_handle(client_name, dbg_client_id, dbg_signal_sel_start, dbg_signal_sel_end);
}

void Jtag::tt_write_axi(uint32_t reg_addr, uint32_t data, uint32_t* status) {
    loadFunction(tt_write_axi_handle, (const char*)"tt_write_axi");
    tt_write_axi_handle(reg_addr, data, status);
}

uint32_t Jtag::tt_write_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, uint32_t noc_data,
                               bool set_tlb, uint32_t noc_tlb) {
    loadFunction(tt_write_noc_xy_handle, (const char*)"tt_write_noc_xy");
    return tt_write_noc_xy_handle(node_x_id, node_y_id, noc_addr, noc_data, set_tlb, noc_tlb);
}

void Jtag::tt_read_axi(uint32_t reg_addr, uint32_t* data, uint32_t* status) {
    loadFunction(tt_read_axi_handle, (const char*)"tt_read_axi");
    tt_read_axi_handle(reg_addr, data, status);
}

uint32_t Jtag::tt_read_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, bool set_tlb, uint32_t noc_tlb,
                              uint32_t* rddata) {
    loadFunction(tt_read_noc_xy_handle, (const char*)"tt_read_noc_xy");
    return tt_read_noc_xy_handle(node_x_id, node_y_id, noc_addr, set_tlb, noc_tlb, rddata);
}

std::vector<uint32_t> Jtag::tt_enumerate_jlink() {
    loadFunction(tt_enumerate_jlink_handle, (const char*)"_Z18tt_enumerate_jlinkv");
    return tt_enumerate_jlink_handle();
}

template <typename Func>
void Jtag::loadFunction(Func& funcPtr, const char* name) {
    if (!funcPtr) {
        funcPtr = (Func)dlsym(handle, name);
        const char* dlsym_error = dlerror();
        if (dlsym_error) {
            std::cerr << "Cannot load symbol: " << dlsym_error << '\n';
            throw std::runtime_error("Failed to load function");
        }
    }
}

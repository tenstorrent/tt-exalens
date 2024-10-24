// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "dbdserver/jtag.h"

#include <dlfcn.h>
#include <stdint.h>

#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

Jtag::Jtag(const char* libName) {
    handle = dlopen(libName, RTLD_LAZY);
    if (!handle) {
        throw std::runtime_error("Failed to load library");
    }
}

Jtag::~Jtag() {
    if (handle) {
        dlclose(handle);
    }
}

#define LOAD_FUNCTION(name) \
    loadFunction(#name);    \
    auto func = reinterpret_cast<decltype(::name)*>(funcMap[#name]);

int Jtag::tt_open_jlink_by_serial_wrapper(unsigned int serial_number) {
    LOAD_FUNCTION(tt_open_jlink_by_serial_wrapper);
    return func(serial_number);
}

int Jtag::tt_open_jlink_wrapper() {
    LOAD_FUNCTION(tt_open_jlink_wrapper);
    return func();
}

uint32_t Jtag::tt_read_tdr(const char* client, uint32_t reg_offset) {
    LOAD_FUNCTION(tt_read_tdr);
    return func(client, reg_offset);
}

uint32_t Jtag::tt_readmon_tdr(const char* client, uint32_t id, uint32_t reg_offset) {
    LOAD_FUNCTION(tt_readmon_tdr);
    return func(client, id, reg_offset);
}

void Jtag::tt_writemon_tdr(const char* client, uint32_t id, uint32_t reg_offset, uint32_t data) {
    LOAD_FUNCTION(tt_writemon_tdr);
    func(client, id, reg_offset, data);
}

void Jtag::tt_write_tdr(const char* client, uint32_t reg_offset, uint32_t data) {
    LOAD_FUNCTION(tt_write_tdr);
    func(client, reg_offset, data);
}

void Jtag::tt_dbus_memdump(const char* client_name, const char* mem, const char* thread_id_name, const char* start_addr,
                           const char* end_addr) {
    LOAD_FUNCTION(tt_dbus_memdump);
    func(client_name, mem, thread_id_name, start_addr, end_addr);
}

void Jtag::tt_dbus_sigdump(const char* client_name, uint32_t dbg_client_id, uint32_t dbg_signal_sel_start,
                           uint32_t dbg_signal_sel_end) {
    LOAD_FUNCTION(tt_dbus_sigdump);
    func(client_name, dbg_client_id, dbg_signal_sel_start, dbg_signal_sel_end);
}

void Jtag::tt_write_axi(uint32_t reg_addr, uint32_t data, uint32_t* status) {
    LOAD_FUNCTION(tt_write_axi);
    func(reg_addr, data, status);
}

uint32_t Jtag::tt_write_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, uint32_t noc_data,
                               bool set_tlb, uint32_t noc_tlb) {
    LOAD_FUNCTION(tt_write_noc_xy);
    return func(node_x_id, node_y_id, noc_addr, noc_data, set_tlb, noc_tlb);
}

void Jtag::tt_read_axi(uint32_t reg_addr, uint32_t* data, uint32_t* status) {
    LOAD_FUNCTION(tt_read_axi);
    func(reg_addr, data, status);
}

uint32_t Jtag::tt_read_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, bool set_tlb, uint32_t noc_tlb,
                              uint32_t* rddata) {
    LOAD_FUNCTION(tt_read_noc_xy);
    return func(node_x_id, node_y_id, noc_addr, set_tlb, noc_tlb, rddata);
}

std::vector<uint32_t> Jtag::tt_enumerate_jlink() {
    loadFunction("_Z18tt_enumerate_jlinkv");
    auto func = reinterpret_cast<decltype(::tt_enumerate_jlink)*>(funcMap["_Z18tt_enumerate_jlinkv"]);
    return func();
}

void Jtag::loadFunction(const char* name) {
    if (funcMap.find(name) == funcMap.end()) {
        void* funcPtr = dlsym(handle, name);
        const char* dlsym_error = dlerror();
        if (dlsym_error) {
            std::cerr << "Cannot load symbol: " << dlsym_error << '\n';
            throw std::runtime_error("Failed to load function");
        }
        funcMap[name] = funcPtr;
    }
}

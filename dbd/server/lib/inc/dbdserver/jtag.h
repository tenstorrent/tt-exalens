// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#ifndef LIBJTAG_H
#define LIBJTAG_H

#include <cstdint>
#include <stdexcept>
#include <unordered_map>
#include <vector>

int tt_open_jlink_by_serial_wrapper(unsigned int serial_number);
int tt_open_jlink_wrapper();
uint32_t tt_read_tdr(const char* client, uint32_t reg_offset);
uint32_t tt_readmon_tdr(const char* client, uint32_t id, uint32_t reg_offset);
void tt_writemon_tdr(const char* client, uint32_t id, uint32_t reg_offset, uint32_t data);
void tt_write_tdr(const char* client, uint32_t reg_offset, uint32_t data);
void tt_dbus_memdump(const char* client_name, const char* mem, const char* thread_id_name, const char* start_addr,
                     const char* end_addr);
void tt_dbus_sigdump(const char* client_name, uint32_t dbg_client_id, uint32_t dbg_signal_sel_start,
                     uint32_t dbg_signal_sel_end);
void tt_write_axi(uint32_t reg_addr, uint32_t data, uint32_t* status);
uint32_t tt_write_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, uint32_t noc_data, bool set_tlb,
                         uint32_t noc_tlb);
void tt_read_axi(uint32_t reg_addr, uint32_t* data, uint32_t* status);
uint32_t tt_read_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, bool set_tlb, uint32_t noc_tlb,
                        uint32_t* rddata);
std::vector<uint32_t> tt_enumerate_jlink();

class Jtag {
   public:
    explicit Jtag(const char* libName);
    ~Jtag();

    int tt_open_jlink_by_serial_wrapper(unsigned int serial_number);
    int tt_open_jlink_wrapper();
    uint32_t tt_read_tdr(const char* client, uint32_t reg_offset);
    uint32_t tt_readmon_tdr(const char* client, uint32_t id, uint32_t reg_offset);
    void tt_writemon_tdr(const char* client, uint32_t id, uint32_t reg_offset, uint32_t data);
    void tt_write_tdr(const char* client, uint32_t reg_offset, uint32_t data);
    void tt_dbus_memdump(const char* client_name, const char* mem, const char* thread_id_name, const char* start_addr,
                         const char* end_addr);
    void tt_dbus_sigdump(const char* client_name, uint32_t dbg_client_id, uint32_t dbg_signal_sel_start,
                         uint32_t dbg_signal_sel_end);
    void tt_write_axi(uint32_t reg_addr, uint32_t data, uint32_t* status);
    uint32_t tt_write_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, uint32_t noc_data, bool set_tlb,
                             uint32_t noc_tlb);
    void tt_read_axi(uint32_t reg_addr, uint32_t* data, uint32_t* status);
    uint32_t tt_read_noc_xy(uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, bool set_tlb, uint32_t noc_tlb,
                            uint32_t* rddata);
    std::vector<uint32_t> tt_enumerate_jlink();

   private:
    void* handle;
    std::unordered_map<std::string, void*> funcMap;

    void loadFunction(const char* name);
};

#endif

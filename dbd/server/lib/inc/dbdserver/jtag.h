// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#ifndef LIBJTAG_H
#define LIBJTAG_H

#include <cstdint>
#include <stdexcept>
#include <vector>

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

    typedef int (*tt_open_jlink_by_serial_wrapper_t)(unsigned int);
    typedef int (*tt_open_jlink_wrapper_t)();
    typedef uint32_t (*tt_read_tdr_t)(const char*, uint32_t);
    typedef uint32_t (*tt_readmon_tdr_t)(const char*, uint32_t, uint32_t);
    typedef void (*tt_writemon_tdr_t)(const char*, uint32_t, uint32_t, uint32_t);
    typedef void (*tt_write_tdr_t)(const char*, uint32_t, uint32_t);
    typedef void (*tt_dbus_memdump_t)(const char*, const char*, const char*, const char*, const char*);
    typedef void (*tt_dbus_sigdump_t)(const char*, uint32_t, uint32_t, uint32_t);
    typedef void (*tt_write_axi_t)(uint32_t, uint32_t, uint32_t*);
    typedef uint32_t (*tt_write_noc_xy_t)(uint32_t, uint32_t, uint64_t, uint32_t, bool, uint32_t);
    typedef void (*tt_read_axi_t)(uint32_t, uint32_t*, uint32_t*);
    typedef uint32_t (*tt_read_noc_xy_t)(uint32_t, uint32_t, uint64_t, bool, uint32_t, uint32_t*);
    typedef std::vector<uint32_t> (*tt_enumerate_jlink_t)();

    tt_open_jlink_by_serial_wrapper_t tt_open_jlink_by_serial_wrapper_handle = nullptr;
    tt_open_jlink_wrapper_t tt_open_jlink_wrapper_handle = nullptr;
    tt_read_tdr_t tt_read_tdr_handle = nullptr;
    tt_readmon_tdr_t tt_readmon_tdr_handle = nullptr;
    tt_writemon_tdr_t tt_writemon_tdr_handle = nullptr;
    tt_write_tdr_t tt_write_tdr_handle = nullptr;
    tt_dbus_memdump_t tt_dbus_memdump_handle = nullptr;
    tt_dbus_sigdump_t tt_dbus_sigdump_handle = nullptr;
    tt_write_axi_t tt_write_axi_handle = nullptr;
    tt_write_noc_xy_t tt_write_noc_xy_handle = nullptr;
    tt_read_axi_t tt_read_axi_handle = nullptr;
    tt_read_noc_xy_t tt_read_noc_xy_handle = nullptr;
    tt_enumerate_jlink_t tt_enumerate_jlink_handle = nullptr;

    template <typename Func>
    void loadFunction(Func& funcPtr, const char*);
};

#endif

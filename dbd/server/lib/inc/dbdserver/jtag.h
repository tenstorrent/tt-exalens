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

#define DEFINE_JTAG_FUNCTION_MANGLED(return_type, name, mangled_name, args, call_args) \
    return_type name args {                                                            \
        loadFunction(#mangled_name);                                                   \
        auto func = reinterpret_cast<decltype(::name)*>(funcMap[#mangled_name]);       \
        return func call_args;                                                         \
    }

#define DEFINE_JTAG_FUNCTION(return_type, name, args, call_args) \
    DEFINE_JTAG_FUNCTION_MANGLED(return_type, name, name, args, call_args)

    DEFINE_JTAG_FUNCTION(int, tt_open_jlink_by_serial_wrapper, (unsigned int serial_number), (serial_number))
    DEFINE_JTAG_FUNCTION(int, tt_open_jlink_wrapper, (), ())
    DEFINE_JTAG_FUNCTION(uint32_t, tt_read_tdr, (const char* client, uint32_t reg_offset), (client, reg_offset))
    DEFINE_JTAG_FUNCTION(uint32_t, tt_readmon_tdr, (const char* client, uint32_t id, uint32_t reg_offset),
                         (client, id, reg_offset))
    DEFINE_JTAG_FUNCTION(void, tt_writemon_tdr, (const char* client, uint32_t id, uint32_t reg_offset, uint32_t data),
                         (client, id, reg_offset, data))
    DEFINE_JTAG_FUNCTION(void, tt_write_tdr, (const char* client, uint32_t reg_offset, uint32_t data),
                         (client, reg_offset, data))
    DEFINE_JTAG_FUNCTION(void, tt_dbus_memdump,
                         (const char* client_name, const char* mem, const char* thread_id_name, const char* start_addr,
                          const char* end_addr),
                         (client_name, mem, thread_id_name, start_addr, end_addr))
    DEFINE_JTAG_FUNCTION(void, tt_dbus_sigdump,
                         (const char* client_name, uint32_t dbg_client_id, uint32_t dbg_signal_sel_start,
                          uint32_t dbg_signal_sel_end),
                         (client_name, dbg_client_id, dbg_signal_sel_start, dbg_signal_sel_end))
    DEFINE_JTAG_FUNCTION(void, tt_write_axi, (uint32_t reg_addr, uint32_t data, uint32_t* status),
                         (reg_addr, data, status))
    DEFINE_JTAG_FUNCTION(uint32_t, tt_write_noc_xy,
                         (uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, uint32_t noc_data, bool set_tlb,
                          uint32_t noc_tlb),
                         (node_x_id, node_y_id, noc_addr, noc_data, set_tlb, noc_tlb))
    DEFINE_JTAG_FUNCTION(void, tt_read_axi, (uint32_t reg_addr, uint32_t* data, uint32_t* status),
                         (reg_addr, data, status))
    DEFINE_JTAG_FUNCTION(uint32_t, tt_read_noc_xy,
                         (uint32_t node_x_id, uint32_t node_y_id, uint64_t noc_addr, bool set_tlb, uint32_t noc_tlb,
                          uint32_t* rddata),
                         (node_x_id, node_y_id, noc_addr, set_tlb, noc_tlb, rddata))
    DEFINE_JTAG_FUNCTION_MANGLED(std::vector<uint32_t>, tt_enumerate_jlink, _Z18tt_enumerate_jlinkv, (), ())

   private:
    void* handle;
    std::unordered_map<std::string, void*> funcMap;

    void loadFunction(const char* name);
};

#endif

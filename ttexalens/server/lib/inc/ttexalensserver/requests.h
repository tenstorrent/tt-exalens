// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <cstdint>

namespace tt::exalens {

// When adding new request, please add it into category
// New requests should always be added at the end of request group
enum class request_type : uint8_t {
    // Basic requests
    invalid = 0,
    ping = 1,

    // Device requests
    pci_read32 = 10,
    pci_write32,
    pci_read,
    pci_write,
    pci_read32_raw,
    pci_write32_raw,
    dma_buffer_read32,
    // Removed: get_harvester_coordinate_translation = 17,
    get_device_ids = 18,
    get_device_arch,
    get_device_soc_description,
    arc_msg,
    read_arc_telemetry_entry,

    // Device requests over jtag
    jtag_read32 = 50,
    jtag_write32 = 51,
    jtag_read32_axi = 52,
    jtag_write32_axi = 53,

    // Runtime requests
    pci_read_tile = 100,
    get_cluster_description = 102,
    convert_from_noc0 = 103,

    // File server requests
    get_file = 200,
};

// Structures for receiving requests
// If request doesn't need data, structure shouldn't be defined
// Structures are named as <name_of_request_type>_request.
// For example: request_type::pci_read32 has structure pci_read32_request.

struct request {
    request_type type;
} __attribute__((packed));

struct pci_read32_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
} __attribute__((packed));

struct pci_write32_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
    uint32_t data;
} __attribute__((packed));

struct pci_read_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
    uint32_t size;
} __attribute__((packed));

struct pci_write_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
    uint32_t size;
    uint8_t data[0];
} __attribute__((packed));

struct pci_read32_raw_request : request {
    uint8_t chip_id;
    uint32_t address;
} __attribute__((packed));

struct pci_write32_raw_request : request {
    uint8_t chip_id;
    uint32_t address;
    uint32_t data;
} __attribute__((packed));

struct dma_buffer_read32_request : request {
    uint8_t chip_id;
    uint64_t address;
    uint16_t channel;
} __attribute__((packed));

struct pci_read_tile_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
    uint32_t size;
    uint8_t data_format;
} __attribute__((packed));

struct get_device_arch_request : request {
    uint8_t chip_id;
} __attribute__((packed));

struct get_device_soc_description_request : request {
    uint8_t chip_id;
} __attribute__((packed));

struct get_file_request : request {
    uint32_t size;
    char data[0];
} __attribute__((packed));

struct convert_from_noc0_request : request {
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint32_t core_type_size;
    uint32_t coord_system_size;
    char data[0];
} __attribute__((packed));

struct arc_msg_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint32_t msg_code;
    bool wait_for_done;
    uint32_t arg0;
    uint32_t arg1;
    int timeout;
} __attribute__((packed));

struct read_arc_telemetry_entry_request : request {
    uint8_t chip_id;
    uint8_t telemetry_tag;
} __attribute__((packed));

struct jtag_read32_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
} __attribute__((packed));

struct jtag_write32_request : request {
    uint8_t noc_id;
    uint8_t chip_id;
    uint8_t noc_x;
    uint8_t noc_y;
    uint64_t address;
    uint32_t data;
} __attribute__((packed));

struct jtag_read32_axi_request : request {
    uint8_t chip_id;
    uint32_t address;
} __attribute__((packed));

struct jtag_write32_axi_request : request {
    uint8_t chip_id;
    uint32_t address;
    uint32_t data;
} __attribute__((packed));

}  // namespace tt::exalens

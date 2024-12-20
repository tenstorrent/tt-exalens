// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <ttlensserver/communication.h>

#include <string>

#include "ttlensserver/requests.h"

// Simple implementation of tt::lens::communication class that serializes every received request
// into yaml and returns it as response to the client.
class yaml_communication : public tt::lens::communication {
   protected:
    void process(const tt::lens::request& request) override;

   private:
    std::string serialize(const tt::lens::request& request);
    std::string serialize(const tt::lens::pci_read32_request& request);
    std::string serialize(const tt::lens::pci_write32_request& request);
    std::string serialize(const tt::lens::pci_read_request& request);
    std::string serialize(const tt::lens::pci_write_request& request);
    std::string serialize(const tt::lens::pci_read32_raw_request& request);
    std::string serialize(const tt::lens::pci_write32_raw_request& request);
    std::string serialize(const tt::lens::dma_buffer_read32_request& request);
    std::string serialize(const tt::lens::pci_read_tile_request& request);
    std::string serialize(const tt::lens::convert_from_noc0_request& request);
    std::string serialize(const tt::lens::get_device_arch_request& request);
    std::string serialize(const tt::lens::get_device_soc_description_request& request);
    std::string serialize(const tt::lens::get_file_request& request);
    std::string serialize(const tt::lens::arc_msg_request& request);
    std::string serialize(const tt::lens::jtag_read32_request& request);
    std::string serialize(const tt::lens::jtag_write32_request& request);
    std::string serialize(const tt::lens::jtag_read32_axi_request& request);
    std::string serialize(const tt::lens::jtag_write32_axi_request& request);
    std::string serialize_bytes(const uint8_t* data, size_t size);
};

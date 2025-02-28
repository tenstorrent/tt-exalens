// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <ttexalensserver/communication.h>

#include <string>

#include "ttexalensserver/requests.h"

// Simple implementation of tt::exalens::communication class that serializes every received request
// into yaml and returns it as response to the client.
class yaml_communication : public tt::exalens::communication {
   protected:
    void process(const tt::exalens::request& request) override;

   private:
    std::string serialize(const tt::exalens::request& request);
    std::string serialize(const tt::exalens::pci_read32_request& request);
    std::string serialize(const tt::exalens::pci_write32_request& request);
    std::string serialize(const tt::exalens::pci_read_request& request);
    std::string serialize(const tt::exalens::pci_write_request& request);
    std::string serialize(const tt::exalens::pci_read32_raw_request& request);
    std::string serialize(const tt::exalens::pci_write32_raw_request& request);
    std::string serialize(const tt::exalens::dma_buffer_read32_request& request);
    std::string serialize(const tt::exalens::pci_read_tile_request& request);
    std::string serialize(const tt::exalens::convert_from_noc0_request& request);
    std::string serialize(const tt::exalens::get_device_arch_request& request);
    std::string serialize(const tt::exalens::get_device_soc_description_request& request);
    std::string serialize(const tt::exalens::get_file_request& request);
    std::string serialize(const tt::exalens::arc_msg_request& request);
    std::string serialize(const tt::exalens::jtag_read32_request& request);
    std::string serialize(const tt::exalens::jtag_write32_request& request);
    std::string serialize(const tt::exalens::jtag_read32_axi_request& request);
    std::string serialize(const tt::exalens::jtag_write32_axi_request& request);
    std::string serialize_bytes(const uint8_t* data, size_t size);
};

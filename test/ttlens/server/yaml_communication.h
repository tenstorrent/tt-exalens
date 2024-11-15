// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <ttlensserver/communication.h>

#include <string>

#include "ttlensserver/requests.h"

// Simple implementation of tt::ttlens::communication class that serializes every received request
// into yaml and returns it as response to the client.
class yaml_communication : public tt::ttlens::communication {
   protected:
    void process(const tt::ttlens::request& request) override;

   private:
    std::string serialize(const tt::ttlens::request& request);
    std::string serialize(const tt::ttlens::pci_read32_request& request);
    std::string serialize(const tt::ttlens::pci_write32_request& request);
    std::string serialize(const tt::ttlens::pci_read_request& request);
    std::string serialize(const tt::ttlens::pci_write_request& request);
    std::string serialize(const tt::ttlens::pci_read32_raw_request& request);
    std::string serialize(const tt::ttlens::pci_write32_raw_request& request);
    std::string serialize(const tt::ttlens::dma_buffer_read32_request& request);
    std::string serialize(const tt::ttlens::pci_read_tile_request& request);
    std::string serialize(const tt::ttlens::get_harvester_coordinate_translation_request& request);
    std::string serialize(const tt::ttlens::get_device_arch_request& request);
    std::string serialize(const tt::ttlens::get_device_soc_description_request& request);
    std::string serialize(const tt::ttlens::get_file_request& request);
    std::string serialize(const tt::ttlens::arc_msg_request& request);
    std::string serialize(const tt::ttlens::jtag_read32_request& request);
    std::string serialize(const tt::ttlens::jtag_write32_request& request);
    std::string serialize(const tt::ttlens::jtag_read32_axi_request& request);
    std::string serialize(const tt::ttlens::jtag_write32_axi_request& request);
    std::string serialize_bytes(const uint8_t* data, size_t size);
};

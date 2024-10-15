// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <dbdserver/communication.h>

#include <string>

#include "dbdserver/requests.h"

// Simple implementation of tt::dbd::communication class that serializes every received request
// into yaml and returns it as response to the client.
class yaml_communication : public tt::dbd::communication {
   protected:
    void process(const tt::dbd::request& request) override;

   private:
    std::string serialize(const tt::dbd::request& request);
    std::string serialize(const tt::dbd::pci_read32_request& request);
    std::string serialize(const tt::dbd::pci_write32_request& request);
    std::string serialize(const tt::dbd::pci_read_request& request);
    std::string serialize(const tt::dbd::pci_write_request& request);
    std::string serialize(const tt::dbd::pci_read32_raw_request& request);
    std::string serialize(const tt::dbd::pci_write32_raw_request& request);
    std::string serialize(const tt::dbd::dma_buffer_read32_request& request);
    std::string serialize(const tt::dbd::pci_read_tile_request& request);
    std::string serialize(const tt::dbd::get_harvester_coordinate_translation_request& request);
    std::string serialize(const tt::dbd::get_device_arch_request& request);
    std::string serialize(const tt::dbd::get_device_soc_description_request& request);
    std::string serialize(const tt::dbd::get_file_request& request);
    std::string serialize(const tt::dbd::arc_msg_request& request);
    std::string serialize_bytes(const uint8_t* data, size_t size);
};

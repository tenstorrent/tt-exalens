// SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include <iostream>

#include "noc_overlay_parameters.h"
#include "noc_overlay_parameters.hpp"

using namespace Noc;

std::string replace(const std::string& input, const std::string& from, const std::string& to) {
    if (from.empty()) {
        return input;
    }
    std::string str = input;
    size_t start_pos = 0;
    while ((start_pos = str.find(from, start_pos)) != std::string::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length();
    }
    return str;
}

std::string trimRightBeforeNewline(std::string input) {
    size_t pos = 0;

    while (pos < input.size()) {
        // Find the next newline character
        size_t newline_pos = input.find('\n', pos);
        if (newline_pos == std::string::npos) {
            break;
        }

        // Find the position where trailing spaces start
        size_t trim_pos = newline_pos;
        while (trim_pos > pos && std::isspace(input[trim_pos - 1])) {
            --trim_pos;
        }

        // Remove trailing spaces before newline
        if (trim_pos < newline_pos) {
            input.replace(trim_pos, newline_pos - trim_pos, "");
        }

        pos = trim_pos + 1;  // Move to the next line
    }

    return input;
}

std::string fixDescription(const std::string& input, const std::string& to) {
    std::string description = replace(replace(input, "// ", to), "//", "");
    description = trimRightBeforeNewline(description);
    return description;
}

int main() {
    std::cout << "# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC" << std::endl;
    std::cout << std::endl;
    std::cout << "# SPDX-License-Identifier: Apache-2.0" << std::endl;
    std::cout << "############################################################" << std::endl;
    std::cout << "# AUTO_GENERATED! DO NOT MODIFY!" << std::endl;
    std::cout << "# File was generated using scripts/noc_to_python/n2p.sh." << std::endl;
    std::cout << "############################################################" << std::endl;
    std::cout << std::endl;
    std::cout << "from ctypes import LittleEndianStructure, c_uint32" << std::endl;
    std::cout << "from functools import cached_property" << std::endl;
    std::cout << "import struct" << std::endl;
    std::cout << std::endl;
    std::cout << "NOC_NUM_STREAMS = " << NOC_NUM_STREAMS << std::endl;
#ifdef ETH_NOC_NUM_STREAMS
    std::cout << "ETH_NOC_NUM_STREAMS = " << ETH_NOC_NUM_STREAMS << std::endl;
#endif
    std::cout << "NOC_OVERLAY_START_ADDR = 0x" << std::hex << std::uppercase << NOC_OVERLAY_START_ADDR << std::endl;
    std::cout << "NOC_STREAM_REG_SPACE_SIZE = 0x" << std::hex << std::uppercase << NOC_STREAM_REG_SPACE_SIZE
              << std::endl;
    std::cout << "NOC0_REGS_START_ADDR = 0x" << std::hex << std::uppercase << NOC0_REGS_START_ADDR << std::endl;
    std::cout << "NOC1_REGS_START_ADDR = 0x" << std::hex << std::uppercase << NOC1_REGS_START_ADDR << std::endl;
    std::cout << std::endl;
    std::cout << std::endl;
    std::cout << "def unpack_int(buffer: memoryview) -> int:" << std::endl;
    std::cout << "    int_value: int = struct.unpack_from(\"<I\", buffer)[0]" << std::endl;
    std::cout << "    return int_value" << std::endl;
    std::cout << std::endl;

    // Print structures used for parsing registers
    for (auto& reg : OLP::GetAllRegs()) {
        // Empty registers will be exposed on different place - reading them as whole
        if (reg.fields.size() == 0) {
            continue;
        }

        // Check if structure is defined as a sequence of fields in bitmask
        uint32_t calculatedOffset = 0;
        bool uniqueBitmasks = true;

        for (auto& field : reg.fields) {
            if (field.offset != calculatedOffset) {
                uniqueBitmasks = false;
                break;
            }
            calculatedOffset += field.width;
        }

        std::cout << std::endl;

        // Generate structure that will be used to read register
        std::string baseClass = uniqueBitmasks ? "(LittleEndianStructure)" : "";
        std::cout << "class Noc_" << reg.name << baseClass << ":" << std::endl;

        // Add class description
        if (!reg.description.empty()) {
            std::cout << "    \"\"\"" << std::endl
                      << fixDescription(reg.description, "    ") << "    \"\"\"" << std::endl
                      << std::endl;
        }

        // Add field type hints and description
        for (auto& field : reg.fields) {
            std::cout << "    " << field.name << ": int" << std::endl;
            if (!field.description.empty()) {
                std::cout << "    \"\"\"" << std::endl
                          << fixDescription(field.description, "    ") << "    \"\"\"" << std::endl
                          << std::endl;
            }
        }

        if (uniqueBitmasks) {
            // Print ctypes structure definition
            std::cout << "    _fields_ = [" << std::endl;
            for (auto& field : reg.fields) {
                std::cout << "        (\"" << field.name << "\", c_uint32, " << std::dec << field.width << "),"
                          << std::endl;
            }
            std::cout << "    ]" << std::endl;
        } else {
            // Print class definition with parser function
            std::cout << std::endl;
            std::cout << "    @classmethod" << std::endl;
            std::cout << "    def from_buffer_copy(cls, buffer: memoryview) -> Noc_" << reg.name << ":" << std::endl;
            std::cout << "        instance = cls()" << std::endl;
            std::cout << "        value = unpack_int(buffer[0:4])" << std::endl;
            for (auto& field : reg.fields) {
                std::cout << "        instance." << field.name << " = (value >> " << std::dec << field.offset
                          << ") & ((1 << " << std::dec << field.width << ") - 1)" << std::endl;
            }
            std::cout << "        return instance" << std::endl;
        }
        std::cout << std::endl;
    }

    std::cout << std::endl;

    // Print class definition to parse all registers
    std::cout << "class NocOverlayRegistersState:" << std::endl;
    std::cout << "    def __init__(self, buffer: bytes):" << std::endl;
    std::cout << "        self.__buffer = memoryview(buffer)" << std::endl;
    std::cout << std::endl;

    // Print properties that are fetching registers
    for (auto& reg : OLP::GetAllRegs()) {
        if (reg.fields.size() == 0) {
            std::cout << "    @cached_property" << std::endl;
            std::cout << "    def " << reg.name << "(self) -> int:" << std::endl;
            if (!reg.description.empty()) {
                std::cout << "        \"\"\"" << std::endl
                          << fixDescription(reg.description, "        ") << "        \"\"\"" << std::endl;
            }
            std::cout << "        return unpack_int(self.__buffer[" << std::dec << (reg.index * 4) << ":])"
                      << std::endl;
            std::cout << std::endl;
        } else {
            std::cout << "    @cached_property" << std::endl;
            std::cout << "    def " << reg.name << "(self) -> Noc_" << reg.name << ":" << std::endl;
            if (!reg.description.empty()) {
                std::cout << "        \"\"\"" << std::endl
                          << fixDescription(reg.description, "        ") << "        \"\"\"" << std::endl;
            }
            std::cout << "        return Noc_" << reg.name << ".from_buffer_copy(self.__buffer[" << std::dec
                      << (reg.index * 4) << ":])" << std::endl;
            std::cout << std::endl;

            for (auto& field : reg.fields) {
                std::cout << "    @cached_property" << std::endl;
                std::cout << "    def " << field.name << "(self) -> int:" << std::endl;
                if (!field.description.empty()) {
                    std::cout << "        \"\"\"" << std::endl
                              << fixDescription(field.description, "        ") << "        \"\"\"" << std::endl;
                }
                std::cout << "        return self." << reg.name << "." << field.name << std::endl;
                std::cout << std::endl;
            }
        }
    }

    std::cout << "    def get_stream_reg_field(self, reg_index: int, start_bit: int, num_bits: int):" << std::endl;
    std::cout << "        value = unpack_int(self.__buffer[reg_index * 4 :])" << std::endl;
    std::cout << "        mask = (1 << num_bits) - 1" << std::endl;
    std::cout << "        value = (value >> start_bit) & mask" << std::endl;
    std::cout << "        return value" << std::endl;

#ifdef GENERATE_DEBUG_INFO
    // Print methods to read registers (debugging info)
    for (auto& reg : OLP::GetAllRegs()) {
        if (reg.fields.size() == 0) {
            std::cout << "    def read_" << reg.name << "(self, device, location, stream_id) -> int:" << std::endl;
            std::cout << "        return device.get_stream_reg_field(location, stream_id, " << std::dec << reg.index
                      << ", 0, 32)" << std::endl;
            std::cout << std::endl;
        } else {
            for (auto& field : reg.fields) {
                std::cout << "    def read_" << field.name
                          << "(self, device, location, stream_id) -> int:" << std::endl;
                std::cout << "        return device.get_stream_reg_field(location, stream_id, " << std::dec << reg.index
                          << ", " << field.offset << ", " << field.width << ")" << std::endl;
                std::cout << std::endl;
            }
        }
    }
#endif

    return 0;
}

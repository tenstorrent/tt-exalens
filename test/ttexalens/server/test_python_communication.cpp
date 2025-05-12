// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include <gtest/gtest.h>

#include <cstdlib>
#include <filesystem>
#include <fstream>

#include "yaml_communication.h"

constexpr int DEFAULT_TEST_SERVER_PORT = 6667;

std::unique_ptr<yaml_communication> start_yaml_server(int port = DEFAULT_TEST_SERVER_PORT);

std::string execute_command(const std::string& cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);

    if (!pipe) {
        throw std::runtime_error("popen() failed!");
    }

    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }

    return result;
}

bool check_script_exists(std::string python_script) {
    std::replace(python_script.begin(), python_script.end(), '.', '/');
    return std::filesystem::exists(python_script + ".py");
}

void call_python(const std::string& python_script, int server_port, const std::string& python_args,
                 const std::string& expected_output) {
    // Check if the python script exists
    ASSERT_TRUE(check_script_exists(python_script));

    std::string command = "python3 -m " + python_script + " " + std::to_string(server_port) + " " + python_args;

    auto output = execute_command(command);
    ASSERT_EQ(output, expected_output);
}

static void call_python(const std::string& python_args, const std::string& expected_output) {
    auto server = start_yaml_server();
    std::string python_tests_path = "test.ttexalens.server.test_communication";
    call_python(python_tests_path, server->get_port(), python_args, expected_output);
}

TEST(ttexalens_python_communication, ping) { call_python("ping", "- type: 1\n"); }

TEST(ttexalens_python_communication, get_cluster_description) {
    call_python("get_cluster_description", "- type: 102\n");
}

TEST(ttexalens_python_communication, get_device_ids) { call_python("get_device_ids", "- type: 18\n"); }

TEST(ttexalens_python_communication, pci_read32) {
    call_python("pci_read32", "- type: 10\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n");
}

TEST(ttexalens_python_communication, pci_write32) {
    call_python("pci_write32",
                "- type: 11\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  data: 987654\n");
}

TEST(ttexalens_python_communication, pci_read) {
    call_python("pci_read",
                "- type: 12\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024\n");
}

TEST(ttexalens_python_communication, pci_read32_raw) {
    call_python("pci_read32_raw", "- type: 14\n  chip_id: 1\n  address: 123456\n");
}

TEST(ttexalens_python_communication, pci_write32_raw) {
    call_python("pci_write32_raw", "- type: 15\n  chip_id: 1\n  address: 123456\n  data: 987654\n");
}

TEST(ttexalens_python_communication, dma_buffer_read32) {
    call_python("dma_buffer_read32", "- type: 16\n  chip_id: 1\n  address: 123456\n  channel: 456\n");
}

TEST(ttexalens_python_communication, pci_read_tile) {
    call_python("pci_read_tile",
                "- type: 100\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024\n  "
                "data_format: 14\n");
}

TEST(ttexalens_python_communication, get_device_arch) { call_python("get_device_arch", "- type: 19\n  chip_id: 1\n"); }

TEST(ttexalens_python_communication, get_device_soc_description) {
    call_python("get_device_soc_description", "- type: 20\n  chip_id: 1\n");
}

TEST(ttexalens_python_communication, convert_from_noc0) {
    call_python("convert_from_noc0",
                "- type: 103\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  core_type_size: 9\n  coord_system_size: 12\n  "
                "data: core_typecoord_system\n");
}

TEST(ttexalens_python_communication, pci_write) {
    call_python("pci_write",
                "- type: 13\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 8\n  data: "
                "[10, 11, 12, 13, 14, "
                "15, 16, 17]\n");
}

TEST(ttexalens_python_communication, get_file) {
    call_python("get_file", "- type: 200\n  size: 9\n  path: test_file\n");
}

TEST(ttexalens_python_communication, jtag_read32) {
    call_python("jtag_read32", "- type: 50\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n");
}

TEST(ttexalens_python_communication, jtag_write32) {
    call_python("jtag_write32",
                "- type: 51\n  noc_id: 0\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  data: 987654\n");
}

TEST(ttexalens_python_communication, jtag_read32_axi) {
    call_python("jtag_read32_axi", "- type: 52\n  chip_id: 1\n  address: 123456\n");
}

TEST(ttexalens_python_communication, jtag_write32_axi) {
    call_python("jtag_write32_axi", "- type: 53\n  chip_id: 1\n  address: 123456\n  data: 987654\n");
}

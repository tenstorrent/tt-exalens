// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include <gtest/gtest.h>

#include <memory>
#include <string>
#include <zmq.hpp>

#include "dbdserver/requests.h"
#include "yaml_communication.h"

constexpr int DEFAULT_TEST_SERVER_PORT = 6666;

zmq::message_t send_message(zmq::const_buffer buffer, int port = DEFAULT_TEST_SERVER_PORT) {
    zmq::message_t respond;
    zmq::context_t context;
    zmq::socket_t socket(context, zmq::socket_type::req);

    socket.connect("tcp://127.0.0.1:" + std::to_string(port));

    auto send_result = socket.send(buffer);
    auto receive_result = socket.recv(respond);

    return respond;
}

template <typename T>
std::string send_message_yaml(const T& request, int port = DEFAULT_TEST_SERVER_PORT) {
    auto respond = send_message(zmq::const_buffer(&request, sizeof(T)), port);

    return respond.to_string();
}

std::unique_ptr<yaml_communication> start_yaml_server(int port = DEFAULT_TEST_SERVER_PORT) {
    std::unique_ptr<yaml_communication> server = std::make_unique<yaml_communication>();

    server->start(port);
    return server;
}

TEST(debuda_communication, fail_second_server_starts) {
    auto server1 = start_yaml_server();
    ASSERT_TRUE(server1->is_connected());
    std::unique_ptr<yaml_communication> server2;
    ASSERT_THROW(server2 = start_yaml_server(), zmq::error_t);
}

TEST(debuda_communication, safe_deinitialize) {
    {
        auto server1 = start_yaml_server();
        ASSERT_TRUE(server1->is_connected());
    }
    {
        auto server2 = start_yaml_server();
        ASSERT_TRUE(server2->is_connected());
    }
}

template <typename T>
void test_yaml_request(const T& request, const std::string& expected_response) {
    auto server = start_yaml_server();
    ASSERT_TRUE(server->is_connected());
    auto response = send_message_yaml(request);
    ASSERT_EQ(response, expected_response);
}

TEST(debuda_communication, ping) { test_yaml_request(tt::dbd::request{tt::dbd::request_type::ping}, "- type: 1"); }

TEST(debuda_communication, get_runtime_data) {
    test_yaml_request(tt::dbd::request{tt::dbd::request_type::get_runtime_data}, "- type: 101");
}

TEST(debuda_communication, get_cluster_description) {
    test_yaml_request(tt::dbd::request{tt::dbd::request_type::get_cluster_description}, "- type: 102");
}

TEST(debuda_communication, get_device_ids) {
    test_yaml_request(tt::dbd::request{tt::dbd::request_type::get_device_ids}, "- type: 18");
}

TEST(debuda_communication, pci_read32) {
    test_yaml_request(tt::dbd::pci_read32_request{tt::dbd::request_type::pci_read32, 1, 2, 3, 123456},
                      "- type: 10\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456");
}

TEST(debuda_communication, pci_write32) {
    test_yaml_request(tt::dbd::pci_write32_request{tt::dbd::request_type::pci_write32, 1, 2, 3, 123456, 987654},
                      "- type: 11\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  data: 987654");
}

TEST(debuda_communication, pci_read) {
    test_yaml_request(tt::dbd::pci_read_request{tt::dbd::request_type::pci_read, 1, 2, 3, 123456, 1024},
                      "- type: 12\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024");
}

TEST(debuda_communication, pci_read32_raw) {
    test_yaml_request(tt::dbd::pci_read32_raw_request{tt::dbd::request_type::pci_read32_raw, 1, 123456},
                      "- type: 14\n  chip_id: 1\n  address: 123456");
}

TEST(debuda_communication, pci_write32_raw) {
    test_yaml_request(tt::dbd::pci_write32_raw_request{tt::dbd::request_type::pci_write32_raw, 1, 123456, 987654},
                      "- type: 15\n  chip_id: 1\n  address: 123456\n  data: 987654");
}

TEST(debuda_communication, dma_buffer_read32) {
    test_yaml_request(tt::dbd::dma_buffer_read32_request{tt::dbd::request_type::dma_buffer_read32, 1, 123456, 456},
                      "- type: 16\n  chip_id: 1\n  address: 123456\n  channel: 456");
}

TEST(debuda_communication, pci_read_tile) {
    test_yaml_request(
        tt::dbd::pci_read_tile_request{tt::dbd::request_type::pci_read_tile, 1, 2, 3, 123456, 1024, 14},
        "- type: 100\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024\n  data_format: 14");
}

TEST(debuda_communication, get_harvester_coordinate_translation) {
    test_yaml_request(
        tt::dbd::get_harvester_coordinate_translation_request{
            tt::dbd::request_type::get_harvester_coordinate_translation, 1},
        "- type: 17\n  chip_id: 1");
}

TEST(debuda_communication, get_device_arch) {
    test_yaml_request(tt::dbd::get_device_arch_request{tt::dbd::request_type::get_device_arch, 1},
                      "- type: 19\n  chip_id: 1");
}

TEST(debuda_communication, get_device_soc_description) {
    test_yaml_request(tt::dbd::get_device_soc_description_request{tt::dbd::request_type::get_device_soc_description, 1},
                      "- type: 20\n  chip_id: 1");
}

TEST(debuda_communication, pci_write) {
    // This test is different because we are trying to send request that has dynamic structure size
    std::string expected_response =
        "- type: 13\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 8\n  data: [10, 11, 12, 13, 14, "
        "15, 16, 17]";
    constexpr size_t data_size = 8;
    std::array<uint8_t, data_size + sizeof(tt::dbd::pci_write_request)> request_data = {0};
    auto request = reinterpret_cast<tt::dbd::pci_write_request*>(&request_data[0]);
    request->type = tt::dbd::request_type::pci_write;
    request->chip_id = 1;
    request->noc_x = 2;
    request->noc_y = 3;
    request->address = 123456;
    request->size = data_size;
    for (size_t i = 0; i < data_size; i++) request->data[i] = 10 + i;

    auto server = start_yaml_server();
    ASSERT_TRUE(server->is_connected());
    auto response = send_message(zmq::const_buffer(request_data.data(), request_data.size())).to_string();
    ASSERT_EQ(response, expected_response);
}

TEST(debuda_communication, get_file) {
    constexpr std::string_view filename = "test_file";
    std::string expected_response =
        "- type: 200\n  size: " + std::to_string(filename.size()) + "\n  path: " + filename.data();
    std::array<uint8_t, filename.size() + sizeof(tt::dbd::get_file_request)> request_data = {0};
    auto request = reinterpret_cast<tt::dbd::get_file_request*>(&request_data[0]);
    request->type = tt::dbd::request_type::get_file;
    request->size = filename.size();
    for (size_t i = 0; i < filename.size(); i++) request->data[i] = filename[i];

    auto server = start_yaml_server();
    ASSERT_TRUE(server->is_connected());
    auto response = send_message(zmq::const_buffer(request_data.data(), request_data.size())).to_string();
    ASSERT_EQ(response, expected_response);
}

TEST(debuda_communication, arc_msg) {
    auto req = tt::dbd::arc_msg_request{tt::dbd::request_type::arc_msg, 1, 2, true, 3, 4, 5};

    test_yaml_request(
        req, "- type: " + std::to_string(static_cast<int>(tt::dbd::request_type::arc_msg)) +" \n  chip_id: 1\n  msg_code: 2\n  wait_for_done: 1\n  arg0: 3\n  arg1: 4\n  timeout: 5");
}

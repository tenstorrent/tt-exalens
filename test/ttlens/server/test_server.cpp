// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include <gtest/gtest.h>
#include <ttlensserver/server.h>
#include <ttlensserver/ttlens_implementation.h>

#include <memory>
#include <string>
#include <vector>
#include <zmq.hpp>

#include "ttlensserver/requests.h"

constexpr int DEFAULT_TEST_SERVER_PORT = 6668;

namespace tt::lens {

class yaml_not_implemented_server : public server {
   private:
    bool enable_yaml;
    friend class yaml_not_implemented_implementation;

    void send_yaml(const std::string &yaml_response) {
        if (enable_yaml) {
            // This is not intended implementation in production. This server is returning two messages for every
            // request. First message is yaml of input data and second is NOT_SUPPORTED. Since returning two messages is
            // not allowed in REP/REQ pattern in ZMQ, we receive one more message from the test and ignore it.
            communication::respond(yaml_response);
            zmq::message_t ignored_message;
            auto receive_result = zmq_socket.recv(ignored_message);
        }
    }

   public:
    yaml_not_implemented_server(bool enable_yaml);

    std::optional<std::vector<uint8_t>> get_file(const std::string &path) override {
        if (enable_yaml) {
            send_yaml("- type: 200\n  size: " + std::to_string(path.size()) + "\n  data: " + path);
            return {};
        } else {
            return {};
        }
    }

    bool is_yaml_enabled() const { return enable_yaml; }
};

class yaml_not_implemented_implementation : public ttlens_implementation {
   private:
    yaml_not_implemented_server *server;

   public:
    yaml_not_implemented_implementation(yaml_not_implemented_server *server) : server(server) {}

    std::optional<uint32_t> pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_read32)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address));
        return {};
    }
    std::optional<uint32_t> pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                        uint32_t data) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_write32)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address) +
                          "\n  data: " + std::to_string(data));
        return {};
    }
    std::optional<std::vector<uint8_t>> pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                 uint32_t size) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_read)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address) +
                          "\n  size: " + std::to_string(size));
        return {};
    }
    std::optional<uint32_t> pci_write(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                      const uint8_t *data, uint32_t size) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_write)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address) +
                          "\n  size: " + std::to_string(size) + "\n  data: " + serialize_bytes(data, size));
        return {};
    }
    std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_read32_raw)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  address: " + std::to_string(address));
        return {};
    }
    std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_write32_raw)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  address: " + std::to_string(address) +
                          "\n  data: " + std::to_string(data));
        return {};
    }
    std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::dma_buffer_read32)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  address: " + std::to_string(address) +
                          "\n  channel: " + std::to_string(channel));
        return {};
    }

    std::optional<std::string> pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                             uint32_t size, uint8_t data_format) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::pci_read_tile)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address) +
                          "\n  size: " + std::to_string(size) + "\n  data_format: " + std::to_string(data_format));
        return {};
    }

    std::optional<std::string> get_cluster_description() override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::get_cluster_description)));
        return {};
    }
    std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                  const std::string &core_type,
                                                                  const std::string &coord_system) override {
        server->send_yaml(
            "- type: " + std::to_string(static_cast<int>(request_type::convert_from_noc0)) +
            "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
            "\n  noc_y: " + std::to_string(noc_y) + "\n  core_type_size: " + std::to_string(core_type.size()) +
            "\n  coord_system_size: " + std::to_string(coord_system.size()) + "\n  data: " + core_type + coord_system);
        return {};
    }
    std::optional<std::vector<uint8_t>> get_device_ids() override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::get_device_ids)));
        return {};
    }
    std::optional<std::string> get_device_arch(uint8_t chip_id) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::get_device_arch)) +
                          "\n  chip_id: " + std::to_string(chip_id));
        return {};
    }
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::get_device_soc_description)) +
                          "\n  chip_id: " + std::to_string(chip_id));
        return {};
    }

    std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t chip_id, uint32_t msg_code, bool wait_for_done,
                                                               uint32_t arg0, uint32_t arg1, int timeout) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::arc_msg)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  msg_code: " + std::to_string(msg_code) +
                          "\n  wait_for_done: " + std::to_string(wait_for_done) + "\n  arg0: " + std::to_string(arg0) +
                          "\n  arg1: " + std::to_string(arg1) + "\n  timeout: " + std::to_string(timeout));
        return {};
    }

    std::optional<uint32_t> jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::jtag_read32)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address));
        return {};
    }
    std::optional<int> jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::jtag_write32)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  noc_x: " + std::to_string(noc_x) +
                          "\n  noc_y: " + std::to_string(noc_y) + "\n  address: " + std::to_string(address) +
                          "\n  data: " + std::to_string(data));
        return {};
    }

    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::jtag_read32_axi)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  address: " + std::to_string(address));
        return {};
    }
    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override {
        server->send_yaml("- type: " + std::to_string(static_cast<int>(request_type::jtag_write32_axi)) +
                          "\n  chip_id: " + std::to_string(chip_id) + "\n  address: " + std::to_string(address) +
                          "\n  data: " + std::to_string(data));
        return {};
    }

    static std::string serialize_bytes(const uint8_t *data, size_t size) {
        std::string bytes;

        for (size_t i = 0; i < size; i++) {
            if (!bytes.empty()) {
                bytes += ", ";
            }
            bytes += std::to_string(data[i]);
        }
        return "[" + bytes + "]";
    }
};

yaml_not_implemented_server::yaml_not_implemented_server(bool enable_yaml)
    : server(std::make_unique<yaml_not_implemented_implementation>(this)), enable_yaml(enable_yaml) {}

}  // namespace tt::lens

zmq::message_t send_message(zmq::const_buffer buffer, int port = DEFAULT_TEST_SERVER_PORT);

std::pair<zmq::message_t, zmq::message_t> send_message_receive2(zmq::const_buffer buffer, bool do_yaml_test,
                                                                int port = DEFAULT_TEST_SERVER_PORT) {
    zmq::message_t respond1, respond2;
    zmq::context_t context;
    zmq::socket_t socket(context, zmq::socket_type::req);

    socket.connect("tcp://127.0.0.1:" + std::to_string(port));

    auto send_result = socket.send(buffer);

    if (do_yaml_test) {
        // This message pair is not intended in production as it is returning yaml representation and excepts one more
        // message from the client in test function.
        auto receive_result_yaml = socket.recv(respond1);
        auto send_result_ignored = socket.send(buffer);
    }

    auto receive_result = socket.recv(respond2);

    return std::make_pair(std::move(respond1), std::move(respond2));
}

std::unique_ptr<tt::lens::server> start_server(bool enable_yaml, int port = DEFAULT_TEST_SERVER_PORT) {
    auto server = std::make_unique<tt::lens::yaml_not_implemented_server>(enable_yaml);

    server->start(port);
    return server;
}

template <typename T>
void test_not_implemented_request(const T &request, const std::string &expected_yaml, size_t size = sizeof(T)) {
    bool do_yaml_test = true;
    auto server = start_server(do_yaml_test);
    ASSERT_TRUE(server->is_connected());
    auto response = send_message_receive2(zmq::const_buffer(&request, size), do_yaml_test);
    ASSERT_EQ(response.first.to_string(), expected_yaml);
    ASSERT_EQ(response.second.to_string(), std::string("NOT_SUPPORTED"));
}

TEST(ttlens_server, ping) {
    tt::lens::request request{tt::lens::request_type::ping};
    auto server = start_server(false);
    ASSERT_TRUE(server->is_connected());
    auto response = send_message(zmq::const_buffer(&request, sizeof(request))).to_string();
    ASSERT_EQ(response, std::string("PONG"));
}

TEST(ttlens_server, get_cluster_description) {
    test_not_implemented_request(tt::lens::request{tt::lens::request_type::get_cluster_description}, "- type: 102");
}

TEST(ttlens_server, get_device_ids) {
    test_not_implemented_request(tt::lens::request{tt::lens::request_type::get_device_ids}, "- type: 18");
}

TEST(ttlens_server, pci_read32) {
    test_not_implemented_request(tt::lens::pci_read32_request{tt::lens::request_type::pci_read32, 1, 2, 3, 123456},
                                 "- type: 10\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456");
}

TEST(ttlens_server, pci_write32) {
    test_not_implemented_request(
        tt::lens::pci_write32_request{tt::lens::request_type::pci_write32, 1, 2, 3, 123456, 987654},
        "- type: 11\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  data: 987654");
}

TEST(ttlens_server, pci_read) {
    test_not_implemented_request(tt::lens::pci_read_request{tt::lens::request_type::pci_read, 1, 2, 3, 123456, 1024},
                                 "- type: 12\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024");
}

TEST(ttlens_server, pci_read32_raw) {
    test_not_implemented_request(tt::lens::pci_read32_raw_request{tt::lens::request_type::pci_read32_raw, 1, 123456},
                                 "- type: 14\n  chip_id: 1\n  address: 123456");
}

TEST(ttlens_server, pci_write32_raw) {
    test_not_implemented_request(
        tt::lens::pci_write32_raw_request{tt::lens::request_type::pci_write32_raw, 1, 123456, 987654},
        "- type: 15\n  chip_id: 1\n  address: 123456\n  data: 987654");
}

TEST(ttlens_server, dma_buffer_read32) {
    test_not_implemented_request(
        tt::lens::dma_buffer_read32_request{tt::lens::request_type::dma_buffer_read32, 1, 123456, 456},
        "- type: 16\n  chip_id: 1\n  address: 123456\n  channel: 456");
}

TEST(ttlens_server, pci_read_tile) {
    test_not_implemented_request(
        tt::lens::pci_read_tile_request{tt::lens::request_type::pci_read_tile, 1, 2, 3, 123456, 1024, 14},
        "- type: 100\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 1024\n  data_format: 14");
}

TEST(ttlens_server, get_device_arch) {
    test_not_implemented_request(tt::lens::get_device_arch_request{tt::lens::request_type::get_device_arch, 1},
                                 "- type: 19\n  chip_id: 1");
}

TEST(ttlens_server, get_device_soc_description) {
    test_not_implemented_request(
        tt::lens::get_device_soc_description_request{tt::lens::request_type::get_device_soc_description, 1},
        "- type: 20\n  chip_id: 1");
}

TEST(ttlens_server, jtag_read32) {
    test_not_implemented_request(tt::lens::jtag_read32_request{tt::lens::request_type::jtag_read32, 1, 2, 3, 123456},
                                 "- type: 50\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456");
}

TEST(ttlens_server, jtag_write32) {
    test_not_implemented_request(
        tt::lens::jtag_write32_request{tt::lens::request_type::jtag_write32, 1, 2, 3, 123456, 987654},
        "- type: 51\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  data: 987654");
}

TEST(ttlens_server, jtag_read32_axi) {
    test_not_implemented_request(tt::lens::jtag_read32_axi_request{tt::lens::request_type::jtag_read32_axi, 1, 123456},
                                 "- type: 52\n  chip_id: 1\n  address: 123456");
}

TEST(ttlens_server, jtag_write32_axi) {
    test_not_implemented_request(
        tt::lens::jtag_write32_axi_request{tt::lens::request_type::jtag_write32_axi, 1, 123456, 987654},
        "- type: 53\n  chip_id: 1\n  address: 123456\n  data: 987654");
}

TEST(ttlens_server, pci_write) {
    // This test is different because we are trying to send request that has dynamic structure size
    std::string expected_response =
        "- type: 13\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  address: 123456\n  size: 8\n  data: [10, 11, 12, 13, 14, "
        "15, 16, 17]";
    constexpr size_t data_size = 8;
    std::array<uint8_t, data_size + sizeof(tt::lens::pci_write_request)> request_data = {0};
    auto request = reinterpret_cast<tt::lens::pci_write_request *>(&request_data[0]);
    request->type = tt::lens::request_type::pci_write;
    request->chip_id = 1;
    request->noc_x = 2;
    request->noc_y = 3;
    request->address = 123456;
    request->size = data_size;
    for (size_t i = 0; i < data_size; i++) request->data[i] = 10 + i;

    test_not_implemented_request(*request, expected_response, request_data.size());
}

TEST(ttlens_server, get_file) {
    // This test is different because we are trying to send request that has dynamic structure size
    constexpr std::string_view filename = "test_file";
    std::string expected_response =
        "- type: 200\n  size: " + std::to_string(filename.size()) + "\n  data: " + filename.data();
    std::array<uint8_t, filename.size() + sizeof(tt::lens::get_file_request)> request_data = {0};
    auto request = reinterpret_cast<tt::lens::get_file_request *>(&request_data[0]);
    request->type = tt::lens::request_type::get_file;
    request->size = filename.size();
    for (size_t i = 0; i < filename.size(); i++) request->data[i] = filename[i];
    test_not_implemented_request(*request, expected_response, request_data.size());
}

TEST(ttlens_server, convert_from_noc0) {
    // This test is different because we are trying to send request that has dynamic structure size
    constexpr std::string_view core_type = "core_type";
    constexpr std::string_view coord_system = "coord_system";
    std::string expected_response =
        "- type: 103\n  chip_id: 1\n  noc_x: 2\n  noc_y: 3\n  core_type_size: 9\n  coord_system_size: 12\n  data: "
        "core_typecoord_system";
    std::array<uint8_t, core_type.size() + coord_system.size() + sizeof(tt::lens::convert_from_noc0_request)>
        request_data = {0};
    auto request = reinterpret_cast<tt::lens::convert_from_noc0_request *>(&request_data[0]);
    request->type = tt::lens::request_type::convert_from_noc0;
    request->chip_id = 1;
    request->noc_x = 2;
    request->noc_y = 3;
    request->core_type_size = core_type.size();
    request->coord_system_size = coord_system.size();
    memcpy(request->data, core_type.data(), request->core_type_size);
    memcpy(request->data + request->core_type_size, coord_system.data(), request->coord_system_size);

    test_not_implemented_request(*request, expected_response, request_data.size());
}

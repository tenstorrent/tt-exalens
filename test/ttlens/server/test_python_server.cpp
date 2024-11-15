// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include <dbdserver/ttlens_implementation.h>
#include <dbdserver/server.h>
#include <gtest/gtest.h>

#include <map>
#include <tuple>
#include <vector>
#include <zmq.hpp>

constexpr int DEFAULT_TEST_SERVER_PORT = 6669;

// Simple implementation of tt::dbd::server that simulates real server.
class simulation_server : public tt::dbd::server {
   public:
    simulation_server(std::unique_ptr<tt::dbd::ttlens_implementation> implementation)
        : tt::dbd::server(std::move(implementation)) {}

    std::optional<std::vector<uint8_t>> get_file(const std::string& path) override {
        std::string response = "get_file(" + path + ")";
        return std::vector<uint8_t>(response.begin(), response.end());
    }

    std::optional<std::string> get_run_dirpath() override { return "get_run_dirpath"; }
};

// Simple implementation of tt::dbd::ttlens_implementation that simulates real implementation.
// For every write combination, read of the same communication will return that result.
class simulation_implementation : public tt::dbd::ttlens_implementation {
   private:
    std::map<std::tuple<uint8_t, uint8_t, uint8_t, uint64_t>, uint32_t> read_write_4;
    std::map<std::tuple<uint8_t, uint8_t, uint8_t, uint64_t, uint32_t>, std::vector<uint8_t>> read_write;
    std::map<std::tuple<uint8_t, uint64_t>, uint32_t> read_write_4_raw;
    std::map<std::tuple<uint8_t, uint8_t, uint8_t, uint64_t>, uint32_t> jtag_read_write_4;
    std::map<uint32_t, uint32_t> jtag_read_write_2;

   protected:
    std::optional<uint32_t> pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override {
        auto it = read_write_4.find(std::make_tuple(chip_id, noc_x, noc_y, address));
        if (it != read_write_4.end()) {
            return it->second;
        }
        return {};
    }
    std::optional<uint32_t> pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                        uint32_t data) override {
        read_write_4[std::make_tuple(chip_id, noc_x, noc_y, address)] = data;
        return 4;
    }
    std::optional<std::vector<uint8_t>> pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                 uint32_t size) override {
        auto it = read_write.find(std::make_tuple(chip_id, noc_x, noc_y, address, size));
        if (it != read_write.end()) {
            return it->second;
        }
        return {};
    }
    std::optional<uint32_t> pci_write(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                      const uint8_t* data, uint32_t size) override {
        std::vector<uint8_t> data_vector(size);
        for (size_t i = 0; i < size; i++) {
            data_vector[i] = data[i];
        }
        read_write[std::make_tuple(chip_id, noc_x, noc_y, address, size)] = data_vector;
        return size;
    }
    std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) override {
        auto it = read_write_4_raw.find(std::make_tuple(chip_id, address));
        if (it != read_write_4_raw.end()) {
            return it->second;
        }
        return {};
    }
    std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) override {
        read_write_4_raw[std::make_tuple(chip_id, address)] = data;
        return 4;
    }
    std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) override {
        auto it = read_write_4_raw.find(std::make_tuple(chip_id, address));
        if (it != read_write_4_raw.end()) {
            return it->second + channel;
        }
        return {};
    }

    std::optional<uint32_t> jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address) override {
        auto it = jtag_read_write_4.find(std::make_tuple(chip_id, noc_x, noc_y, address));
        if (it != jtag_read_write_4.end()) {
            return it->second;
        }
        return {};
    }
    std::optional<int> jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override {
        jtag_read_write_4[std::make_tuple(chip_id, noc_x, noc_y, address)] = data;
        return 4;
    }

    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override {
        auto it = jtag_read_write_2.find(address);
        if (it != jtag_read_write_2.end()) {
            return it->second;
        }
        return {};
    }
    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override {
        jtag_read_write_2[address] = data;
        return 4;
    }

    std::optional<std::string> pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                             uint32_t size, uint8_t data_format) override {
        return "pci_read_tile(" + std::to_string(chip_id) + ", " + std::to_string(noc_x) + ", " +
               std::to_string(noc_y) + ", " + std::to_string(address) + ", " + std::to_string(size) + ", " +
               std::to_string(data_format) + ")";
    }
    std::optional<std::string> get_runtime_data() override { return "get_runtime_data()"; }
    std::optional<std::string> get_cluster_description() override { return "get_cluster_description()"; }
    std::optional<std::string> get_harvester_coordinate_translation(uint8_t chip_id) override {
        return "get_harvester_coordinate_translation(" + std::to_string(chip_id) + ")";
    }
    std::optional<std::vector<uint8_t>> get_device_ids() override { return std::vector<uint8_t>{0, 1}; }
    std::optional<std::string> get_device_arch(uint8_t chip_id) override {
        return "get_device_arch(" + std::to_string(chip_id) + ")";
    }
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override {
        return "get_device_soc_description(" + std::to_string(chip_id) + ")";
    }
};

void call_python(const std::string& python_script, int server_port, const std::string& python_args,
                 const std::string& expected_output);
std::unique_ptr<tt::dbd::server> start_server(bool enable_yaml, int port = DEFAULT_TEST_SERVER_PORT);

static void call_python_empty_server(const std::string& python_args, int port = DEFAULT_TEST_SERVER_PORT) {
    auto server = start_server(false, port);
    ASSERT_TRUE(server->is_connected());
    std::string python_tests_path = "test.ttlens.server.test_server";
    call_python(python_tests_path, server->get_port(), python_args, "pass\n");
}

static void call_python_server(const std::string& python_args, int port = DEFAULT_TEST_SERVER_PORT) {
    simulation_server simulation_server(std::make_unique<simulation_implementation>());
    simulation_server.start(port);
    ASSERT_TRUE(simulation_server.is_connected());
    std::string python_tests_path = "test.ttlens.server.test_server";
    call_python(python_tests_path, simulation_server.get_port(), python_args, "pass\n");
}

TEST(ttlens_python_empty_server, get_runtime_data) { call_python_empty_server("empty_get_runtime_data"); }

TEST(ttlens_python_empty_server, get_cluster_description) { call_python_empty_server("empty_get_cluster_description"); }

TEST(ttlens_python_empty_server, pci_read32) { call_python_empty_server("empty_pci_read32"); }

TEST(ttlens_python_empty_server, pci_write32) { call_python_empty_server("empty_pci_write32"); }

TEST(ttlens_python_empty_server, pci_read) { call_python_empty_server("empty_pci_read"); }

TEST(ttlens_python_empty_server, pci_read32_raw) { call_python_empty_server("empty_pci_read32_raw"); }

TEST(ttlens_python_empty_server, pci_write32_raw) { call_python_empty_server("empty_pci_write32_raw"); }

TEST(ttlens_python_empty_server, dma_buffer_read32) { call_python_empty_server("empty_dma_buffer_read32"); }

TEST(ttlens_python_empty_server, pci_read_tile) { call_python_empty_server("empty_pci_read_tile"); }

TEST(ttlens_python_empty_server, get_harvester_coordinate_translation) {
    call_python_empty_server("empty_get_harvester_coordinate_translation");
}

TEST(ttlens_python_empty_server, pci_write) { call_python_empty_server("empty_pci_write"); }

TEST(ttlens_python_empty_server, get_file) { call_python_empty_server("empty_get_file"); }

TEST(ttlens_python_empty_server, get_run_dirpath) { call_python_empty_server("empty_get_run_dirpath"); }

TEST(ttlens_python_server, pci_write32_pci_read32) { call_python_server("pci_write32_pci_read32"); }

TEST(ttlens_python_server, pci_write_pci_read) { call_python_server("pci_write_pci_read"); }

TEST(ttlens_python_server, pci_write32_raw_pci_read32_raw) { call_python_server("pci_write32_raw_pci_read32_raw"); }

TEST(ttlens_python_server, dma_buffer_read32) { call_python_server("dma_buffer_read32"); }

TEST(ttlens_python_server, pci_read_tile) { call_python_server("pci_read_tile"); }

TEST(ttlens_python_server, get_runtime_data) { call_python_server("get_runtime_data"); }

TEST(ttlens_python_server, get_cluster_description) { call_python_server("get_cluster_description"); }

TEST(ttlens_python_server, get_harvester_coordinate_translation) {
    call_python_server("get_harvester_coordinate_translation");
}

TEST(ttlens_python_server, jtag_write32_jtag_read32) { call_python_server("jtag_write32_jtag_read32"); }

TEST(ttlens_python_server, jtag_write32_axi_jtag_read32_axi) { call_python_server("jtag_write32_axi_jtag_read32_axi"); }

TEST(ttlens_python_server, get_device_ids) { call_python_server("get_device_ids"); }

TEST(ttlens_python_server, get_device_arch) { call_python_server("get_device_arch"); }

TEST(ttlens_python_server, get_device_soc_description) { call_python_server("get_device_soc_description"); }

TEST(ttlens_python_server, get_file) { call_python_server("get_file"); }

TEST(ttlens_python_server, get_run_dirpath) { call_python_server("get_run_dirpath"); }

TEST(ttlens_python_empty_server, jtag_read32) { call_python_empty_server("empty_jtag_read32"); }

TEST(ttlens_python_empty_server, jtag_write32) { call_python_empty_server("empty_jtag_write32"); }

TEST(ttlens_python_empty_server, jtag_read32_axi) { call_python_empty_server("empty_jtag_read32_axi"); }

TEST(ttlens_python_empty_server, jtag_write32_axi) { call_python_empty_server("empty_jtag_write32_axi"); }

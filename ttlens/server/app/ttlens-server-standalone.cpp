// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
// The main purpose of this file is to create a ttlens-server (see loader/ttlens_server.cpp) so that TTLens can connect
// to it.
#include <ctime>
#include <experimental/filesystem>
#include <fstream>
#include <iostream>

#include "ttlensserver/open_implementation.h"
#include "ttlensserver/server.h"
#include "utils/logger.hpp"

namespace fs = std::experimental::filesystem;

struct server_config {
   public:
    int port;
    bool run_in_background;
    std::string vcs_binary;
    std::vector<uint8_t> wanted_devices;
    bool init_jtag;
};

// Make sure that the file exists, and that it is a regular file
void ensure_file(const std::string& filetype, const std::string& filename) {
    if (!fs::exists(filename)) {
        log_error("{} file '{}' does not exist. Exiting.", filetype, filename);
        exit(1);
    }
    if (!fs::is_regular_file(filename)) {
        log_error("{} file '{}' is not a regular file. Exiting.", filetype, filename);
        exit(1);
    }
}

int run_ttlens_server(const server_config& config) {
    if (config.port > 1024 && config.port < 65536) {
        // Open wanted devices
        std::unique_ptr<tt::lens::open_implementation<tt::lens::umd_implementation>> implementation_umd;
        std::unique_ptr<tt::lens::open_implementation<tt::lens::jtag_implementation>> implementation_jtag;
        // Try to open only wanted devices
        try {
            if (config.vcs_binary.empty()) {
                if (config.init_jtag) {
                    implementation_jtag =
                        tt::lens::open_implementation<tt::lens::jtag_implementation>::open({}, config.wanted_devices);
                } else {
                    implementation_umd =
                        tt::lens::open_implementation<tt::lens::umd_implementation>::open({}, config.wanted_devices);
                }
            } else {
                ensure_file("VCS binary", config.vcs_binary);
                setenv("TT_REMOTE_EXE", config.vcs_binary.c_str(), 1);
                implementation_umd = tt::lens::open_implementation<tt::lens::umd_implementation>::open_simulation();
            }
        } catch (std::runtime_error& error) {
            log_custom(tt::Logger::Level::Error, tt::LogTTLens, "Cannot open device: {}.", error.what());
            return 1;
        }

        auto connection_address = std::string("tcp://*:") + std::to_string(config.port);
        log_info(tt::LogTTLens, "Debug server starting on {}...", connection_address);

        // Spawn server
        std::unique_ptr<tt::lens::server> server;
        try {
            if (config.init_jtag) {
                server = std::make_unique<tt::lens::server>(std::move(implementation_jtag));
            } else {
                server = std::make_unique<tt::lens::server>(std::move(implementation_umd));
            }
            server->start(config.port);
            log_info(tt::LogTTLens, "Debug server started on {}.", connection_address);
        } catch (...) {
            log_custom(tt::Logger::Level::Error, tt::LogTTLens,
                       "Debug server cannot start on {}. An instance of debug server might already be running.",
                       connection_address);
            return 1;
        }

        if (!config.run_in_background) {
            // Wait terminal input to stop the server
            log_info(tt::LogTTLens, "The debug server is running. Press ENTER to stop execution...");
            std::cin.get();
        } else {
            log_info(tt::LogTTLens, "The debug server is running in the background.");
            log_info(tt::LogTTLens, "To stop the server, use the command: touch exit.server");
            std::filesystem::remove("exit.server");
            while (!std::filesystem::exists("exit.server")) {
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        }

        // Stop server in destructor
        log_info(tt::LogTTLens, "Debug server ended on {}", connection_address);
        return 0;
    } else {
        log_error("port should be between 1024 and 65535 (inclusive)");
        return 1;
    }
}

// This variable is used in tt_cluster.cpp to cache cluster descriptor path. We set it here to bypass generating it when
// we have it.
extern std::string cluster_desc_path;

server_config parse_args(int argc, char** argv) {
    server_config config = server_config();
    config.port = atoi(argv[1]);
    config.init_jtag = false;

    int i = 2;
    while (i < argc) {
        if (strcmp(argv[i], "-d") == 0) {
            i++;
            if (i >= argc) {
                log_error("Expected space-delimited list of integer ids after -d");
                return {};
            } else {
                while (i < argc) {
                    try {
                        int device_id = std::atoi(argv[i]);
                        if (device_id < 0 || device_id > 255) throw std::invalid_argument("Invalid device id");
                        config.wanted_devices.push_back(device_id);
                    } catch (std::invalid_argument& e) {
                        log_error("Invalid device id: {}", argv[i]);
                        return {};
                    }
                    i++;
                }
            }
        } else if (strcmp(argv[i], "-s") == 0) {
            i += 1;
            if (i >= argc) {
                log_error("Expected path to VCS binary after -s");
                return {};
            }
            config.vcs_binary = argv[i];
            i += 1;
        } else if (strcmp(argv[i], "--background") == 0) {
            config.run_in_background = true;
            i++;
        } else if (strcmp(argv[i], "--jtag") == 0) {
            config.init_jtag = true;
            i++;
        } else {
            log_error("Unknown argument: {}", argv[i]);
            return {};
        }
    }

    return std::move(config);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        log_error(
            "Need arguments: <port> [-s <simulation_VCS_binary>] [-d <device_id1> [<device_id2> ... "
            "<device_idN>]] [--jtag] [--background]");
        return 1;
    }

    server_config config = parse_args(argc, argv);

    std::string log_starting = "Starting ttlens-server: " + std::string(argv[0]) + " " + std::string(argv[1]);
    for (int i = 2; i < argc; i++) {
        log_starting += " " + std::string(argv[i]);
    }
    log_info(tt::LogTTLens, log_starting.c_str());
    log_info(tt::LogTTLens, "Use environment variable TT_PCI_LOG_LEVEL to set the logging level (1 or 2)");

    if (argc == 2) {
        return run_ttlens_server(config);
    }

    return run_ttlens_server(config);
}

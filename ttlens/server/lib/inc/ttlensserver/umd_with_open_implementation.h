// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <filesystem>
#include <map>
#include <memory>

#include "jtag_device.h"
#include "umd_implementation.h"

namespace tt::lens {

class umd_with_open_implementation : public umd_implementation {
   private:
    std::unique_ptr<tt::umd::Cluster> device;
    std::unique_ptr<JtagDevice> jtag_device;
    std::vector<uint8_t> device_ids;
    std::map<uint8_t, std::string> device_soc_descriptors;

    std::string cluster_descriptor_path;
    std::string device_configuration_path;

   public:
    umd_with_open_implementation(std::unique_ptr<tt::umd::Cluster> device, std::unique_ptr<JtagDevice> jtag_device);

    static std::unique_ptr<umd_with_open_implementation> open(const std::filesystem::path& binary_directory = {},
                                                              const std::vector<uint8_t>& wanted_devices = {},
                                                              bool init_jtag = false);
    static std::unique_ptr<umd_with_open_implementation> open_jtag(const std::filesystem::path& binary_directory,
                                                                   const std::vector<uint8_t>& wanted_devices);

    std::optional<std::string> get_cluster_description() override;
    std::optional<std::vector<uint8_t>> get_device_ids() override;
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override;
};

}  // namespace tt::lens

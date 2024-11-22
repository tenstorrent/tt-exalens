// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <filesystem>
#include <map>
#include <memory>

#include "device/cluster.h"
#include "jtag_device.h"
#include "jtag_implementation.h"
#include "ttlens_implementation.h"
#include "umd_implementation.h"

namespace tt::lens {

template <typename BaseType>
struct DeviceTypeMap {
    using type = void;
};

template <>
struct DeviceTypeMap<umd_implementation> {
    using type = tt::umd::Cluster;
};

template <>
struct DeviceTypeMap<jtag_implementation> {
    using type = JtagDevice;
};

template <typename BaseClass>
class open_implementation : public BaseClass {
   public:
    using DeviceType = typename DeviceTypeMap<BaseClass>::type;

   private:
    std::unique_ptr<DeviceType> device;
    std::vector<uint8_t> device_ids;
    std::map<uint8_t, std::string> device_soc_descriptors;

    std::string cluster_descriptor_path;
    std::string device_configuration_path;

   public:
    static std::unique_ptr<open_implementation<BaseClass>> open(const std::filesystem::path& binary_directory = {},
                                                                const std::vector<uint8_t>& wanted_devices = {});
    open_implementation(std::unique_ptr<DeviceType> device);

    std::optional<std::string> get_cluster_description() override;
    std::optional<std::vector<uint8_t>> get_device_ids() override;
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override;
};

}  // namespace tt::lens

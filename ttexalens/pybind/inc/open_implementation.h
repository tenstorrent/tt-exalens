// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <filesystem>
#include <map>
#include <memory>
#include <optional>

#include "umd/device/tt_soc_descriptor.h"

namespace tt::exalens {

template <typename BaseClass>
class open_implementation : public BaseClass {
   public:
    typedef typename BaseClass::DeviceType DeviceType;

   private:
    std::unique_ptr<DeviceType> device;
    std::vector<uint8_t> device_ids;
    std::map<uint8_t, std::string> device_soc_descriptors_yamls;
    std::map<uint8_t, tt_SocDescriptor> soc_descriptors;

    std::string cluster_descriptor_path;

    open_implementation(std::unique_ptr<DeviceType> device);

   public:
    ~open_implementation();

    static std::unique_ptr<open_implementation<BaseClass>> open(const std::filesystem::path& binary_directory = {},
                                                                const std::vector<uint8_t>& wanted_devices = {},
                                                                bool initialize_with_noc1 = false);
    static std::unique_ptr<open_implementation<BaseClass>> open_simulation(
        const std::filesystem::path& simulation_directory);

    std::optional<std::string> get_cluster_description() override;
    std::optional<std::vector<uint8_t>> get_device_ids() override;
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override;
    std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                  const std::string& core_type,
                                                                  const std::string& coord_system) override;
};

}  // namespace tt::exalens

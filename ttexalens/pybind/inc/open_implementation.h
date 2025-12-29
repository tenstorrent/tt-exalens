// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <filesystem>
#include <map>
#include <memory>
#include <optional>

#include "umd/device/soc_descriptor.hpp"

namespace tt::exalens {

template <typename BaseClass>
class open_implementation : public BaseClass {
   public:
    typedef typename BaseClass::DeviceType DeviceType;

   private:
    std::unique_ptr<DeviceType> device;
    std::vector<uint8_t> device_ids;
    std::map<uint8_t, uint64_t> device_id_to_unique_id;
    std::map<uint8_t, std::string> device_soc_descriptors_yamls;
    std::map<uint8_t, umd::SocDescriptor> soc_descriptors;
    bool is_simulation = false;

    std::string cluster_descriptor_path;

    open_implementation(std::unique_ptr<DeviceType> device, bool is_simulation);

   public:
    ~open_implementation();

    static std::unique_ptr<open_implementation<BaseClass>> open(const std::filesystem::path& binary_directory = {},
                                                                const std::vector<uint8_t>& wanted_devices = {},
                                                                bool initialize_with_noc1 = false,
                                                                bool init_jtag = false);
    static std::unique_ptr<open_implementation<BaseClass>> open_simulation(
        const std::filesystem::path& simulation_directory);

    std::optional<std::string> get_cluster_description() override;
    std::optional<std::vector<uint8_t>> get_device_ids() override;
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override;
    std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                  const std::string& core_type,
                                                                  const std::string& coord_system) override;
    std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> get_firmware_version(uint8_t chip_id) override;
    std::optional<uint64_t> get_device_unique_id(uint8_t chip_id) override;
    virtual void warm_reset(bool is_galaxy_configuration = false) override;
    virtual std::optional<std::tuple<uint8_t, uint8_t>> get_remote_transfer_eth_core(uint8_t chip_id) override;
};

}  // namespace tt::exalens

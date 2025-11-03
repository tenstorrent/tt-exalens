// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "open_implementation.h"

#include <limits.h>
#include <unistd.h>

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#include "umd/device/cluster.hpp"
#include "umd/device/cluster_descriptor.hpp"
#include "umd/device/jtag/jtag.hpp"
#include "umd/device/jtag/jtag_device.hpp"
#include "umd/device/logging/config.hpp"
#include "umd/device/soc_descriptor.hpp"
#include "umd/device/tt_device/tt_device.hpp"
#include "umd/device/types/arch.hpp"
#include "umd/device/types/communication_protocol.hpp"
#include "umd/device/types/core_coordinates.hpp"
#include "umd_implementation.h"

static std::filesystem::path get_temp_working_directory() {
    std::filesystem::path temp_path = std::filesystem::temp_directory_path();
    std::string temp_name = temp_path / "ttexalens_server_XXXXXX";

    return mkdtemp(temp_name.data());
}

static std::optional<std::string> read_string_from_file(const std::string &file_name) {
    if (file_name.empty()) {
        return std::nullopt;
    }

    std::ifstream file(file_name, std::ios::in);
    if (!file) {
        return std::nullopt;
    }

    return std::string(std::istreambuf_iterator<char>(file), {});
}

static std::filesystem::path temp_working_directory = get_temp_working_directory();

// Identifies and returns the directory path of the currently running executable in a Linux environment.
static std::filesystem::path find_binary_directory() {
    char buffer[PATH_MAX + 1];
    ssize_t len = readlink("/proc/self/exe", buffer, sizeof(buffer) - 1);

    if (len != -1) {
        buffer[len] = '\0';
        std::string path(buffer);
        std::string::size_type pos = path.find_last_of("/");
        return path.substr(0, pos);
    }
    return {};
}

static std::string create_simulation_cluster_descriptor_file(tt::ARCH arch) {
    std::string cluster_descriptor_path = temp_working_directory / "cluster_desc.yaml";
    std::ofstream cluster_descriptor(cluster_descriptor_path);

    if (!cluster_descriptor.is_open()) {
        throw std::runtime_error("Failed to open file for writing: " + cluster_descriptor_path);
    }

    std::string arch_str = tt::arch_to_str(arch);

    cluster_descriptor << "arch: {" << std::endl;
    cluster_descriptor << "   0: " << arch_str << "," << std::endl;
    cluster_descriptor << "}" << std::endl << std::endl;
    cluster_descriptor << "chips: {" << std::endl;
    cluster_descriptor << "   0: [0,0,0,0]," << std::endl;
    cluster_descriptor << "}" << std::endl << std::endl;
    cluster_descriptor << "ethernet_connections: [" << std::endl;
    cluster_descriptor << "]" << std::endl << std::endl;
    cluster_descriptor << "chips_with_mmio: [" << std::endl;
    cluster_descriptor << "   0: 0," << std::endl;
    cluster_descriptor << "]" << std::endl << std::endl;
    cluster_descriptor << "# harvest_mask is the bit indicating which tensix row is harvested. So bit 0 = first "
                          "tensix row; bit 1 = second tensix row etc..."
                       << std::endl;
    cluster_descriptor << "harvesting: {" << std::endl;
    cluster_descriptor << "   0: {noc_translation: false, harvest_mask: 0}," << std::endl;
    cluster_descriptor << "}" << std::endl << std::endl;
    cluster_descriptor << "# This value will be null if the boardtype is unknown, should never happen in practice "
                          "but to be defensive it would be useful to throw an error on this case."
                       << std::endl;
    cluster_descriptor << "boardtype: {" << std::endl;
    cluster_descriptor << "   0: " << arch_str << "Simulator," << std::endl;
    cluster_descriptor << "}" << std::endl;
    cluster_descriptor << "io_device_type: SIMULATION" << std::endl;

    return cluster_descriptor_path;
}

static std::map<uint8_t, std::string> create_device_soc_descriptors(tt::umd::Cluster *cluster,
                                                                    const std::vector<uint8_t> &device_ids) {
    std::map<uint8_t, std::string> device_soc_descriptors_yamls;

    for (auto device_id : device_ids) {
        auto &soc_descriptor = cluster->get_soc_descriptor(device_id);
        std::string file_name = temp_working_directory / ("device_desc_runtime_" + std::to_string(device_id) + ".yaml");
        soc_descriptor.serialize_to_file(file_name);

        device_soc_descriptors_yamls[device_id] = file_name;
    }
    return device_soc_descriptors_yamls;
}

static std::string jtag_create_temp_network_descriptor_file(JtagDevice *jtag_device) {
    // In python we only need chips_with_mmio, harvesting and chips_with_jtag, other fields are not needed
    // We are doing this beacause we are reusing this file in python which was originaly created for UMD initialization
    std::string cluster_descriptor_path = temp_working_directory / "cluster_desc.yaml";
    std::ofstream outfile(cluster_descriptor_path);
    outfile << "chips_with_mmio: [\n]\n\n";

    outfile << "harvesting: {\n";
    for (size_t chip_id = 0; chip_id < jtag_device->get_device_cnt(); chip_id++) {
        uint32_t actual_harvesting = *jtag_device->get_efuse_harvesting(chip_id);

        outfile << "   " << chip_id << ": {noc_translation: true, harvest_mask: " << actual_harvesting << "},\n";
    }
    outfile << "}\n\n";

    outfile << "chips_with_jtag: [\n";
    for (size_t chip_id = 0; chip_id < jtag_device->get_device_cnt(); chip_id++) {
        outfile << "   " << chip_id << ": " << chip_id << ",\n";
    }
    outfile << "]";

    return cluster_descriptor_path;
}

static std::string jtag_create_device_soc_descriptor(const tt::umd::SocDescriptor &soc_descriptor, uint32_t device_id) {
    std::string file_name = temp_working_directory / ("device_desc_runtime_" + std::to_string(device_id) + ".yaml");
    soc_descriptor.serialize_to_file(file_name);
    return file_name;
}

namespace tt::exalens {

template <typename BaseClass>
open_implementation<BaseClass>::open_implementation(std::unique_ptr<DeviceType> device)
    : BaseClass(device.get()), device(std::move(device)) {}

template <typename BaseClass>
open_implementation<BaseClass>::~open_implementation() {
    if (is_simulation) {
        device->close_device();
    }
}

template <>
std::unique_ptr<open_implementation<umd_implementation>> open_implementation<umd_implementation>::open(
    const std::filesystem::path &binary_directory, const std::vector<uint8_t> &wanted_devices,
    bool initialize_with_noc1, bool init_jtag) {
    // Respect UMD's existing env var first; default to ERROR otherwise.
    // If Python wants DEBUG, it can set TT_LOGGER_LEVEL=debug before calling into this function.
    const char *tt_logger_level = std::getenv("TT_LOGGER_LEVEL");
    if (tt_logger_level == nullptr) {
        tt::umd::logging::set_level(tt::umd::logging::level::error);
    }

    // TODO: Hack on UMD on how to use/initialize with noc1. This should be removed once we have a proper way to use
    // noc1
    tt::umd::TTDevice::use_noc1(initialize_with_noc1);
    tt::umd::IODeviceType device_type = init_jtag ? tt::umd::IODeviceType::JTAG : tt::umd::IODeviceType::PCIe;

    auto cluster_descriptor = tt::umd::Cluster::create_cluster_descriptor("", {}, device_type);

    if (cluster_descriptor->get_number_of_chips() == 0) {
        throw std::runtime_error("No Tenstorrent devices were detected on this system.");
    }

    // Check that all chips are of the same type
    tt::ARCH arch = cluster_descriptor->get_arch(0);

    for (auto chip_id : cluster_descriptor->get_all_chips()) {
        auto newArch = cluster_descriptor->get_arch(chip_id);

        if (arch != newArch) {
            throw std::runtime_error("Not all devices have the same architecture.");
        }
    }

    // Create device
    std::vector<uint8_t> device_ids;
    std::unique_ptr<tt::umd::Cluster> cluster;

    // Try to read cluster descriptor
    std::unordered_set<ChipId> target_devices;

    for (ChipId i : cluster_descriptor->get_all_chips()) {
        device_ids.push_back(i);
    }

    // If we specified which devices we want, check that they are available and then extract their ids
    for (auto wanted_device : wanted_devices)
        if (std::find(device_ids.begin(), device_ids.end(), wanted_device) == device_ids.end())
            throw std::runtime_error("Device " + std::to_string(wanted_device) + " is not available.");
    if (!wanted_devices.empty()) device_ids = wanted_devices;

    for (auto device_id : device_ids) target_devices.insert(device_id);

    switch (arch) {
        case tt::ARCH::WORMHOLE_B0:
        case tt::ARCH::BLACKHOLE:
            cluster = std::make_unique<tt::umd::Cluster>(
                tt::umd::ClusterOptions{.target_devices = target_devices, .io_device_type = device_type});
            break;
        default:
            throw std::runtime_error("Unsupported architecture " + tt::arch_to_str(arch) + ".");
    }

    auto device_soc_descriptors_yamls = create_device_soc_descriptors(cluster.get(), device_ids);
    std::map<uint8_t, umd::SocDescriptor> soc_descriptors;
    for (auto device_id : device_ids) {
        soc_descriptors[device_id] = cluster->get_soc_descriptor(device_id);
    }

    auto implementation = std::unique_ptr<open_implementation<umd_implementation>>(
        new open_implementation<umd_implementation>(std::move(cluster)));
    auto &unique_ids = cluster_descriptor->get_chip_unique_ids();

    for (auto device_id : device_ids) {
        auto it = unique_ids.find(device_id);

        if (it != unique_ids.end()) {
            implementation->device_id_to_unique_id[device_id] = it->second;
        }
    }

    std::string file_path = temp_working_directory / "cluster_desc.yaml";
    cluster_descriptor->serialize_to_file(file_path);
    implementation->cluster_descriptor_path = file_path;
    implementation->device_ids = device_ids;
    implementation->device_soc_descriptors_yamls = std::move(device_soc_descriptors_yamls);
    implementation->soc_descriptors = std::move(soc_descriptors);
    return std::move(implementation);
}

template <>
std::unique_ptr<open_implementation<umd_implementation>> open_implementation<umd_implementation>::open_simulation(
    const std::filesystem::path &simulation_directory) {
    tt::umd::logging::set_level(tt::umd::logging::level::debug);
    std::unique_ptr<tt::umd::Cluster> cluster =
        std::make_unique<tt::umd::Cluster>(tt::umd::ClusterOptions{.chip_type = tt::umd::ChipType::SIMULATION,
                                                                   .target_devices = {0},
                                                                   .simulator_directory = simulation_directory});

    // Initialize simulation device
    cluster->start_device({});

    // Default behavior is to start brisc on all functional workers.
    // Since it is easier to put brisc in endless loop then to put it in reset, we will do that.
    // Write 0x6f (JAL x0, 0) to address 0 in L1 of all tensix cores.
    auto &soc_descriptor = cluster->get_soc_descriptor(0);

    for (const auto &worker : soc_descriptor.get_cores(CoreType::TENSIX)) {
        uint32_t data = 0x6f;  // while (true);

        cluster->write_to_device(&data, sizeof(data), 0, worker, 0);
    }

    cluster->deassert_risc_reset();

    std::vector<uint8_t> device_ids{0};
    auto device_soc_descriptors_yamls = create_device_soc_descriptors(cluster.get(), device_ids);
    std::map<uint8_t, umd::SocDescriptor> soc_descriptors;
    for (auto device_id : device_ids) {
        soc_descriptors[device_id] = cluster->get_soc_descriptor(device_id);
    }

    auto implementation = std::unique_ptr<open_implementation<umd_implementation>>(
        new open_implementation<umd_implementation>(std::move(cluster)));

    implementation->is_simulation = true;
    implementation->cluster_descriptor_path = create_simulation_cluster_descriptor_file(soc_descriptor.arch);
    implementation->device_ids = device_ids;
    implementation->device_soc_descriptors_yamls = std::move(device_soc_descriptors_yamls);
    implementation->soc_descriptors = std::move(soc_descriptors);
    return std::move(implementation);
}

template <typename BaseClass>
std::optional<std::string> open_implementation<BaseClass>::get_cluster_description() {
    return cluster_descriptor_path;
}

template <typename BaseClass>
std::optional<std::vector<uint8_t>> open_implementation<BaseClass>::get_device_ids() {
    return device_ids;
}

template <typename BaseClass>
std::optional<std::string> open_implementation<BaseClass>::get_device_soc_description(uint8_t chip_id) {
    try {
        return device_soc_descriptors_yamls[chip_id];
    } catch (...) {
        return {};
    }
}

template <typename BaseClass>
std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> open_implementation<BaseClass>::get_firmware_version(
    uint8_t chip_id) {
    if (!is_simulation) {
        return BaseClass::get_firmware_version(chip_id);
    }
    return std::make_tuple(0, 0, 0);
}

template <typename BaseClass>
std::optional<uint64_t> open_implementation<BaseClass>::get_device_unique_id(uint8_t chip_id) {
    auto it = device_id_to_unique_id.find(chip_id);

    if (it != device_id_to_unique_id.end()) {
        return it->second;
    }
    return {};
}

template <typename BaseClass>
std::optional<std::tuple<uint8_t, uint8_t>> open_implementation<BaseClass>::convert_from_noc0(
    uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, const std::string &core_type, const std::string &coord_system) {
    CoreType core_type_enum;

    if (core_type == "arc") {
        core_type_enum = CoreType::ARC;
    } else if (core_type == "dram") {
        core_type_enum = CoreType::DRAM;
    } else if (core_type == "active_eth") {
        core_type_enum = CoreType::ACTIVE_ETH;
    } else if (core_type == "idle_eth") {
        core_type_enum = CoreType::IDLE_ETH;
    } else if (core_type == "pcie") {
        core_type_enum = CoreType::PCIE;
    } else if (core_type == "tensix") {
        core_type_enum = CoreType::TENSIX;
    } else if (core_type == "router_only") {
        core_type_enum = CoreType::ROUTER_ONLY;
    } else if (core_type == "harvested") {
        core_type_enum = CoreType::HARVESTED;
    } else if (core_type == "eth") {
        core_type_enum = CoreType::ETH;
    } else if (core_type == "worker") {
        core_type_enum = CoreType::WORKER;
    } else if (core_type == "security") {
        core_type_enum = CoreType::SECURITY;
    } else if (core_type == "l2cpu") {
        core_type_enum = CoreType::L2CPU;
    } else {
        return {};
    }

    CoordSystem coord_system_enum;

    if (coord_system == "logical") {
        coord_system_enum = CoordSystem::LOGICAL;
    } else if (coord_system == "translated") {
        coord_system_enum = CoordSystem::TRANSLATED;
    } else if (coord_system == "noc0") {
        coord_system_enum = CoordSystem::NOC0;
    } else if (coord_system == "noc1") {
        coord_system_enum = CoordSystem::NOC1;
    } else {
        return {};
    }

    try {
        auto &soc_descriptor = soc_descriptors.at(chip_id);
        tt::umd::CoreCoord core_coord{noc_x, noc_y, core_type_enum, CoordSystem::NOC0};
        auto output = soc_descriptor.translate_coord_to(core_coord, coord_system_enum);

        return std::make_tuple(static_cast<uint8_t>(output.x), static_cast<uint8_t>(output.y));
    } catch (...) {
        return {};
    }
}

}  // namespace tt::exalens

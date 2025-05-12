// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttexalensserver/open_implementation.h"

#include <limits.h>
#include <unistd.h>

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#include "ttexalensserver/jtag.h"
#include "ttexalensserver/jtag_device.h"
#include "ttexalensserver/jtag_implementation.h"
#include "ttexalensserver/umd_implementation.h"
#include "umd/device/cluster.h"
#include "umd/device/tt_cluster_descriptor.h"
#include "umd/device/tt_core_coordinates.h"
#include "umd/device/tt_simulation_device.h"
#include "umd/device/tt_soc_descriptor.h"
#include "umd/device/tt_xy_pair.h"
#include "umd/device/types/arch.h"

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

static std::string write_temp_file(const std::string &file_name, const char *bytes, size_t length) {
    std::string temp_file_name = temp_working_directory / file_name;
    std::ofstream conf_file(temp_file_name, std::ios::out | std::ios::binary);

    if (!conf_file.is_open()) {
        throw std::runtime_error("Couldn't write configuration to temp file " + temp_file_name + ".");
    }
    conf_file.write(bytes, length);
    conf_file.close();
    return temp_file_name;
}

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

    return cluster_descriptor_path;
}

static std::unique_ptr<tt::umd::Cluster> create_wormhole_device(const std::set<chip_id_t> &target_devices) {
    uint32_t num_host_mem_ch_per_mmio_device = 4;

    auto device = std::make_unique<tt::umd::Cluster>(target_devices, num_host_mem_ch_per_mmio_device);
    for (auto chip_id : device->get_target_mmio_device_ids()) {
        device->configure_active_ethernet_cores_for_mmio_device(chip_id, {});
    }

    return device;
}

static std::unique_ptr<tt::umd::Cluster> create_blackhole_device(const std::set<chip_id_t> &target_devices) {
    uint32_t num_host_mem_ch_per_mmio_device = 4;

    auto device = std::make_unique<tt::umd::Cluster>(target_devices, num_host_mem_ch_per_mmio_device);

    return device;
}

static void write_coord(std::ostream &out, const tt::umd::CoreCoord &input, CoreType core_type,
                        const tt_SocDescriptor &soc_descriptor) {
    auto output = soc_descriptor.translate_coord_to(input, CoordSystem::NOC0);
    out << output.x << "-" << output.y << ", ";
}

static void write_coord(std::ostream &out, const tt_xy_pair &xy, CoreType core_type,
                        const tt_SocDescriptor &soc_descriptor) {
    write_coord(out, tt::umd::CoreCoord{xy.x, xy.y, core_type, CoordSystem::NOC0}, core_type, soc_descriptor);
}

// Creates SOC descriptor files by serializing tt_SocDescroptor structure to yaml.
// TODO: Current copied from runtime/runtime_utils.cpp: print_device_description. It should be moved to UMD and reused
// on both places.
static void write_soc_descriptor(std::string file_name, const tt_SocDescriptor &soc_descriptor) {
    std::ofstream outfile(file_name);

    outfile << "grid:" << std::endl;
    outfile << "  x_size: " << soc_descriptor.grid_size.x << std::endl;
    outfile << "  y_size: " << soc_descriptor.grid_size.y << std::endl << std::endl;

    outfile << "arc:" << std::endl;
    outfile << "  [" << std::endl;

    for (const auto &arc : soc_descriptor.get_cores(CoreType::ARC)) {
        if (arc.x < soc_descriptor.grid_size.x && arc.y < soc_descriptor.grid_size.y) {
            write_coord(outfile, arc, CoreType::ARC, soc_descriptor);
        }
    }
    outfile << std::endl;
    outfile << "  ]" << std::endl << std::endl;

    outfile << "pcie:" << std::endl;
    outfile << "  [" << std::endl;

    for (const auto &pcie : soc_descriptor.get_cores(CoreType::PCIE)) {
        if (pcie.x < soc_descriptor.grid_size.x && pcie.y < soc_descriptor.grid_size.y) {
            write_coord(outfile, pcie, CoreType::PCIE, soc_descriptor);
        }
    }
    outfile << std::endl;
    outfile << "  ]" << std::endl << std::endl;

    // List of available dram cores in full grid
    outfile << "dram:" << std::endl;
    outfile << "  [" << std::endl;

    for (const auto &dram_cores : soc_descriptor.get_dram_cores()) {
        // Insert the dram core if it's within the given grid
        bool has_data = false;

        for (const auto &dram_core : dram_cores) {
            if ((dram_core.x < soc_descriptor.grid_size.x) and (dram_core.y < soc_descriptor.grid_size.y)) {
                has_data = true;
            }
        }
        if (has_data) {
            outfile << "[";

            for (const auto &dram_core : dram_cores) {
                if ((dram_core.x < soc_descriptor.grid_size.x) and (dram_core.y < soc_descriptor.grid_size.y)) {
                    write_coord(outfile, dram_core, CoreType::DRAM, soc_descriptor);
                }
            }

            outfile << "]," << std::endl;
        }
    }
    outfile << std::endl << "]" << std::endl << std::endl;

    outfile << "eth:" << std::endl << "  [" << std::endl;
    for (const auto &ethernet_core : soc_descriptor.get_cores(CoreType::ETH)) {
        // Insert the eth core if it's within the given grid
        if (ethernet_core.x < soc_descriptor.grid_size.x && ethernet_core.y < soc_descriptor.grid_size.y) {
            write_coord(outfile, ethernet_core, CoreType::ETH, soc_descriptor);
        }
    }
    outfile << std::endl << "]" << std::endl << std::endl;
    // Insert worker cores that are within the given grid
    outfile << "harvested_workers:" << std::endl;
    outfile << "  [" << std::endl;

    for (const auto &worker : soc_descriptor.get_harvested_cores(CoreType::TENSIX)) {
        if (worker.x < soc_descriptor.grid_size.x && worker.y < soc_descriptor.grid_size.y) {
            write_coord(outfile, worker, CoreType::TENSIX, soc_descriptor);
        }
    }
    outfile << std::endl;
    outfile << "  ]" << std::endl << std::endl;

    outfile << "functional_workers:" << std::endl;
    outfile << "  [" << std::endl;
    for (const auto &worker : soc_descriptor.get_cores(CoreType::TENSIX)) {
        if (worker.x < soc_descriptor.grid_size.x && worker.y < soc_descriptor.grid_size.y) {
            write_coord(outfile, worker, CoreType::TENSIX, soc_descriptor);
        }
    }
    outfile << std::endl;
    outfile << "  ]" << std::endl << std::endl;

    outfile << "router_only:" << std::endl << "  []" << std::endl << std::endl;

    // Fill in the rest that are static to our device
    outfile << "worker_l1_size:" << std::endl;
    outfile << "  " << soc_descriptor.worker_l1_size << std::endl << std::endl;
    outfile << "dram_bank_size:" << std::endl;
    outfile << "  " << soc_descriptor.dram_bank_size << std::endl << std::endl;
    outfile << "eth_l1_size:" << std::endl;
    outfile << "  " << soc_descriptor.eth_l1_size << std::endl << std::endl;
    outfile << "arch_name: " << tt::arch_to_str(soc_descriptor.arch) << std::endl << std::endl;
    outfile << "features:" << std::endl;
    outfile << "  noc:" << std::endl;
    outfile << "    translation_id_enabled: True" << std::endl;
    outfile << "  unpacker:" << std::endl;
    outfile << "    version: " << soc_descriptor.unpacker_version << std::endl;
    outfile << "    inline_srca_trans_without_srca_trans_instr: False" << std::endl;
    outfile << "  math:" << std::endl;
    outfile << "    dst_size_alignment: " << soc_descriptor.dst_size_alignment << std::endl;
    outfile << "  packer:" << std::endl;
    outfile << "    version: " << soc_descriptor.packer_version << std::endl;
    outfile << "  overlay:" << std::endl;
    outfile << "    version: " << soc_descriptor.overlay_version << std::endl;
    outfile << std::endl;
}

static std::map<uint8_t, std::string> create_device_soc_descriptors(tt_device *device,
                                                                    const std::vector<uint8_t> &device_ids) {
    std::map<uint8_t, std::string> device_soc_descriptors_yamls;

    for (auto device_id : device_ids) {
        auto &soc_descriptor = device->get_soc_descriptor(device_id);
        std::string file_name = temp_working_directory / ("device_desc_runtime_" + std::to_string(device_id) + ".yaml");
        write_soc_descriptor(file_name, soc_descriptor);

        device_soc_descriptors_yamls[device_id] = file_name;
    }
    return device_soc_descriptors_yamls;
}

std::unique_ptr<JtagDevice> init_jtag(std::filesystem::path binary_directory) {
    if (binary_directory.empty()) {
        binary_directory = find_binary_directory();
    }

    std::unique_ptr<JtagDevice> jtag_implementation;
    std::unique_ptr<Jtag> jtag;
    jtag = std::make_unique<Jtag>((binary_directory / std::string("../lib/libttexalens_jtag.so")).c_str());
    jtag_implementation = std::make_unique<JtagDevice>(std::move(jtag));

    return jtag_implementation;
}

static std::string jtag_create_temp_network_descriptor_file(JtagDevice *jtag_device) {
    // In python we only need chips_with_mmio, harvesting and chips_with_jtag, other fields are not needed
    // We are doing this beacause we are reusing this file in python which was originaly created for UMD initailization
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

static std::string jtag_create_device_soc_descriptor(const tt_SocDescriptor &soc_descriptor, uint32_t device_id) {
    std::string file_name = temp_working_directory / ("device_desc_runtime_" + std::to_string(device_id) + ".yaml");
    write_soc_descriptor(file_name, soc_descriptor);
    return file_name;
}

namespace tt::exalens {

template <typename BaseClass>
open_implementation<BaseClass>::open_implementation(std::unique_ptr<DeviceType> device)
    : BaseClass(device.get()), device(std::move(device)) {}

template <>
std::unique_ptr<open_implementation<jtag_implementation>> open_implementation<jtag_implementation>::open(
    const std::filesystem::path &binary_directory, const std::vector<uint8_t> &wanted_devices,
    bool initialize_with_noc1) {
    // TODO: initialize with noc1 in JTAG

    std::vector<uint8_t> device_ids;
    std::unique_ptr<tt::umd::Cluster> device;
    std::unique_ptr<JtagDevice> jtag_device;

    jtag_device = std::move(init_jtag(binary_directory));

    // Check that all chips are of the same type
    tt::ARCH arch = *jtag_device->get_jtag_arch(0);
    for (size_t i = 1; i < jtag_device->get_device_cnt(); i++) {
        auto newArch = *jtag_device->get_jtag_arch(i);

        if (arch != newArch) {
            throw std::runtime_error("Not all devices have the same architecture.");
        }
    }
    auto cluster_descriptor_path = jtag_create_temp_network_descriptor_file(jtag_device.get());

    std::map<uint8_t, std::string> device_soc_descriptors_yamls;
    std::map<uint8_t, tt_SocDescriptor> soc_descriptors;

    for (size_t device_id = 0; device_id < jtag_device->get_device_cnt(); device_id++) {
        tt::ARCH arch = *jtag_device->get_jtag_arch(device_id);
        uint32_t harvesting = *jtag_device->get_efuse_harvesting(device_id);
        soc_descriptors[device_id] = tt_SocDescriptor(arch, harvesting);
        device_soc_descriptors_yamls[device_id] =
            jtag_create_device_soc_descriptor(soc_descriptors[device_id], device_id);
        device_ids.push_back(device_id);
    }

    auto implementation = std::unique_ptr<open_implementation<jtag_implementation>>(
        new open_implementation<jtag_implementation>(std::move(jtag_device)));

    implementation->cluster_descriptor_path = cluster_descriptor_path;
    implementation->device_ids = device_ids;
    implementation->soc_descriptors = std::move(soc_descriptors);
    implementation->device_soc_descriptors_yamls = std::move(device_soc_descriptors_yamls);
    return std::move(implementation);
}

#include "umd/device/tt_device/tt_device.h"

template <>
std::unique_ptr<open_implementation<umd_implementation>> open_implementation<umd_implementation>::open(
    const std::filesystem::path &binary_directory, const std::vector<uint8_t> &wanted_devices,
    bool initialize_with_noc1) {
    // TODO: Hack on UMD on how to use/initialize with noc1. This should be removed once we have a proper way to use
    // noc1
    umd::TTDevice::use_noc1(initialize_with_noc1);

    auto cluster_descriptor = tt::umd::Cluster::create_cluster_descriptor();

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
    std::unique_ptr<tt::umd::Cluster> device;

    // Try to read cluster descriptor
    std::set<chip_id_t> target_devices;

    for (chip_id_t i : cluster_descriptor->get_all_chips()) {
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
            device = create_wormhole_device(target_devices);
            break;
        case tt::ARCH::BLACKHOLE:
            device = create_blackhole_device(target_devices);
            break;
        default:
            throw std::runtime_error("Unsupported architecture " + tt::arch_to_str(arch) + ".");
    }

    auto device_soc_descriptors_yamls = create_device_soc_descriptors(device.get(), device_ids);
    std::map<uint8_t, tt_SocDescriptor> soc_descriptors;
    for (auto device_id : device_ids) {
        soc_descriptors[device_id] = device->get_soc_descriptor(device_id);
    }

    auto implementation = std::unique_ptr<open_implementation<umd_implementation>>(
        new open_implementation<umd_implementation>(std::move(device)));

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
    std::unique_ptr<tt_SimulationDevice> device = std::make_unique<tt_SimulationDevice>(simulation_directory);

    // Initialize simulation device
    device->start_device({});

    // Default behavior is to start brisc on all functional workers.
    // Since it is easier to put brisc in endless loop then to put it in reset, we will do that.
    // Write 0x6f (JAL x0, 0) to address 0 in L1 of all tensix cores.
    auto &soc_descriptor = device->get_soc_descriptor(0);

    for (const auto &worker : soc_descriptor.get_cores(CoreType::TENSIX)) {
        uint32_t data = 0x6f;  // while (true);

        device->write_to_device(&data, sizeof(data), 0, worker, 0);
    }

    device->deassert_risc_reset();

    std::vector<uint8_t> device_ids{0};
    auto device_soc_descriptors_yamls = create_device_soc_descriptors(device.get(), device_ids);
    std::map<uint8_t, tt_SocDescriptor> soc_descriptors;
    for (auto device_id : device_ids) {
        soc_descriptors[device_id] = device->get_soc_descriptor(device_id);
    }

    auto implementation = std::unique_ptr<open_implementation<umd_implementation>>(
        new open_implementation<umd_implementation>(std::move(device)));

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
    } else {
        return {};
    }

    CoordSystem coord_system_enum;

    if (coord_system == "logical") {
        coord_system_enum = CoordSystem::LOGICAL;
    } else if (coord_system == "physical") {
        coord_system_enum = CoordSystem::PHYSICAL;
    } else if (coord_system == "virtual") {
        coord_system_enum = CoordSystem::VIRTUAL;
    } else if (coord_system == "translated") {
        coord_system_enum = CoordSystem::TRANSLATED;
    } else {
        return {};
    }

    try {
        auto &soc_descriptor = soc_descriptors.at(chip_id);
        tt::umd::CoreCoord core_coord{noc_x, noc_y, core_type_enum, CoordSystem::PHYSICAL};
        auto output = soc_descriptor.translate_coord_to(core_coord, coord_system_enum);

        return std::make_tuple(static_cast<uint8_t>(output.x), static_cast<uint8_t>(output.y));
    } catch (...) {
        return {};
    }
}

}  // namespace tt::exalens

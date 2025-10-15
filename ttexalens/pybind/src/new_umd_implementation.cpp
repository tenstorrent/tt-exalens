// SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "new_umd_implementation.h"

#include <umd/device/logging/config.h>

#include <stdexcept>
#include <umd/device/firmware/firmware_utils.hpp>
#include <umd/device/topology/topology_discovery.hpp>
#include <umd/device/types/core_coordinates.hpp>
#include <umd/device/types/xy_pair.hpp>

static std::filesystem::path get_temp_working_directory() {
    std::filesystem::path temp_path = std::filesystem::temp_directory_path();
    std::string temp_name = temp_path / "ttexalens_server_XXXXXX";

    return mkdtemp(temp_name.data());
}

static std::filesystem::path temp_working_directory = get_temp_working_directory();

void read_from_device_reg_unaligned(tt::umd::TTDevice* device, void* mem_ptr, uint8_t noc_id, tt::xy_pair noc_coords,
                                    uint64_t address, uint32_t size) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    tt::umd::TTDevice::use_noc1(noc_id == 1);

    // Read first unaligned word
    uint32_t first_unaligned_index = address % 4;
    if (first_unaligned_index != 0) {
        uint32_t temp = 0;
        device->read_from_device(&temp, noc_coords, address - first_unaligned_index, sizeof(temp));
        if (first_unaligned_index + size <= sizeof(temp)) {
            memcpy(mem_ptr, ((uint8_t*)&temp) + first_unaligned_index, size);
            return;
        }
        memcpy(mem_ptr, ((uint8_t*)&temp) + first_unaligned_index, 4 - first_unaligned_index);
        mem_ptr = (uint8_t*)mem_ptr + 4 - first_unaligned_index;
        address += 4 - first_unaligned_index;
        size -= 4 - first_unaligned_index;
    }

    // Read aligned bytes
    uint32_t aligned_size = size - (size % 4);
    if (aligned_size > 0) {
        device->read_from_device(mem_ptr, noc_coords, address, aligned_size);
        mem_ptr = (uint8_t*)mem_ptr + aligned_size;
        address += aligned_size;
        size -= aligned_size;
    }

    // Read last unaligned word
    uint32_t last_unaligned_size = size;
    if (last_unaligned_size != 0) {
        uint32_t temp = 0;
        device->read_from_device(&temp, noc_coords, address, sizeof(temp));
        memcpy(mem_ptr, &temp, last_unaligned_size);
    }
}

void write_to_device_reg_unaligned(tt::umd::TTDevice* device, const void* mem_ptr, uint32_t size_in_bytes,
                                   uint8_t noc_id, tt::xy_pair noc_coords, uint64_t address) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    tt::umd::TTDevice::use_noc1(noc_id == 1);

    // Read/Write first unaligned word
    uint32_t first_unaligned_index = address % 4;
    if (first_unaligned_index != 0) {
        uint32_t temp = 0;
        uint64_t aligned_address = address - first_unaligned_index;
        device->read_from_device(&temp, noc_coords, aligned_address, sizeof(temp));
        if (first_unaligned_index + size_in_bytes <= sizeof(temp)) {
            memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, size_in_bytes);
            device->write_to_device(&temp, noc_coords, aligned_address, sizeof(temp));
            return;
        }
        memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, 4 - first_unaligned_index);
        device->write_to_device(&temp, noc_coords, aligned_address, sizeof(temp));
        mem_ptr = (uint8_t*)mem_ptr + 4 - first_unaligned_index;
        address += 4 - first_unaligned_index;
        size_in_bytes -= 4 - first_unaligned_index;
    }

    // Write aligned bytes
    uint32_t aligned_size = size_in_bytes - (size_in_bytes % 4);
    if (aligned_size > 0) {
        device->write_to_device(mem_ptr, noc_coords, address, aligned_size);
        mem_ptr = (uint8_t*)mem_ptr + aligned_size;
        address += aligned_size;
        size_in_bytes -= aligned_size;
    }

    // Read/Write last unaligned word
    uint32_t last_unaligned_size = size_in_bytes;
    if (last_unaligned_size != 0) {
        uint32_t temp = 0;
        device->read_from_device(&temp, noc_coords, address, sizeof(temp));
        memcpy(&temp, mem_ptr, last_unaligned_size);
        device->write_to_device(&temp, noc_coords, address, sizeof(temp));
    }
}

namespace tt::exalens {

new_umd_implementation::new_umd_implementation(const std::string& binary_directory,
                                               const std::vector<uint8_t>& wanted_devices, bool initialize_with_noc1) {
    // Disable UMD logging
    tt::umd::logging::set_level(tt::umd::logging::level::error);

    // TODO: Hack on UMD on how to use/initialize with noc1. This should be removed once we have a proper way to use
    // noc1
    tt::umd::TTDevice::use_noc1(initialize_with_noc1);

    cluster_descriptor = umd::TopologyDiscovery::create_cluster_descriptor({}, "", umd::IODeviceType::PCIe);

    if (cluster_descriptor->get_number_of_chips() == 0) {
        throw std::runtime_error("No Tenstorrent devices were detected on this system.");
    }

    cluster_descriptor_path = temp_working_directory / "cluster_desc.yaml";
    cluster_descriptor->serialize_to_file(cluster_descriptor_path);

    auto& unique_ids = cluster_descriptor->get_chip_unique_ids();
    for (auto device_id : device_ids) {
        auto it = unique_ids.find(device_id);

        if (it != unique_ids.end()) {
            device_id_to_unique_id[device_id] = it->second;
        }
    }

    // Setup used devices
    std::unordered_set<chip_id_t> target_devices;

    for (chip_id_t i : cluster_descriptor->get_all_chips()) {
        device_ids.push_back(i);
    }

    // If we specified which devices we want, check that they are available and then extract their ids
    for (auto wanted_device : wanted_devices)
        if (std::find(device_ids.begin(), device_ids.end(), wanted_device) == device_ids.end())
            throw std::runtime_error("Device " + std::to_string(wanted_device) + " is not available.");
    if (!wanted_devices.empty()) device_ids = wanted_devices;

    for (auto device_id : device_ids) target_devices.insert(device_id);

    // Construct all the required devices from the cluster descriptor.
    for (auto& chip_id : cluster_descriptor->get_chips_local_first(cluster_descriptor->get_all_chips())) {
        if (cluster_descriptor->is_chip_mmio_capable(chip_id)) {
            auto physical_device_id = cluster_descriptor->get_chips_with_mmio().at(chip_id);
            auto tt_device = umd::TTDevice::create(physical_device_id, umd::IODeviceType::PCIe);
            uint32_t num_host_mem_channels = 1;
            tt_device->init_tt_device();  // TODO: We might want to remove init_tt_device from here since it will wait
                                          // for device to be up and running
            tlb_managers[chip_id] = std::make_unique<umd::TLBManager>(tt_device.get());
            sysmem_managers[chip_id] =
                std::make_unique<umd::SysmemManager>(tlb_managers[chip_id].get(), num_host_mem_channels);
            devices[chip_id] = std::move(tt_device);
        } else {
            chip_id_t gateway_id = cluster_descriptor->get_closest_mmio_capable_chip(chip_id);
            const auto& active_channels = cluster_descriptor->get_active_eth_channels(gateway_id);
            auto local_device = devices[gateway_id].get();
            auto target_eth_coord = cluster_descriptor->get_chip_location(chip_id);
            umd::SysmemManager* sysmem_manager = sysmem_managers[gateway_id].get();
            auto remote_transfer_eth_channels = cluster_descriptor->get_active_eth_channels(gateway_id);
            auto remote_communication =
                umd::RemoteCommunication::create_remote_communication(local_device, target_eth_coord, sysmem_manager);
            remote_communication->set_remote_transfer_ethernet_cores(
                soc_descriptors[gateway_id].get_eth_xy_pairs_for_channels(remote_transfer_eth_channels,
                                                                          CoordSystem::TRANSLATED));
            auto remote_tt_device = umd::TTDevice::create(std::move(remote_communication), target_eth_coord);
            remote_tt_device->init_tt_device();
            devices[chip_id] = std::move(remote_tt_device);
        }

        SocDescriptor soc_descriptor(devices[chip_id]->get_arch(), devices[chip_id]->get_chip_info());
        std::string file_name = temp_working_directory / ("device_desc_runtime_" + std::to_string(chip_id) + ".yaml");

        soc_descriptor.serialize_to_file(file_name);
        device_soc_descriptors_yamls[chip_id] = file_name;
        soc_descriptors[chip_id] = soc_descriptor;
    }
    cached_arc_telemetry_readers.resize(cluster_descriptor->get_number_of_chips());
}

umd::TTDevice* new_umd_implementation::get_device(uint8_t chip_id) {
    auto it = devices.find(chip_id);
    if (it == devices.end()) {
        throw std::runtime_error("Device with chip id " + std::to_string(chip_id) + " not found.");
    }
    return it->second.get();
}

tt::xy_pair new_umd_implementation::get_noc0_to_device_coords(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y) {
    auto& soc_descriptor = soc_descriptors.at(chip_id);
    return soc_descriptor.translate_coord_to(soc_descriptor.get_coord_at({noc_x, noc_y}, CoordSystem::NOC0),
                                             CoordSystem::TRANSLATED);
}

bool new_umd_implementation::is_chip_mmio_capable(uint8_t chip_id) {
    return cluster_descriptor->is_chip_mmio_capable(chip_id);
}

tt::umd::ArcTelemetryReader* new_umd_implementation::get_arc_telemetry_reader(uint8_t chip_id) {
    auto& cached_arc_telemetry_reader = cached_arc_telemetry_readers[chip_id];
    if (!cached_arc_telemetry_reader) {
        std::lock_guard<std::mutex> lock(cached_arc_telemetry_readers_mutex);
        if (!cached_arc_telemetry_reader) {
            cached_arc_telemetry_reader = tt::umd::ArcTelemetryReader::create_arc_telemetry_reader(get_device(chip_id));
        }
    }
    return cached_arc_telemetry_reader.get();
}

std::optional<uint32_t> new_umd_implementation::pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                           uint8_t noc_y, uint64_t address) {
    uint32_t result = 0;

    read_from_device_reg_unaligned(get_device(chip_id), &result, noc_id,
                                   get_noc0_to_device_coords(chip_id, noc_x, noc_y), address, sizeof(result));
    return result;
}

std::optional<uint32_t> new_umd_implementation::pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                            uint8_t noc_y, uint64_t address, uint32_t data) {
    write_to_device_reg_unaligned(get_device(chip_id), &data, sizeof(data), noc_id,
                                  get_noc0_to_device_coords(chip_id, noc_x, noc_y), address);
    return sizeof(data);
}

std::optional<std::vector<uint8_t>> new_umd_implementation::pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                                     uint8_t noc_y, uint64_t address, uint32_t size) {
    std::vector<uint8_t> result(size);
    auto* device = get_device(chip_id);
    auto noc_coords = get_noc0_to_device_coords(chip_id, noc_x, noc_y);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            read_from_device_reg_unaligned(device, result.data() + done, noc_id, noc_coords, address + done, block);
            done += block;
        }
        return result;
    }

    read_from_device_reg_unaligned(device, result.data(), noc_id, noc_coords, address, size);
    return result;
}

std::optional<uint32_t> new_umd_implementation::pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                          uint64_t address, const uint8_t* data, uint32_t size) {
    auto* device = get_device(chip_id);
    auto noc_coords = get_noc0_to_device_coords(chip_id, noc_x, noc_y);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            write_to_device_reg_unaligned(device, data + done, block, noc_id, noc_coords, address + done);
            done += block;
        }
        return size;
    }

    write_to_device_reg_unaligned(device, data, size, noc_id, noc_coords, address);
    return size;
}

std::optional<uint32_t> new_umd_implementation::pci_read32_raw(uint8_t chip_id, uint64_t address) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        return get_device(chip_id)->bar_read32(address);
    }
    return {};
}

std::optional<uint32_t> new_umd_implementation::pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        get_device(chip_id)->bar_write32(address, data);
        return 4;
    }
    return {};
}

std::optional<uint32_t> new_umd_implementation::dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
    // TODO: We are not using this functionionally, so just throw for now
    throw std::runtime_error("DMA buffer read not implemented");
}

std::optional<std::string> new_umd_implementation::pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                                 uint8_t noc_y, uint64_t address, uint32_t size,
                                                                 uint8_t data_format) {
    // TODO: We are not using this functionionally, so just throw for now
    throw std::runtime_error("pci_read_tile not implemented");
}

std::optional<std::string> new_umd_implementation::get_cluster_description() { return cluster_descriptor_path; }

std::optional<std::vector<uint8_t>> new_umd_implementation::get_device_ids() { return device_ids; }

std::optional<std::string> new_umd_implementation::get_device_arch(uint8_t chip_id) {
    try {
        return tt::arch_to_str(soc_descriptors[chip_id].arch);
    } catch (...) {
        return {};
    }
}

std::optional<std::string> new_umd_implementation::get_device_soc_description(uint8_t chip_id) {
    try {
        return device_soc_descriptors_yamls[chip_id];
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<uint8_t, uint8_t>> new_umd_implementation::convert_from_noc0(uint8_t chip_id, uint8_t noc_x,
                                                                                      uint8_t noc_y,
                                                                                      const std::string& core_type,
                                                                                      const std::string& coord_system) {
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
        auto& soc_descriptor = soc_descriptors.at(chip_id);
        tt::umd::CoreCoord core_coord{noc_x, noc_y, core_type_enum, CoordSystem::NOC0};
        auto output = soc_descriptor.translate_coord_to(core_coord, coord_system_enum);

        return std::make_tuple(static_cast<uint8_t>(output.x), static_cast<uint8_t>(output.y));
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<int, uint32_t, uint32_t>> new_umd_implementation::arc_msg(uint8_t noc_id, uint8_t chip_id,
                                                                                   uint32_t msg_code,
                                                                                   bool wait_for_done, uint32_t arg0,
                                                                                   uint32_t arg1, int timeout) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    std::vector<uint32_t> arc_msg_return_value(2, 0);
    auto return_code =
        get_device(chip_id)->get_arc_messenger()->send_message(msg_code, arc_msg_return_value, arg0, arg1, timeout);

    return std::make_tuple(return_code, arc_msg_return_value[0], arc_msg_return_value[1]);
}

std::optional<uint32_t> new_umd_implementation::read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag) {
    auto* arc_telemetry_reader = get_arc_telemetry_reader(chip_id);
    auto umd_telemetry_tag = static_cast<tt::umd::TelemetryTag>(telemetry_tag);
    if (!arc_telemetry_reader->is_entry_available(telemetry_tag)) {
        return {};
    }
    return arc_telemetry_reader->read_entry(telemetry_tag);
}

std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> new_umd_implementation::get_firmware_version(uint8_t chip_id) {
    const auto& firmware_version = tt::umd::get_firmware_version_util(get_device(chip_id));
    return std::make_tuple(firmware_version.major, firmware_version.minor, firmware_version.patch);
}

std::optional<uint64_t> new_umd_implementation::get_device_unique_id(uint8_t chip_id) {
    auto it = device_id_to_unique_id.find(chip_id);

    if (it != device_id_to_unique_id.end()) {
        return it->second;
    }
    return {};
}

std::optional<int> new_umd_implementation::jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) {
    throw std::runtime_error("JTAG not implemented");
}

std::optional<int> new_umd_implementation::jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                        uint64_t address, uint32_t data) {
    throw std::runtime_error("JTAG not implemented");
}

std::optional<uint32_t> new_umd_implementation::jtag_read32_axi(uint8_t chip_id, uint32_t address) {
    throw std::runtime_error("JTAG not implemented");
}

std::optional<uint32_t> new_umd_implementation::jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                            uint8_t noc_y, uint64_t address) {
    throw std::runtime_error("JTAG not implemented");
}

}  // namespace tt::exalens

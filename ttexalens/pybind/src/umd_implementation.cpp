// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "umd_implementation.h"

#include <cstdint>
#include <tuple>

#include "read_tile.hpp"
#include "umd/device/arc/arc_telemetry_reader.hpp"
#include "umd/device/cluster.hpp"
#include "umd/device/firmware/firmware_utils.hpp"

namespace tt::exalens {

// TODO #375: Remove read/write unaligned functions once UMD implements ability to set unaligned access for our TLB

void read_from_device_reg_unaligned(tt::umd::Cluster* cluster, void* mem_ptr, ChipId chip, tt::umd::CoreCoord core,
                                    uint64_t addr, uint32_t size) {
    // Read first unaligned word
    uint32_t first_unaligned_index = addr % 4;
    if (first_unaligned_index != 0) {
        uint32_t temp = 0;
        cluster->read_from_device_reg(&temp, chip, core, addr - first_unaligned_index, sizeof(temp));
        if (first_unaligned_index + size <= sizeof(temp)) {
            memcpy(mem_ptr, ((uint8_t*)&temp) + first_unaligned_index, size);
            return;
        }
        memcpy(mem_ptr, ((uint8_t*)&temp) + first_unaligned_index, 4 - first_unaligned_index);
        mem_ptr = (uint8_t*)mem_ptr + 4 - first_unaligned_index;
        addr += 4 - first_unaligned_index;
        size -= 4 - first_unaligned_index;
    }

    // Read aligned bytes
    uint32_t aligned_size = size - (size % 4);
    if (aligned_size > 0) {
        cluster->read_from_device_reg(mem_ptr, chip, core, addr, aligned_size);
        mem_ptr = (uint8_t*)mem_ptr + aligned_size;
        addr += aligned_size;
        size -= aligned_size;
    }

    // Read last unaligned word
    uint32_t last_unaligned_size = size;
    if (last_unaligned_size != 0) {
        uint32_t temp = 0;
        cluster->read_from_device_reg(&temp, chip, core, addr, sizeof(temp));
        memcpy(mem_ptr, &temp, last_unaligned_size);
    }
}

void write_to_device_reg_unaligned(tt::umd::Cluster* cluster, const void* mem_ptr, uint32_t size_in_bytes, ChipId chip,
                                   tt::umd::CoreCoord core, uint64_t addr) {
    {
        // Read/Write first unaligned word
        uint32_t first_unaligned_index = addr % 4;
        if (first_unaligned_index != 0) {
            uint32_t temp = 0;
            uint64_t aligned_address = addr - first_unaligned_index;
            cluster->read_from_device_reg(&temp, chip, core, aligned_address, sizeof(temp));
            if (first_unaligned_index + size_in_bytes <= sizeof(temp)) {
                memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, size_in_bytes);
                cluster->write_to_device_reg(&temp, sizeof(temp), chip, core, aligned_address);
                return;
            }
            memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, 4 - first_unaligned_index);
            cluster->write_to_device_reg(&temp, sizeof(temp), chip, core, aligned_address);
            mem_ptr = (uint8_t*)mem_ptr + 4 - first_unaligned_index;
            addr += 4 - first_unaligned_index;
            size_in_bytes -= 4 - first_unaligned_index;
        }

        // Write aligned bytes
        uint32_t aligned_size = size_in_bytes - (size_in_bytes % 4);
        if (aligned_size > 0) {
            cluster->write_to_device_reg(mem_ptr, aligned_size, chip, core, addr);
            mem_ptr = (uint8_t*)mem_ptr + aligned_size;
            addr += aligned_size;
            size_in_bytes -= aligned_size;
        }

        // Read/Write last unaligned word
        uint32_t last_unaligned_size = size_in_bytes;
        if (last_unaligned_size != 0) {
            uint32_t temp = 0;
            cluster->read_from_device_reg(&temp, chip, core, addr, sizeof(temp));
            memcpy(&temp, mem_ptr, last_unaligned_size);
            cluster->write_to_device_reg(&temp, sizeof(temp), chip, core, addr);
        }
    }
}

umd_implementation::umd_implementation(tt::umd::Cluster* cluster) : cluster(cluster) {
    cached_arc_telemetry_readers.resize(cluster->get_cluster_description()->get_number_of_chips());
}

std::optional<uint32_t> umd_implementation::read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                   uint64_t address) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    uint32_t result;
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    read_from_device_reg_unaligned(cluster, &result, chip_id, target, address, sizeof(result));
    return result;
}

std::optional<uint32_t> umd_implementation::write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                    uint64_t address, uint32_t data) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    write_to_device_reg_unaligned(cluster, &data, sizeof(data), chip_id, target, address);
    return 4;
}

std::optional<std::vector<uint8_t>> umd_implementation::read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                             uint8_t noc_y, uint64_t address, uint32_t size) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    std::vector<uint8_t> result(size);
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);
    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            read_from_device_reg_unaligned(cluster, result.data() + done, chip_id, target, address + done, block);
            done += block;
        }
        return result;
    }

    read_from_device_reg_unaligned(cluster, result.data(), chip_id, target, address, size);
    return result;
}

std::optional<uint32_t> umd_implementation::write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                  uint64_t address, const uint8_t* data, uint32_t size) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            write_to_device_reg_unaligned(cluster, data + done, block, chip_id, target, address + done);
            done += block;
        }
        return size;
    }

    write_to_device_reg_unaligned(cluster, data, size, chip_id, target, address);
    return size;
}

bool umd_implementation::is_chip_mmio_capable(uint8_t chip_id) {
    if (!cluster) {
        return false;
    }

    auto mmio_targets = cluster->get_target_mmio_device_ids();

    return mmio_targets.find(chip_id) != mmio_targets.end();
}

std::optional<uint32_t> umd_implementation::pci_read32_raw(uint8_t chip_id, uint64_t address) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        if (cluster) {
            return cluster->get_chip(chip_id)->get_tt_device()->bar_read32(address);
        }
    }
    return {};
}

std::optional<uint32_t> umd_implementation::pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        if (cluster) {
            cluster->get_chip(chip_id)->get_tt_device()->bar_write32(address, data);
            return 4;
        }
    }
    return {};
}

std::optional<uint32_t> umd_implementation::dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
    uint32_t result;

    cluster->read_from_sysmem(&result, address, channel, sizeof(result), chip_id);
    return result;
}

std::optional<std::string> umd_implementation::read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                         uint64_t address, uint32_t size, uint8_t data_format) {
    return tt::exalens::tile::read_tile_implementation(noc_id, chip_id, noc_x, noc_y, address, size, data_format,
                                                       cluster);
}

std::optional<std::string> umd_implementation::get_device_arch(uint8_t chip_id) {
    try {
        return tt::arch_to_str(cluster->get_soc_descriptor(chip_id).arch);
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<int, uint32_t, uint32_t>> umd_implementation::arc_msg(uint8_t noc_id, uint8_t chip_id,
                                                                               uint32_t msg_code, bool wait_for_done,
                                                                               uint32_t arg0, uint32_t arg1,
                                                                               int timeout) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    uint32_t return_3 = 0;
    uint32_t return_4 = 0;
    int return_code = cluster->arc_msg(chip_id, msg_code, wait_for_done, arg0, arg1, timeout, &return_3, &return_4);
    return std::make_tuple(return_code, return_3, return_4);
}

tt::umd::ArcTelemetryReader* umd_implementation::get_arc_telemetry_reader(uint8_t chip_id) {
    auto& cached_arc_telemetry_reader = cached_arc_telemetry_readers[chip_id];
    if (!cached_arc_telemetry_reader) {
        std::lock_guard<std::mutex> lock(cached_arc_telemetry_readers_mutex);
        if (!cached_arc_telemetry_reader) {
            cached_arc_telemetry_reader =
                tt::umd::ArcTelemetryReader::create_arc_telemetry_reader(cluster->get_tt_device(chip_id));
        }
    }
    return cached_arc_telemetry_reader.get();
}

std::optional<uint32_t> umd_implementation::read_arc_telemetry_entry_helper(uint8_t chip_id, uint8_t telemetry_tag) {
    auto* arc_telemetry_reader = get_arc_telemetry_reader(chip_id);
    auto umd_telemetry_tag = static_cast<tt::umd::TelemetryTag>(telemetry_tag);
    if (!arc_telemetry_reader->is_entry_available(telemetry_tag)) {
        return {};
    }
    return arc_telemetry_reader->read_entry(telemetry_tag);
}

std::optional<uint32_t> umd_implementation::read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag) {
    return read_arc_telemetry_entry_helper(chip_id, telemetry_tag);
}

std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> umd_implementation::get_firmware_version(uint8_t chip_id) {
    const auto& firmware_version = tt::umd::get_firmware_version_util(cluster->get_tt_device(chip_id));
    return std::make_tuple(firmware_version.major, firmware_version.minor, firmware_version.patch);
}
}  // namespace tt::exalens

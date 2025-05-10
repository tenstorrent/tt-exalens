// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttexalensserver/umd_implementation.h"

#include <cstdint>
#include <tuple>

#include "ttexalensserver/read_tile.hpp"
#include "umd/device/cluster.h"

namespace tt::exalens {

umd_implementation::umd_implementation(tt::umd::Cluster* cluster) : cluster(cluster) {}

std::optional<uint32_t> umd_implementation::pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                       uint64_t address) {
    uint32_t result;
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    cluster->read_from_device_reg(&result, chip_id, target, address, sizeof(result));
    return result;
}

std::optional<uint32_t> umd_implementation::pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                        uint32_t data) {
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    cluster->write_to_device_reg(&data, sizeof(data), chip_id, target, address);
    return 4;
}

std::optional<std::vector<uint8_t>> umd_implementation::pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                 uint64_t address, uint32_t size) {
    std::vector<uint8_t> result(size);
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            cluster->read_from_device_reg(result.data() + done, chip_id, target, address + done, block);
            done += block;
        }
        return result;
    }

    cluster->read_from_device_reg(result.data(), chip_id, target, address, size);
    return result;
}

std::optional<uint32_t> umd_implementation::pci_write(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                      const uint8_t* data, uint32_t size) {
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            cluster->write_to_device(data + done, block, chip_id, target, address + done);
            done += block;
        }
        return size;
    }

    cluster->write_to_device(data, size, chip_id, target, address);
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

std::optional<std::string> umd_implementation::pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                             uint64_t address, uint32_t size, uint8_t data_format) {
    return tt::exalens::tile::read_tile_implementation(chip_id, noc_x, noc_y, address, size, data_format, cluster);
}

std::optional<std::string> umd_implementation::get_device_arch(uint8_t chip_id) {
    try {
        return tt::arch_to_str(cluster->get_soc_descriptor(chip_id).arch);
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<int, uint32_t, uint32_t>> umd_implementation::arc_msg(uint8_t chip_id, uint32_t msg_code,
                                                                               bool wait_for_done, uint32_t arg0,
                                                                               uint32_t arg1, int timeout) {
    uint32_t return_3 = 0;
    uint32_t return_4 = 0;
    int return_code = cluster->arc_msg(chip_id, msg_code, wait_for_done, arg0, arg1, timeout, &return_3, &return_4);
    return std::make_tuple(return_code, return_3, return_4);
}

}  // namespace tt::exalens

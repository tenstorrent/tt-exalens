// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttlensserver/umd_implementation.h"

#include <tuple>

#include "ttlensserver/jtag_device.h"
#include "ttlensserver/read_tile.hpp"
#include "umd/device/cluster.h"

static std::string REG_TLB_STR = "REG_TLB";
static std::string SMALL_READ_WRITE_TLB_STR = "SMALL_READ_WRITE_TLB";
static std::string LARGE_READ_TLB_STR = "LARGE_READ_TLB";
static std::string LARGE_WRITE_TLB_STR = "LARGE_WRITE_TLB";

namespace tt::lens {

umd_implementation::umd_implementation(tt::umd::Cluster* device, JtagDevice* jtag_device)
    : device(device), jtag_device(jtag_device) {}

std::optional<uint32_t> umd_implementation::pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                       uint64_t address) {
    if (!device) {
        return {};
    }

    uint32_t result;
    tt_cxy_pair target(chip_id, noc_x, noc_y);

    device->read_from_device(&result, target, address, sizeof(result), REG_TLB_STR);
    return result;
}

std::optional<uint32_t> umd_implementation::pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                        uint32_t data) {
    if (!device) {
        return {};
    }

    tt_cxy_pair target(chip_id, noc_x, noc_y);

    device->write_to_device(&data, sizeof(data), target, address, LARGE_WRITE_TLB_STR);
    return 4;
}

std::optional<std::vector<uint8_t>> umd_implementation::pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                 uint64_t address, uint32_t size) {
    if (!device) {
        return {};
    }

    tt_cxy_pair target(chip_id, noc_x, noc_y);
    std::vector<uint8_t> result(size);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            device->read_from_device(result.data() + done, target, address + done, block, REG_TLB_STR);
            done += block;
        }
        return result;
    }

    device->read_from_device(result.data(), target, address, size, REG_TLB_STR);
    return result;
}

std::optional<uint32_t> umd_implementation::pci_write(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                      const uint8_t* data, uint32_t size) {
    if (!device) {
        return {};
    }

    tt_cxy_pair target(chip_id, noc_x, noc_y);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            device->write_to_device(data + done, block, target, address + done, LARGE_WRITE_TLB_STR);
            done += block;
        }
        return size;
    }

    device->write_to_device(data, size, target, address, LARGE_WRITE_TLB_STR);
    return size;
}

bool umd_implementation::is_chip_mmio_capable(uint8_t chip_id) {
    if (!device) {
        return false;
    }

    auto mmio_targets = device->get_target_mmio_device_ids();

    return mmio_targets.find(chip_id) != mmio_targets.end();
}

std::optional<uint32_t> umd_implementation::pci_read32_raw(uint8_t chip_id, uint64_t address) {
    if (!device) {
        return {};
    }

    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        return device->bar_read32(chip_id, address);
    } else {
        return {};
    }
}

std::optional<uint32_t> umd_implementation::pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
    if (!device) {
        return {};
    }

    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        device->bar_write32(chip_id, address, data);
        return 4;
    } else {
        return {};
    }
}

std::optional<uint32_t> umd_implementation::dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
    if (!device) {
        return {};
    }

    uint32_t result;

    device->read_from_sysmem(&result, address, channel, sizeof(result), chip_id);
    return result;
}

std::optional<std::string> umd_implementation::pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                             uint64_t address, uint32_t size, uint8_t data_format) {
    if (!device) {
        return {};
    }

    return tt::lens::tile::read_tile_implementation(chip_id, noc_x, noc_y, address, size, data_format, device);
}

std::optional<std::string> umd_implementation::get_harvester_coordinate_translation(uint8_t chip_id) {
    if (!device) {
        return {};
    }

    std::unordered_map<tt_xy_pair, tt_xy_pair> harvested_coord_translation =
        device->get_harvested_coord_translation_map(chip_id);
    std::string ret = "{ ";
    for (auto& kv : harvested_coord_translation) {
        ret += "(" + std::to_string(kv.first.x) + "," + std::to_string(kv.first.y) + ") : (" +
               std::to_string(kv.second.x) + "," + std::to_string(kv.second.y) + "), ";
    }
    return ret + " }";
}

std::optional<std::string> umd_implementation::get_device_arch(uint8_t chip_id) {
    tt_device* d = static_cast<tt_device*>(device);

    try {
        return get_arch_str(d->get_soc_descriptor(chip_id).arch);
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<int, uint32_t, uint32_t>> umd_implementation::arc_msg(uint8_t chip_id, uint32_t msg_code,
                                                                               bool wait_for_done, uint32_t arg0,
                                                                               uint32_t arg1, int timeout) {
    if (!device) {
        return {};
    }
    tt_device* d = static_cast<tt_device*>(device);

    uint32_t return_3 = 0;
    uint32_t return_4 = 0;
    int return_code = d->arc_msg(chip_id, msg_code, wait_for_done, arg0, arg1, timeout, &return_3, &return_4);
    return std::make_tuple(return_code, return_3, return_4);
}

std::optional<int> umd_implementation::jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) {
    if (!jtag_device) {
        return {};
    }
    return jtag_device->write32_axi(chip_id, address, data);
}
std::optional<int> umd_implementation::jtag_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                    uint32_t data) {
    if (!jtag_device) {
        return {};
    }
    return jtag_device->write32(chip_id, noc_x, noc_y, address, data);
}
std::optional<uint32_t> umd_implementation::jtag_read32_axi(uint8_t chip_id, uint32_t address) {
    if (!jtag_device) {
        return {};
    }
    return jtag_device->read32_axi(chip_id, address);
}
std::optional<uint32_t> umd_implementation::jtag_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                        uint64_t address) {
    if (!jtag_device) {
        return {};
    }
    return jtag_device->read32(chip_id, noc_x, noc_y, address);
}

}  // namespace tt::lens

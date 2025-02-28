// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttexalensserver/umd_implementation.h"

#include <cstdint>
#include <tuple>

#include "ttexalensserver/read_tile.hpp"
#include "umd/device/cluster.h"

static std::string REG_TLB_STR = "REG_TLB";
static std::string SMALL_READ_WRITE_TLB_STR = "SMALL_READ_WRITE_TLB";
static std::string LARGE_READ_TLB_STR = "LARGE_READ_TLB";
static std::string LARGE_WRITE_TLB_STR = "LARGE_WRITE_TLB";

namespace tt::exalens {

umd_implementation::umd_implementation(tt_device* device) : device(device) {}

std::optional<uint32_t> umd_implementation::pci_read32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                       uint64_t address) {
    uint32_t result;
    tt_cxy_pair target(chip_id, noc_x, noc_y);

    device->read_from_device(&result, target, address, sizeof(result), REG_TLB_STR);
    return result;
}

std::optional<uint32_t> umd_implementation::pci_write32(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                                        uint32_t data) {
    tt_cxy_pair target(chip_id, noc_x, noc_y);

    device->write_to_device(&data, sizeof(data), target, address, LARGE_WRITE_TLB_STR);
    return 4;
}

std::optional<std::vector<uint8_t>> umd_implementation::pci_read(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                 uint64_t address, uint32_t size) {
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
    tt::umd::Cluster* silicon_device = dynamic_cast<tt::umd::Cluster*>(device);

    if (!silicon_device) {
        return false;
    }

    auto mmio_targets = silicon_device->get_target_mmio_device_ids();

    return mmio_targets.find(chip_id) != mmio_targets.end();
}

std::optional<uint32_t> umd_implementation::pci_read32_raw(uint8_t chip_id, uint64_t address) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        tt::umd::Cluster* silicon_device = dynamic_cast<tt::umd::Cluster*>(device);

        if (silicon_device) {
            return silicon_device->bar_read32(chip_id, address);
        }
    }
    return {};
}

std::optional<uint32_t> umd_implementation::pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) {
    // TODO: @ihamer, finish this
    if (is_chip_mmio_capable(chip_id)) {
        tt::umd::Cluster* silicon_device = dynamic_cast<tt::umd::Cluster*>(device);

        if (silicon_device) {
            silicon_device->bar_write32(chip_id, address, data);
            return 4;
        }
    }
    return {};
}

std::optional<uint32_t> umd_implementation::dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) {
    uint32_t result;

    device->read_from_sysmem(&result, address, channel, sizeof(result), chip_id);
    return result;
}

std::optional<std::string> umd_implementation::pci_read_tile(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                             uint64_t address, uint32_t size, uint8_t data_format) {
    return tt::exalens::tile::read_tile_implementation(chip_id, noc_x, noc_y, address, size, data_format, device);
}

std::optional<std::string> umd_implementation::get_device_arch(uint8_t chip_id) {
    tt_device* d = static_cast<tt_device*>(device);

    try {
        return tt::arch_to_str(d->get_soc_descriptor(chip_id).arch);
    } catch (...) {
        return {};
    }
}

std::optional<std::tuple<int, uint32_t, uint32_t>> umd_implementation::arc_msg(uint8_t chip_id, uint32_t msg_code,
                                                                               bool wait_for_done, uint32_t arg0,
                                                                               uint32_t arg1, int timeout) {
    tt_device* d = static_cast<tt_device*>(device);

    uint32_t return_3 = 0;
    uint32_t return_4 = 0;
    int return_code = d->arc_msg(chip_id, msg_code, wait_for_done, arg0, arg1, timeout, &return_3, &return_4);
    return std::make_tuple(return_code, return_3, return_4);
}

}  // namespace tt::exalens

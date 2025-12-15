// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "umd_implementation.h"

#include <chrono>
#include <cstdint>
#include <exception>
#include <sstream>
#include <string>
#include <tuple>

#include "read_tile.hpp"
#include "umd/device/arc/arc_telemetry_reader.hpp"
#include "umd/device/cluster.hpp"
#include "umd/device/firmware/firmware_utils.hpp"
#include "umd/device/warm_reset.hpp"

namespace tt::exalens {

std::chrono::microseconds READ_TIMEOUT = []() -> std::chrono::microseconds {
    const char* timeout_ms_str = getenv("TT_EXALENS_READ_TIMEOUT_MS");
    int timeout_ms = timeout_ms_str ? std::stoi(timeout_ms_str) : 2;
    return std::chrono::microseconds(timeout_ms * 1000);
}();

std::chrono::microseconds WRITE_TIMEOUT = []() -> std::chrono::microseconds {
    const char* timeout_ms_str = getenv("TT_EXALENS_WRITE_TIMEOUT_MS");
    int timeout_ms = timeout_ms_str ? std::stoi(timeout_ms_str) : 2;
    return std::chrono::microseconds(timeout_ms * 1000);
}();

int NUM_OF_CONSECUTIVE_TIMEOUTS = []() -> int {
    const char* num_of_consecutive_timeouts = getenv("TT_EXALENS_NUM_OF_CONSECUTIVE_TIMEOUTS");
    return num_of_consecutive_timeouts ? std::stoi(num_of_consecutive_timeouts) : 5;
}();

class TimeoutDeviceRegisterException : public std::exception {
   public:
    TimeoutDeviceRegisterException(uint8_t chip_id, tt::umd::CoreCoord core, uint64_t addr, uint32_t size, bool is_read,
                                   std::chrono::microseconds duration)
        : chip_id(chip_id), core(core), addr(addr), size(size), duration(duration) {
        std::string msg = is_read ? "Timeout reading from device register" : "Timeout writing to device register";
        std::ostringstream oss;
        oss << msg << ": device_id=" << static_cast<int>(chip_id) << ", location=(" << core.x << "," << core.y << ","
            << to_str(core.core_type) << ")"
            << ", address=0x" << std::hex << addr << ", size=" << std::dec << size << ", duration=" << duration.count()
            << "us";
        message = oss.str();
    }

    const char* what() const noexcept override { return message.c_str(); }

    const uint8_t chip_id;
    const tt::umd::CoreCoord core;
    const uint64_t addr;
    const uint32_t size;
    const std::chrono::microseconds duration;

   private:
    std::string message;
};

void read_from_device_reg(tt::umd::Cluster* cluster, bool is_simulation, void* temp, uint8_t chip_id,
                          tt::umd::CoreCoord tensix_core, uint64_t addr, uint32_t size) {
    auto start_time = std::chrono::high_resolution_clock::now();
    cluster->read_from_device_reg(temp, chip_id, tensix_core, addr, size);
    auto end_time = std::chrono::high_resolution_clock::now();
    auto elapsed_time = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    // Address will always be aligned to 4 bytes, so we can check the last 4 bytes for 0xFFFFFFFF
    if (cluster->get_cluster_description()->is_chip_mmio_capable(chip_id) && !is_simulation &&
        elapsed_time > READ_TIMEOUT && *((uint32_t*)temp + size / 4 - 1) == 0xFFFFFFFF) {
        tensix_core = cluster->get_soc_descriptor(chip_id).translate_coord_to(tensix_core, CoordSystem::LOGICAL);
        throw TimeoutDeviceRegisterException(chip_id, tensix_core, addr, size, true, elapsed_time);
    }
}

void write_to_device_reg(tt::umd::Cluster* cluster, bool is_simulation, const void* temp, uint32_t size,
                         uint8_t chip_id, tt::umd::CoreCoord tensix_core, uint64_t addr) {
    struct TimeoutEvent {
        const tt::umd::CoreCoord core;
        const uint64_t addr;
        const uint32_t size;
        const std::chrono::microseconds elapsed_time;

        TimeoutEvent(tt::umd::CoreCoord core, uint64_t addr, uint32_t size, std::chrono::microseconds elapsed_time)
            : core(core), addr(addr), size(size), elapsed_time(elapsed_time) {}
    };

    auto start_time = std::chrono::high_resolution_clock::now();
    cluster->write_to_device_reg(temp, size, chip_id, tensix_core, addr);
    auto end_time = std::chrono::high_resolution_clock::now();
    auto elapsed_time = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);

    static std::mutex lock;
    static std::unordered_map<uint8_t, std::vector<TimeoutEvent>> timeout_events_per_chip;

    // Timeout is set for 1 word write so we only check timeout for that case
    // To avoid raising false alarms, we only throw an exception if we have multiple consecutive timeouts (5 by default)
    if (cluster->get_cluster_description()->is_chip_mmio_capable(chip_id) && !is_simulation && size == 4 &&
        elapsed_time > WRITE_TIMEOUT) {
        TimeoutEvent timeout_event(tensix_core, addr, size, elapsed_time);
        lock.lock();
        timeout_events_per_chip[chip_id].push_back(timeout_event);
        if (timeout_events_per_chip[chip_id].size() >= NUM_OF_CONSECUTIVE_TIMEOUTS) {
            TimeoutEvent oldest_event = timeout_events_per_chip[chip_id].front();
            throw TimeoutDeviceRegisterException(chip_id, oldest_event.core, oldest_event.addr, oldest_event.size,
                                                 false, oldest_event.elapsed_time);
        }
        lock.unlock();
    } else {
        lock.lock();
        timeout_events_per_chip[chip_id].clear();
        lock.unlock();
    }
}

// Find working active eth core and configure it for remote communication
void _configure_working_active_eth(tt::umd::Cluster* cluster, uint8_t chip_id) {
    ChipId mmio_chip_id = cluster->get_cluster_description()->get_closest_mmio_capable_chip(chip_id);
    // Define tensix core for testing remote communication
    const tt::umd::CoreCoord tensix_core = tt::umd::CoreCoord(0, 0, CoreType::TENSIX, CoordSystem::LOGICAL);
    std::unordered_set<tt::umd::CoreCoord> active_eth_cores =
        cluster->get_soc_descriptor(mmio_chip_id)
            .get_eth_cores_for_channels(cluster->get_cluster_description()->get_active_eth_channels(mmio_chip_id),
                                        CoordSystem::LOGICAL);
    for (auto core : active_eth_cores) {
        cluster->configure_active_ethernet_cores_for_mmio_device(mmio_chip_id,
                                                                 std::unordered_set<tt::umd::CoreCoord>({core}));
        try {
            // Try to read from remote device to see if remote communication is working
            uint32_t temp = 0;
            read_from_device_reg(cluster, false, &temp, chip_id, tensix_core, 0, sizeof(temp));
            // If reading from remote device is successful, we found the working active eth core
            return;
            // If reading from remote device fails, try the next active eth core
        } catch (const std::exception& e) {
            continue;
        }
    }
    throw std::runtime_error("Failed to configure working active Ethernet");
}

// TODO #375: Remove read/write unaligned functions once UMD implements ability to set unaligned access for our TLB
void read_from_device_reg_unaligned_helper(tt::umd::Cluster* cluster, bool is_simulation, void* mem_ptr, ChipId chip,
                                           tt::umd::CoreCoord core, uint64_t addr, uint32_t size, bool use_4B_mode) {
    // Read first unaligned word
    uint32_t first_unaligned_index = addr % 4;
    if (first_unaligned_index != 0) {
        uint32_t temp = 0;
        read_from_device_reg(cluster, is_simulation, &temp, chip, core, addr - first_unaligned_index, sizeof(temp));
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
    uint32_t block_size = use_4B_mode ? 4 : aligned_size;
    while (aligned_size > 0) {
        read_from_device_reg(cluster, is_simulation, mem_ptr, chip, core, addr, block_size);
        aligned_size -= block_size;
        mem_ptr = (uint8_t*)mem_ptr + block_size;
        addr += block_size;
        size -= block_size;
    }

    // Read last unaligned word
    uint32_t last_unaligned_size = size;
    if (last_unaligned_size != 0) {
        uint32_t temp = 0;
        read_from_device_reg(cluster, is_simulation, &temp, chip, core, addr, sizeof(temp));
        memcpy(mem_ptr, &temp, last_unaligned_size);
    }
}

void read_from_device_reg_unaligned(tt::umd::Cluster* cluster, bool is_simulation, void* mem_ptr, ChipId chip,
                                    tt::umd::CoreCoord core, uint64_t addr, uint32_t size, bool use_4B_mode) {
    try {
        read_from_device_reg_unaligned_helper(cluster, is_simulation, mem_ptr, chip, core, addr, size, use_4B_mode);
    } catch (const TimeoutDeviceRegisterException& e) {
        throw;
    } catch (const std::runtime_error& e) {
        if (is_simulation || cluster->get_cluster_description()->is_chip_mmio_capable(chip)) {
            throw;
        }
        _configure_working_active_eth(cluster, chip);
        read_from_device_reg_unaligned_helper(cluster, false, mem_ptr, chip, core, addr, size, use_4B_mode);
    }
}

void write_to_device_reg_unaligned_helper(tt::umd::Cluster* cluster, bool is_simulation, const void* mem_ptr,
                                          uint32_t size_in_bytes, ChipId chip, tt::umd::CoreCoord core, uint64_t addr,
                                          bool use_4B_mode) {
    {
        // Read/Write first unaligned word
        uint32_t first_unaligned_index = addr % 4;
        if (first_unaligned_index != 0) {
            uint32_t temp = 0;
            uint64_t aligned_address = addr - first_unaligned_index;
            read_from_device_reg(cluster, is_simulation, &temp, chip, core, aligned_address, sizeof(temp));
            if (first_unaligned_index + size_in_bytes <= sizeof(temp)) {
                memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, size_in_bytes);
                write_to_device_reg(cluster, is_simulation, &temp, sizeof(temp), chip, core, aligned_address);
                return;
            }
            memcpy(((uint8_t*)&temp) + first_unaligned_index, mem_ptr, 4 - first_unaligned_index);
            write_to_device_reg(cluster, is_simulation, &temp, sizeof(temp), chip, core, aligned_address);
            mem_ptr = (uint8_t*)mem_ptr + 4 - first_unaligned_index;
            addr += 4 - first_unaligned_index;
            size_in_bytes -= 4 - first_unaligned_index;
        }

        // Write aligned bytes
        uint32_t aligned_size = size_in_bytes - (size_in_bytes % 4);
        uint32_t block_size = use_4B_mode ? 4 : aligned_size;
        while (aligned_size > 0) {
            write_to_device_reg(cluster, is_simulation, mem_ptr, block_size, chip, core, addr);
            aligned_size -= block_size;
            mem_ptr = (uint8_t*)mem_ptr + block_size;
            addr += block_size;
            size_in_bytes -= block_size;
        }

        // Read/Write last unaligned word
        uint32_t last_unaligned_size = size_in_bytes;
        if (last_unaligned_size != 0) {
            uint32_t temp = 0;
            read_from_device_reg(cluster, is_simulation, &temp, chip, core, addr, sizeof(temp));
            memcpy(&temp, mem_ptr, last_unaligned_size);
            write_to_device_reg(cluster, is_simulation, &temp, sizeof(temp), chip, core, addr);
        }
    }
}

void write_to_device_reg_unaligned(tt::umd::Cluster* cluster, bool is_simulation, const void* mem_ptr,
                                   uint32_t size_in_bytes, ChipId chip, tt::umd::CoreCoord core, uint64_t addr,
                                   bool use_4B_mode) {
    try {
        write_to_device_reg_unaligned_helper(cluster, is_simulation, mem_ptr, size_in_bytes, chip, core, addr,
                                             use_4B_mode);
    } catch (const TimeoutDeviceRegisterException& e) {
        throw;
    } catch (const std::runtime_error& e) {
        if (is_simulation || cluster->get_cluster_description()->is_chip_mmio_capable(chip)) {
            throw;
        }
        _configure_working_active_eth(cluster, chip);
        write_to_device_reg_unaligned_helper(cluster, false, mem_ptr, size_in_bytes, chip, core, addr, use_4B_mode);
    }
}

umd_implementation::umd_implementation(tt::umd::Cluster* cluster, bool is_simulation)
    : cluster(cluster), is_simulation(is_simulation) {
    cached_arc_telemetry_readers.resize(cluster->get_cluster_description()->get_number_of_chips());
}

std::optional<uint32_t> umd_implementation::read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                   uint64_t address) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    uint32_t result;
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    read_from_device_reg_unaligned(cluster, is_simulation, &result, chip_id, target, address, sizeof(result), true);
    return result;
}

std::optional<uint32_t> umd_implementation::write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                    uint64_t address, uint32_t data) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    write_to_device_reg_unaligned(cluster, is_simulation, &data, sizeof(data), chip_id, target, address, true);
    return 4;
}

std::optional<std::vector<uint8_t>> umd_implementation::read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x,
                                                             uint8_t noc_y, uint64_t address, uint32_t size,
                                                             bool use_4B_mode) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    std::vector<uint8_t> result(size);
    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);
    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            read_from_device_reg_unaligned(cluster, is_simulation, result.data() + done, chip_id, target,
                                           address + done, block, use_4B_mode);
            done += block;
        }
        return result;
    }

    read_from_device_reg_unaligned(cluster, is_simulation, result.data(), chip_id, target, address, size, use_4B_mode);
    return result;
}

std::optional<uint32_t> umd_implementation::write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                  uint64_t address, const uint8_t* data, uint32_t size,
                                                  bool use_4B_mode) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    tt::umd::CoreCoord target = cluster->get_soc_descriptor(chip_id).get_coord_at({noc_x, noc_y}, CoordSystem::NOC0);

    // TODO #124: Mitigation for UMD bug #77
    if (!is_chip_mmio_capable(chip_id)) {
        for (uint32_t done = 0; done < size;) {
            uint32_t block = std::min(size - done, 1024u);
            write_to_device_reg_unaligned(cluster, is_simulation, data + done, block, chip_id, target, address + done,
                                          use_4B_mode);
            done += block;
        }
        return size;
    }

    write_to_device_reg_unaligned(cluster, is_simulation, data, size, chip_id, target, address, use_4B_mode);
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
                                                                               const std::vector<uint32_t>& args,
                                                                               std::chrono::milliseconds timeout) {
    // TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
    umd::TTDevice::use_noc1(noc_id == 1);

    uint32_t return_3 = 0;
    uint32_t return_4 = 0;
    int return_code = cluster->arc_msg(chip_id, msg_code, wait_for_done, args, timeout, &return_3, &return_4);
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
    try {
        return read_arc_telemetry_entry_helper(chip_id, telemetry_tag);
    } catch (const std::exception& e) {
        _configure_working_active_eth(cluster, chip_id);
        return read_arc_telemetry_entry_helper(chip_id, telemetry_tag);
    }
}

std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> umd_implementation::get_firmware_version(uint8_t chip_id) {
    tt::umd::semver_t firmware_version(0, 0, 0);
    try {
        firmware_version = tt::umd::get_firmware_version_util(cluster->get_tt_device(chip_id));
    } catch (const std::runtime_error& e) {
        _configure_working_active_eth(cluster, chip_id);
        firmware_version = tt::umd::get_firmware_version_util(cluster->get_tt_device(chip_id));
    }
    return std::make_tuple(firmware_version.major, firmware_version.minor, firmware_version.patch);
}

void umd_implementation::warm_reset(bool is_galaxy_configuration) {
    if (is_galaxy_configuration) {
        tt::umd::WarmReset::ubb_warm_reset();
    } else {
        tt::umd::WarmReset::warm_reset();
    }
}

// Function returns logical coordinates on local device of the active eth core used for remote communication
std::optional<std::tuple<uint8_t, uint8_t>> umd_implementation::get_remote_transfer_eth_core(uint8_t chip_id) {
    tt_xy_pair active_eth_core =
        cluster->get_remote_chip(chip_id)->get_remote_communication()->get_remote_transfer_ethernet_core();
    const tt::umd::CoreCoord eth_translated =
        tt::umd::CoreCoord(active_eth_core.x, active_eth_core.y, CoreType::ETH, CoordSystem::TRANSLATED);
    const tt::umd::CoreCoord eth_logical =
        cluster->get_soc_descriptor(chip_id).translate_coord_to(eth_translated, CoordSystem::LOGICAL);
    return std::make_tuple(eth_logical.x, eth_logical.y);
}
}  // namespace tt::exalens

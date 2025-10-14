// SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <map>
#include <memory>
#include <string>
#include <umd/device/cluster_descriptor.hpp>
#include <umd/device/soc_descriptor.hpp>
#include <umd/device/tt_device/tt_device.hpp>
#include <umd/device/types/xy_pair.hpp>
#include <vector>

#include "ttexalens_implementation.h"
#include "umd/device/chip_helpers/tlb_manager.hpp"

namespace tt::exalens {

class new_umd_implementation : public ttexalens_implementation {
   public:
    new_umd_implementation(const std::string& binary_directory, const std::vector<uint8_t>& wanted_devices,
                           bool initialize_with_noc1);

    std::optional<uint32_t> pci_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                       uint64_t address) override;
    std::optional<uint32_t> pci_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                        uint32_t data) override;
    std::optional<std::vector<uint8_t>> pci_read(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                 uint64_t address, uint32_t size) override;
    std::optional<uint32_t> pci_write(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                      const uint8_t* data, uint32_t size) override;
    std::optional<uint32_t> pci_read32_raw(uint8_t chip_id, uint64_t address) override;
    std::optional<uint32_t> pci_write32_raw(uint8_t chip_id, uint64_t address, uint32_t data) override;
    std::optional<uint32_t> dma_buffer_read32(uint8_t chip_id, uint64_t address, uint32_t channel) override;

    std::optional<std::string> pci_read_tile(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                             uint64_t address, uint32_t size, uint8_t data_format) override;
    std::optional<std::string> get_cluster_description() override;
    std::optional<std::vector<uint8_t>> get_device_ids() override;
    std::optional<std::string> get_device_arch(uint8_t chip_id) override;
    std::optional<std::string> get_device_soc_description(uint8_t chip_id) override;
    std::optional<std::tuple<uint8_t, uint8_t>> convert_from_noc0(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                                                  const std::string& core_type,
                                                                  const std::string& coord_system) override;

    std::optional<std::tuple<int, uint32_t, uint32_t>> arc_msg(uint8_t noc_id, uint8_t chip_id, uint32_t msg_code,
                                                               bool wait_for_done, uint32_t arg0, uint32_t arg1,
                                                               int timeout) override;
    std::optional<uint32_t> read_arc_telemetry_entry(uint8_t chip_id, uint8_t telemetry_tag) override;
    std::optional<std::tuple<uint64_t, uint64_t, uint64_t>> get_firmware_version(uint8_t chip_id) override;
    std::optional<uint64_t> get_device_unique_id(uint8_t chip_id) override;

    std::optional<int> jtag_write32_axi(uint8_t chip_id, uint32_t address, uint32_t data) override;
    std::optional<int> jtag_write32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y, uint64_t address,
                                    uint32_t data) override;
    std::optional<uint32_t> jtag_read32_axi(uint8_t chip_id, uint32_t address) override;
    std::optional<uint32_t> jtag_read32(uint8_t noc_id, uint8_t chip_id, uint8_t noc_x, uint8_t noc_y,
                                        uint64_t address) override;

   private:
    umd::TTDevice* get_device(uint8_t chip_id);
    tt::xy_pair get_noc0_to_device_coords(uint8_t chip_id, uint8_t noc_x, uint8_t noc_y);
    bool is_chip_mmio_capable(uint8_t chip_id);
    tt::umd::ArcTelemetryReader* get_arc_telemetry_reader(uint8_t chip_id);

    std::unique_ptr<umd::ClusterDescriptor> cluster_descriptor;
    std::map<uint8_t, std::string> device_soc_descriptors_yamls;
    std::map<uint8_t, umd::SocDescriptor> soc_descriptors;
    std::map<uint8_t, std::unique_ptr<umd::TTDevice>> devices;
    std::map<uint8_t, std::unique_ptr<umd::TLBManager>> tlb_managers;
    std::map<uint8_t, std::unique_ptr<umd::SysmemManager>> sysmem_managers;
    std::vector<uint8_t> device_ids;
    std::string cluster_descriptor_path;
    std::map<uint8_t, uint64_t> device_id_to_unique_id;
    std::vector<std::unique_ptr<tt::umd::ArcTelemetryReader>> cached_arc_telemetry_readers;
    std::mutex cached_arc_telemetry_readers_mutex;
};

}  // namespace tt::exalens

// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttexalensserver/server.h"

#include <fstream>

#include "ttexalensserver/communication.h"

void tt::exalens::server::process(const tt::exalens::request& base_request) {
    switch (base_request.type) {
        case tt::exalens::request_type::invalid:
            respond_not_supported();
            break;
        case tt::exalens::request_type::ping:
            respond("PONG");
            break;

        case tt::exalens::request_type::pci_read32: {
            auto& request = static_cast<const tt::exalens::pci_read32_request&>(base_request);
            respond(implementation->pci_read32(request.chip_id, request.noc_x, request.noc_y, request.address));
            break;
        }
        case tt::exalens::request_type::pci_write32: {
            auto& request = static_cast<const tt::exalens::pci_write32_request&>(base_request);
            respond(implementation->pci_write32(request.chip_id, request.noc_x, request.noc_y, request.address,
                                                request.data));
            break;
        }
        case tt::exalens::request_type::pci_read: {
            auto& request = static_cast<const tt::exalens::pci_read_request&>(base_request);
            respond(
                implementation->pci_read(request.chip_id, request.noc_x, request.noc_y, request.address, request.size));
            break;
        }
        case tt::exalens::request_type::pci_write: {
            auto& request = static_cast<const tt::exalens::pci_write_request&>(base_request);
            respond(implementation->pci_write(request.chip_id, request.noc_x, request.noc_y, request.address,
                                              request.data, request.size));
            break;
        }
        case tt::exalens::request_type::pci_read32_raw: {
            auto& request = static_cast<const tt::exalens::pci_read32_raw_request&>(base_request);
            respond(implementation->pci_read32_raw(request.chip_id, request.address));
            break;
        }
        case tt::exalens::request_type::pci_write32_raw: {
            auto& request = static_cast<const tt::exalens::pci_write32_raw_request&>(base_request);
            respond(implementation->pci_write32_raw(request.chip_id, request.address, request.data));
            break;
        }
        case tt::exalens::request_type::dma_buffer_read32: {
            auto& request = static_cast<const tt::exalens::dma_buffer_read32_request&>(base_request);
            respond(implementation->dma_buffer_read32(request.chip_id, request.address, request.channel));
            break;
        }

        case tt::exalens::request_type::pci_read_tile: {
            auto& request = static_cast<const tt::exalens::pci_read_tile_request&>(base_request);
            respond(implementation->pci_read_tile(request.chip_id, request.noc_x, request.noc_y, request.address,
                                                  request.size, request.data_format));
            break;
        }
        case tt::exalens::request_type::get_cluster_description:
            respond(implementation->get_cluster_description());
            break;
        case tt::exalens::request_type::convert_from_noc0: {
            auto& request = static_cast<const tt::exalens::convert_from_noc0_request&>(base_request);
            respond(implementation->convert_from_noc0(
                request.chip_id, request.noc_x, request.noc_y, std::string(request.data, request.core_type_size),
                std::string(request.data + request.core_type_size, request.coord_system_size)));
            break;
        }
        case tt::exalens::request_type::get_device_ids:
            respond(implementation->get_device_ids());
            break;
        case tt::exalens::request_type::get_device_arch: {
            auto& request = static_cast<const tt::exalens::get_device_arch_request&>(base_request);
            respond(implementation->get_device_arch(request.chip_id));
            break;
        }
        case tt::exalens::request_type::get_device_soc_description: {
            auto& request = static_cast<const tt::exalens::get_device_soc_description_request&>(base_request);
            respond(implementation->get_device_soc_description(request.chip_id));
            break;
        }
        case tt::exalens::request_type::get_file: {
            auto& request = static_cast<const tt::exalens::get_file_request&>(base_request);
            if (request.size == 0) {
                respond_not_supported();
                break;
            }
            respond(get_file(std::string(request.data, request.size)));
            break;
        }
        case tt::exalens::request_type::arc_msg: {
            auto& request = static_cast<const tt::exalens::arc_msg_request&>(base_request);
            respond(implementation->arc_msg(request.chip_id, request.msg_code, request.wait_for_done, request.arg0,
                                            request.arg1, request.timeout));
            break;
        }

        case tt::exalens::request_type::jtag_read32: {
            auto& request = static_cast<const tt::exalens::jtag_read32_request&>(base_request);
            respond(implementation->jtag_read32(request.chip_id, request.noc_x, request.noc_y, request.address));
            break;
        }

        case tt::exalens::request_type::jtag_write32: {
            auto& request = static_cast<const tt::exalens::jtag_write32_request&>(base_request);
            respond(implementation->jtag_write32(request.chip_id, request.noc_x, request.noc_y, request.address,
                                                 request.data));
            break;
        }

        case tt::exalens::request_type::jtag_read32_axi: {
            auto& request = static_cast<const tt::exalens::jtag_read32_axi_request&>(base_request);
            respond(implementation->jtag_read32_axi(request.chip_id, request.address));
            break;
        }

        case tt::exalens::request_type::jtag_write32_axi: {
            auto& request = static_cast<const tt::exalens::jtag_write32_axi_request&>(base_request);
            respond(implementation->jtag_write32_axi(request.chip_id, request.address, request.data));
            break;
        }
    }
}

// TODO: Add more informative error responses? (Issue #56)
void tt::exalens::server::respond_not_supported() {
    static std::string not_supported = "NOT_SUPPORTED";
    communication::respond(not_supported);
}

void tt::exalens::server::respond(std::optional<std::string> response) {
    if (!response) {
        respond_not_supported();
    } else {
        communication::respond(response.value());
    }
}

void tt::exalens::server::respond(std::optional<uint32_t> response) {
    if (!response) {
        respond_not_supported();
    } else {
        communication::respond(&response.value(), sizeof(response.value()));
    }
}

void tt::exalens::server::respond(std::optional<std::vector<uint8_t>> response) {
    if (!response) {
        respond_not_supported();
    } else {
        communication::respond(response.value().data(), response.value().size());
    }
}

void tt::exalens::server::respond(std::optional<std::tuple<uint8_t, uint8_t>> response) {
    if (!response) {
        respond_not_supported();
    } else {
        std::vector<uint8_t> data;
        data.push_back(std::get<0>(response.value()));
        data.push_back(std::get<1>(response.value()));
        communication::respond(data.data(), data.size());
    }
}

void tt::exalens::server::respond(std::optional<std::tuple<int, uint32_t, uint32_t>> response) {
    if (!response) {
        respond_not_supported();
    } else {
        std::vector<uint32_t> data;
        data.push_back(std::get<0>(response.value()));
        data.push_back(std::get<1>(response.value()));
        data.push_back(std::get<2>(response.value()));
        communication::respond(data.data(), data.size());
    }
}

std::optional<std::vector<uint8_t>> tt::exalens::server::get_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        return {};
    }
    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), {});
}

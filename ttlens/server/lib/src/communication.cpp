// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#include "ttlensserver/communication.h"

#include <memory>
#include <zmq.hpp>

#include "ttlensserver/requests.h"

namespace tt::lens {

// Simple function that forwards background thread to member function
int communication_loop(tt::lens::communication* communication) {
    communication->request_loop();
    return 0;
}

}  // namespace tt::lens

tt::lens::communication::communication() : port(-1) {}

tt::lens::communication::~communication() {
    try {
        stop();
    } catch (...) {
    }
}

void tt::lens::communication::stop() {
    port = -1;
    should_stop = true;
    zmq_context.shutdown();
    if (background_thread) {
        background_thread->join();
        background_thread = nullptr;
    }
    zmq_socket.close();
    zmq_context.close();
}

void tt::lens::communication::start(int port) {
    stop();
    zmq_context = zmq::context_t();
    zmq_socket = zmq::socket_t(zmq_context, zmq::socket_type::rep);
    zmq_socket.bind(std::string("tcp://*:") + std::to_string(port));
    should_stop = false;
    background_thread = std::make_unique<std::thread>(communication_loop, this);
    this->port = port;
}

void tt::lens::communication::request_loop() {
    while (!should_stop) {
        try {
            // Receive message
            bool invalid_message = false;
            zmq::message_t message;
            auto result = zmq_socket.recv(message);

            if (should_stop) break;

            // Get request type
            if (message.size() >= sizeof(request)) {
                auto r = static_cast<const request*>(message.data());

                switch (r->type) {
                    default:
                    case request_type::invalid:
                        invalid_message = true;
                        break;

                    // Requests with no structure - no input except request type
                    case request_type::ping:
                    case request_type::get_cluster_description:
                    case request_type::get_device_ids:
                        invalid_message = message.size() != sizeof(request);
                        break;

                    // Static sized structures
                    case request_type::pci_read32:
                        invalid_message = message.size() != sizeof(pci_read32_request);
                        break;
                    case request_type::pci_write32:
                        invalid_message = message.size() != sizeof(pci_write32_request);
                        break;
                    case request_type::pci_read:
                        invalid_message = message.size() != sizeof(pci_read_request);
                        break;
                    case request_type::pci_read32_raw:
                        invalid_message = message.size() != sizeof(pci_read32_raw_request);
                        break;
                    case request_type::pci_write32_raw:
                        invalid_message = message.size() != sizeof(pci_write32_raw_request);
                        break;
                    case request_type::dma_buffer_read32:
                        invalid_message = message.size() != sizeof(dma_buffer_read32_request);
                        break;
                    case request_type::pci_read_tile:
                        invalid_message = message.size() != sizeof(pci_read_tile_request);
                        break;
                    case request_type::get_harvester_coordinate_translation:
                        invalid_message = message.size() != sizeof(get_harvester_coordinate_translation_request);
                        break;
                    case request_type::get_device_arch:
                        invalid_message = message.size() != sizeof(get_device_arch_request);
                        break;
                    case request_type::get_device_soc_description:
                        invalid_message = message.size() != sizeof(get_device_soc_description_request);
                        break;
                    case tt::lens::request_type::arc_msg:
                        invalid_message = message.size() != sizeof(arc_msg_request);
                        break;

                    case request_type::jtag_read32:
                        invalid_message = message.size() != sizeof(jtag_read32_request);
                        break;
                    case request_type::jtag_write32:
                        invalid_message = message.size() != sizeof(jtag_write32_request);
                        break;
                    case request_type::jtag_read32_axi:
                        invalid_message = message.size() != sizeof(jtag_read32_axi_request);
                        break;
                    case request_type::jtag_write32_axi:
                        invalid_message = message.size() != sizeof(jtag_write32_axi_request);
                        break;

                    // Dynamic sized structures
                    case request_type::pci_write:
                        invalid_message = (message.size() < sizeof(pci_write_request)) ||
                                          (message.size() !=
                                           sizeof(pci_write_request) + static_cast<const pci_write_request*>(r)->size);
                        break;
                    case request_type::get_file:
                        invalid_message = (message.size() < sizeof(get_file_request)) ||
                                          (message.size() !=
                                           sizeof(get_file_request) + static_cast<const get_file_request*>(r)->size);
                        break;
                }

                // Currenly no additional parsing is needed, so we just call process with current request that can be
                // casted safely to correct type
                if (!invalid_message) {
                    process(*r);
                }
            } else {
                invalid_message = true;
            }

            if (invalid_message) {
                respond("BAD_REQUEST");
            }
        } catch (zmq::error_t) {
            // Something went wrong
        } catch (...) {
            // We are guarding exceptions stopping our background thread
        }
    }
}

void tt::lens::communication::respond(const std::string& message) { respond(message.c_str(), message.size()); }

void tt::lens::communication::respond(const void* data, size_t size) { zmq_socket.send(zmq::const_buffer(data, size)); }

bool tt::lens::communication::is_connected() const { return port != -1; }

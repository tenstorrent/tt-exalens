// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
#pragma once

#include <memory>

#include "communication.h"
#include "ttlens_implementation.h"

namespace tt::lens {

// Server class implements tt::lens::communication to process requests and provides
// virtual functions for each request type. If function is not implemented, it should return {},
// which means that command is not supported by the server.
class server : public communication {
   public:
    server(std::unique_ptr<ttlens_implementation> implementation, const std::string& run_dirpath = {})
        : implementation(std::move(implementation)), run_dirpath(run_dirpath) {}

   protected:
    void process(const request& request) override;

   private:
    // Helper functions that wrap optional into tt::lens::communication::respond function calls.
    void respond(std::optional<std::string> response);
    void respond(std::optional<uint32_t> response);
    void respond(std::optional<std::vector<uint8_t>> response);
    void respond(std::optional<std::tuple<int, uint32_t, uint32_t>> response);
    void respond_not_supported();

    virtual std::optional<std::vector<uint8_t>> get_file(const std::string& path);
    virtual std::optional<std::string> get_run_dirpath();

    std::unique_ptr<ttlens_implementation> implementation;
    std::string run_dirpath;
};

}  // namespace tt::lens

#!/usr/bin/env bash
# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
#
# The prebuilt sfpi RISC-V toolchain in build_riscv/sfpi needs glibc >= 2.33,
# but the RHEL8 dev host only has 2.28, so riscv-tt-elf-g++ cannot run natively:
#   /lib64/libc.so.6: version `GLIBC_2.33' not found
# Run the real build.sh inside the tt-metal Ubuntu 22.04 image (glibc 2.35),
# which is already pulled on this host.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${IMAGE:-ghcr.io/tenstorrent/tt-metal/tt-metalium/ubuntu-22.04-dev-amd64:latest}"

exec docker run --rm \
    -v "$REPO":"$REPO" -w "$REPO/rocket_callstack_test" \
    -u "$(id -u):$(id -g)" \
    --entrypoint /bin/bash \
    "$IMAGE" ./build.sh

#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# This script is used to generate the python code for the NoC overlay parameters
# If you have tt-metal in same parent folder as tt-exalens, than you can run this script
# from tt-exalens root
#
# DEVNOTE: At the moment of wormhole version of noc_overlay_parameters.cpp
# is missing to include noc_overlay_parameters.hpp. In order to build, you need to
# include it into the wormhole/noc/noc_overlay_parameters.cpp file.
# Grayskull is not supported.

METAL_HW_INC="../tt-metal/tt_metal/hw/inc/"

g++ -o ./scripts/noc_to_python/codegen-noc-overlay-wormhole \
    -I"$METAL_HW_INC"wormhole/noc \
    scripts/noc_to_python/noc_to_python.cpp \
    "$METAL_HW_INC"wormhole/noc/noc_overlay_parameters.cpp

g++ -o ./scripts/noc_to_python/codegen-noc-overlay-blackhole \
    -I"$METAL_HW_INC"blackhole/noc \
    scripts/noc_to_python/noc_to_python.cpp \
    "$METAL_HW_INC"blackhole/noc/noc_overlay_parameters.cpp

./scripts/noc_to_python/codegen-noc-overlay-wormhole > ./ttexalens/hw/tensix/wormhole/noc_overlay.py
./scripts/noc_to_python/codegen-noc-overlay-blackhole > ./ttexalens/hw/tensix/blackhole/noc_overlay.py

#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# DO NOT RUN DIRECTLY.
set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

############################################################################################
# Running tests

TTEXALENS_COMMANDS='h;wxy 0,0 0 0x123;brxy 0,0 0 64;gpr;d -d 0 logical-tensix virtual;cfg;dreg dbg 0x54;x'

echo -e "${YELLOW}INFO: ${NC}Running simple TTExaLens commands ..."
tt-exalens --test --commands="$TTEXALENS_COMMANDS"

echo -e "${GREEN}Wheel tests passed.${NC}"

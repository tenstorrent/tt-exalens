#! /bin/bash

# DO NOT RUN DIRECTLY.
set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

############################################################################################
# Running tests

TTLENS_COMMANDS='h;wxy 0,0 0 0x123;brxy 0,0 0 64;gpr;d 0 logical-tensix virtual;x'

echo -e "${YELLOW}INFO: ${NC}Running simple TTLens commands ..."
tt-lens --test --commands="$TTLENS_COMMANDS"

echo -e "${GREEN}Wheel tests passed.${NC}"

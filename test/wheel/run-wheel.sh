#! /bin/bash

# DO NOT RUN DIRECTLY.
set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

############################################################################################
# Running tests

DEBUDA_COMMANDS='h;wxy 0,0 0 0x123;brxy 0,0 0 64;cdr;gpr;d 0 netlist nocVirt;x'

echo -e "${YELLOW}INFO: ${NC}Running simple debuda commands ..."
debuda --test --commands="$DEBUDA_COMMANDS"

echo -e "${GREEN}Wheel tests passed.${NC}"
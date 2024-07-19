#! /bin/bash

# DO NOT RUN DIRECTLY.
set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OUTPUT_DIR=

source ${THIS_SCRIPT_DIR}/../test-base.sh

# set default value for TIMEOUT
if [ -z "$TEST_RUN_TIMEOUT" ]; then TEST_RUN_TIMEOUT=500; fi
echo -e "${YELLOW}TEST_RUN_TIMEOUT=$TEST_RUN_TIMEOUT${NC}"

mkdir -p build/test
TMP_OUT_FILE=$(realpath build/test/dbd-out.tmp)
echo -e "${YELLOW}TMP_OUT_FILE=$TMP_OUT_FILE${NC}"

if [ "$1" = "skip-build" ]; then
    echo Skipping build used for CI and tests
elif [ -z "${DEBUDA_HOME}" ]; then
    echo -e "${RED}Error:${NC} DEBUDA_HOME is not set. Please set DEBUDA_HOME to the root of the budabackend repository"
    exit 1
fi

############################################################################################
# Running tests

# TODO: Add the rest of commands ion Limited.
DEBUDA_COMMANDS='h;brxy 0,0 0 64;d 0 netlist nocVirt;x'

RUN_OUTPUT_DIR=${BASE_TEST_DIR}/debuda_test

echo -e "${YELLOW}INFO: ${NC}Running simple debuda commands ..."
debuda --test --commands="$DEBUDA_COMMANDS"

echo -e "${GREEN}Wheel tests passed.${NC}"
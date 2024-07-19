#! /bin/bash

# DO NOT RUN DIRECTLY.
set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BUDA_BUILD_DIR=
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
elif [ -z "${BUDA_HOME}" ]; then
    echo -e "${RED}Error:${NC} BUDA_HOME is not set. Please set BUDA_HOME to the root of the budabackend repository"
    exit 1
elif [ -z "${DEBUDA_HOME}" ]; then
    echo -e "${RED}Error:${NC} DEBUDA_HOME is not set. Please set DEBUDA_HOME to the root of the budabackend repository"
    exit 1
else
    echo -e "${YELLOW}Setting BUDA_BUILD_DIR ...${NC}"
    BUDA_BUILD_DIR="${BUDA_HOME}/build"

    echo -e "${YELLOW}Setting OUTPUT_DIR ...${NC}"
    OUTPUT_DIR=${DEBUDA_HOME}/debuda_test

    echo -e "${YELLOW}Building 'make build_hw'...${NC}"
    cd "${BUDA_HOME}" && make build_hw >> $TMP_OUT_FILE 2>&1

    echo -e "${YELLOW}Building verif/op_tests ...${NC}"
    cd "${BUDA_HOME}" && make verif/op_tests >> $TMP_OUT_FILE 2>&1
fi

NETLIST_FILE=${THIS_SCRIPT_DIR}/../netlists/netlist_multi_matmul_perf.yaml
echo "Running op_tests/test_op on $NETLIST_FILE ...${NC}"
${BUDA_HOME}/build/test/verif/op_tests/test_op --outdir ${OUTPUT_DIR} --netlist $NETLIST_FILE --seed 0 --silicon --timeout $TEST_RUN_TIMEOUT
if [ $? -ne 0 ]; then
    echo "${RED}Error:${NC} Error in running ./build/test/verif/op_tests/test_op"
    exit 1
fi


############################################################################################
# Running tests

SIMPLE_DEBUDA_COMMANDS='h;brxy 0,0 0 64;d 0 netlist nocVirt;x'
COMPLEX_DEBUDA_COMMANDS='op-map;d;d 0 netlist nocTr;q;q input0;q input0 16 16;eq;eq 1;dq;p 130000000000;brxy 0,0 0x0 32 --format i8;cdr;cdr 0,0;srs 0;srs 1;srs 2;ddb 0 32;ddb 0 16 hex8 0,0 0;ddb 0 16 hex16 1,1 0;pcir 0;wxy 0,0 0 0xabcd;full-dump;ha;s 0,0 4;t 1;t 1 --raw;d 0 netlist nocVirt;x'
COMPLEX_NO_TILE_DEBUDA_COMMANDS='op-map;d;d 0 netlist nocTr;q;q input0;q input0 16 16;eq;eq 1;dq;p 130000000000;brxy 0,0 0x0 32 --format i8;cdr;cdr 0,0;srs 0;srs 1;srs 2;ddb 0 32;ddb 0 16 hex8 0,0 0;ddb 0 16 hex16 1,1 0;pcir 0;wxy 0,0 0 0xabcd;full-dump;ha;s 0,0 4;d 0 netlist nocVirt;x'

RUN_OUTPUT_DIR=${BASE_TEST_DIR}/debuda_test

echo -e "${YELLOW}INFO: ${NC}Running simple debuda commands ..."
debuda --test --commands="$SIMPLE_DEBUDA_COMMANDS"

echo -e "${YELLOW}INFO: ${NC}Running complex debuda commands with output dir ..."
debuda --test --commands="$COMPLEX_DEBUDA_COMMANDS" "$OUTPUT_DIR"

echo -e "${YELLOW}INFO: ${NC}Running complex debuda commands with no tile ..."
debuda  --test --commands="$COMPLEX_NO_TILE_DEBUDA_COMMANDS" "$OUTPUT_DIR"

echo -e "${YELLOW}INFO: ${NC}Running complex debuda commands with no output ..."
debuda --test --commands="$COMPLEX_DEBUDA_COMMANDS"

echo -e "${GREEN}Wheel tests passed.${NC}"
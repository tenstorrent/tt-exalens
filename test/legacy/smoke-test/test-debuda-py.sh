#!/bin/bash

set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BUDA_BUILD_DIR=
OUTPUT_DIR=

source ${THIS_SCRIPT_DIR}/../test-base.sh

# set default value for TIMEOUT
if [ -z "$TEST_RUN_TIMEOUT" ]; then TEST_RUN_TIMEOUT=500; fi
echo -e "${YELLOW}TEST_RUN_TIMEOUT=$TEST_RUN_TIMEOUT${NC}"

mkdir -p build/test
touch build/test/ttlens-out.tmp
TMP_OUT_FILE=$(realpath build/test/ttlens-out.tmp)
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

    echo -e "${YELLOW}Building debuda-server-standalone ...${NC}"
    cd "${DEBUDA_HOME}" && make build
fi

echo -e "${YELLOW}Installing Python dependencies ...${NC}"
pip install -r ttlens/requirements.txt
mkdir -p debuda_test

TEST_EXPORT_PATH="debuda_test/tmp"
mkdir -p $TEST_EXPORT_PATH
: "${RM_TEST_FRAGS:=1}"

##################################################################################################################################################
NETLIST_FILE=${BUDA_HOME}/verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml
#
# 1. Sanity
#
# ┌────────┐  0   ┌───────┐  0   ┌─────┐  0   ┌───────┐  0   ┌────────┐
# │ input0 │ ───▶ │ f_op0 │ ───▶ │ op2 │ ───▶ │ d_op3 │ ───▶ │ output │
# └────────┘      └───────┘      └─────┘      └───────┘      └────────┘
#                                  ▲
#                                  │
#                                  │
# ┌────────┐  0   ┌───────┐  1     │
# │ input1 │ ───▶ │ f_op1 │ ───────┘
# └────────┘      └───────┘
echo -e "${YELLOW}Running op_tests/test_op on $NETLIST_FILE ...${NC}"
${BUDA_HOME}/build/test/verif/op_tests/test_op --outdir ${OUTPUT_DIR} --netlist $NETLIST_FILE --seed 0 --silicon --timeout $TEST_RUN_TIMEOUT
if [ $? -ne 0 ]; then
    echo -e "${RED}Error:${NC} Error in running ${BUDA_HOME}/build/test/verif/op_tests/test_op"
    exit 1
fi
source $THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh "netlist_matmul_op_with_fd" --write-cache


##################################################################################################################################################
NETLIST_FILE=${THIS_SCRIPT_DIR}/../netlists/netlist_multi_matmul_perf.yaml
#
# 2. Hang analysis on a passing test
#
#      ┌────────┐  0   ┌───────┐  0   ┌─────────┐  0   ┌──────┐  0   ┌───────┐  0   ┌────────┐
#      │ input0 │ ───▶ │ f_op0 │ ───▶ │ matmul1 │ ───▶ │ add1 │ ───▶ │ d_op3 │ ───▶ │ output │
#      └────────┘      └───────┘      └─────────┘      └──────┘      └───────┘      └────────┘
#                        │              ▲                ▲
#   ┌────────────────────┘              │                │
#   │                                   │                │
#   │  ┌────────┐  0   ┌───────┐  1     │                │
#   │  │ input1 │ ───▶ │ f_op1 │ ───────┘                │
#   │  └────────┘      └───────┘                         │
#   │                    │                               │
#   │                    │ 0                             │
#   │                    ▼                               │
#   │                  ┌───────┐  1   ┌─────────┐  1     │
#   │                  │ recip │ ───▶ │ matmul2 │ ───────┘
#   │                  └───────┘      └─────────┘
#   │   0                               ▲
#   └───────────────────────────────────┘
echo "${YELLOW}Running op_tests/test_op on $NETLIST_FILE ...${NC}"
${BUDA_HOME}/build/test/verif/op_tests/test_op --outdir ${OUTPUT_DIR} --netlist $NETLIST_FILE --seed 0 --silicon --timeout $TEST_RUN_TIMEOUT
if [ $? -ne 0 ]; then
    echo "${RED}Error:${NC} Error in running ./build/test/verif/op_tests/test_op"
    exit 1
fi

source $THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh "netlist_multi_matmul_perf" --write-cache

##################################################################################################################################################
# Test with server cache enabled
source $THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh "netlist_multi_matmul_perf" --cached

##################################################################################################################################################
# Test with no server cache
source $THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh "netlist_multi_matmul_perf"

##################################################################################################################################################
# Test remote on local w/ limited context
source $THIS_SCRIPT_DIR/test-debuda-server-limited.sh "netlist_multi_matmul_perf-remote"

if [[ "$RM_TEST_FRAGS" == "1" ]]; then
    echo -e "${YELLOW}Cleaning up ...${NC}"
    rm -rf $TEST_EXPORT_PATH
    rm debuda_cache.pkl
    # rm debuda-command-history.yaml
fi

echo -e "${GREEN}Done.${NC}"

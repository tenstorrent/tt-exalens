#!/bin/bash
THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TMP_OUT_FILE=build/test/dbd-out.tmp
echo "TMP_OUT_FILE=$TMP_OUT_FILE"

# set default value for TIMEOUT
if [ -z "$TIMEOUT" ]; then TIMEOUT=500; fi
echo "TIMEOUT=$TIMEOUT"

mkdir -p build/test

touch $TMP_OUT_FILE

if [ "$1" = "skip-build" ]; then
    echo Skipping build used for CI and tests
    echo Building debuda-server-standalone ...
    make verif/netlist_tests/debuda-server-standalone >> $TMP_OUT_FILE
else
    echo make build_hw
    make build_hw
    echo Building verif/op_tests ...
    make verif/op_tests >> $TMP_OUT_FILE
    echo Building debuda-server-standalone ...
    make verif/netlist_tests/debuda-server-standalone >> $TMP_OUT_FILE
fi

pip install sortedcontainers prompt_toolkit pyzmq tabulate rapidyaml deprecation
mkdir -p debuda_test

NETLIST_FILE=verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml

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
echo Running op_tests/test_op on $NETLIST_FILE ...
./build/test/verif/op_tests/test_op --outdir debuda_test --netlist $NETLIST_FILE --seed 0 --silicon --timeout $TIMEOUT >> $TMP_OUT_FILE
if [ $? -ne 0 ]; then
    echo Error in running ./build/test/verif/op_tests/test_op
    exit 1
fi

$THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh

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
NETLIST_FILE=dbd/test/netlists/netlist_multi_matmul_perf.yaml
echo Running op_tests/test_op on $NETLIST_FILE ...
./build/test/verif/op_tests/test_op --outdir debuda_test --netlist $NETLIST_FILE --seed 0 --silicon --timeout $TIMEOUT >> $TMP_OUT_FILE
if [ $? -ne 0 ]; then
    echo Error in running ./build/test/verif/op_tests/test_op
    exit 1
fi

$THIS_SCRIPT_DIR/test-run-all-debuda-commands.sh
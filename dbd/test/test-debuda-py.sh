#!/bin/bash
TMP_OUT_FILE=build/test/dbd-out.tmp

touch $TMP_OUT_FILE

if [ "$1" = "skip-build" ]; then
    echo Skipping build used for CI and tests
    # Hack - CI will copy only build directory.
    # We should either move debuda-stub to build directory,
    # or extend CI to pickup debuda binaries from dbd directory.
    # cp build/bin/debuda-stub dbd/debuda-stub
else
    echo make build_hw
    make build_hw
    echo Building verif/op_tests ...
    make verif/op_tests >> $TMP_OUT_FILE
    echo Building debuda-server-standalone ...
    make verif/netlist_tests/debuda-server-standalone >> $TMP_OUT_FILE
fi

pip install prompt_toolkit sortedcontainers

mkdir -p debuda_test

NETLIST_FILE=verif/op_tests/netlists/netlist_matmul_op_with_fd.yaml

echo Running op_tests/test_op on $NETLIST_FILE ...
./build/test/verif/op_tests/test_op --outdir debuda_test --netlist $NETLIST_FILE --seed 0 --silicon --timeout 500 >> $TMP_OUT_FILE
if [ $? -ne 0 ]; then
    echo Error in running ./build/test/verif/op_tests/test_op
    exit 1
fi

echo Running debuda.py ...
dbd/debuda.py debuda_test --netlist $NETLIST_FILE --commands "s 1 1 8;exit"
if [ $? -ne 0 ]; then
    echo Error in running dbd/debuda.py
    exit 2
fi

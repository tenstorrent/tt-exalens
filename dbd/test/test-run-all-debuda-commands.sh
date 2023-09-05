#!/bin/bash

# --test is used to prevent main REPL loop from catching the exception. Instead,
# it will be propagated back to the shell as a non-zero exit code.
run_debuda() {
    timeout 30 dbd/debuda.py debuda_test --test --commands "$1"
    if [ $? -ne 0 ]; then
        echo "***"
        echo "Error: test failed while running dbd/debuda.py with commands: $1"
        echo "***"
        exit 2
    fi
}

# Simple tests do detect only the most basic functionality
run_debuda "op-map; d; d 0 netlist nocTr; exit"
run_debuda "q; q input0; q input0 16 16; eq; eq 1; dq; p 130000000000; exit"
run_debuda "brxy 1 1 1 1 1; cdr; cdr 1 1; srs 0; srs 1; srs 2; exit"
run_debuda "ddb 0 32; ddb 0 16 hex8 1 1 0; ddb 0 16 hex16 2 2 0; exit"
run_debuda "pcir 0; wxy 1 1 0 0xabcd; rxy 1 1 0; exit"
run_debuda "full-dump; export; ha; exit"

# if [ "$ARCH_NAME" = "grayskull" ]; then
#     run_debuda "s 1 1 4; t 1 0; t 1 1; exit"
# else
#     run_debuda "s 20 18 4; t 1 0; t 1 1; exit"
# fi
# run_debuda "gpr"
# gpr needs a core to be hung. To reproduce:
#   git apply dbd/test/inject-errors/sfpu_reciprocal-infinite-spin-wormhole_b0.patch
#   ./build/test/verif/op_tests/test_op --netlist dbd/test/netlists/netlist_multi_matmul_perf.yaml --seed 0 --silicon --timeout 60
#   ctrl-C
# Then find a valid core (using op-map) and try gpr on it.

echo ""
echo "All tests passed!"
#!/bin/bash
RUN_DIR=dbd/run           # Where to store run results
EXPECTED_COVER_PCT=80     # Complain when coverage is below this percantage
COVERAGE_RUN="coverage run --include=dbd/**"
# DEBUDA_CMD="dbd/debuda.py --stream-cache" # For faster debugging
DEBUDA_CMD="dbd/debuda.py"
set -o pipefail # Propagate exit codes through pipes

# Checks whether Debuda run failed
check_logfile_exit_code () {
    log_file="$1"
    DBD_EXIT_CODE=`cat $log_file | grep "Exiting with code " | awk '{print $4}'`
    if [ "$DBD_EXIT_CODE" == "0" ]; then echo "Debuda run OK"; else
        echo "FAIL: Debuda run failed with exit code '$DBD_EXIT_CODE' (see $log_file)";
        exit $DBD_EXIT_CODE
    fi
}

# Run one coverrage command
coverage_run () {
    log_file=$1
    cov_command="$2"
    cov_args="$3"
    debuda_cmd="$4"
    debuda_commands_arg="$6"
    $cov_command $cov_args $debuda_cmd "$5" "$debuda_commands_arg" | tee "$log_file"
    check_logfile_exit_code "$log_file"
}

# Setup environment
mkdir -p $RUN_DIR
sudo pip install coverage
make -j8 && make -j8 verif/op_tests/test_op
device/bin/silicon/reset.sh
# Apply patch to cause a hang
git apply dbd/test/inject-errors/sfpu_reciprocal-infinite-spin.patch

# # Run the test
./build/test/verif/op_tests/test_op --netlist dbd/test/netlists/netlist_multi_matmul_perf.yaml --seed 0 --silicon --timeout 10

# Run Debuda
## This debuda run command sequence is supposed to return exact same text always
coverage_run $RUN_DIR/coverage-exact-match.log "$COVERAGE_RUN" ""       "$DEBUDA_CMD" --commands "hq; dq; abs; abs 1; s 1 1 8; cdr 1 1; c 1 1; d; t 1 0; d 0; d 1; cdr 1 1; b 10000030000; 0; 0; eq; brxy 1 1 0 0; help; x"
## This command might read stuff that is not always the same
coverage_run $RUN_DIR/coverage-fuzzy-match.log "$COVERAGE_RUN" --append "$DEBUDA_CMD" --commands "srs 0; srs 1; srs 2; t 1 1; op-map; x"

# Undo the patch
git apply -R dbd/test/inject-errors/sfpu_reciprocal-infinite-spin.patch

# Check coverage
coverage report --sort=cover | tee $RUN_DIR/coverage-report.txt
COVER_PCT=`cat $RUN_DIR/coverage-report.txt | tail -n 1 | awk '{print $4}' | tr -d "%"`
if (( $COVER_PCT < $EXPECTED_COVER_PCT )); then echo "FAIL: Coverage ($COVER_PCT) is smaller then expected ($EXPECTED_COVER_PCT)"; exit 1; fi

# Compare the output with the expected
compare_files="$RUN_DIR/coverage-exact-match.log dbd/test/expected-results/coverage-exact-match.expected"
echo Comparing $compare_files
diff $compare_files
compare_exit_code="$?"
if [ "$compare_exit_code" == "0" ]; then echo PASS; else echo FAIL; exit "$compare_exit_code"; fi
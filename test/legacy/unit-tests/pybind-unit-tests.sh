#! /bin/bash

set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

echo -e "${YELLOW}Running pybind unit tests ...${NC}"

# Run pybind unit tests
make dbd_pybind_unit_tests_run_only
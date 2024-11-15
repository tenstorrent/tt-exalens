#! /bin/bash

set -e

function big_echo {
	echo -e "----------------------------------------------------------------"
	echo -e "\n\n"
	echo -e "${YELLOW}    $1 ${NC}"
	echo -e "\n\n"
	echo -e "----------------------------------------------------------------"
}

BASE_TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${BASE_TEST_DIR}/test-base.sh

big_echo "BUILDING TTLENS"
make build


big_echo "RUNNING SMOKE TEST"
source ${BASE_TEST_DIR}/smoke-test/test-debuda-py.sh


big_echo "RUNNING UNIT TESTS"
source ${BASE_TEST_DIR}/unit-tests/server-unit-tests.sh
source ${BASE_TEST_DIR}/unit-tests/coverage-run.sh
# Python tests can also be run separately:
# source ${BASE_TEST_DIR}/unit-tests/pybind-unit-tests.sh
# source ${BASE_TEST_DIR}/unit-tests/base-unit-tests.sh


big_echo "RUNNING WHEEL TEST"
source ${BASE_TEST_DIR}/wheel-test/wheel-test.sh
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

echo ""
echo ""
echo -e "${RED}This script is intended for running all tests in the project locally.${NC}"
echo ""
echo ""

big_echo "BUILDING DEBUDA" 
make clean
make build

big_echo "BUILDING C++ TESTS"
make dbd/server_tests
make dbd/pybind_tests

big_echo "RUNNING C++ TESTS"
make dbd_server_unit_tests_run_only

big_echo "RUNNING PYTHON DBD TESTS"
python3 -m unittest discover -v -t . -s test/dbd -p *test*.py

big_echo "RUNNING PYTHON APP TESTS"
python3 -m unittest discover -v -t . -s test/app -p *test*.py

big_echo "RUNNING WHEEL TESTS"
source ${BASE_TEST_DIR}/wheel/wheel-test.sh
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


big_echo "BUILDING DEBUDA" 
make clean
make build

big_echo "RUNNING C++ TESTS"
make dbdtests

big_echo "RUNNING PYTHON TESTS"
python -m unittest discover -v -t . -s test/dbd -p *test*.py
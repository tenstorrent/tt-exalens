#! /bin/bash

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

echo -e "${YELLOW}Running wheel test ...${NC}"

if ! test -d ${THIS_SCRIPT_DIR}/.venv; then
	echo -e "Creating virtual environment ..."
	python -m venv ${THIS_SCRIPT_DIR}/.venv
fi

echo -e "Activating virtual environment ..."
source ${THIS_SCRIPT_DIR}/.venv/bin/activate

echo -e "Installing wheel ..."
pip3 install --upgrade pip
pip3 install --upgrade build
pip3 install --upgrade setuptools
pip3 install wheel

echo -e "Building debuda ..."
make build

echo -e "Building wheel ..."
make dbd/wheel_release

echo -e "Installing wheel ..."
pip install build/debuda_wheel/*.whl

echo -e " --- Running wheel test ---"
source ${THIS_SCRIPT_DIR}/run-wheel.sh

: "${DELETE_VENV:=0}"
if [ ${DELETE_VENV} == "1" ]; then
	echo -e "Deleting environment ..."
	deactivate
	rm -rf ${THIS_SCRIPT_DIR}/.venv
fi
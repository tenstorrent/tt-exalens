#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Define color variables
source ${THIS_SCRIPT_DIR}/../test-base.sh

echo -e "${YELLOW}Running wheel test ...${NC}"

if ! test -d ${THIS_SCRIPT_DIR}/.venv; then
    echo -e "Creating virtual environment ..."
    python3 -m venv ${THIS_SCRIPT_DIR}/.venv
fi

echo -e "Activating virtual environment ..."
source ${THIS_SCRIPT_DIR}/.venv/bin/activate || { echo "Activation failed, removing .venv"; rm -rf ${THIS_SCRIPT_DIR}/.venv; exit 1; }

echo -e "Installing wheel ..."
pip3 install --upgrade pip
pip3 install --upgrade build
pip3 install --upgrade setuptools
pip3 install typing-extensions
pip3 install wheel

echo -e "Building TTExaLens ..."
make

echo -e "Building wheel ..."
make wheel

echo -e "Installing wheel ..."
pip install build/ttexalens_wheel/*.whl

echo -e " --- Running wheel test ---"
source ${THIS_SCRIPT_DIR}/run-wheel.sh

deactivate

: "${DELETE_VENV:=1}"
if [ ${DELETE_VENV} == "1" ]; then
	echo -e "Deleting environment ..."
	rm -rf ${THIS_SCRIPT_DIR}/.venv
fi

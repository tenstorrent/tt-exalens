#!/bin/bash
set -eo pipefail

if [ -z "$PYTHON_ENV_DIR" ]; then
    PYTHON_ENV_DIR="$(pwd)/.venv"
fi

echo "Creating virtual env in: $PYTHON_ENV_DIR"
python3 -m venv $PYTHON_ENV_DIR

source $PYTHON_ENV_DIR/bin/activate

echo "Updating pip"
python3 -m pip install --upgrade pip

echo "Setting up virtual env"
python3 -m pip install setuptools wheel

echo "Installing dev dependencies"
python3 -m pip install -r $(pwd)/dbd/requirements.txt
python3 -m pip install -r $(pwd)/dbd/tests/test_requirements.txt

#!/bin/bash
set -eo pipefail

if [ -z "$PYTHON_ENV_DIR" ]; then
    PYTHON_ENV_DIR="$(pwd)/.venv"
fi

DBD_INSTALL=${DBD_INSTALL:-}
TEST_INSTALL=${TEST_INSTALL:-}
WHEEL_INSTALL=${WHEEL_INSTALL:-}

echo "Creating virtual env in: $PYTHON_ENV_DIR"
python3 -m venv $PYTHON_ENV_DIR

source $PYTHON_ENV_DIR/bin/activate

echo "Ensuring pip is installed and up-to-date"
python3 -m ensurepip
pip install --upgrade pip

if [ -n "$DBD_INSTALL" ]; then
    echo "Installing dbd dependencies..."
    pip install -r dbd/requirements.txt
fi

if [ -n "$TEST_INSTALL" ]; then
    echo "Installing test dependencies..."
    pip install -r test/test_requirements.txt
fi

if [ -n "$WHEEL_INSTALL" ] then
    echo "Installing wheel dependencies..."
    pip install -r wheel build setuptools
fi
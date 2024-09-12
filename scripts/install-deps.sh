#! /bin/bash
set -eo pipefail

DBD_INSTALL=${DBD_INSTALL:-}
TEST_INSTALL=${TEST_INSTALL:-}
WHEEL_INSTALL=${WHEEL_INSTALL:-}

if [ -n "$DBD_INSTALL" ]; then
    echo "Installing dbd dependencies..."
    python -m pip install -r dbd/requirements.txt
fi

if [ -n "$TEST_INSTALL" ]; then
    echo "Installing test dependencies..."
    python -m pip install -r test/test_requirements.txt
fi

if [ -n "$WHEEL_INSTALL" ] then
    echo "Installing wheel dependencies..."
    python -m pip install -r wheel build setuptools
fi

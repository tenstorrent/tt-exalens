#! /bin/bash
set -eo pipefail

TTLENS_INSTALL=${TTLENS_INSTALL:-}
TEST_INSTALL=${TEST_INSTALL:-}
WHEEL_INSTALL=${WHEEL_INSTALL:-}

if [ -n "$TTLENS_INSTALL" ]; then
    echo "Installing ttlens dependencies..."
    pip install -r ttlens/requirements.txt
fi

if [ -n "$TEST_INSTALL" ]; then
    echo "Installing test dependencies..."
    pip install -r test/test_requirements.txt
fi

if [ -n "$WHEEL_INSTALL" ]; then
    echo "Installing wheel dependencies..."
    pip install -r wheel build setuptools
fi

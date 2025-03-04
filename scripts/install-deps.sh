#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

set -eo pipefail

TTEXALENS_INSTALL=${TTEXALENS_INSTALL:-}
TEST_INSTALL=${TEST_INSTALL:-}
WHEEL_INSTALL=${WHEEL_INSTALL:-}

if [ -n "$TTEXALENS_INSTALL" ]; then
    echo "Installing ttexalens dependencies..."
    pip install -r ttexalens/requirements.txt
fi

if [ -n "$TEST_INSTALL" ]; then
    echo "Installing test dependencies..."
    pip install -r test/test_requirements.txt
fi

if [ -n "$WHEEL_INSTALL" ]; then
    echo "Installing wheel dependencies..."
    pip install -r wheel build setuptools
fi

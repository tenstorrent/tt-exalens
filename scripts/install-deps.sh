#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

set -eo pipefail

EXALENS_HOME=$(dirname "$0")/..

# Parse command line arguments
PIP_QUIET=""
if [[ "$1" == "--quiet" || "$1" == "-q" ]]; then
    PIP_QUIET="-q"
fi

echo "Installing ttexalens dependencies..."
pip install $PIP_QUIET --extra-index-url https://test.pypi.org/simple/ -r $EXALENS_HOME/ttexalens/requirements.txt

echo "Installing ttexalens dev dependencies..."
pip install $PIP_QUIET -r $EXALENS_HOME/ttexalens/dev-requirements.txt

echo "Installing test dependencies..."
pip install $PIP_QUIET -r $EXALENS_HOME/test/test_requirements.txt

echo "Installing wheel dependencies..."
pip install $PIP_QUIET wheel build setuptools

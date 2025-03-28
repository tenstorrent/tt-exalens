#!/bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

set -eo pipefail

if [ -z "$PYTHON_ENV_DIR" ]; then
    PYTHON_ENV_DIR="$(pwd)/.venv"
fi

echo "Creating virtual env in: $PYTHON_ENV_DIR"
python3 -m venv $PYTHON_ENV_DIR

source $PYTHON_ENV_DIR/bin/activate

echo "Ensuring pip is installed and up-to-date"
python3 -m ensurepip
pip install --upgrade pip

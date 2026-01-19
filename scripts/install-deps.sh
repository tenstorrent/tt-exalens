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

# Determine whether to use uv or pip
if command -v uv &>/dev/null; then
  PIP_CMD="uv pip"
  # uv needs --index-strategy unsafe-best-match to check all indexes for best version
  # (test.pypi.org has older versions of some transitive deps like deprecation)
  UV_INDEX_STRATEGY="--index-strategy unsafe-best-match"
  echo "Using uv for package management"
else
  PIP_CMD="python3 -m pip"
  UV_INDEX_STRATEGY=""
  echo "uv not found, falling back to pip"
fi

echo "Installing ttexalens dependencies..."
$PIP_CMD install $PIP_QUIET --extra-index-url https://test.pypi.org/simple/ -r $EXALENS_HOME/ttexalens/requirements.txt

echo "Installing ttexalens dev dependencies..."
$PIP_CMD install $PIP_QUIET -r $EXALENS_HOME/ttexalens/dev-requirements.txt

echo "Installing test dependencies..."
$PIP_CMD install $PIP_QUIET -r $EXALENS_HOME/test/test_requirements.txt

echo "Installing wheel dependencies..."
$PIP_CMD install $PIP_QUIET wheel build setuptools

echo "Installing pip..."
$PIP_CMD install $PIP_QUIET --upgrade pip

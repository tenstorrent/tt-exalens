#! /bin/bash

set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

echo -e "${YELLOW}Running unit tests coverage ...${NC}"

# Run unit tests coverage
coverage run --branch --include=ttlens/** -m pytest ttlens/ --junitxml=${TTLENS_HOME}/debuda_test/debuda_tests_grayskull.xml
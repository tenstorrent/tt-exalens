#! /bin/bash

set -e

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source ${THIS_SCRIPT_DIR}/../test-base.sh

echo -e "${YELLOW}Running base unit tests ...${NC}"

# Run base unit tests
python3 -m unittest discover -s ./ttlens -p *test*.py

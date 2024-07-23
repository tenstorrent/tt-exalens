#!/bin/bash

set -e

# Define color variables
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # No Color


if [ -z "$DEBUDA_HOME" ]; then
	echo -e "${RED}Error:${NC} DEBUDA_HOME is not set. Trying to set it automatically..."
	DEBUDA_HOME="$(git rev-parse --show-toplevel)"
	echo -e "${GREEN}Success:${NC} DEBUDA_HOME is set to $DEBUDA_HOME"
	exit 1
fi

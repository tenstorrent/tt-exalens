#!/bin/bash

set -e

# Define color variables
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # No Color


if [ -z "$DEBUDA_HOME" ]; then
	echo -e "${RED}Error:${NC} DEBUDA_HOME is not set. Please set DEBUDA_HOME to the root of the debuda repository"
	exit 1
fi

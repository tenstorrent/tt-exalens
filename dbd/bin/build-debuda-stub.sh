#!/bin/bash
# Minimal compile and test for silicon driver
set -e
TARGET_EXE=build/test/verif/netlist_tests/debuda-server-standalone

echo Compiling $TARGET_EXE
make verif/netlist_tests/debuda-server-standalone
echo To run debuda_stub enter: $TARGET_EXE
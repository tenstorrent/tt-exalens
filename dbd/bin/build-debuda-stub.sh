#!/bin/bash
# Minimal compile and test for silicon driver
set -e
TARGET_EXE=dbd/debuda-stub

echo Compiling dependencies
make device
make model

echo Compiling $TARGET_EXE
g++ -DFMT_HEADER_ONLY  -Ithird_party/fmt/ -Isrc/firmware/riscv/grayskull/ -Icommon/model -Idevice/grayskull/ -Inetlist -Imodel -I. -Icore_graph_lib device/tt_silicon_driver_debuda_stub.cpp -std=gnu++17 -Isrc/firmware/riscv/ -Iversim/grayskull/headers/vendor/yaml-cpp/include ./device/lib/libyaml-cpp.a ./build/lib/libmodel.a ./build/lib/libdevice.so -lzmq -lpthread -o $TARGET_EXE

echo To run debuda_stub enter: $TARGET_EXE

# TT_PCI_LOG_LEVEL=1 $TARGET_EXE

# Copy debuda-stub to build directory
mkdir -p build
mkdir -p build/bin
cp dbd/debuda-stub build/bin/debuda-stub

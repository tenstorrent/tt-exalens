#!/bin/bash
set -e

# Validate git root
[ -d .git ] || { echo "ERROR: Not in git root"; exit 1; }

# Validate parameter
[ $# -eq 1 ] || { echo "ERROR: Need output directory"; exit 1; }
DBD_OUT=`realpath $1`

# Create staging folder
STAGING_DIR="$DBD_OUT/staging"
rm -rf $STAGING_DIR
mkdir -p $STAGING_DIR

# Build
make -j32 build_hw verif/op_tests dbd

# Copy LIB_FILES
LIB_FILES="./build/lib/libtt.so ./build/lib/libdevice.so"
for i in $LIB_FILES; do cp -f $i $STAGING_DIR; done

# Compile debuda-server-standalone (shorten as needed)
# HACK: Build the debuda-server-standalone with relative path to libtt
g++ -MMD -Wdelete-non-virtual-dtor -Wreturn-type -Wswitch -Wuninitialized -Wno-unused-parameter -Wmaybe-uninitialized -I. -DTT_ENABLE_CODE_TIMERS -mavx2 -mfma -DFMT_HEADER_ONLY -Ithird_party/fmt -DPERF_DUMP_LEVEL=0 -DPERF_DUMP_LEVEL=0 \
    -DPERF_DUMP_LEVEL=0 --std=c++17 -fvisibility-inlines-hidden -Isrc/firmware/riscv/wormhole -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include \
    -Isrc/firmware/riscv/wormhole -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Icommon -Imodel -Inetlist -Iumd -Inetlist -Imodel -Imodel/ops -I. -Ithird_party/json/ -Icommon/model/ -Icommon -Isrc/firmware/riscv/wormhole \
    -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/json -Iumd -Isrc/firmware/riscv/wormhole -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include \
    -Imodel  -Inetlist -Iops -Iperf_lib -Icommon -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include -Iumd -I./loader -I./runtime -I./. -I./umd -I./umd/device/wormhole/ -Isrc/firmware/riscv/wormhole \
    -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include -Imodel -Inetlist -Icommon -Iumd \
    -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include -Isrc/firmware/riscv/wormhole_b0/ -Isrc/firmware/riscv/wormhole -Isrc/firmware/riscv/wormhole/wormhole_b0_defines \
    -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include -Icommon -Igolden -Iops -Inetlist -Inetlist -Imodel -Imodel/ops -I. -Ithird_party/json/ -Icommon/model/ -Icommon -Isrc/firmware/riscv/wormhole \
    -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/json -Iumd -Iumd  -Isrc/firmware/riscv/wormhole -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include \
    -Imodel  -Inetlist -Iops -Iperf_lib -Icommon -Ithird_party/confidential_tenstorrent_modules/versim/wormhole_b0/headers/vendor/yaml-cpp/include -Iumd -Inetlist -Imodel -Imodel/ops -I. -Ithird_party/json/ -Icommon/model/ -Icommon -Isrc/firmware/riscv/wormhole \
    -Isrc/firmware/riscv/wormhole/wormhole_b0_defines -Ithird_party/json -Iumd  -Iverif/netlist_tests -Iverif  -o $STAGING_DIR/debuda-server-standalone ./build/obj/verif/netlist_tests/debuda-server-standalone.o ./build/lib/libtt.so ./build/lib/libverif.a  \
    -Wl,-rpath,.:umd/build/lib -L./build/lib -Lumd/build/lib -ldl -lstdc++ -ltt -ldevice -lop_model -lstdc++fs -lpthread -lyaml-cpp -lcommon -lhwloc -lyaml-cpp -lpthread -lboost_fiber -lboost_date_time -lboost_filesystem -lboost_iostreams -lboost_serialization \
    -lboost_timer -lboost_program_options -lzmq

# Copy compiled files and others to staging
cp dbd/README.txt dbd/debuda.py dbd/tt* $STAGING_DIR
cp build/dbd/debuda-help.pdf $STAGING_DIR/debuda-manual.pdf

# Filter NON_DEV_COMMAND_FILES
NON_DEV_COMMAND_FILES=""
for i in `ls dbd/debuda_commands -p | grep -v /`; do
    grep -q '"type" : "dev"' dbd/debuda_commands/$i || NON_DEV_COMMAND_FILES="$NON_DEV_COMMAND_FILES dbd/debuda_commands/$i"
done
mkdir -p $STAGING_DIR/debuda_commands
cp $NON_DEV_COMMAND_FILES $STAGING_DIR/debuda_commands

# Run strip-debug-only-code.py
dbd/bin/strip-debug-only-code.py $STAGING_DIR

# Create zip
cd $STAGING_DIR
zip $DBD_OUT/debuda.zip * debuda_commands/* -x "debuda_commands/*test*" -x "debuda_commands/__pycache__"
cd -

# move the file to /home_mnt/ihamer/work/debuda-releases and rename it to inlude date and git hash
NAME=/home_mnt/ihamer/work/debuda-releases/debuda-`date +%Y%m%d`-`git rev-parse --short HEAD`.zip
cp -f $DBD_OUT/debuda.zip $NAME

# Show the contents of the dir in the order of last modified being at the bottom
echo "Contents of /home_mnt/ihamer/work/debuda-releases: "
ls -ltr /home_mnt/ihamer/work/debuda-releases

# Echo the target file
echo
echo "Released to: $NAME"
echo "DONE"

# Cleanup
# rm -rf $STAGING_DIR

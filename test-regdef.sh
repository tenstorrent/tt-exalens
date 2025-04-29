#!/bin/bash

# Use lspci to see if we have WH or BH device:
# BLACKHOLE: [ 0 ] ~  > lspci -d 1e52:
# 0c:00.0 Processing accelerators: Device 1e52:b140
# WORMHOLE: [ 0 ] ~/work/tt-exalens  > lspci -d 1e52:
# 31:00.0 Processing accelerators: Device 1e52:401e (rev 01)

LSPCI=`lspci -d 1e52:`

if [[ $LSPCI == *"b140"* ]]; then
    DEV="BH"
elif [[ $LSPCI == *"401e"* ]]; then
    DEV="WH"
fi

if [ -z "$DEV" ]; then
    echo "Unknown device"
    exit 1
fi

if [ "$DEV" == "BH" ]; then
    export REGDEF=../regdef/arc.json
elif [ "$DEV" == "WH" ]; then
    export REGDEF=../regdef/data/wormhole/axi-noc.yaml
fi

python3 -m unittest test/ttexalens/unit_tests/test_regdef_load.py -v
python3 -m unittest test/ttexalens/unit_tests/test_regdef_real_access.py -v

#!/bin/bash
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# declare -a ARCH_LIST=("grayskull" "wormhole")
declare -a ARCH_LIST=("grayskull")
OUT_FILE="local-regression-dbd-run.txt"

if [ -f "$OUT_FILE" ]; then rm $OUT_FILE; fi
for ARCH_NAME in ${ARCH_LIST[@]}; do
    echo Testing $ARCH_NAME
    ARCH_NAME=$ARCH_NAME $SCRIPTPATH/run-offline-tests.sh >> $OUT_FILE
    EXIT_CODE=$?
    if [ "$EXIT_CODE" != "0" ]; then echo "FAIL"; exit $EXIT_CODE; fi
done
echo PASS. See $OUT_FILE for output
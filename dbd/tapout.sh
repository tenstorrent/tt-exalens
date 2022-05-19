#!/bin/bash
if [[ $# -eq 0 ]] ; then
    echo Missing argument
    exit 1
fi

TMP_OUT_DIR=debuda_test
mkdir $TMP_OUT_DIR

export ARCH_NAME="grayskull"

netlist_filename=$(echo $1 | sed -e 's/.*\(--netlist[ ]*[^ ]*\).*$/\1/' | awk '{print $2}')
base_filename=$(basename $netlist_filename)
i=0
if [ $2 == "--single" ]
then
    modified_netlist_filename=$TMP_OUT_DIR'/'$base_filename
    ./build/bin/dbd_modify_netlist --netlist $netlist_filename --o $modified_netlist_filename --g >dev\null
    command=$(echo $1 | sed -e 's|'$netlist_filename'|'$modified_netlist_filename'|')
    echo $command'>'$modified_netlist_filename'.log'
    $command > $modified_netlist_filename'.log'
    printf "Log is stored in $modified_netlist_filename.log\n"
else
    ./build/bin/dbd_modify_netlist --netlist $netlist_filename | grep "DBG_" | while read line
    do
        ((i++))
        # generate netlist by appending new output queue to netlist
        modified_netlist_filename=$TMP_OUT_DIR'/'$i'_'$base_filename
        echo $line | awk '{print $1}'
        sed "/queues:.*/a \ \ $line" $netlist_filename > $modified_netlist_filename

        command=$(echo $1 | sed -e 's|'$netlist_filename'|'$modified_netlist_filename'|')
        echo $command
        $command >> $modified_netlist_filename'.log'
        if [ "$?" -ne 0 ]
        then
            echo "FAILED!"
        else
            echo "PASSED"
        fi
    done
fi
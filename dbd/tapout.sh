#!/bin/bash
if [[ $# -eq 0 ]] ; then
    echo Missing argument
    exit 1
fi

TMP_OUT_DIR=debuda_test
mkdir -p $TMP_OUT_DIR

export ARCH_NAME="grayskull"

netlist_filename=$(echo $1 | sed -e 's/.*\(--netlist[ ]*[^ ]*\).*$/\1/' | awk '{print $2}')
base_filename=$(basename $netlist_filename)

if [ "$2" == "--single" ]
then
    #reset silicon
    device/bin/silicon/reset.sh

    # create filename for new netlist
    modified_netlist_filename=$TMP_OUT_DIR'/'$base_filename

    # create netlist file with added all operations to output
    ./build/bin/dbd_modify_netlist --netlist $netlist_filename --o $modified_netlist_filename --g >dev\null

    # format new test command
    command=$(echo $1 | sed -e 's|'$netlist_filename'|'$modified_netlist_filename'|')
    echo $command'>'$modified_netlist_filename'.log'

    # run new test command and save log
    $command > $modified_netlist_filename'.log'

    printf "Log is stored in $modified_netlist_filename.log\n"
else
    i=0
    ./build/bin/dbd_modify_netlist --netlist $netlist_filename | grep "DBG_" | while read line
    do
        ((i++))
        #reset silicon before each run
        device/bin/silicon/reset.sh

        # create filename for new netlist
        modified_netlist_filename=$TMP_OUT_DIR'/'$i'_'$base_filename

        # log operation name that is tapped out
        echo $line | awk '{print $1}'

        # create new netlist file with added output queue for one operation
        sed "/queues:.*/a \ \ $line" $netlist_filename > $modified_netlist_filename

        # format new test command
        command=$(echo $1 | sed -e 's|'$netlist_filename'|'$modified_netlist_filename'|')
        echo $command

        # run new test command and save log
        $command > $modified_netlist_filename'.log'

        if [ "$?" -ne 0 ]
        then
            echo "FAILED! Check log file $modified_netlist_filename.log"
        else
            echo "PASSED"
        fi
    done
fi
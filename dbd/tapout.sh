#!/bin/bash
if [[ $# -eq 0 ]] ; then
    echo Missing argument
    exit 1
fi

TMP_OUT_DIR=debuda_test
mkdir -p $TMP_OUT_DIR

TMP_FAILED_OP_FILE=$TMP_OUT_DIR'/tapout_failed_ops.log'
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
    echo "Failed operations" > $TMP_FAILED_OP_FILE
    i=0
    ./build/bin/dbd_modify_netlist --netlist $netlist_filename | grep "DBG_" | while read line
    do
        ((i++))
        #reset silicon before each run
        device/bin/silicon/reset.sh

        # create filename for new netlist
        modified_netlist_filename=$TMP_OUT_DIR'/'$i'_'$base_filename
        test_log=$modified_netlist_filename'.log'
        # log operation name that is tapped out
        queue_name=$(echo $line | awk '{print substr($1, 1, length($1)-1)}')
        echo $queue_name

        # create new netlist file with added output queue for one operation
        sed "/queues:.*/a \ \ $line" $netlist_filename > $modified_netlist_filename

        # format new test command
        command=$(echo $1 | sed -e 's|'$netlist_filename'|'$modified_netlist_filename'|')
        echo $command

        # run new test command and save log
        $command > $test_log

        if [ "$?" -ne 0 ]
        then
            echo "FAILED! Check log file $test_log"
            cat $test_log | grep Error | grep $queue_name
            if [ "$?" -eq 0 ]
            then
                echo $queue_name '"'$command'"' $test_log >> $TMP_FAILED_OP_FILE
            fi
        else
            echo "PASSED"
        fi
    done
fi
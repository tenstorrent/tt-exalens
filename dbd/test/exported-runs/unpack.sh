#!/bin/bash

# Unzips the files such that if there is a directory already it will be used; otherwise a directory
# will created with the same basename of the zip

for f in *.zip
do
  NUM_UNIQ_FILES=`unzip -Z1 $f | tr '/' ' ' | awk '{ print $1 }' |sort -u | wc -l | bc`
  d=`basename $f .zip`

  if [ "$NUM_UNIQ_FILES" == "1" ]
  then
    unzip $f
  else
    unzip $f -d $d
  fi
done

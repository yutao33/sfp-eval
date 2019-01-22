#!/bin/bash

AS_REL=$1
STUBS=$2
START=$3
END=$4

mkdir -p results

for i in `seq $START $END`; do
    ./bubblecast_group_sim.py $AS_REL $STUBS $i > results/output-$i.txt &
done

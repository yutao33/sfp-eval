#!/bin/bash

AS_REL=$1
AS_COUNTRY=$2
STUBS=$3
START=$4
END=$5

mkdir -p us-results

for i in `seq $START $END`; do
    ./bubblecast_usgroup_sim.py $AS_REL $AS_COUNTRY $STUBS $i > us-results/output-$i.txt &
done

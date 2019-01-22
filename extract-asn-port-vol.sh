#!/bin/bash

# 0    1      2      3     4   5        6
# time|src_ip|dst_ip|proto|vol|src_port|dst_port

for pcap in $(find $1 -name '*.pcap.gz'); do
    tshark -r "$pcap" | awk '{print $2 "|" $3 "|" $5 "|" $6 "|" $7 "|" $8 "|" $10}' | ./ip2asn.py > "$pcap".json
done

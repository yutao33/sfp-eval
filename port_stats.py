#!/usr/bin/env python3

import re
import json


def stats_merge_filter(port_stats, new_port_stats):
    for direct in ['out', 'in']:
        for asn in new_port_stats.get(direct, {}):
            if asn not in port_stats[direct]:
                port_stats[direct][asn] = {}
            for p in new_port_stats[direct][asn]:
                if re.match('.*/\d+', p) is None:
                    continue
                port_stats[direct][asn][p] = port_stats[direct][asn].get(p, 0) + new_port_stats[direct][asn][p]

def stats_summary(port_stats_by_as):
    port_stats = { 'out': {}, 'in': {} }
    for direct in ['out', 'in']:
        for asn in port_stats_by_as.get(direct, {}):
            for p in port_stats_by_as[direct][asn]:
                port_stats[direct][p] = port_stats[direct].get(p, 0) + port_stats_by_as[direct][asn][p]
    print(json.dumps(port_stats, indent=2, sort_keys=True))

def main1(basedir):
    import os
    port_stats = { 'out': {}, 'in': {} }
    for fn in os.listdir(basedir):
        if fn.endswith('.json'):
            with open(os.path.join(basedir, fn)) as f:
                new_port_stats = json.load(f)
                stats_merge_filter(port_stats, new_port_stats)
    print(json.dumps(port_stats, indent=2, sort_keys=True))

def main2(filename):
    with open(filename, 'r') as f:
        port_stats_by_as = json.load(f)
        stats_summary(port_stats_by_as)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        sys.exit()
    if sys.argv[2] == '1':
        main1(sys.argv[1])
    elif sys.argv[2] == '2':
        main2(sys.argv[1])

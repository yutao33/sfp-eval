#!/usr/bin/env python3

import sys
import pyasn

DEFAULT_ASNDB='ipasn.20190116.1600.dat'
asndb = pyasn.pyasn(DEFAULT_ASNDB)

def ip2asn(func, *args, **kwargs):
    while True:
        line = sys.stdin.readline()
        columns = line.strip('\n').split('|')
        if len(columns) < 2:
            break
        src_asn = asndb.lookup(columns[1])[0]
        if not src_asn:
            continue
        dst_asn = asndb.lookup(columns[2])[0]
        if not dst_asn:
            continue
        func(columns, src_asn, dst_asn, *args, **kwargs)

def port_stats_func(columns, src_asn, dst_asn, port_stats):
        proto = columns[3]
        vol = int(columns[4])
        src_port = proto+'/'+columns[5]
        dst_port = proto+'/'+columns[6]
        if src_asn not in port_stats['out']:
            port_stats['out'][src_asn] = {}
        port_stats['out'][src_asn][src_port] = port_stats['out'][src_asn].get(src_port, 0) + vol
        if dst_asn not in port_stats['in']:
            port_stats['in'][dst_asn] = {}
        port_stats['in'][dst_asn][dst_port] = port_stats['in'][dst_asn].get(dst_port, 0) + vol


def port_stats_by_as():
    port_stats = {'out': {}, 'in': {}}
    try:
        ip2asn(port_stats_func, port_stats)
    except KeyboardInterrupt:
        pass
    finally:
        return port_stats

if __name__ == '__main__':
    port_stats = port_stats_by_as()
    import json
    print(json.dumps(port_stats, indent=2, sort_keys=True))

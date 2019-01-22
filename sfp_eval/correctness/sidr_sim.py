#!/usr/bin/env python

import math
import random

import networkx
from pytricia import PyTricia

from sfp_eval.correctness.topology import read_topo
from sfp_eval.bin.announcement_sim import read_flows

DEFAULT_SERVICE_TYPES = {21: 0.1, 80: 0.1, 2801: 0.2, 8444: 0.3, 8445: 0.3}


"""
Abstraction:
    2-tier SDX: providers, customers
    for two SDXes: SDX_A, SDX_B, other customers

20: 42-44, 60-66 (23, 24)
23: 44-50, 60-73 (20, 24)
24: 44-56, 60-79 (20, 23, 27)
27: 51-58, 74-79 (24, 29)
29: 57-59 (27)
"""


def sidr_deflection_sim(G,
                        flows,
                        SDXes,
                        service_types=DEFAULT_SERVICE_TYPES,
                        network_ratio=0.5,
                        prefix_ratio=0.2,
                        **kwargs):
    """
    Simulate false-positive cases of SIDR
        SDXes: [sdx]
        sdx: (sdxi, dests, peers)
    """
    for sdxi in SDXes.keys():
        policy = PyTricia()
        for dest in SDXes[sdxi]['dests']:
            node_prefixes = G.node[dest]['ip-prefixes']
            sidr_random_deflect(node_prefixes, policy,
                                service_types, network_ratio, prefix_ratio)
        SDXes[sdxi]['policy'] = policy

    total_reject_cnt = 0
    total_tp_reject_cnt = 0
    total_fp_volume = 0
    for sdxi in SDXes.keys():
        reject_cnt, tp_reject_cnt, fp_rejected_policy = sidr_reject_by_peer(SDXes, sdxi)
        fp_volume = fp_affected_volume(G, fp_rejected_policy, SDXes[sdxi]['srcs'], flows)
        print(sdxi, reject_cnt, tp_reject_cnt, fp_volume)
        total_reject_cnt += reject_cnt
        total_tp_reject_cnt += tp_reject_cnt
        total_fp_volume += fp_volume
    print(total_reject_cnt, total_reject_cnt - total_tp_reject_cnt, total_fp_volume)


def fp_affected_volume(G, fp_rejected_policy, srcs, flows):
    """
    """
    src_trie = PyTricia()
    volume = 0
    for src in srcs:
        node_prefixes = G.node[src]['ip-prefixes']
        for prefix in node_prefixes:
            src_trie[prefix] = 1
    for flow in flows:
        if src_trie.get(flow['src_ip'], 0) and \
           fp_rejected_policy.get(flow['dst_ip'], {}).get(flow['dst_port'], 0):
            volume += flow['volume']
    return volume


def sidr_reject_by_peer(SDXes, sdxi):
    """
    Reject policy by checking peers
    """
    policy = SDXes[sdxi]['policy']
    reject_cnt = 0
    tp_reject_cnt = 0
    peer_policy = [SDXes[p]['policy'] for p in SDXes[sdxi]['peers']]
    merge_peer_policy = PyTricia()
    for p_policy in peer_policy:
        for p in p_policy.keys():
            if p not in merge_peer_policy.keys():
                merge_peer_policy[p] = {}
            merge_peer_policy[p].update(p_policy[p])
    rejected_prefixes = set(policy.keys()).intersection(merge_peer_policy.keys())

    fp_rejected_policy = PyTricia()

    for prefix in rejected_prefixes:
        deflect_port = {p for p in policy[prefix].keys()}
        peer_deflect_port = {p for p in merge_peer_policy[prefix].keys()}
        reject_cnt += len(deflect_port)
        tp_reject_cnt += len(deflect_port.intersection(peer_deflect_port))
        fp_rejected_policy[prefix] = {p: 1 for p in deflect_port
                                      if p not in peer_deflect_port}
    return reject_cnt, tp_reject_cnt, fp_rejected_policy


def sidr_peer_deflection_sim(G,
                             dests,
                             service_types=DEFAULT_SERVICE_TYPES,
                             network_ratio=0.5,
                             prefix_ratio=0.2,
                             **kwargs):
    """
    Simulate false-positive cases of SIDR between peer SDXes
    """
    peer1 = PyTricia()
    peer2 = PyTricia()
    for dest in dests:
        node_prefixes = G.node[dest]['ip-prefixes']
        sidr_random_deflect(node_prefixes, peer1,
                            service_types, network_ratio, prefix_ratio)
        sidr_random_deflect(node_prefixes, peer2,
                            service_types, network_ratio, prefix_ratio)
    total_reject_cnt, tp_reject_cnt = sidr_reject(peer1, peer2)
    print(total_reject_cnt, tp_reject_cnt)


def sidr_random_deflect(node_prefixes,
                        local_policy,
                        service_types=DEFAULT_SERVICE_TYPES,
                        network_ratio=0.5,
                        prefix_ratio=0.2,
                        **kwargs):
    """
    Randomly insert deflection policy for SIDR simulation
    """
    for prefix in random.sample(
            node_prefixes, math.ceil(
                len(node_prefixes) * float(prefix_ratio))):
        local_policy[prefix] = {
            port: 1 for port in random.sample(service_types.keys(),
                                                random.randint(1, 4))
        }


def sidr_reject(peer1, peer2):
    """
    Compare prefixes to decide rejected policies
    """
    rejected_prefixes = set(peer1.keys()).intersection(peer2.keys())
    peer1_reject_cnt = 0
    peer2_reject_cnt = 0
    tp_reject_cnt = 0
    for prefix in rejected_prefixes:
        deflect_port1 = {p for p in peer1[prefix].keys()}
        deflect_port2 = {p for p in peer2[prefix].keys()}
        peer1_reject_cnt += len(deflect_port1)
        peer2_reject_cnt += len(deflect_port2)
        tp_reject_cnt += 2 * len(deflect_port1.intersection(deflect_port2))
    total_reject_cnt = peer1_reject_cnt + peer2_reject_cnt
    return total_reject_cnt, total_reject_cnt - tp_reject_cnt


def main(topo_filepath, flow_filepath):
    G = read_topo(topo_filepath)
    flows = read_flows(flow_filepath)
    # dests = [i for i in range(18, 23)] + [i for i in range(28, 44)] + [25, 26, 59]
    # sidr_peer_deflection_sim(G, dests)

    SDX2 = {
        23: {
            'srcs': [d for d in G.node if 44 <= d <= 50 or 60 <= d <= 73],
            'dests': [d for d in G.node if d < 44 or 50 < d < 60 or d > 73],
            'peers': [24]
        },
        24: {
            'srcs': [d for d in G.node if 44 <= d <= 56 or 60 <= d <= 79],
            'dests': [d for d in G.node if d < 44 or 56 < d < 60],
            'peers': [23]
        },
    }

    print('====== 2 SDX =======')
    sidr_deflection_sim(G, flows, SDX2)

    SDX3 = {
        20: {
            'srcs': [d for d in G.node if 42 <= d <= 44 or 60 <= d <= 66],
            'dests': [d for d in G.node if d < 42 or 44 < d < 60 or d > 66],
            'peers': [23, 24]
        },
        23: {
            'srcs': [d for d in G.node if 44 <= d <= 50 or 60 <= d <= 73],
            'dests': [d for d in G.node if d < 44 or 50 < d < 60 or d > 73],
            'peers': [20, 24]
        },
        24: {
            'srcs': [d for d in G.node if 44 <= d <= 56 or 60 <= d <= 79],
            'dests': [d for d in G.node if d < 44 or 56 < d < 60],
            'peers': [20, 23]
        },
    }

    print('====== 3 SDX =======')
    sidr_deflection_sim(G, flows, SDX3)

    SDX4 = {
        20: {
            'srcs': [d for d in G.node if 42 <= d <= 44 or 60 <= d <= 66],
            'dests': [d for d in G.node if d < 42 or 44 < d < 60 or d > 66],
            'peers': [23, 24]
        },
        23: {
            'srcs': [d for d in G.node if 44 <= d <= 50 or 60 <= d <= 73],
            'dests': [d for d in G.node if d < 44 or 50 < d < 60 or d > 73],
            'peers': [20, 24]
        },
        24: {
            'srcs': [d for d in G.node if 44 <= d <= 56 or 60 <= d <= 79],
            'dests': [d for d in G.node if d < 44 or 56 < d < 60],
            'peers': [20, 23, 27]
        },
        27: {
            'srcs': [d for d in G.node if 51 <= d <= 58 or 74 <= d <= 79],
            'dests': [d for d in G.node if d < 51 or 58 < d < 74],
            'peers': [24]
        },
    }

    print('====== 4 SDX =======')
    sidr_deflection_sim(G, flows, SDX4)

    SDX5 = {
        20: {
            'srcs': [d for d in G.node if 42 <= d <= 44 or 60 <= d <= 66],
            'dests': [d for d in G.node if d < 42 or 44 < d < 60 or d > 66],
            'peers': [23, 24]
        },
        23: {
            'srcs': [d for d in G.node if 44 <= d <= 50 or 60 <= d <= 73],
            'dests': [d for d in G.node if d < 44 or 50 < d < 60 or d > 73],
            'peers': [20, 24]
        },
        24: {
            'srcs': [d for d in G.node if 44 <= d <= 56 or 60 <= d <= 79],
            'dests': [d for d in G.node if d < 44 or 56 < d < 60],
            'peers': [20, 23, 27]
        },
        27: {
            'srcs': [d for d in G.node if 51 <= d <= 58 or 74 <= d <= 79],
            'dests': [d for d in G.node if d < 51 or 58 < d < 74],
            'peers': [24, 29]
        },
        29: {
            'srcs': [d for d in G.node if 57 <= d <= 59],
            'dests': [d for d in G.node if d < 57 or d > 59],
            'peers': [27]
        }
    }

    print('====== 5 SDX =======')
    sidr_deflection_sim(G, flows, SDX5)


if __name__ == '__main__':
    import sys
    main(sys.argv[1], sys.argv[2])

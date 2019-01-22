#!/usr/bin/env python
"""
Simulation for the correctness of BGP announcement in fine-grained networks.
"""

import sys
from random import randint, sample, choice

import networkx
import yaml

SERVICE_TYPES = 7
MAX_BLOCK_TYPES = 2
RATIO = 0.9


def read_topo(filename):
    """
    Read inter-domain network topology
    """
    G = networkx.Graph()
    data = yaml.load(open(filename))
    nodes = data['nodes']
    links = data['links']
    for n in nodes:
        nid = nodes[n]['id']
        G.add_node(nid, name=n, **nodes[n])
        if nodes[n].get('vrf', False) or nodes[n].get('prefixes', ''):
            G.node[nid]['type'] = 'transit'
        else:
            G.node[nid]['type'] = 'edge'
    for l in links:
        G.add_edge(*l)
    return G


def set_random_block_policy(G):
    """
    Randomly setup black-hole policies in transit network
    """
    for d in G.nodes():
        if G.node[d].get('type', '') == 'transit':
            G.node[d]['block'] = [randint(0, SERVICE_TYPES)
                                  for i in range(randint(0, MAX_BLOCK_TYPES))]


def set_random_policy(G):
    """
    Randomly setup black-hole or deflection policies in transit network
    """
    edge_networks = [n for n in G.nodes() if G.node[n].get('type', '') == 'edge']
    transit_networks = [n for n in G.nodes() if G.node[n].get('type', '') == 'transit']
    for d in transit_networks:
        G.node[d]['policy'] = {randint(0, SERVICE_TYPES):
                                   {dest: choice([None, random_deflection(G, d, dest)])
                                    for dest in sample(edge_networks,
                                                       randint(0, int(len(edge_networks) * RATIO)))}
                               for i in sample(range(MAX_BLOCK_TYPES),
                                               randint(0, MAX_BLOCK_TYPES))}


def random_deflection(G, d, dest):
    next_hop = networkx.shortest_path(G, d, dest)[1]
    subG = G.copy()
    subG.remove_edge(d, next_hop)
    if dest not in networkx.descendants(subG, d):
        return None
    else:
        return networkx.shortest_path(subG, d, dest)[1]


def gen_random_flow(G, flow_num=2000):
    edge_networks = [n for n in G.nodes() if G.node[n].get('type', '') == 'edge']
    return [(sample(edge_networks, 2), randint(0, SERVICE_TYPES)) for i in range(flow_num)]


def check_reachability(G, flows):
    paths = networkx.shortest_path(G)
    drop_cnt = 0
    loop_cnt = 0
    for f in flows:
        result = check_path(f, paths, G)
        if result == 1:
            drop_cnt += 1
        elif result == 2:
            loop_cnt += 1
        # block = False
        # for d in p:
        #     if f[1] in G.node[d].get('block', []):
        #         block = True
        #         break
        # if not block:
        #     cnt += 1
    print('block_policies', 'deflection_policies')
    print('%d\t%d' % policy_summary(G))
    print('total\tdrop\tloop\treachability_rate')
    print('%d\t%d\t%d\t%f' % (len(flows), drop_cnt, loop_cnt, 1 - float(drop_cnt + loop_cnt) / len(flows)))


def check_path(f, paths, G):
    loop_remover = {}
    pair = f[0]
    src = pair[0]
    dst = pair[1]
    srv = f[1]
    p = paths[src][dst][:]
    d = p.pop(0)
    while p:
        loop_remover[d] = loop_remover.get(d, 0) + 1
        # print d, p, loop_remover
        if loop_remover[d] > 1:
            return 2
        policy = G.node[d].get('policy', {})
        if (srv in policy) and (dst in policy[srv]):
            d = policy[srv][dst]
            if d:
                # print srv, dst, d, p, policy
                p = paths[d][dst][1:]
            else:
                p = []
        else:
            d = p.pop(0)
    if d != dst:
        return 1
    return 0


def policy_summary(G):
    block_cnt = 0
    deflection_cnt = 0
    for d in G.nodes():
        p = G.node[d].get('policy', {})
        for srv in p:
            for dst in p[srv]:
                if p[srv][dst]:
                    deflection_cnt += 1
                else:
                    block_cnt += 1
    return block_cnt, deflection_cnt


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("%s topo_file [flow_num [ratio [max_block_types [service_types]]]]" % sys.argv[0])
        sys.exit(0)
    flow_num = 100000
    if len(sys.argv) > 2:
        flow_num = int(sys.argv[2])
    if len(sys.argv) > 3:
        RATIO = float(sys.argv[3])
    if len(sys.argv) > 4:
        MAX_BLOCK_TYPES = int(sys.argv[4])
    if len(sys.argv) > 5:
        SERVICE_TYPES = int(sys.argv[5])

    G = read_topo(sys.argv[1])
    set_random_policy(G)
    flows = gen_random_flow(G, flow_num)
    # print G.node
    check_reachability(G, flows)

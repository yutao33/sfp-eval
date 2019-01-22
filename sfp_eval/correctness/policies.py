import math
import random
from copy import deepcopy

import networkx
from pytricia import PyTricia

DEFAULT_SERVICE_TYPES = {21: 0.1, 80: 0.1, 2801: 0.2, 8444: 0.3, 8445: 0.3}


def generate_local_policies(G, **kwargs):
    # TODO
    return generate_random_policy(G, **kwargs)


def generate_random_policy(G,
                           random_type='r',
                           service_types=DEFAULT_SERVICE_TYPES,
                           network_ratio=0.5,
                           prefix_ratio=0.2,
                           policy_place='transit',
                           policy_type='both',
                           triangle=None,
                           **kwargs):
    """
    Randomly setup black-hole or deflection policies in transit network

    Args:
        G: Topology
        service_types: supported service port distribution.
        network_ratio: how many networks is selected. default 0.5
        prefix_ratio: how many prefix is seleted. default: 0.2
        policy_place: transit, edge or both. default: 'transit'
        policy_type: blackhole, deflection or both. default: 'both'
        args: additional arguments.

    Returns:
        Topology with generated local policies.
    """
    if 'r' in random_type:
        generate_fully_random_policy(G,
                                     service_types=service_types,
                                     network_ratio=network_ratio,
                                     prefix_ratio=prefix_ratio,
                                     policy_place=policy_place,
                                     policy_type=policy_type,
                                     **kwargs)
    if 't' in random_type and triangle:
        generate_triangle_based_random_policy(G,
                                              triangle=triangle,
                                              service_types=service_types,
                                              network_ratio=network_ratio,
                                              prefix_ratio=prefix_ratio,
                                              policy_type=policy_type,
                                              **kwargs)
    if 'b' in random_type:
        generate_funny_block_policy(G,
                                    service_types=service_types,
                                    network_ratio=network_ratio,
                                    prefix_ratio=prefix_ratio,
                                    policy_type=policy_type,
                                    **kwargs)
    if 'h' in random_type and triangle:
        block_half_policy(G,
                          triangle=triangle,
                          service_types=service_types,
                          network_ratio=network_ratio,
                          prefix_ratio=prefix_ratio,
                          policy_type=policy_type,
                          **kwargs)
    return G


def block_half_policy(G,
                      triangle,
                      service_types=DEFAULT_SERVICE_TYPES,
                      network_ratio=0.5,
                      prefix_ratio=0.2,
                      policy_type='both',
                      **kwargs):
    for tr in random.sample(triangle, math.ceil(len(triangle) * float(network_ratio))):
        peer1, peer2, dests = tr
        for dest in dests:
            node_prefixes = G.node[dest]['ip-prefixes']
            for prefix in random.sample(
                    node_prefixes, math.ceil(
                        len(node_prefixes) * float(prefix_ratio))):
                peer = random.choice([peer1, peer2])
                G.node[peer]['local_policy'][prefix] = {
                    port: None for port in random.sample(service_types.keys(),
                                                         random.randint(1, 4))
                }
        # print(peer, dict(G.node[peer]['local_policy']))
    return G


def generate_funny_block_policy(G,
                                service_types=DEFAULT_SERVICE_TYPES,
                                network_ratio=0.5,
                                prefix_ratio=0.2,
                                policy_type='both',
                                **kwargs):
    magic_ratio = 3  # Magic!
    funny_ports = [p for p in range(1, 65536) if p not in DEFAULT_SERVICE_TYPES.keys()]
    # funny_ports = [21, 80, 22, 23, 24, 25, 32, 44, 98]
    edge_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'edge'
    ]
    transit_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'transit' and n != 1
    ]
    for d in random.sample(transit_networks, math.ceil(len(transit_networks) *
                                                       float(network_ratio) / magic_ratio)):
        # print(d)
        if 'local_policy' not in G.node[d]:
            G.node[d]['local_policy'] = PyTricia()
        local_policy = G.node[d]['local_policy']
        for dest in random.sample([n for n in edge_networks if n != d],
                                  math.ceil(len(edge_networks) * float(network_ratio))):
            node_prefixes = G.node[dest]['ip-prefixes']
            for prefix in random.sample(
                    node_prefixes, math.ceil(
                        len(node_prefixes) * float(prefix_ratio))):
                local_policy[prefix] = {
                    port: None
                    for port in random.sample(funny_ports,
                                              random.randint(1, 4))
                }
    return G


def generate_fully_random_policy(G,
                                 service_types=DEFAULT_SERVICE_TYPES,
                                 network_ratio=0.5,
                                 prefix_ratio=0.2,
                                 policy_place='transit',
                                 policy_type='both',
                                 **kwargs):
    edge_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'edge'
    ]
    transit_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'transit'
    ]
    if policy_place == 'transit':
        policy_networks = transit_networks
    elif policy_place == 'edge':
        policy_networks = edge_networks
    else:
        policy_networks = G.nodes()
    for d in policy_networks:
        if 'local_policy' not in G.node[d]:
            G.node[d]['local_policy'] = PyTricia()
        local_policy = G.node[d]['local_policy']
        for dest in random.sample([n for n in edge_networks if n != d],
                                  math.ceil(
                                      len(edge_networks) * float(network_ratio))):
            node_prefixes = G.node[dest]['ip-prefixes']
            for prefix in random.sample(
                    node_prefixes, math.ceil(
                        len(node_prefixes) * float(prefix_ratio))):
                local_policy[prefix] = {
                    port: gen_single_policy(G, d, dest, policy_type)
                    for port in random.sample(service_types.keys(),
                                              random.randint(1, 4))
                }
    return G


def generate_triangle_based_random_policy(G,
                                          triangle,
                                          service_types=DEFAULT_SERVICE_TYPES,
                                          network_ratio=0.5,
                                          prefix_ratio=0.2,
                                          policy_type='both',
                                          **kwargs):
    for tr in random.sample(triangle, math.ceil(len(triangle) * float(network_ratio))):
        peer1, peer2, dests = tr
        for dest in dests:
            node_prefixes = G.node[dest]['ip-prefixes']
            for prefix in random.sample(
                    node_prefixes, math.ceil(
                        len(node_prefixes) * float(prefix_ratio))):
                G.node[peer1]['local_policy'][prefix] = {
                    port: peer2 for port in random.sample(service_types.keys(),
                                                          random.randint(1, 4))
                }
                G.node[peer2]['local_policy'][prefix] = {
                    port: peer1 for port in random.sample(service_types.keys(),
                                                          random.randint(1, 4))
                }
    return G


def gen_single_policy(G, d, dest, policy_type):
    if policy_type == 'both':
        return random.choice([None, random_deflection(G, d, dest)])
    elif policy_type == 'deflection':
        return random_deflection(G, d, dest)
    return None


def random_deflection(G, d, dest):
    next_hop = networkx.shortest_path(G, d, dest)[1]
    subG = G.copy()
    subG.remove_edge(d, next_hop)
    if dest not in networkx.descendants(subG, d):
        return None
    else:
        # return networkx.shortest_path(subG, d, dest)[1]
        return random.choice([x for x in subG.neighbors(d)])


def manual_policy(G):
    # for prefix in G.node[3]['ip-prefixes']:
    # for prefix in G.ip_prefixes:
        # G.node[3]['local_policy'][prefix] = {8444: None, 8445: None, 80: None, 21: None, 2801: None}
        # G.node[1]['local_policy'][prefix] = {81: None}
        # G.node[43]['local_policy'][prefix] = {81: None}
        # G.node[23]['local_policy'][prefix] = {81: None}
        # G.node[57]['local_policy'][prefix] = {81: None}
        # G.node[24]['local_policy'][prefix] = {81: None}
        # G.node[6]['local_policy'][prefix] = {8444: None, 8445: None}
        # G.node[8]['local_policy'][prefix] = {8444: None, 8445: None}
    for prefix in G.ip_prefixes:
        # G.node[24]['local_policy'][prefix] = {port: 3 for port in DEFAULT_SERVICE_TYPES.keys()}
        # G.node[23]['local_policy'][prefix] = {port: 27 for port in DEFAULT_SERVICE_TYPES.keys()}
        # G.node[27]['local_policy'][prefix] = {port: 23 for port in DEFAULT_SERVICE_TYPES.keys()}
        # G.node[3]['local_policy'][prefix] = {port: 1 for port in DEFAULT_SERVICE_TYPES.keys()}
        # G.node[1]['local_policy'][prefix] = {port: 3 for port in DEFAULT_SERVICE_TYPES.keys()}
        G.node[57]['local_policy'][prefix] = {port: 8 for port in DEFAULT_SERVICE_TYPES.keys()}
        G.node[8]['local_policy'][prefix] = {port: 1 for port in DEFAULT_SERVICE_TYPES.keys()}
        G.node[1]['local_policy'][prefix] = {port: 8 for port in DEFAULT_SERVICE_TYPES.keys()}
    for prefix in (G.node[42]['ip-prefixes'] + G.node[60]['ip-prefixes'] + G.node[61]['ip-prefixes'] +
                   G.node[62]['ip-prefixes'] + G.node[63]['ip-prefixes'] + G.node[64]['ip-prefixes']):
        G.node[23]['local_policy'][prefix] = {port: 27 for port in DEFAULT_SERVICE_TYPES.keys()}
        G.node[27]['local_policy'][prefix] = {port: 23 for port in DEFAULT_SERVICE_TYPES.keys()}
    for prefix in (G.node[71]['ip-prefixes'] + G.node[70]['ip-prefixes']):
        G.node[24]['local_policy'][prefix] = {port: 23 for port in DEFAULT_SERVICE_TYPES.keys()}
        G.node[23]['local_policy'][prefix] = {port: 24 for port in DEFAULT_SERVICE_TYPES.keys()}
    # for prefix in (G.node[51]['ip-prefixes'] + G.node[52]['ip-prefixes'] + G.node[53]['ip-prefixes'] +
    #                G.node[54]['ip-prefixes'] + list(G.node[55]['ip-prefixes']) + list(G.node[56]['ip-prefixes'])):
    # G.node[24]['local_policy'][prefix] = {8444: 27, 8445: 27, 21: 27, 80: 27, 2801: 27}
    # G.node[24]['local_policy'][prefix] = {81: None}
    # for n in policies:
    #     for prefix in policies[n]:
    #         G.node[n]['local_policy'][prefix] = policies[n][prefix]


def generate_random_peered_bubblecast(G,
                                      default_count=10,
                                      prefix_num=100,
                                      service_types=DEFAULT_SERVICE_TYPES):
    edge_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'edge'
    ]
    peer1, peer2 = list(random.sample(edge_networks, 2))
    # Set dcast for peer1
    G.node[peer1]['dcast'] = {
        prefix: {
            port: default_count
            for port in service_types.keys()
        } for prefix in random.sample(G.ip_prefixes.keys(),
                                      max(len(G.ip_prefixes, prefix_num)))
    }
    # Set the same qcast for peer2
    G.node[peer2]['qcast'] = deepcopy(G.node[peer1]['dcast'])


def dump_bubblecast(G, filename):
    bubblecast_table = {}
    for n in G.nodes():
        bubblecast_table[n] = {}
        bubblecast_table[n]['qcast'] = dict(G.node[n]['qcast'])
        bubblecast_table[n]['qcast-in'] = dict(G.node[n]['qcast-in'])
        bubblecast_table[n]['dcast'] = dict(G.node[n]['dcast'])
        bubblecast_table[n]['dcast-in'] = dict(G.node[n]['dcast-in'])
    import json
    with open(filename, 'w') as f:
        json.dump(bubblecast_table, f, indent=2, sort_keys=True)


def dump_tables(G, filename):
    big_table = {}
    for n in G.nodes():
        big_table[n] = {}
        big_table[n]['local_policy'] = dict(G.node[n]['local_policy'])
        big_table[n]['rib'] = dict(G.node[n]['rib'])
        big_table[n]['adj-ribs-in'] = {d: dict(G.node[n]['adj-ribs-in'][d]) for d in G.node[n]['adj-ribs-in']}
        big_table[n]['adj-ribs-out'] = {d: dict(G.node[n]['adj-ribs-out'][d]) for d in G.node[n]['adj-ribs-in']}
    import json
    json.dump(big_table, open(filename, 'w'), indent=2, sort_keys=True)

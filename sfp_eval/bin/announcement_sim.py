#!/usr/bin/env python

import datetime
import json
import math
import random
import sys
from ipaddress import ip_address, ip_network

import numpy as np
import pytricia
import yaml

import networkx

ip_prefixes = pytricia.PyTricia()

seed = hash(datetime.datetime.now())
global_policy = {}


def read_topo(filename, local_policy=None):
    data = yaml.load(open(filename))
    G = networkx.Graph()
    nodes = data["nodes"]
    links = data["links"]
    for n in nodes:
        nid = nodes[n]['id']
        G.add_node(nid, name=n, **nodes[n])
        G.node[nid]['type'] = nodes[n]['type']
        G.node[nid]['ip-prefix'] = nodes[n].get('ip-prefix', [])
        G.node[nid]['routing'] = pytricia.PyTricia()
        G.node[nid]['fine_grained'] = pytricia.PyTricia()
        for prefix in nodes[n].get('ip-prefix', []):
            ip_prefixes[prefix] = nid
    for l in links:
        G.add_edge(*l)
    return G


bgp_general_policy = networkx.shortest_path


# FIXME: The generation algorithm does not make sense
# Refer to the evaluation part of SDX and SIDR
def generate_local_policy(G, **args):
    """
    Generate the local policy for each node in G.

    Args:
        G: graph.
        args: additional arguments to config the generation algorithm.

    Returns:
        The mapping from node id to a local_policy table.
        local_policy_table ::= Trie<prefix, Map<port, next_hop>>
    """
    global global_policy
    random.seed(seed)
    policies = dict()
    max_ports = 30
    for node in G.nodes():
        if node not in policies:
            policies[node] = pytricia.PyTricia()
        # FIXME: select prefix by following a distribution
        for prefix in G.node[node]["ip-prefix"]:
            # FIXME: select ports by following a distribution
            ports = set([
                random.randint(10000, 60000)
                for _ in range(random.randint(1, max_ports))
            ])
            for port in ports:
                policies[node][port] = random.choice(
                    [i for i in G.neighbors(node)] + [None])
    global_policy = policies


DEFAULT_SERVICE_TYPES = {21: 0.1, 80: 0.1, 2801: 0.2, 8444: 0.3, 8445: 0.3}


# TODO: Some key points
# - What's the distribution for policy type (blackhole/deflection) selection
# - What's the distribution for node selection
# - How many network we need to fwd
# - What's the distribution for the tcp port selection
def generate_random_policy(G,
                           service_types=DEFAULT_SERVICE_TYPES,
                           network_ratio=0.5,
                           prefix_ratio=0.2,
                           policy_place='transit',
                           policy_type='both',
                           **args):
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
        global local policy table.
    """
    edge_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'edge'
    ]
    transit_networks = [
        n for n in G.nodes() if G.node[n].get('type', '') == 'transit'
    ]
    policies = {}
    if policy_place == 'transit':
        policy_networks = transit_networks
    elif policy_place == 'edge':
        policy_networks = edge_networks
    else:
        policy_networks = G.nodes()
    for d in policy_networks:
        if d not in policies:
            policies[d] = pytricia.PyTricia()
        for dest in random.sample([n for n in edge_networks if n != d],
                                  math.ceil(
                                      len(edge_networks) * float(network_ratio))):
            node_prefixes = G.node[dest]['ip-prefix']
            for prefix in random.sample(
                    node_prefixes, math.ceil(
                        len(node_prefixes) * float(prefix_ratio))):
                policies[d][prefix] = {
                    port: gen_single_policy(G, d, dest, policy_type)
                    for port in random.sample(service_types.keys(),
                                              random.randint(1, 4))
                }
    return policies


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
        return networkx.shortest_path(subG, d, dest)[1]


def get_local_policy(node):
    """
    local_policy is not a simple prefix based routing.

    For simplicity, assume the format of local_policy for each node is:

    local_policy ::= Trie<prefix, Map<port, next_hop>>
    """
    global global_policy
    return global_policy.get(node, pytricia.PyTricia())


def default_routing_policy(node,
                           dst_ip,
                           dst_port=None,
                           src_ip=None,
                           src_port=None,
                           protocol='tcp',
                           **args):
    """
    Default routing policy for networks.

    Args:
        node: node id for the network.
        dst_ip: destination ip address.
        dst_port: optional.
        src_ip: optional.
        src_port: optional.
        protocol: optional.
        args: additional flow spec.

    Returns:
        The next hop of the give flow spec from this node.
    """
    for prefix in node.get('ip-prefix', []):
        if ip_address(dst_ip) in ip_network(prefix):
            return None
    local_policy = get_local_policy(node['id'])
    if dst_ip in local_policy:
        local_policy_for_ip = local_policy[dst_ip]
        if dst_port in local_policy_for_ip:
            return local_policy_for_ip[dst_port]
    fg_routing = node['fine_grained']
    if dst_ip in fg_routing:
        fg_routing_for_ip = fg_routing[dst_ip]
        if dst_port in fg_routing_for_ip:
            return fg_routing_for_ip[dst_port]
    if dst_ip in node['routing']:
        return node['routing'][dst_ip]


def fp_bgp_convergence(G):
    """
    False-positive BGP Convergence. node["routing"] is the table of  {ip-prefix -> next hop node}
    """
    paths = networkx.shortest_path(G)
    for src in G.nodes:
        for dst in G.nodes:
            if src != dst:
                try:
                    path = paths[src].get(dst)
                except KeyError:
                    path = None
                if path:
                    prefixes = G.node[dst]['ip-prefix']
                    for hop, next_hop in zip(path[:-1], path[1:]):
                        for prefix in prefixes:
                            G.node[hop]["routing"][prefix] = next_hop


def all_fg_nodes(G, prefix):
    """
    Let's assume the local_policy is generated from the prefixes of nodes first.
    """
    # FIXME: If the granularity of prefixes in local_policy is different from ones in node, it will conduct error.
    fg_nodes = []
    for node in G.nodes:
        local = get_local_policy(node)
        if local.get(prefix):
            fg_nodes.append(node)
    return fg_nodes


def correct_bgp_convergence(G):
    """
    Correct BGP Convergence
    """
    for dst in G.nodes:
        prefixes = G.node[dst]['ip-prefix']
        for prefix in prefixes:
            H = G.copy()
            for node in all_fg_nodes(G, prefix):
                H.remove_node(node)
            paths = networkx.shortest_path(H)
            for src in H.nodes:
                if src != dst:
                    # path = paths[src][dst]
                    path = paths[src].get(dst, [])
                    for hop, next_hop in zip(path[:-1], path[1:]):
                        G.node[hop]["routing"][prefix] = next_hop


def find_fine_grained_routes(G, prefix_port):
    for prefix, ports in prefix_port.items():
        for port in ports:
            delete_nodes = set()
            delete_links = set()
            H = G.copy()  # A copy of directed graph to modify links and nodes
            # Step 1: Remove unused links for <prefix, port>
            for node in H.nodes:
                action = get_local_policy(node).get(prefix)
                if action and (port in action):
                    action = action[port]
                    if action:
                        for neig in H.neighbors(node):
                            if action != neig:
                                delete_links.add((node, neig))
                    else:
                        delete_nodes.add(node)
            for edge in delete_links:
                H.remove_edge(*edge)
            for node in delete_nodes:
                H.remove_node(node)
            # Step 2: Find shortest path (Is it possible to be not found?)
            dst = ip_prefixes[prefix]
            paths = networkx.shortest_path(H, target=dst)
            # Step 3: Traverse the shortest path
            for src in H.nodes:
                if src != dst:
                    path = paths.get(src)
                    if path:
                        for hop, next_hop in zip(path[:-1], path[1:]):
                            if prefix not in G.node[hop]["fine_grained"]:
                                G.node[hop]["fine_grained"][prefix] = dict()
                            G.node[hop]["fine_grained"][prefix][port] = next_hop

    # Step 4: BGP shortest path in all nodes
    fp_bgp_convergence(G)
    return G


def fine_grained_announcement(G):
    for node in G.nodes:
        del G.node[node]["routing"]
        del G.node[node]["fine_grained"]
    G = G.to_directed()
    for node in G.nodes:
        G.node[node]["routing"] = pytricia.PyTricia()
        G.node[node]["fine_grained"] = pytricia.PyTricia()
    prefix_port = dict()  # type: dict{str, set{int}}
    for node in G.nodes:
        local = get_local_policy(node)
        for prefix in local:
            ports_actions = local[prefix]
            if prefix not in prefix_port:
                prefix_port[prefix] = set()
            for port in ports_actions:
                prefix_port[prefix].add(port)
    return find_fine_grained_routes(G, prefix_port)


def read_flows(filename, port_dist=DEFAULT_SERVICE_TYPES):
    """
    Examples:
        [{
            "src_ip": "10.0.0.1",
            "src_port": 22,
            "dst_ip": "10.0.10.1",
            "dst_port": 80,
            "protocol": "tcp",
            "start_time": 1516292713,
            "end_time": 1516313885,
            "volume": 4089456904
        }]

        required: src_ip, dst_ip, start_time, end_time, volume
        optional: src_port, dst_port, protocol
    """
    data = json.load(open(filename))
    for d in data:
        if not d.get('dst_port', None):
            d['dst_port'] = int(np.random.choice(
                list(port_dist.keys()), p=list(port_dist.values())))
        # (d['src_ip'], d['dst_ip']) = (d['dst_ip'], d['src_ip'])
    return data


statistic_as_length = {}


def coarse_grained_correct_bgp(G, F):
    """
    The principle of Correct BGP is very simple:

    For a specific IP p, compute the subgraph G' of G in which every node with local_policy covering p will not show.
    The final path of p is the shortest_path of subgraph G'.

    The Correct BGP MUST guarantee the local_policy NEVER be triggered.
    """
    for flow in F:
        node = G.node[ip_prefixes[flow["src_ip"]]]
        if node is not None:
            as_length = [node]
            prefixes = [ip_network(p) for p in node['ip-prefix']]
            while ip_address(flow["dst_ip"]) not in prefixes:
                if len(node["fine_grained"]) > 0:
                    try:
                        next_hop = node["fine_grained"][flow["dst_ip"]][
                            "dst_port"]
                        in_fg = True  # In fine grained policy
                    except KeyError:
                        in_fg = False
                if not in_fg:
                    next_hop = node["routing"][flow["dst_ip"]]
                as_length.append(next_hop)
        print("AS Length: %d" % len(as_length))
        if len(as_length) not in statistic_as_length:
            statistic_as_length[len(as_length)] = 0
        statistic_as_length[len(as_length)] += 1


# def match(ip, prefix):
#     return ip in prefix

# TODO: No need, merge it with routing_policy
# def compute_next_hop(flow, rib):
#     """
#     Compute the next hop of the flow from  RIB.
#
#     Args:
#         flow: flow spec.
#         rib: the RIB table from the Graph node.
#
#     Returns:
#         the next hop. (None if no route.)
#     """
#     for rule in rib:
#         if match(flow['dst-ip'], rule):
#             return rib[rule]
#     return None


def check_path(flow, G, routing_policy=default_routing_policy, debug=False):
    """
    Check the path of a given flow in the topology.

    Args:
        flow: The flow spec to check.
        G: The topology object.

    Returns:
        the AS-PATH length of the route.
        nan - no route
        inf - there is a loop
    """
    if debug:
        path = []
    loop_remover = {}
    src = ip_prefixes[flow['src_ip']]
    dst = ip_prefixes[flow['dst_ip']]
    if src == dst:
        if debug:
            return 1, [src]
        return 1
    d = src
    if debug:
        path = [src]
    dn = routing_policy(G.node[src], **flow)
    path_len = 1
    while dn:
        loop_remover[d] = loop_remover.get(d, 0) + 1
        # print d, p, loop_remover
        if loop_remover[d] > 1:
            if debug:
                return math.inf, []
            return math.inf
        d = dn
        if debug:
            path.append(dn)
        dn = routing_policy(G.node[d], **flow)
        path_len += 1
    if d != dst:
        if debug:
            return math.nan, []
        return math.nan
    if debug:
        return path_len, path
    return path_len


debug_dict = {}


def check_reachability(G, F, max_len=10, debug=False, debug_num=None):
    as_length_dist = {}
    success_volume = 0
    unsuccess_volume = 0
    R_F = []
    for f in F:
        if debug:
            global debug_dict
            result, path = check_path(f, G, debug=True)
            if debug_num not in debug_dict:
                debug_dict[debug_num] = dict()
            debug_dict[debug_num][(f["src_ip"], f["dst_ip"], f["start_time"],
                                   f["end_time"], f["volume"])] = (result, path)
        else:
            result = check_path(f, G)
        as_length_dist[result] = as_length_dist.get(result, 0) + 1
        if type(result) == float:
            unsuccess_volume += f['volume']
        elif result > 1:
            success_volume += f['volume']
            R_F.append(f)
    # print 'block_policies', 'deflection_policies'
    # print '%d\t%d' % policy_summary(G)
    if debug:
        as_len_nan = as_length_dist.pop(math.nan) if math.nan in as_length_dist else 0
        as_lens = sorted(as_length_dist.keys())
        as_lens.append(math.nan)
        as_length_dist[math.nan] = as_len_nan
        print('\t'.join([str(l) for l in as_lens]))
        print('\t'.join([str(as_length_dist[l]) for l in as_lens]))
    as_len_pdf = []
    for al in range(max_len - 1):
        as_len_pdf.append(as_length_dist.get(al + 2, 0))
    as_len_pdf.append(as_length_dist.get(math.inf, 0))
    as_len_pdf.append(as_length_dist.get(math.nan, 0))
    as_len_pdf.append(success_volume)
    as_len_pdf.append(unsuccess_volume)
    # Format: flow_num from 2 to max_len, inf, nan, success_volume, unsuccess_volume
    print('\t'.join([str(a) for a in as_len_pdf]))
    return R_F


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("%s topo-filename flow-filename mode" % sys.argv[0])
    topo_filename = sys.argv[1]
    flow_filename = sys.argv[2]
    mode = sys.argv[3]
    args = dict([tuple(k.split('=')) for k in sys.argv[4:]])

    G = read_topo(topo_filename)
    F = read_flows(flow_filename)
    # generate_local_policy(G)
    # global_policy = generate_random_policy(G, network_ratio=0.1, prefix_ratio=0.1, policy_type='blackhole')
    global_policy = generate_random_policy(G, **args)

    if '1' in mode:
        H = G.copy()
        fp_bgp_convergence(H)
        # print("FP_BGP:")
        check_reachability(H, F)
    if '2' in mode:
        H = G.copy()
        correct_bgp_convergence(H)
        # print("C_BGP:")
        R_F = check_reachability(H, F, debug=False, debug_num=2)
    if '3' in mode:
        H = G.copy()
        H = fine_grained_announcement(H)
        # print("SFP:")
        check_reachability(H, F, debug=False, debug_num=3)
    if '4' in mode:
        H = G.copy()
        H = fine_grained_announcement(H)
        # print("Reachable-SFP:")
        check_reachability(H, R_F, debug=False, debug_num=4)

    if len(debug_dict) > 0:
        flow_diff = list()
        for flow in debug_dict[3]:
            if debug_dict[3][flow][0] == math.nan and debug_dict[2][flow][0] != math.nan:
                print(str(flow))
        with open("debug.json", 'w') as f:
            f.write(debug_dict.__str__())

    # coarse_grained_correct_bgp(G, F)
    # print("AS Length statistics: %d" % statistic_as_length)

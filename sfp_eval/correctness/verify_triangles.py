#!/usr/bin/env python3
"""
Function: To verify the triangle pattern of topology
"""

import json
import sys

import networkx
import yaml


def read_topo(topo_filepath):
    # type: (str) -> networkx.Graph
    G = networkx.Graph()
    topo = yaml.load(open(topo_filepath))
    links = topo["links"]
    nodes = topo["nodes"]
    for node_name in nodes:
        node_yaml = nodes[node_name]
        G.add_node(node_yaml['id'])
        node_obj = G.nodes[node_yaml['id']]
        node_obj["customers"] = node_yaml["customers"]
        node_obj["providers"] = node_yaml["providers"]
        node_obj["peers"] = node_yaml["peers"]
    for link in links:
        G.add_edge(link[0], link[1])
    return G


def read_triangle(triagnle_filepath):
    # type: (str) -> list[tuple[int, int, list[int]]]
    triangles = json.load(open(triagnle_filepath))
    ret = []
    for triangle in triangles:
        ret.append((triangle['peer1'], triangle['peer2'], triangle['customers']))
    return ret


def identify(G, T):
    # type: (networkx.Graph, list[tuple[int, int, list[int]]]) -> None
    for triangle in T:
        peer1 = triangle[0]
        peer2 = triangle[1]
        customers = triangle[2]
        if not check_peer(G, peer1, peer2):
            print("%s and %s are not peer" % (peer1, peer2))
        for customer in customers:
            if not check_customer(G, peer1, customer):
                print("%s are not provider of %s" % (peer1, customer))
            if not check_customer(G, peer2, customer):
                print("%s are not provider of %s" % (peer2, customer))


def check_customer(G, provider, customer):
    if provider not in G.neighbors(customer):
        return False
    if customer not in G.neighbors(provider):
        return False
    if provider not in G.nodes[customer]["providers"]:
        return False
    if customer not in G.nodes[provider]["customers"]:
        return False
    return True


def check_peer(G, peer1, peer2):
    # type: (networkx.Graph, int, int) -> bool
    if peer2 not in G.nodes[peer1]["peers"]:
        return False
    if peer1 not in G.nodes[peer2]["peers"]:
        return False
    if peer1 not in G.neighbors(peer2):
        return False
    if peer2 not in G.neighbors(peer1):
        return False
    return True


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: %s topo_filepath, triangle_filepath" % sys.argv[0])
        exit(-1)
    topo_filepath = sys.argv[1]
    triangle_filepath = sys.argv[2]

    G = read_topo(topo_filepath)
    T = read_triangle(triangle_filepath)

    identify(G, T)

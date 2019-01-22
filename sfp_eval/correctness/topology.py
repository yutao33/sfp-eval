import networkx
import yaml
from pytricia import PyTricia


"""
adj-ribs-in = {
"neighbor": rib,
...
}
rib = PyTricia()
rib["10.0.0.0/24"] = {
  80: next_hop1,
  2801: next_hop2,
  0: next_hop0
}
"""


def read_topo(filepath):
    # type: (str) -> networkx.Graph
    topo = yaml.load(open(filepath))
    nodes = topo["nodes"]
    links = topo["links"]
    G = networkx.DiGraph()
    G.ip_prefixes = PyTricia()
    for node_name in nodes:
        node = nodes[node_name]
        node_id = node['id']
        G.add_node(node_id)
        node_obj = G.nodes[node_id]
        node_obj['id'] = node_id
        node_obj['type'] = node['type']
        node_obj['asn'] = node.get('asn', None)
        node_obj['ip-prefixes'] = node.get('ip-prefixes', set()) or set()
        node_obj['ip'] = node.get('ip', None)
        node_obj['providers'] = set(node.get('providers', []))
        node_obj['customers'] = set(node.get('customers', []))
        node_obj['peers'] = set(node.get('peers', []))
        node_obj['name'] = node_name
        if 'topology-name' in node:
            node_obj['topology-name'] = node['topology-name']
        for prefix in node_obj['ip-prefixes']:
            G.ip_prefixes[prefix] = node_id
    for link in links:
        G.add_edge(*link)
        G.add_edge(*link[::-1])
    for node_id in G.nodes():
        node_obj = G.node[node_id]
        node_obj['adj-ribs-in'] = {n: PyTricia() for n in G.neighbors(node_id)}
        node_obj['rib'] = PyTricia()
        node_obj['adj-ribs-out'] = {n: PyTricia() for n in G.neighbors(node_id)}
        node_obj['local_policy'] = PyTricia()
    return G


def dump_topo(G, filepath):
    topo = dict()
    topo["links"] = list()
    topo["nodes"] = dict()
    for node in sorted(G.nodes):
        node_obj = G.nodes[node]
        node_obj_dump = {}
        node_obj_dump['id'] = node_obj['id']
        node_obj_dump['type'] = node_obj['type']
        node_obj_dump['providers'] = sorted(node_obj['providers'])
        node_obj_dump['customers'] = sorted(node_obj['customers'])
        node_obj_dump['peers'] = sorted(node_obj['peers'])
        node_obj_dump['ip-prefixes'] = sorted(node_obj['ip-prefixes'])
        if 'asn' in node_obj:
            node_obj_dump['asn'] = node_obj['asn']
        if 'topology-name' in node_obj:
            node_obj_dump['topology-name'] = str(node_obj['topology-name'])
        if 'attach' in node_obj:
            node_obj_dump['attach'] = dict(node_obj['attach'])
        if 'gateway' in node_obj:
            node_obj_dump['gateway'] = dict(node_obj['gateway'])
        topo["nodes"][node_obj["name"]] = node_obj_dump
    for link in sorted(G.edges):
        topo["links"].append(list(link))
    yaml.dump(topo, open(filepath, 'w'))


class ASRelationsReader(object):
    def __init__(self, filepath):
        super(ASRelationsReader, self).__init__()
        self._G = networkx.DiGraph()
        self._peers = set()
        self._read_file(filepath)

    def _read_file(self, filepath):
        peer_num = 0
        pc_num = 0
        with open(filepath) as f:
            for line in f:
                setence = line.split('#')[0].split('|')
                if len(setence) == 4:
                    asn1, asn2, code, _ = setence
                    asn1, asn2, code = int(asn1), int(asn2), int(code)

                    if code == -1:  # P-C
                        self._G.add_node(asn1)
                        self._G.add_node(asn2)
                        self._G.add_edge(asn1, asn2)
                        pc_num += 1
                    if code == 0:
                        self._peers.add((asn1, asn2))
                        self._peers.add((asn2, asn1))
                        peer_num += 1
        print(peer_num, pc_num)

    def get_customers(self, asn):
        return self._provider_dict.get(asn, set())

    def get_providers(self, asn):
        return self._customer_dict.get(asn, set())

    def get_peers(self, asn):
        return self._peer_dict.get(asn, set())

    def augment_to_topology(self, G: networkx.Graph) -> networkx.Graph:
        # asn_nodes = dict([[G.nodes[node]['asn'], node] for node in G.nodes])  # type: dict[]
        # for (asn1, asn2) in self._peers:
        #     node1 = None
        #     node2 = None
        #     for node in G.nodes:
        #         if G.nodes[node]['asn'] == asn1:
        #             node1 = node
        #         elif G.nodes[node]['asn'] == asn2:
        #             node2 = node
        #         else:
        #             continue
        #     if node1 and node2:
        #         print((node1, node2))
        for node in G.nodes:
            neighbors = G.neighbors(node)
            for neigh in neighbors:
                # if((G.nodes[node]['asn'], G.nodes[neigh]['asn']) in self._peers):
                #     print((node, neigh))
                if neigh not in G.nodes[node]['customers'] \
                        and neigh not in G.nodes[node]['providers'] \
                        and neigh not in G.nodes[node]['peers']:
                    if networkx.has_path(self._G, G.nodes[node]['asn'], G.nodes[neigh]['asn']):
                        G.nodes[node]['customers'].add(neigh)
                        G.nodes[neigh]['providers'].add(node)
                    elif networkx.has_path(self._G, G.nodes[neigh]['asn'], G.nodes[node]['asn']):
                        G.nodes[node]['providers'].add(neigh)
                        G.nodes[neigh]['customers'].add(node)
                    else:
                        G.nodes[node]['peers'].add(neigh)
                        G.nodes[neigh]['peers'].add(node)
        return G

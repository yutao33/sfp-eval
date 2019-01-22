#!/usr/bin/env python3

import networkx

def load_as_rel(filepath):
    """
    Read AS relationships from CAIDA dataset and augment it into a networkx
    directed graph.
    """
    dg = networkx.DiGraph()
    with open(filepath, 'r') as as_rel:
        for line in as_rel.readlines():
            # Skip commented lines
            if line.startswith('#'):
                continue
            src_as, dst_as, rel = line.strip('\n').split('|')
            src_as = int(src_as)
            dst_as = int(dst_as)
            rel = int(rel)
            if rel:
                dg.add_edge(src_as, dst_as, rel='pc')
                dg.add_edge(dst_as, src_as, rel='cp')
            else:
                dg.add_edge(src_as, dst_as, rel='pp')
                dg.add_edge(dst_as, src_as, rel='pp')
    return dg

def load_as_type(filepath, dg):
    """
    Read AS types from CAIDA dataset and augment it into a networkx directed
    graph.
    """
    with open(filepath, 'r') as as_types:
        for line in as_types.readlines():
            # Skip commented lines
            if line.startswith('#'):
                continue
            asn, _, as_type = line.strip('\n').split('|')
            asn = int(asn)
            if asn in dg.nodes():
                dg.nodes[asn]['type'] = as_type[0]

def load_as_country(filepath, dg):
    """
    Read AS countries and augment it.
    """
    with open(filepath, 'r') as as_country:
        for line in as_country.readlines():
            asn, country = line.strip('\n').split('|')
            asn = int(asn)
            if asn in dg.nodes():
                dg.nodes[asn]['country'] = country

def read_as_by_country(dg, country):
    return [n for n in dg.nodes() if dg.nodes[n].get('country', '') == country]

def get_subtopo(dg, country):
    sub_nodes = read_as_by_country(dg, country)
    sdg = dg.subgraph(sub_nodes)
    good_comps = [c for c in networkx.components.connected_components(sdg.to_undirected()) if len(c) > 10]
    good_sub_nodes = good_comps[0]
    return dg.subgraph(good_sub_nodes)

def get_stub_networks_by_rel(dg):
    return [n for n in dg.nodes() if all([dg.edges[e]['rel'] != 'pc' for e in dg.out_edges(n)])]

def get_stub_networks(dg):
    return [n for n in dg.nodes() if dg.nodes[n].get('type', '') in ('C', 'E')]

def init_ribs(dg):
    for n in dg.nodes():
        dg.nodes[n]['local-rib'] = {n: 1}
        dg.nodes[n]['adj-ribs-in'] = {}
        dg.nodes[n]['adj-ribs-out'] = {}
        for p in dg.neighbors(n):
            dg.nodes[n]['adj-ribs-in'][p] = {}
            dg.nodes[n]['adj-ribs-out'][p] = {}

def update_rib(rib, merged_rib):
    for k in merged_rib.keys():
        rib[k] = rib.get(k, 0) + merged_rib[k]

def init_hints(dg):
    for n in dg.nodes():
        dg.nodes[n]['hint'] = 0

def compose_ribs(dg):
    for n in dg.nodes():
        for p in dg.neighbors(n):
            dg.nodes[n]['adj-ribs-out'][p] = dg.nodes[n]['adj-ribs-in'][p]
            dg.nodes[n]['adj-ribs-in'][p] = {}

def advertise(dg):
    for n in dg.nodes():
        print('Advertising', n)
        for eo in dg.out_edges(n):
            eo_n_rib = {}
            update_rib(eo_n_rib, dg.nodes[n]['local-rib'])
            _, post_node = eo
            curr_rel = dg.edges[eo]['rel']
            for ei in dg.in_edges(n):
                prev_node, _ = ei
                prev_rel = dg.edges[ei]['rel']
                if prev_node != post_node and valid_edge(prev_rel, curr_rel):
                    update_rib(eo_n_rib, dg.nodes[n]['adj-ribs-out'][prev_node])
            dg.nodes[post_node]['adj-ribs-in'][n] = eo_n_rib
    compose_ribs(dg)

def dump_rib(dg, fdump):
    ribs = {}
    for n in dg.nodes():
        ribs[n] = dg.nodes[n]['local-rib']
        for p in dg.neighbors(n):
            update_rib(ribs[n], dg.nodes[n]['adj-ribs-out'][p])
    # import json
    # json.dump(ribs, fdump, indent=2, sort_keys=True)
    import yaml
    yaml.dump(ribs, fdump)

def valid_edge(prev_rel, curr_rel):
    if prev_rel in ['pp', 'pc'] and curr_rel != 'pc':
        return False
    return True

def bfs_with_rel(dg, src):
    init_hints(dg)
    edge_to_traverse = [e for e in dg.out_edges(src)]
    while edge_to_traverse:
        curr_edge = edge_to_traverse.pop()
        prev_node, curr_node = curr_edge
        prev_rel = dg.edges[curr_edge]['rel']
        dg.nodes[curr_node]['hint'] += 1
        next_edges = [e for e in dg.out_edges(curr_node)
                      if e[1] != prev_node and valid_edge(prev_rel, dg.edges[e]['rel'])]
        edge_to_traverse.extend(next_edges)

def dump_path_diversity(fopen, dg, src):
    hints = [str(dg.nodes[n]['hint']) for n in sorted(list(dg.nodes()))]
    line = str(src) + ' ' + ' '.join(hints)
    fopen.write(line + '\n')
    fopen.flush()

def find_all_paths(dg, src, dst):
    """
    Find all simple paths for one src-dst pair.
    """
    return networkx.all_simple_paths(dg, src, dst)

def validate_path_rel(dg, path):
    prev_rel = 'cp'
    for e in zip(path[:-1], path[1:]):
        curr_rel = dg.edges[e]['rel']
        if prev_rel in ['pp', 'pc'] and curr_rel != 'pc':
            return False
        prev_rel = curr_rel
    return True

def find_all_valid_paths(dg, src, dst):
    return [p for p in find_all_paths(dg, src, dst) if validate_path_rel(dg, p)]

def random_pair(dg):
    import random
    return random.choices(list(dg.nodes()), k=2)

def main():
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <as-rel.txt> <output.txt> [from_asn]' % sys.argv[0])
        sys.exit()
    dg = load_as_rel(sys.argv[1])
    nodes = sorted(list(dg.nodes()))
    start_idx = 0
    if len(sys.argv) > 3:
        from_asn = int(sys.argv[3])
        start_idx = nodes.index(from_asn)

    with open(sys.argv[2], 'a') as fopen:
        for src in nodes[start_idx:]:
            print('Digging for path from AS', src)
            bfs_with_rel(dg, src)
            dump_path_diversity(fopen, dg, src)

    # src_as, dst_as = random_pair(dg)
    # print(src_as, dst_as)
    # valid_paths = find_all_valid_paths(dg, src_as, dst_as)
    # print(valid_paths)
    # print(len(valid_paths))

def advertise_main():
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <as-rel.txt> <iter_num>' % sys.argv[0])
        sys.exit()
    dg = load_as_rel(sys.argv[1])
    iter_num = int(sys.argv[2])
    init_ribs(dg)
    for i in range(iter_num):
        print('Start advertisement iteration', i)
        advertise(dg)
        print('Finished and dumping ribs', i)
        with open('ribs-iter-%d.json' % i, 'w') as fdump:
            dump_rib(dg, fdump)


if __name__ == '__main__':
    advertise_main()


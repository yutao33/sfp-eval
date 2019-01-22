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
                # dg.add_edge(src_as, dst_as, rel='pp')
                # dg.add_edge(dst_as, src_as, rel='pp')
                pass
            else:
                dg.add_edge(src_as, dst_as, rel='pc')
                # dg.add_edge(dst_as, src_as, rel='cp')
    return dg

def init_hints(dg):
    for n in dg.nodes():
        dg.nodes[n]['hint'] = 0

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


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <as-rel.txt> <output.txt> [from_asn]' % sys.argv[0])
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


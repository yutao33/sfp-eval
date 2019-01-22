#!/usr/bin/env python3

from as_rel import load_as_rel, valid_edge
from as_rel import load_as_country, get_subtopo

def init_hints(dg, hint_key='qhint'):
    for n in dg.nodes():
        dg.nodes[n][hint_key] = 0

def bfs_with_rel(dg, src, count=100, hint_key='qhint'):
    init_hints(dg, hint_key=hint_key)

    edge_to_traverse = [e for e in dg.out_edges(src)]
    while edge_to_traverse and count:
        count -= 1
        curr_edge = edge_to_traverse.pop()
        prev_node, curr_node = curr_edge
        prev_rel = dg.edges[curr_edge]['rel']
        dg.nodes[curr_node][hint_key] += 1
        next_edges = [e for e in dg.out_edges(curr_node)
                      if e[1] != prev_node and valid_edge(prev_rel, dg.edges[e]['rel'])]
        edge_to_traverse.extend(next_edges)


def bubblecast_match(dg):
    qcast_walk_nodes = {n for n in dg.nodes() if dg.node[n]['qhint']}
    dcast_walk_nodes = {n for n in dg.nodes() if dg.node[n]['dhint']}
    return qcast_walk_nodes.intersection(dcast_walk_nodes)


def read_stubs(filename, i):
    with open(filename, 'r') as f:
        line = f.readlines()[i]
        stubs = [int(n) for n in line.strip('\n').split()]
        return stubs


def main():
    import sys
    if len(sys.argv) < 5:
        print("Usage: %s <as-rel.txt> <as-country.txt> <stubs.txt> <line_num> [count]" % sys.argv[0])
        sys.exit()
    rdg = load_as_rel(sys.argv[1])
    load_as_country(sys.argv[2], rdg)
    dg = get_subtopo(rdg, 'US')
    count = 100
    if len(sys.argv) > 5:
        count = int(sys.argv[5])

    stubs = read_stubs(sys.argv[3], int(sys.argv[4]))

    total = 0
    success = 0

    for src in stubs:
        for dst in stubs:
            if src == dst:
                continue

            init_hints(dg, hint_key='qhint')
            bfs_with_rel(dg, src, count=count, hint_key='qhint')

            init_hints(dg, hint_key='dhint')
            bfs_with_rel(dg, dst, count=count, hint_key='dhint')

            match_nodes = bubblecast_match(dg)
            # print('number of nodes matching qcast/dcast: %d' % len(match_nodes))
            total += 1
            if len(match_nodes) > 0:
                success += 1
            print(len(match_nodes))


    print('*** %d/%d  src-dst pairs had at least one match' % success, total)


if __name__ == '__main__':
    main()

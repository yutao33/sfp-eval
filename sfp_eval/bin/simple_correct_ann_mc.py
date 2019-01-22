#!/usr/bin/env python

import sys

from random import randint


def random_network(domain=20, service_types=3,
                   dest_num_range=(1, 100), path_num_range=(1, 4)):
    net = {}
    for d in range(domain):
        dest = randint(*dest_num_range)
        path = randint(*path_num_range)
        net[d + 1] = (dest, service_types, path)
    return net


def random_block(net):
    dom = randint(1, len(net.keys()))
    return dom, randint(1, net[dom][0]), randint(1, net[dom][1]), randint(1, net[dom][2])


def random_flow(net):
    dom = randint(1, len(net.keys()))
    return dom, randint(1, net[dom][0]), randint(1, net[dom][1]), 1


def mc(domain=20, service_types=3,
       dest_num_range=(1, 100), path_num_range=(1, 4)):
    """
    Monte-Carlo simulation
    """
    net = random_network(domain, service_types,
                         dest_num_range, path_num_range)
    dom = len(net.keys())
    blocks = {random_block(net) for i in range(10 * dom)}
    flows = {random_flow(net) for i in range(200 * dom)}
    print(len(flows), len(blocks), len(flows.intersection(blocks)))


if __name__ == '__main__':
    if len(sys.argv) == 7:
        mc(int(sys.argv[1]), int(sys.argv[2]),
           (int(sys.argv[3]), int(sys.argv[4])),
           (int(sys.argv[5]), int(sys.argv[6])))
    elif len(sys.argv) == 5:
        mc(int(sys.argv[1]), int(sys.argv[2]),
           (int(sys.argv[3]), int(sys.argv[4])))
    elif len(sys.argv) == 3:
        mc(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 2:
        mc(int(sys.argv[1]))
    elif len(sys.argv) == 1:
        mc()
    else:
        sys.stdout.write("%s [domain_num [service_types [min_dests max_dests [min_paths max_paths]]]]\n" % sys.argv[0])

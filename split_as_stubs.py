#!/usr/bin/env python3

import math
import random
from as_rel import load_as_rel, load_as_type, get_stub_networks
from as_rel import load_as_country, get_subtopo

def split_stubs(stubs, K=50):
    random.shuffle(stubs)
    for i in range(math.ceil(len(stubs)/K)):
        start = i*K
        end = min(len(stubs), start+K)
        print(' '.join([str(n) for n in stubs[start:end]]))

def main():
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <as-rel.txt> <as-types.txt>')
        sys.exit()
    dg = load_as_rel(sys.argv[1])
    load_as_type(sys.argv[2], dg)
    stubs = get_stub_networks(dg)

    split_stubs(stubs)

def main1():
    import sys
    if len(sys.argv) < 4:
        print('Usage: %s <as-rel.txt> <as-types.txt> <as-country.txt>')
        sys.exit()
    dg = load_as_rel(sys.argv[1])
    load_as_type(sys.argv[2], dg)
    load_as_country(sys.argv[3], dg)
    sdg = get_subtopo(dg, 'US')
    stubs = get_stub_networks(sdg)

    split_stubs(stubs)


if __name__ == '__main__':
    main1()

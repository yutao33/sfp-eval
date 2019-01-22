#!/usr/bin/env python3

import numpy as np

def read_result(result_dir):
    import os
    total = 0
    success = 0
    for result_f in os.listdir(result_dir):
        with open(os.path.join(result_dir, result_f), 'r') as f:
            results = [int(n.strip('\n')) for n in f.readlines()]
            ftotal = len(results)
            fsuccess = len([n for n in results if n > 0])
            print('%s: %d/%d' % (result_f, fsuccess, ftotal))
            total += ftotal
            success += fsuccess
    return success, total

if __name__ == '__main__':
    import sys
    print('Summary: %d/%d' % (read_result(sys.argv[1])))

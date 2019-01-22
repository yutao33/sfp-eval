#!/usr/bin/env python3

import numpy as np

def read_result(result_dir):
    import os
    total = 0
    success = 0
    results = []
    for result_f in os.listdir(result_dir):
        with open(os.path.join(result_dir, result_f), 'r') as f:
            fresults = [int(n.strip('\n')) for n in f.readlines()]
            results.extend(fresults)
    return results

def plot_cdf(results, filepath=None, nonzero=False, **kwargs):
    import matplotlib.pyplot as plt
    import statsmodels.api as sm
    if nonzero:
        results = [n for n in results if n > 0]
    ecdf = sm.distributions.ECDF(results)
    results_range = range(max(results)+1)
    results_cdf = ecdf(results_range)

    fig = plt.figure(figsize=kwargs.get('figsize', None))

    plt.plot(results_range, results_cdf)
    plt.axis([0, max(results), 0, 1])
    plt.xlabel('Intersection Size')
    plt.ylabel('CDF')

    if filepath:
        fig.savefig(filepath, **kwargs)
        plt.close()

if __name__ == '__main__':
    import sys
    plot_cdf(read_result(sys.argv[1]), filepath=sys.argv[2], dpi=600, figsize=(8, 4), nonzero=False)

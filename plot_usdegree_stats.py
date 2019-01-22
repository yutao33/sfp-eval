#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
import statsmodels.api as sm

from as_rel import load_as_rel, load_as_country, get_subtopo

def plot_degree_stats(dg, filepath=None, **kwargs):
    degrees = np.array([dg.out_degree(n) for n in dg.nodes()])
    ecdf = sm.distributions.ECDF(degrees)
    # e_smooth = np.linspace(0, max(degrees), 10000)
    e_smooth = np.arange(1, max(degrees)+1)
    c_smooth = ecdf(e_smooth)
    fig = plt.figure(figsize=kwargs.get('figsize', None))
    # plt.plot(e_smooth, c_smooth)
    logfunc = np.vectorize(lambda x: np.log2(x) if x > 0 else 0)

    plt.plot(logfunc(e_smooth), c_smooth)
    plt.axis([0, np.log2(max(degrees)), 0, 1])
    plt.xlabel('Degree of AS')
    plt.ylabel('CDF')

    ax = plt.gca()
    x_format = lambda x, pos: r'$2^{%d}$' % x
    ax.xaxis.set_major_formatter(tkr.FuncFormatter(x_format))

    if filepath:
        fig.savefig(filepath, **kwargs)
        plt.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <as-rel.txt> <as-country.txt> <fig.pdf>')
    rdg = load_as_rel(sys.argv[1])
    load_as_country(sys.argv[2], rdg)
    dg = get_subtopo(rdg, 'US')
    plot_degree_stats(dg, filepath=sys.argv[3], dpi=600, figsize=(8, 4))


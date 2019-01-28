import json
import random
import multiprocessing
import pyasn
from matplotlib import pyplot as plt
from pytricia import PyTricia
from networkx import DiGraph, Graph
import pandas as pd
import numpy as np


DEFAULT_ASNDB = 'data/ipasn.20190116.1600.dat'
asndb = pyasn.pyasn(DEFAULT_ASNDB)


def get_vaild_dns_lists():
    j = json.load(open('data/dnsstat.json'))
    r = {}
    for k,v in j.items():
        r[int(k)] = list(v.keys())
    return r


def asn_lookup(ip):
    return asndb.lookup(ip)[0]


def load_as_graph():
    from as_rel import load_as_rel
    return load_as_rel("data/20181201.as-rel.txt")


def load_stub_str_list():
    with open('data/stubs.txt') as f:
        t = str(f.read())
        stubs = t.split()
    return stubs


def divide_stub_as():
    g = load_as_graph()
    stubs = []
    non_stubs = []
    for n in g.nodes:
        adj = g.adj[n]
        if all(a['rel'] == 'cp' for a in adj.values()):
            stubs.append(n)
        else:
            non_stubs.append(n)
    return stubs, non_stubs


def get_non_stub_as_list():
    return divide_stub_as()[1]


def get_stub_as_list():
    return divide_stub_as()[0]


def get_as_country(filepath="as-country.txt"):
    asn_country = {}
    country_asn_set = {}
    with open(filepath, 'r') as as_country:
        for line in as_country.readlines():
            asn, country = line.strip('\n').split('|')
            asn = int(asn)
            asn_country[asn]=country
            country_asn_set.setdefault(country, set())
            country_asn_set[country].add(asn)
    return asn_country, country_asn_set


def filter_stub_as(stat):
    g = load_as_graph()
    stat1 = {}
    upstream = set()
    for k,v in stat.items():
        if int(k) not in g.nodes:
            continue
        adj = g.adj[int(k)]
        if all(a['rel']=='cp' for a in adj.values()):
            stat1[k] = v
            upstream.update(list(adj.keys()))
    return stat1, upstream



def us_topo():
    dg = load_as_graph()
    from as_rel import load_as_country
    load_as_country('as-country.txt', dg)
    from as_rel import get_subtopo
    sdg = get_subtopo(dg, country='US')
    return sdg


def box_plot(x, y, df, name="fig", save=False):
    plt.clf()
    # sns.boxplot(x=x, y=y, data=df)
    # df.boxplot(column=[y], by=[x])
    data = dict(list(df.groupby(x)))
    xi = list(data.keys())
    xi.sort()
    yy = [list(data[i][y]) for i in xi]
    plt.boxplot(yy)
    plt.xticks(list(range(1,len(xi)+1)),xi)
    plt.ylabel(y)
    # sns.plt.ylim([0.,1.])
    if save:
        plt.savefig("result/"+name+".png", dpi=300, bbox_inches='tight')
    else:
        plt.show()


def dump_as_name(f="as-country-raw.txt"):
    lines = open(f).readlines()
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if len(l)>0]
    map={}
    for i in range(len(lines)//2):
        asn = lines[i*2]
        addr = lines[i * 2+1]
        map[asn[2:]]=addr
    return map
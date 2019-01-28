import json
import random
import multiprocessing
import pyasn
from matplotlib import pyplot as plt
from pytricia import PyTricia
from networkx import DiGraph, Graph
import pandas as pd
import numpy as np

from eval_ddos_utils import load_as_graph


def stat():
    alldf = []
    for i in range(19):
        df = pd.read_csv("/home/yutao/Desktop/data-dns-dsr6059" + "/" + str(i) + ".csv", dtype=str);
        alldf.append(df)
    df = pd.concat(alldf, axis=0, ignore_index=True)
    df1 = df[df['src_port'] == '53']
    df2 = df1[df1['dst'] == '144.154.222.228']
    a = np.array(df2.iplen.astype(int))
    b = a+14
    t1 = b.sum()
    print(t1/1996/(1000*1000)*8, "Mbps")  # 0.574 Mbps
    df1iplen = df1.iplen.astype(int)
    t2 = df1iplen.sum()
    print(t2 / 1996 / (1000 * 1000) * 8, "Mbps") # 0.569 Mbps
    df3 = df[df['dst_port'] == '53']
    df3iplen = df3.iplen.astype(int)
    t3 = df3iplen.sum()
    print(t3 / 1996 / (1000 * 1000) * 8, "Mbps")  # 0.002 Mbps
    df4 = df3[df3['src']=='144.154.222.228']


def dns_server_dist_plot():
    nameservers = pd.read_csv("data/nameservers.csv", dtype=str)
    country = nameservers.columns[2]
    ip = nameservers.columns[0]
    d  = nameservers[[country, ip]]
    num_list = d.groupby(country).count()[ip]
    num_list = num_list.sort_values(0,False)
    x=[]; y=[]
    for i in range(30):
        x.append(str(num_list.index[i]))
        y.append(num_list[i])
    xv = list(range(30))
    plt.bar(xv,y)
    plt.xticks(xv,x)
    plt.show()



def get_tier1_as():
    g = load_as_graph()
    ret = []
    for i in g.nodes:
        if all(adj['rel']!='cp' for adj in g.adj[i].values()):
            ret.append(i)
    return ret


def main():
    pass


if __name__ == "__main__":
    main()
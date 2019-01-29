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
    import random
    c_as = 6075
    # a="./lb_eval.py 1 data/20181201.as-rel.txt /home/pcl/8LStudentYuHaitao/tmp/jenson/flow-stats.70min.0.csv %d > result/1-1-23.txt &"%c_as
    # print(a)
    b = "./lb_eval.py 4 data/20181201.as-rel.txt /home/pcl/8LStudentYuHaitao/tmp/jenson/flow-stats.70min.0.csv %d %s > result/%d-4-%d.txt"

    TIER1 = [7018, 209, 3356, 3549, 4323, 3320, 3257, 4436, 286, 6830, 2914, 5511, 3491, 1239, 6453, 6762, 12956, 1299,
             701, 702, 703, 2828, 6461]

    MAXITEM = 50
    ruleslist = []
    inc_sel_list = []

    for n in range(1, 24):
        if len(inc_sel_list)==0:
            if len(TIER1)>MAXITEM:
                sel = random.sample(TIER1, MAXITEM)
            else:
                sel = TIER1
            all_set = set(TIER1)
            for item in sel:
                one_set = {item}
                inc_sel_list.append((one_set, all_set-one_set))
        else:
            old_len = len(inc_sel_list)
            while len(inc_sel_list)<MAXITEM:
                p,q = inc_sel_list[random.randint(0,old_len-1)]
                inc_sel_list.append((set(p), set(q)))
            for p,q in inc_sel_list:
                item = random.sample(q,1)[0]
                p.add(item)
                q.remove(item)
            new_inc_sel_list = []
            for p,q in inc_sel_list:
                in_new = False
                for p1,q1 in new_inc_sel_list:
                    if p==p1:

                        in_new=True
                        break
                if not in_new:
                    new_inc_sel_list.append((p,q))
            inc_sel_list = new_inc_sel_list

        testnum = 1
        for p,q in inc_sel_list:
            s = ",".join(str(i) for i in p)
            cmd = b%(c_as, s, n, testnum)
            target = "result/%d-4-%d.txt"% (n, testnum)
            ruleslist.append((target, cmd))
            testnum += 1
    # print(ruleslist)

    print("all:%s"%(" ".join(a[0] for a in ruleslist)))

    for target, cmd in ruleslist:
        print("%s:"%target)
        print("\t%s"%cmd)



if __name__ == "__main__":
    main()
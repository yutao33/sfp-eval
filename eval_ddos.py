import json
import random
import pyasn
from matplotlib import pyplot as plt
from pytricia import PyTricia
from networkx import DiGraph, Graph
import networkx as nx

import pandas as pd
import numpy as np
import multiprocessing

from sfp_eval.correctness.advertise import fp_bgp_advertise

#####################################################################

DEFAULT_ASNDB = 'data/ipasn.20190116.1600.dat'
asndb = pyasn.pyasn(DEFAULT_ASNDB)


def load_as_graph():
    from as_rel import load_as_rel
    return load_as_rel("data/20181201.as-rel.txt")


def load_stub_str_list():
    with open('data/stubs.txt') as f:
        t = str(f.read())
        stubs = t.split()
    return stubs


def us_topo():
    dg = load_as_graph()
    from as_rel import load_as_country
    load_as_country('as-country.txt', dg)
    from as_rel import get_subtopo
    sdg = get_subtopo(dg, country='US')
    return sdg

#####################################################################


def update_initial_rib(rib, prefix, overwrite=True):
    if overwrite or prefix not in rib:
        rib[prefix] = {0: []}
    else:
        rib[prefix].update({0: []})


def transform(g : Graph, c_as):
    g.ip_prefixes = PyTricia()
    for n in g.nodes():
        cust = set()
        prov = set()
        peer = set()
        for n1,n2 in g.edges(n):
            e=g.edges[n1, n2]
            if e['rel'] == 'pc':
                cust.add(n2)
            elif e['rel'] == 'cp':
                prov.add(n2)
            elif e['rel'] == 'pp':
                peer.add(n2)
        # g.node[n]['asn'] = n
        g.node[n]['customers'] = cust
        g.node[n]['providers'] = prov
        g.node[n]['peers'] = peer
        g.node[n]['ip-prefixes'] = set()
        # g.node[n]['ip'] = None
    g.node[c_as]['ip-prefixes'].add("1.1.1.1/24")

    g.ip_prefixes["1.1.1.1/24"]=c_as
    for node_id in g.nodes():
        node_obj = g.node[node_id]
        node_obj['adj-ribs-in'] = {n: PyTricia() for n in g.neighbors(node_id)}
        node_obj['rib'] = PyTricia()
        node_obj['adj-ribs-out'] = {n: PyTricia() for n in g.neighbors(node_id)}
        node_obj['local_policy'] = PyTricia()

    for n in g.nodes():
        g.node[n]['rib'] = PyTricia()
        for prefix in g.node[n]['ip-prefixes']:
            update_initial_rib(g.node[n]['rib'], prefix, True)
            # out_ribs = G.node[n]['adj-ribs-out']
            # for d in out_ribs:
            #     update_initial_rib(out_ribs[d], prefix, n)
        g.node[n]['adj-ribs-in'] = {n: PyTricia() for n in g.neighbors(n)}
        g.node[n]['adj-ribs-out'] = {n: PyTricia() for n in g.neighbors(n)}


def fp_bgp_simulate(dg : DiGraph, c_as: int, s_as_set : set):
    g = dg.copy()
    transform(g, c_as)
    for i in range(30):
        print(i)
        fp_bgp_advertise(g)
    routes = {}
    for a in s_as_set:
        if a not in g.nodes:
            print("a not in g.nodes")
            continue
        a_rib = g.node[a]['rib']
        assert isinstance(a_rib, PyTricia)
        r = a_rib.get("1.1.1.1/24")
        if r is None:
            print("route is None %s %s"%(str(c_as), str(a)))
            continue
        p = a
        r = []
        while p!=c_as:
            r.append(p)
            p = g.node[p]['rib'].get("1.1.1.1/24")
            assert p is not None
            p = p[0]
        r.append(c_as)
        routes[a] = r
    return routes


#####################################################################


def load_stat(file, client_as_num = 1, max_server_num = 100000):
    stat = json.load(open(file))
    stat, _ = filter_stub_as(stat)
    stat1 = {}
    stubs = load_stub_str_list()
    for k, v in stat.items():
        if str(k) not in stubs:
            continue
        v1 = stat1[int(k)] = {}
        for ip, vol in v.items():
            n = asndb.lookup(ip)[0]
            if n is not None:
                v1[ip] = {"as": n, "vol": float(vol)}
    # top traffic client AS
    t = [(k, sum(a["vol"] for a in v.values())) for k,v in stat1.items()]
    t.sort(key=lambda x: x[1], reverse=True)
    stat1 = {a[0]:stat1[a[0]] for a in t[:client_as_num]}
    # filter target server
    stat2 = {}
    for k, v in stat1.items():
        t = list(v.items())
        t.sort(key=lambda x: x[1]["vol"], reverse=True)
        stat2[k] = dict(t[:max_server_num])
    return stat2


def route_sim(statfile, tmpfile, client_as_num = 1, max_server_num = 100000):
    stat = load_stat(statfile, client_as_num, max_server_num)
    dg = load_as_graph()
    stat1 = {}
    for c_as,c_stat in stat.items():
        s_as_set = set(a["as"] for a in c_stat.values())
        # routes = bfs_bgp_simulate(dg, c_as, s_as_set)
        routes = fp_bgp_simulate(dg, c_as, s_as_set)
        print(routes)
        c_stat1 = {}
        for ip,v in c_stat.items():
            r = routes.get(v["as"])
            if r is not None:
                c_stat1[ip] = dict(v)
                c_stat1[ip]["route"] = r
            else:
                print("r is None")
        if c_stat1:
            stat1[c_as] = c_stat1

    json.dump(stat1, open(tmpfile,'w'), indent=4)


def route_sim_multiprocess(statfile, tmpfile, client_as_num = 1, max_server_num = 100000):
    stat = load_stat(statfile, client_as_num, max_server_num)
    print(stat)
    dg = load_as_graph()
    stat1 = {}
    pool = multiprocessing.Pool(processes=24)
    result_list = []
    for c_as,c_stat in stat.items():
        s_as_set = set(a["as"] for a in c_stat.values())
        # routes = bfs_bgp_simulate(dg, c_as, s_as_set)
        # routes = fp_bgp_simulate(dg, c_as, s_as_set)
        result = pool.apply_async(fp_bgp_simulate, (dg, c_as, s_as_set))
        result_list.append((c_as, c_stat, result))
    pool.close()
    pool.join()
    for c_as, c_stat, result in result_list:
        routes = result.get()
        print(routes)
        c_stat1 = {}
        for ip,v in c_stat.items():
            r = routes.get(v["as"])
            if r is not None:
                c_stat1[ip] = dict(v)
                c_stat1[ip]["route"] = r
            else:
                print("r is None")
        if c_stat1:
            stat1[c_as] = c_stat1
    json.dump(stat1, open(tmpfile,'w'), indent=4)


#####################################################################


def bandwidth_consume(stat: dict, fs_set, block_at_client_upstream=False, metric_func=None):
    total = .0
    fn = .0
    un = .0
    f_blocked = .0
    upstream_blocked = .0
    f_b_m = .0
    u_b_m = .0
    if fs_set is None:
        fs_set = set()
    if metric_func is None:
        metric_func = lambda x : x
    for c_stat in stat.values():
        for t in c_stat.values():
            metric = metric_func(t['vol'])
            total += metric *(len(t['route']) - 1)
            blocked = False
            i = 0
            for p in t['route'][:-1]:
                i += 1
                if p in fs_set:
                    blocked = True
                    break
            # if not blocked:
            #     print(t['route'])
            if blocked:
                fn += 1
                f_blocked += metric*(len(t['route']) - i)
                f_b_m += metric
            elif block_at_client_upstream:
                un += 1
                upstream_blocked += metric
                u_b_m += metric

    return total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m


def get_rate(stat, f_as, func):
    total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m = bandwidth_consume(stat, None, True, func)
    r1 = upstream_blocked / total
    total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m = bandwidth_consume(stat, f_as, True, func)
    r2 = f_blocked / total
    r3 = fn / (fn + un)
    r4 = (f_blocked + upstream_blocked) / total
    r5 = f_b_m / (f_b_m + u_b_m)
    return r1,r2,r3,r4,r5


tier1 = [7018,209,3356,3549,4323,3320,3257,4436,286,6830,2914,5511,3491,1239,6453,6762,12956,1299,701,702,703,2828,6461]


def select_f_as(n):
    return random.sample(tier1,n)


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


def block_traffic_sim(select_stat_file, sim_save_file, random_loop=1000):
    stat = json.load(open(select_stat_file))
    stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : x
    for n in range(1,24):
        print("n=%d"%n)
        for i in range(random_loop):
            print("i=%d"%i)
            f_as = set(select_f_as(n*10))
            r = get_rate(stat, f_as, func)
            data.append([n, *r])

    all_set = set(tier1)
    curr = set()
    for n in range(1,24):
        tmp_list = []
        for i_as in all_set-curr:
            n_set = curr | {i_as}
            r = get_rate(stat, n_set, func)
            tmp_list.append(([n, *r], n_set))
        tmp_list.sort(key=lambda x: x[0][4],reverse=True)
        data.append(tmp_list[0][0])
        curr = tmp_list[0][1]

    curr = set()
    for n in range(1,24):
        tmp_list = []
        for i_as in all_set-curr:
            n_set = curr | {i_as}
            r = get_rate(stat, n_set, func)
            tmp_list.append(([n, *r], n_set))
        tmp_list.sort(key=lambda x: x[0][4])
        data.append(tmp_list[0][0])
        curr = tmp_list[0][1]

    c0 = "Number of selected Tier 1 AS"
    c1 = "Option2 bandwidth saving"
    c2 = "FRIENDAS bandwidth saving"
    c3 = "FRIENDAS block rate"
    c4 = "Option3 Total bandwidth saving"
    c5 = "Option3 FRIENDAS block traffic rate"
    df = pd.DataFrame(data, columns=[c0, c1, c2, c3, c4, c5])
    df.to_csv(sim_save_file)


def block_sim_plot(sim_save_file, fig_save=False, fig_suffix=""):
    c0 = "Number of selected Tier 1 AS"
    c1 = "Option2 bandwidth saving"
    c2 = "FRIENDAS bandwidth saving"
    c3 = "FRIENDAS block rate"
    c4 = "Option3 Total bandwidth saving"
    c5 = "Option3 FRIENDAS block traffic rate"
    df = pd.read_csv(sim_save_file)

    def sim_plot(x, y, df, name=None):
        plt.clf()
        # sns.boxplot(x=x, y=y, data=df)
        # df.boxplot(column=[y], by=[x])
        data = dict(list(df.groupby(x)))
        xi = list(range(1,24))
        yy = [list(data[i][y]) for i in xi]
        plt.boxplot(yy)
        plt.xticks(xi)
        plt.xlabel(x)
        plt.ylabel(y)
        # sns.plt.ylim([0.,1.])
        if fig_save:
            plt.savefig("result/"+name+fig_suffix+".png", dpi=300, bbox_inches='tight')
        else:
            plt.show()

    sim_plot(c0, c1, df, "result-nf-bandwidth-saving")
    sim_plot(c0, c2, df, "result-f-bandwidth-saving")
    sim_plot(c0, c3, df, "result-f-block-rate")
    sim_plot(c0, c4, df, "result-f-total-bandwidth-saving")
    sim_plot(c0, c5, df, "result-f-block-traffic-rate")


#####################################################################


def bandwidth_consume_just_f(stat: dict, sel_set, metric_func=None):
    total_n = .0
    total_m = .0
    total_bw = .0
    b_n = .0
    b_m = .0
    b_bw = .0
    if sel_set is None:
        sel_set = set()
    if metric_func is None:
        metric_func = lambda x : x
    for c_stat in stat.values():
        for t in c_stat.values():
            metric = metric_func(t['vol'])
            total_n +=1
            total_m += metric
            total_bw += metric *(len(t['route']) - 1)
            blocked = False

            i = 0
            for p in t['route'][:-1]:
                i += 1
                if p in sel_set:
                    blocked = True
                    break
            # if not blocked:
            #     print(t['route'])
            if blocked:
                b_bw += metric*(len(t['route']) - i)
                b_m += metric
                b_n += 1
            else:
                print("not blocked")
    return total_n, total_m, total_bw, b_n, b_m, b_bw


def get_rate_just_f(stat: dict, sel_set, metric_func=None):
    r = bandwidth_consume_just_f(stat, sel_set, metric_func)
    return r[3]/r[0], r[4]/r[1], r[5]/r[2]


def bandwidth_consume_flowspec(stat: dict, sel_set, metric_func=None):
    total_n = .0
    total_m = .0
    total_bw = .0
    b_n = .0
    b_m = .0
    b_bw = .0
    if sel_set is None:
        sel_set = set()
    if metric_func is None:
        metric_func = lambda x : x
    for c_stat in stat.values():
        for t in c_stat.values():
            metric = metric_func(t['vol'])
            total_n +=1
            total_m += metric
            total_bw += metric *(len(t['route']) - 1)
            blocked = False
            i = 0
            route = t['route'][:-1]
            route.reverse()
            for p in route:
                if p in sel_set:
                    i+=1
                    blocked = True
                else:
                    break
            if blocked:
                b_bw += metric*i
                b_m += metric
                b_n += 1
    return total_n, total_m, total_bw, b_n, b_m, b_bw


def get_rate_flowspec(stat: dict, sel_set, metric_func=None):
    r = bandwidth_consume_flowspec(stat, sel_set, metric_func)
    return r[3]/r[0], r[4]/r[1], r[5]/r[2]


def get_all_as():
    stubs = load_stub_str_list()
    g = load_as_graph()
    stubs = set([int(a) for a in stubs])
    g_nodes = set([int(a) for a in g.nodes])
    return g_nodes - stubs


def block_traffic_sim_flowspec(select_stat_file, sim_save_file, random_loop=1000):
    stat = json.load(open(select_stat_file))
    stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : x

    all_as = get_all_as()
    for n in range(1000,20000, 1000):
        print("n=%d"%n)
        for i in range(random_loop):
            print("i=%d"%i)
            sel_as = set(random.sample(all_as, n))
            r = get_rate_flowspec(stat, sel_as, func)
            data.append([n, *r])

    c0 = "Number of selected Tier 1 AS"
    c1 = "c1"
    c2 = "FlowSpec block rate"
    c3 = "FlowSpec bandwidth saving"
    df = pd.DataFrame(data, columns=[c0, c1, c2, c3])
    df.to_csv(sim_save_file)
    print(sim_save_file)
    print("to_csv")



def block_sim_flowspec_plot(sim_save_file, fig_save=False, fig_suffix=""):
    c0 = "Number of selected Tier 1 AS"
    c1 = "c1"
    c2 = "FlowSpec block rate"
    c3 = "FlowSpec bandwidth saving"
    df = pd.read_csv(sim_save_file)
    print(df)

    def sim_plot(x, y, df, name=None):
        plt.clf()
        # sns.boxplot(x=x, y=y, data=df)
        # df.boxplot(column=[y], by=[x])
        data = dict(list(df.groupby(x)))
        xi = list(data.keys())
        xi.sort()
        yy = [list(data[i][y]) for i in xi]
        plt.boxplot(yy)
        plt.xticks(list(range(1,len(xi)+1)),xi)
        plt.xlabel("Number of FlowSpec AS")
        plt.ylabel(y)
        # sns.plt.ylim([0.,1.])
        if fig_save:
            plt.savefig("result/"+name+fig_suffix+".png", dpi=300, bbox_inches='tight')
        else:
            plt.show()

    sim_plot(c0, c2, df, "result-fspec-block-rate")
    sim_plot(c0, c3, df, "result-fspec-bandwidth-saving")


#####################################################################


def block_traffic_sim_both(select_stat_file, sim_save_file, random_loop=1000):
    stat = json.load(open(select_stat_file))
    stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : x

    all_as = get_all_as()

    # r = get_rate_flowspec(stat, all_as, func)
    r_f = get_rate_just_f(stat, all_as, func)
    print(r_f)

    for n in range(1000,10000, 1000):
        print("n=%d"%n)
        for i in range(random_loop):
            print("i=%d"%i)
            sel_as = set(random.sample(all_as, n))
            r = get_rate_flowspec(stat, sel_as, func)
            r_f = get_rate_just_f(stat, sel_as, func)
            data.append([n, *r, *r_f])

    c = [""] * 7
    c[0] = "Number of selected Tier 1 AS"
    c[1] = "c1"
    c[2] = "FlowSpec block rate"
    c[3] = "FlowSpec bandwidth saving"

    c[4] = "c4"
    c[5] = "FRIEND block rate"
    c[6] = "FRIEND bandwidth saving"
    df = pd.DataFrame(data, columns=c)
    df.to_csv(sim_save_file, index=False)
    print(sim_save_file)
    print("to_csv")


def block_sim_both_plot(sim_save_file, fig_save=False, fig_suffix=""):
    df = pd.read_csv(sim_save_file)
    c = df.columns
    print(df)

    def sim_plot(x, y, df, name=None):
        plt.clf()
        # sns.boxplot(x=x, y=y, data=df)
        # df.boxplot(column=[y], by=[x])
        data = dict(list(df.groupby(x)))
        xi = list(data.keys())
        xi.sort()
        yy = [list(data[i][y]) for i in xi]
        plt.boxplot(yy)
        plt.xticks(list(range(1,len(xi)+1)),xi)
        # plt.xlabel("Number of FlowSpec AS")
        plt.ylabel(y)
        # sns.plt.ylim([0.,1.])
        if fig_save:
            plt.savefig("result/"+name+"-" + fig_suffix + ".pdf", dpi=300, bbox_inches='tight')
        else:
            plt.show()

    df = df[df[c[2]] != 0]
    df['rate'] = df.apply(lambda x: x[c[5]]/x[c[2]], axis=1)
    print(df)

    # sim_plot(c[0], c[2], df, "result-fspec-block-rate")
    # sim_plot(c[0], c[3], df, "result-fspec-bandwidth-saving")
    # sim_plot(c[0], c[5], df, "result-f-just-block-rate")
    # sim_plot(c[0], c[6], df, "result-f-just-bandwidth-saving")

    sim_plot(c[0], 'rate', df, "result-rate-block-rate")








#####################################################################

def get_as_country(filepath="as-country.txt"):
    asn_country = {}
    country_asn_set = {}
    with open(filepath, 'r') as as_country:
        for line in as_country.readlines():
            asn, country = line.strip('\n').split('|')
            asn_country[asn]=country
            country_asn_set.setdefault(country, set())
            country_asn_set[country].add(asn)
    return asn_country, country_asn_set


def filter_stub_as_set(stubs):
    g = load_as_graph()
    stubs1 = []
    for k in stubs:
        if int(k) not in g.nodes:
            continue
        adj = g.adj[int(k)]
        if all(a['rel']=='cp' for a in adj.values()):
            stubs1.append(k)
    return stubs1


def gen_stat(statfile, stubs_num = 10, dns_server_num = 3000, stubs_country_set=None, dns_country_set=None):
    stubs = load_stub_str_list()
    stubs = filter_stub_as_set(stubs)
    asn_country, country_asn_set = get_as_country()

    if stubs_country_set:
        select_country_as = set()
        for i in stubs_country_set:
            select_country_as |= country_asn_set[i]
    else:
        select_country_as= set(asn_country.keys())

    select_stubs = set(stubs) & select_country_as

    select_stubs = random.sample(select_stubs, stubs_num)

    nameservers = pd.read_csv("data/nameservers.csv", dtype=str)

    country_col = nameservers.columns[2]
    ip_col = nameservers.columns[0]
    dns_ip_list = []
    for i, row in nameservers.iterrows():
        ip = str(row[ip_col])
        if ":" in ip:
            continue
        if dns_country_set:
            country = str(row[country_col])
            if country not in dns_country_set:
                continue
        dns_ip_list.append(ip)

    stat={}
    for asn in select_stubs:
        a = stat[asn] = {}
        for ip in random.sample(dns_ip_list,dns_server_num):
            a[ip]=1.0
    json.dump(stat, open(statfile,'w'), indent=4)


#####################################################################


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


def get_tier1_as():
    g = load_as_graph()
    ret = []
    for i in g.nodes:
        if all(adj['rel']!='cp' for adj in g.adj[i].values()):
            ret.append(i)
    return ret



if __name__ == "__main__":
    common = "gen-stat-20World-5000World"

    stat_file = "result/%s.json" % common
    select_stat_file = 'result/select-%s-20-max.json'%common
    sim_save_file_both = 'result/sim-both-%s-10-3000.csv' % common

    gen_stat(stat_file, 20, 5000, None, None)
    block_traffic_sim_both(select_stat_file, sim_save_file_both, 50)
    block_sim_both_plot(sim_save_file_both, fig_save=False, fig_suffix=common)




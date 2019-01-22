import json
import random
import pyasn
from matplotlib import pyplot as plt
from pytricia import PyTricia
from networkx import DiGraph, Graph

import seaborn as sns
import pandas as pd
import multiprocessing


from as_rel import load_as_rel
from sfp_eval.correctness.advertise import fp_bgp_advertise

#####################################################################

DEFAULT_ASNDB = 'data/ipasn.20190116.1600.dat'
asndb = pyasn.pyasn(DEFAULT_ASNDB)


def load_as_graph():
    return load_as_rel("data/20181201.as-rel.txt")


def load_stub_str_list():
    with open('data/stubs.txt') as f:
        t = str(f.read())
        stubs = t.split()
    return stubs

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


def verify(dg, sp):
    if len(sp)<=2:
        return True
    for i in range(1,len(sp)-1):
        pre = sp[i-1]
        cu = sp[i]
        ne = sp[i+1]
        r1 = dg.edges[pre,cu]["rel"]
        r2 = dg.edges[cu, ne]["rel"]
        if r1=="pp" or r1=="pc":
            assert r2 == "pc"
    return True


def bfs_bgp_simulate(dg : DiGraph, c_as: int, s_as_set : set):
    print("error")
    # g = dg.copy()
    # s_as = set(int(i) for i in s_as_set)
    # ll = set()
    # ll.add(c_as)
    # visited = set()
    # visited.update(ll)
    # g.node[c_as]["as_paths"]=[[c_as]]
    # for n in g.nodes:
    #     g.node[n]["visited"] = False
    # g.node[c_as]["visited"] = True
    # while True:
    #     ll_next = set()
    #     for k in ll:
    #         k_aspaths = g.node[k]["as_paths"]
    #         for m in g.adj[k]:
    #             mn = g.node[m]
    #             if not mn["visited"]:
    #                 assert isinstance(mn, dict)
    #                 mn.setdefault("as_paths",[])
    #                 for k_aspath in k_aspaths:
    #                     path_new = list(k_aspath)
    #                     path_new.append(m)
    #                     if len(k_aspath)==1:
    #                         mn["as_paths"].append(path_new)
    #                         ll_next.add(m)
    #                         break
    #                     else:
    #                         pre = k_aspath[-2]
    #                         cu = k_aspath[-1]
    #                         assert cu==k
    #                         rel = g.edges[pre, cu]['rel']
    #                         if rel=="pp" or rel=="pc":
    #                             rel1 = g.edges[cu,m]['rel']
    #                             if rel1=="pc":
    #                                 mn["as_paths"].append(path_new)
    #                                 ll_next.add(m)
    #                                 break
    #                         else:
    #                             mn["as_paths"].append(path_new)
    #                             ll_next.add(m)
    #                             break
    #     for k in ll_next:
    #         g.node[k]["visited"]=True
    #         print(len(g.node[k]["as_paths"]))
    #     ll = ll_next
    #     if len(ll)==0:
    #         break
    #     visited.update(ll)
    #     if s_as.issubset(visited):
    #         break
    # ret = {}
    # for s in s_as:
    #     ps = g.node[int(s)].get("as_paths")
    #     if ps is None:
    #         print("no route %s %s" %(str(c_as),str(s)))
    #         continue
    #     verify(dg, ps[0])
    #     ret[s]=ps[0]
    # return ret


#####################################################################


def load_stat(client_as_num = 20, max_server_num = 20):
    stat = json.load(open("result/ntpstat.json"))
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


def route_sim(tmpfile):
    stat = load_stat()
    print(stat)
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

    json.dump(stat1, open(tmpfile,'w'))


def route_sim_multiprocess(tmpfile):
    stat = load_stat()
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
    json.dump(stat1, open(tmpfile,'w'))


#####################################################################


def bandwidth_consume(stat: dict, fs_set, block_at_client_upstream=False, metric_func=None):
    total = .0
    fn = .0
    f_blocked = .0
    upstream_blocked = .0
    un = .0
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
            if blocked:
                fn += 1
                f_blocked += metric*(len(t['route']) - i)
            elif block_at_client_upstream:
                un += 1
                upstream_blocked += metric

    return total, fn, f_blocked, un, upstream_blocked


def select_f_as(n):
    tier1 = [7018,209,3356,3549,4323,3320,3257,4436,286,6830,2914,5511,3491,1239,6453,6762,12956,1299,701,702,703,2828,6461]
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


def block_traffic_sim(tmpfile):
    stat = json.load(open(tmpfile))
    stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : 1
    for n in range(1,24):
        for i in range(1000):
            total, fn, f_blocked, un, upstream_blocked = bandwidth_consume(stat, None, True, func)
            r1 = upstream_blocked / total
            f_as = set(select_f_as(n))
            total, fn, f_blocked, un, upstream_blocked = bandwidth_consume(stat, f_as, True, func)
            r2 = f_blocked / total
            r3 = fn / (fn+un)
            r4 = (f_blocked + upstream_blocked)/total
            data.append([n, r1, r2, r3, r4])
    c0 = "Number of selected Tier 1 AS"
    c1 = "Option2 bandwidth saving"
    c2 = "Option3 FRIENDAS bandwidth saving"
    c3 = "Option3 FRIENDAS block rate"
    c4 = "Option3 Total bandwidth saving"
    df = pd.DataFrame(data, columns=[c0, c1, c2, c3, c4])

    def sim_plot(x, y, df, name=None):
        plt.clf()
        sns.boxplot(x=x, y=y, data=df)
        # sns.plt.ylim([0.,1.])
        plt.show()
        # plt.savefig("result/"+name+".png", dpi=300, bbox_inches='tight')

    sim_plot(c0, c1, df, "result-nf-bandwidth-saving")
    sim_plot(c0, c2, df, "result-f-bandwidth-saving")
    sim_plot(c0, c3, df, "result-f-block-rate")
    sim_plot(c0, c4, df, "result-f-total-bandwidth-saving")




#####################################################################


if __name__ == "__main__":
    tmp = 'result/select-ntp-stat1.json'
    # route_sim(tmp)
    block_traffic_sim(tmp)

import json
import multiprocessing
from pytricia import PyTricia
from networkx import DiGraph, Graph

from sfp_eval.correctness.advertise import fp_bgp_advertise
from eval_ddos_utils import load_as_graph


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


def route_sim(stat_file, tmp_file):
    stat = json.load(open(stat_file))
    stat = {int(k):v for k,v in stat.items()}
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

    json.dump(stat1, open(tmp_file,'w'), indent=4)


def route_sim_multiprocess(stat_file, tmp_file):
    stat = json.load(open(stat_file))
    stat = {int(k): v for k, v in stat.items()}
    dg = load_as_graph()
    stat1 = {}
    pool = multiprocessing.Pool(processes=96)
    result_list = []
    for c_as,c_stat in stat.items():
        s_as_set = set(a["as"] for a in c_stat.values())
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
    json.dump(stat1, open(tmp_file,'w'), indent=4)

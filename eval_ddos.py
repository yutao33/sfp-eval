import json
import random

import pandas as pd

from eval_ddos_block_sim import block_traffic_sim_both, block_sim_both_plot
from eval_ddos_route_sim import route_sim
from eval_ddos_utils import load_as_graph, load_stub_str_list, get_stub_as_list, get_as_country, asn_lookup, \
    get_vaild_dns_lists


# #####################################################################
#
# def bandwidth_consume(stat: dict, fs_set, block_at_client_upstream=False, metric_func=None):
#     total = .0
#     fn = .0
#     un = .0
#     f_blocked = .0
#     upstream_blocked = .0
#     f_b_m = .0
#     u_b_m = .0
#     if fs_set is None:
#         fs_set = set()
#     if metric_func is None:
#         metric_func = lambda x : x
#     for c_stat in stat.values():
#         for t in c_stat.values():
#             metric = metric_func(t['vol'])
#             total += metric *(len(t['route']) - 1)
#             blocked = False
#             i = 0
#             for p in t['route'][:-1]:
#                 i += 1
#                 if p in fs_set:
#                     blocked = True
#                     break
#             # if not blocked:
#             #     print(t['route'])
#             if blocked:
#                 fn += 1
#                 f_blocked += metric*(len(t['route']) - i)
#                 f_b_m += metric
#             elif block_at_client_upstream:
#                 un += 1
#                 upstream_blocked += metric
#                 u_b_m += metric
#
#     return total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m
#
#
# def get_rate(stat, f_as, func):
#     total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m = bandwidth_consume(stat, None, True, func)
#     r1 = upstream_blocked / total
#     total, fn, f_blocked, un, upstream_blocked, f_b_m, u_b_m = bandwidth_consume(stat, f_as, True, func)
#     r2 = f_blocked / total
#     r3 = fn / (fn + un)
#     r4 = (f_blocked + upstream_blocked) / total
#     r5 = f_b_m / (f_b_m + u_b_m)
#     return r1,r2,r3,r4,r5
#
#
# tier1 = [7018,209,3356,3549,4323,3320,3257,4436,286,6830,2914,5511,3491,1239,6453,6762,12956,1299,701,702,703,2828,6461]
#
#
# def select_f_as(n):
#     return random.sample(tier1,n)
#
#
# def filter_stub_as(stat):
#     g = load_as_graph()
#     stat1 = {}
#     upstream = set()
#     for k,v in stat.items():
#         if int(k) not in g.nodes:
#             continue
#         adj = g.adj[int(k)]
#         if all(a['rel']=='cp' for a in adj.values()):
#             stat1[k] = v
#             upstream.update(list(adj.keys()))
#     return stat1, upstream
#
#
# def block_traffic_sim(select_stat_file, sim_save_file, random_loop=1000):
#     stat = json.load(open(select_stat_file))
#     stat, upstream = filter_stub_as(stat)
#     data = []
#     func = lambda x : x
#     for n in range(1,24):
#         print("n=%d"%n)
#         for i in range(random_loop):
#             print("i=%d"%i)
#             f_as = set(select_f_as(n*10))
#             r = get_rate(stat, f_as, func)
#             data.append([n, *r])
#
#     all_set = set(tier1)
#     curr = set()
#     for n in range(1,24):
#         tmp_list = []
#         for i_as in all_set-curr:
#             n_set = curr | {i_as}
#             r = get_rate(stat, n_set, func)
#             tmp_list.append(([n, *r], n_set))
#         tmp_list.sort(key=lambda x: x[0][4],reverse=True)
#         data.append(tmp_list[0][0])
#         curr = tmp_list[0][1]
#
#     curr = set()
#     for n in range(1,24):
#         tmp_list = []
#         for i_as in all_set-curr:
#             n_set = curr | {i_as}
#             r = get_rate(stat, n_set, func)
#             tmp_list.append(([n, *r], n_set))
#         tmp_list.sort(key=lambda x: x[0][4])
#         data.append(tmp_list[0][0])
#         curr = tmp_list[0][1]
#
#     c0 = "Number of selected Tier 1 AS"
#     c1 = "Option2 bandwidth saving"
#     c2 = "FRIENDAS bandwidth saving"
#     c3 = "FRIENDAS block rate"
#     c4 = "Option3 Total bandwidth saving"
#     c5 = "Option3 FRIENDAS block traffic rate"
#     df = pd.DataFrame(data, columns=[c0, c1, c2, c3, c4, c5])
#     df.to_csv(sim_save_file)
#
#
# def block_sim_plot(sim_save_file, fig_save=False, name_prefix=""):
#     c0 = "Number of selected Tier 1 AS"
#     c1 = "Option2 bandwidth saving"
#     c2 = "FRIENDAS bandwidth saving"
#     c3 = "FRIENDAS block rate"
#     c4 = "Option3 Total bandwidth saving"
#     c5 = "Option3 FRIENDAS block traffic rate"
#     df = pd.read_csv(sim_save_file)
#     box_plot(c0, c1, df, name_prefix + "nf-bandwidth-saving", fig_save)
#     box_plot(c0, c2, df, name_prefix + "f-bandwidth-saving", fig_save)
#     box_plot(c0, c3, df, name_prefix + "f-block-rate", fig_save)
#     box_plot(c0, c4, df, name_prefix + "f-total-bandwidth-saving", fig_save)
#     box_plot(c0, c5, df, name_prefix + "f-block-traffic-rate", fig_save)
#
#
# #####################################################################
#
#
# def bandwidth_consume_just_f(stat: dict, sel_set, metric_func=None):
#     total_n = .0
#     total_m = .0
#     total_bw = .0
#     b_n = .0
#     b_m = .0
#     b_bw = .0
#     if sel_set is None:
#         sel_set = set()
#     if metric_func is None:
#         metric_func = lambda x : x
#     for c_stat in stat.values():
#         for t in c_stat.values():
#             metric = metric_func(t['vol'])
#             total_n +=1
#             total_m += metric
#             total_bw += metric *(len(t['route']) - 1)
#             blocked = False
#
#             i = 0
#             for p in t['route'][:-1]:
#                 i += 1
#                 if p in sel_set:
#                     blocked = True
#                     break
#             # if not blocked:
#             #     print(t['route'])
#             if blocked:
#                 b_bw += metric*(len(t['route']) - i)
#                 b_m += metric
#                 b_n += 1
#             else:
#                 print("not blocked")
#     return total_n, total_m, total_bw, b_n, b_m, b_bw
#
#
# def get_rate_just_f(stat: dict, sel_set, metric_func=None):
#     r = bandwidth_consume_just_f(stat, sel_set, metric_func)
#     return r[3]/r[0], r[4]/r[1], r[5]/r[2]
#
#
# def bandwidth_consume_flowspec(stat: dict, sel_set, metric_func=None):
#     total_n = .0
#     total_m = .0
#     total_bw = .0
#     b_n = .0
#     b_m = .0
#     b_bw = .0
#     if sel_set is None:
#         sel_set = set()
#     if metric_func is None:
#         metric_func = lambda x : x
#     for c_stat in stat.values():
#         for t in c_stat.values():
#             metric = metric_func(t['vol'])
#             total_n +=1
#             total_m += metric
#             total_bw += metric *(len(t['route']) - 1)
#             blocked = False
#             i = 0
#             route = t['route'][:-1]
#             route.reverse()
#             for p in route:
#                 if p in sel_set:
#                     i+=1
#                     blocked = True
#                 else:
#                     break
#             if blocked:
#                 b_bw += metric*i
#                 b_m += metric
#                 b_n += 1
#     return total_n, total_m, total_bw, b_n, b_m, b_bw
#
#
# def get_rate_flowspec(stat: dict, sel_set, metric_func=None):
#     r = bandwidth_consume_flowspec(stat, sel_set, metric_func)
#     return r[3]/r[0], r[4]/r[1], r[5]/r[2]
#
#
# def get_all_as():
#     stubs = load_stub_str_list()
#     g = load_as_graph()
#     stubs = set([int(a) for a in stubs])
#     g_nodes = set([int(a) for a in g.nodes])
#     return g_nodes - stubs
#
#
# def block_traffic_sim_flowspec(select_stat_file, sim_save_file, random_loop=1000):
#     stat = json.load(open(select_stat_file))
#     stat, upstream = filter_stub_as(stat)
#     data = []
#     func = lambda x : x
#
#     all_as = get_all_as()
#     for n in range(1000,20000, 1000):
#         print("n=%d"%n)
#         for i in range(random_loop):
#             print("i=%d"%i)
#             sel_as = set(random.sample(all_as, n))
#             r = get_rate_flowspec(stat, sel_as, func)
#             data.append([n, *r])
#
#     c0 = "Number of selected Tier 1 AS"
#     c1 = "c1"
#     c2 = "FlowSpec block rate"
#     c3 = "FlowSpec bandwidth saving"
#     df = pd.DataFrame(data, columns=[c0, c1, c2, c3])
#     df.to_csv(sim_save_file)
#     print(sim_save_file)
#     print("to_csv")
#
#
# def block_sim_flowspec_plot(sim_save_file, fig_save=False, name_prefix=""):
#     c0 = "Number of selected Tier 1 AS"
#     c1 = "c1"
#     c2 = "FlowSpec block rate"
#     c3 = "FlowSpec bandwidth saving"
#     df = pd.read_csv(sim_save_file)
#     box_plot(c0, c2, df, name_prefix + "fspec-block-rate", fig_save)
#     box_plot(c0, c3, df, name_prefix + "fspec-bandwidth-saving", fig_save)
#
#
# #####################################################################
#
#
# def block_traffic_sim_both(select_stat_file, sim_save_file, random_loop=1000):
#     stat = json.load(open(select_stat_file))
#     stat, upstream = filter_stub_as(stat)
#     data = []
#     func = lambda x : x
#
#     all_as = get_all_as()
#
#     for n in range(1000,10000, 1000):
#         print("n=%d"%n)
#         for i in range(random_loop):
#             print("i=%d"%i)
#             sel_as = set(random.sample(all_as, n))
#             r = get_rate_flowspec(stat, sel_as, func)
#             r_f = get_rate_just_f(stat, sel_as, func)
#             data.append([n, *r, *r_f])
#
#     c = [""] * 7
#     c[0] = "Number of selected Tier 1 AS"
#     c[1] = "c1"
#     c[2] = "FlowSpec block rate"
#     c[3] = "FlowSpec bandwidth saving"
#
#     c[4] = "c4"
#     c[5] = "FRIEND block rate"
#     c[6] = "FRIEND bandwidth saving"
#     df = pd.DataFrame(data, columns=c)
#     df.to_csv(sim_save_file, index=False)
#     print(sim_save_file)
#     print("to_csv")
#
#
# def block_sim_both_plot(sim_save_file, fig_save=False, name_prefix=""):
#     df = pd.read_csv(sim_save_file)
#     c = df.columns
#     box_plot(c[0], c[2], df, name_prefix + "fspec-block-rate", fig_save)
#     box_plot(c[0], c[3], df, name_prefix + "fspec-bandwidth-saving", fig_save)
#     box_plot(c[0], c[5], df, name_prefix + "friend-block-rate", fig_save)
#     box_plot(c[0], c[6], df, name_prefix + "friend-just-bandwidth-saving", fig_save)
#     # df = df[df[c[2]] != 0]
#     # df['rate'] = df.apply(lambda x: x[c[5]]/x[c[2]], axis=1)
#     # sim_plot(c[0], 'rate', df, "result-rate-block-rate")


#####################################################################


#
#
# def filter_stub_as_set(stubs):
#     g = load_as_graph()
#     stubs1 = []
#     for k in stubs:
#         if int(k) not in g.nodes:
#             continue
#         adj = g.adj[int(k)]
#         if all(a['rel']=='cp' for a in adj.values()):
#             stubs1.append(k)
#     return stubs1


def generate_stat(stat_file, target_num = 10, dns_server_num = 3000, target_country_set=None, dns_country_set=None):
    stubs = get_stub_as_list()

    if target_country_set:
        asn_country, country_asn_set = get_as_country()
        select_country_as = set()
        for i in target_country_set:
            select_country_as |= country_asn_set[i]
        target_stubs = set(stubs) & select_country_as
    else:
        target_stubs = set(stubs)

    target_stubs = random.sample(target_stubs, target_num)
    print("target_stubs", target_stubs)

    nameservers = pd.read_csv("data/nameservers.csv", dtype=str)

    country_col = nameservers.columns[2]
    ip_col = nameservers.columns[0]
    dns_ip_list = []
    for i, row in nameservers.iterrows():
        ip = str(row[ip_col])
        if ":" in ip: # ipv6
            continue
        if dns_country_set:
            country = str(row[country_col])
            if country not in dns_country_set:
                continue
        dns_ip_list.append(ip)
    print("dns ip list length", len(dns_ip_list))

    g = load_as_graph()

    stat={}
    for asn in target_stubs:
        a = stat[asn] = {}
        random.shuffle(dns_ip_list)
        i = 0
        while dns_server_num>0:
            ip = dns_ip_list[i]
            asn = asn_lookup(ip)
            if asn and asn in g.nodes:
                a[ip] = {"bw": 1.0, "as":asn}
                dns_server_num-=1
            i+=1
            if i>=len(dns_ip_list):
                break

    vaild_dns_lists = get_vaild_dns_lists()
    for k,v in stat.items():
        vaild_dns_list = vaild_dns_lists.get(k,[])
        for dns in vaild_dns_list:
            if dns in v:
                v[dns]["inwhitelist"] = True

    json.dump(stat, open(stat_file, 'w'), indent=4)
    print("dumped")


def main():
    common = "gen-stat-20World-5000World-test1"

    stat_file = "result/%s.json" % common
    sim_route_file = 'result/%s-sim-route.json' % common
    sim_block_file_both = 'result/%s-sim-block.csv' % common

    # generate_stat(stat_file, 20, 5000, None, None)
    # route_sim(stat_file, sim_route_file)
    block_traffic_sim_both(sim_route_file, sim_block_file_both, list(range(1000,11000, 1000)) , 50)
    # block_sim_both_plot(sim_block_file_both, fig_save=True, name_prefix=common + "-")


if __name__ == "__main__":
    main()


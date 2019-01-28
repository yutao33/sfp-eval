import json
import random

import pandas as pd

from eval_ddos_utils import load_as_graph, load_stub_str_list, box_plot, filter_stub_as, get_non_stub_as_list


def bandwidth_consume_friend(stat: dict, sel_set, metric_func=None):
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

            if "inwhitelist" in t and t["inwhitelist"]:
                continue

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
    return total_n, total_m, total_bw, b_n, b_m, b_bw


def get_rate_friend(stat: dict, sel_set, metric_func=None):
    r = bandwidth_consume_friend(stat, sel_set, metric_func)
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
            if "inwhitelist" in t and t["inwhitelist"]:
                continue

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


# def block_sim_flowspec_plot(sim_save_file, fig_save=False, name_prefix=""):
#     c0 = "Number of selected Tier 1 AS"
#     c1 = "c1"
#     c2 = "FlowSpec block rate"
#     c3 = "FlowSpec bandwidth saving"
#     df = pd.read_csv(sim_save_file)
#     box_plot(c0, c2, df, name_prefix + "fspec-block-rate", fig_save)
#     box_plot(c0, c3, df, name_prefix + "fspec-bandwidth-saving", fig_save)



def block_traffic_sim_both(select_stat_file, sim_save_file, sel_num_list, random_loop=1000):
    stat = json.load(open(select_stat_file))
    stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : x

    non_stub_as_list = get_non_stub_as_list()

    for n in sel_num_list:
        print("n=%d"%n)
        for i in range(random_loop):
            print("i=%d"%i)
            sel_as = set(random.sample(non_stub_as_list, n))
            r = get_rate_flowspec(stat, sel_as, func)
            r_f = get_rate_friend(stat, sel_as, func)
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


def block_sim_both_plot(sim_save_file, fig_save=False, name_prefix=""):
    df = pd.read_csv(sim_save_file)
    c = df.columns
    box_plot(c[0], c[2], df, name_prefix + "fspec-block-rate", fig_save)
    box_plot(c[0], c[3], df, name_prefix + "fspec-bandwidth-saving", fig_save)
    box_plot(c[0], c[5], df, name_prefix + "friend-block-rate", fig_save)
    box_plot(c[0], c[6], df, name_prefix + "friend-bandwidth-saving", fig_save)
    # df = df[df[c[2]] != 0]
    # df['rate'] = df.apply(lambda x: x[c[5]]/x[c[2]], axis=1)
    # sim_plot(c[0], 'rate', df, "result-rate-block-rate")
    print("plot done!")


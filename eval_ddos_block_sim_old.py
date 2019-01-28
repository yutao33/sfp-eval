import json
import random

import pandas as pd

from eval_ddos_utils import box_plot, filter_stub_as


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


def block_sim_plot(sim_save_file, fig_save=False, name_prefix=""):
    c0 = "Number of selected Tier 1 AS"
    c1 = "Option2 bandwidth saving"
    c2 = "FRIENDAS bandwidth saving"
    c3 = "FRIENDAS block rate"
    c4 = "Option3 Total bandwidth saving"
    c5 = "Option3 FRIENDAS block traffic rate"
    df = pd.read_csv(sim_save_file)
    box_plot(c0, c1, df, name_prefix + "nf-bandwidth-saving", fig_save)
    box_plot(c0, c2, df, name_prefix + "f-bandwidth-saving", fig_save)
    box_plot(c0, c3, df, name_prefix + "f-block-rate", fig_save)
    box_plot(c0, c4, df, name_prefix + "f-total-bandwidth-saving", fig_save)
    box_plot(c0, c5, df, name_prefix + "f-block-traffic-rate", fig_save)



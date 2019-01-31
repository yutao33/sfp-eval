import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing

from eval_ddos_utils import box_plot, filter_stub_as, get_non_stub_as_list


def bandwidth_consume_friend(stat: dict, sel_set, metric_func=None):
    total_n = .0  # flow number
    total_m = .0  # flow metric
    total_bw = .0 # flow metric for each link
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
    r = total_n, total_m, total_bw, b_n, b_m, b_bw
    print("bandwidth_consume_friend", r)
    return r


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


def block_traffic_sim_friend_tier1(sim_route_file, sim_block_file, mp=False):
    stat = json.load(open(sim_route_file))
    data = []
    func = lambda x: x

    TIER1 = {7018, 209, 3356, 3549, 4323, 3320, 3257, 4436, 286, 6830, 2914, 5511, 3491, 1239, 6453, 6762, 12956, 1299,
             701, 702, 703, 2828, 6461}

    if not mp:
        for c_as, dns_server in stat.items():
            single_stat = {c_as: dns_server}
            r = bandwidth_consume_friend(single_stat, TIER1, None)
            data.append((int(c_as), *r))
    else:
        pool = multiprocessing.Pool(processes=96)
        result = []
        for c_as, dns_server in stat.items():
            single_stat = {c_as: dns_server}
            r = pool.apply_async(bandwidth_consume_friend, (single_stat, TIER1, None))
            result.append((c_as, r))
        pool.close()
        pool.join()
        for c_as,r in result:
            r1 = r.get()
            data.append((int(c_as), *r1))

    df = pd.DataFrame(data, columns=['c_as', 'total_n', 'total_m', 'total_bw', 'b_n', 'b_m', 'b_bw'])
    df.to_csv(sim_block_file, index=False)
    print("block_traffic_sim_friend_tier1 done!")


def block_sim_friend_tier1_plot(sim_block_file_both, fig_save=False, figpath_prefix="block_sim_friend_tier1_plot"):
    df = pd.read_csv(sim_block_file_both, dtype=float)
    c = df.columns

    a = df[c[5]] / df[c[2]]
#     print(len(a[a>0.90]))
    a.hist(cumulative = True,density=True, histtype='step',bins=1000,range=(0,1.1))
    plt.xlabel('Traffic Block Rate')
    plt.ylabel('CDF')
    plt.xlim([0,1.01])
    if plt.savefig:
        plt.savefig(figpath_prefix+"-blockrate-cdf.pdf", dpi=300, bbox_inches='tight')
    else:
        plt.show()

    plt.clf()
    a = df[c[6]] / df[c[3]]
    a.hist(cumulative=True, density=True, histtype='step', bins=1000, range=(0,1))
    plt.xlabel('Bandwidth Saving Rate')
    plt.ylabel('CDF')
    plt.xlim([0, 0.8])
    if fig_save:
        plt.savefig(figpath_prefix + "-bandwidthsavingrate-cdf.pdf", dpi=300, bbox_inches='tight')
    else:
        plt.show()
    print("block_sim_friend_tier1_plot")


def block_traffic_sim_both(select_stat_file, sim_save_file, sel_percent_list, random_loop=10, incremental=False):
    stat = json.load(open(select_stat_file))
    # stat, upstream = filter_stub_as(stat)
    data = []
    func = lambda x : x

    non_stub_as_list = get_non_stub_as_list()

    if incremental:
        inc_sel_list = [(set(), set(non_stub_as_list)) for i in range(random_loop)]
        for pn in sel_percent_list:
            n = int(len(non_stub_as_list)*pn)
            print("pn=%d" % pn)
            print("n=%d"%n)
            for i in range(random_loop):
                print("i=%d"%i)
                curr, remained = inc_sel_list[i]
                inc = random.sample(remained, n-len(curr))
                for ii in inc:
                    curr.add(ii)
                    remained.remove(ii)
                sel_as = set(curr)
                r = get_rate_flowspec(stat, sel_as, func)
                r_f = get_rate_friend(stat, sel_as, func)
                data.append([n, *r, *r_f])
    else:
        for pn in sel_percent_list:
            n = int(len(non_stub_as_list)*pn)
            print("pn=%d" % pn)
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
    print("block_traffic_sim_both done!")


def block_sim_both_plot(sim_save_file, fig_save=False, name_prefix=""):
    df = pd.read_csv(sim_save_file)
    c = df.columns
    # box_plot(c[0], c[2], df, name_prefix + "fspec-block-rate", fig_save)
    # box_plot(c[0], c[3], df, name_prefix + "fspec-bandwidth-saving", fig_save)
    # box_plot(c[0], c[5], df, name_prefix + "friend-block-rate", fig_save)
    # box_plot(c[0], c[6], df, name_prefix + "friend-bandwidth-saving", fig_save)

    # df = df[df[c[2]] != 0]
    # df['rate'] = df.apply(lambda x: x[c[5]]/x[c[2]], axis=1)
    # sim_plot(c[0], 'rate', df, "result-rate-block-rate")
    plot_subfunc(df, c[2], c[5], "Successful Blocking Rate", fig_save, name_prefix+"blockrate", ylim=[0,1])
    plot_subfunc(df, c[3], c[6], "Global Bandwidth Saving Rate", fig_save, name_prefix+"bandwidthsaving", ylim=[0,0.8])


def plot_subfunc(df, y1, y2, ylabel, save, name, ylim=None, boxprops=None):
    c = df.columns
    x = c[0]
    y = y1
    
    width=7
    fig=plt.figure(figsize=(width,width/2-0.8))

    plt.clf()

    width=0.35
    half_width = width/2

    data = dict(list(df.groupby(x)))
    xi = list(data.keys())
    xi.sort()
    yy = [list(data[i][y]) for i in xi]

    center_positions = np.linspace(1, len(xi), len(xi))

    p1 = plt.boxplot(yy, positions=center_positions+half_width, widths = width,
                     sym="",#patch_artist=True, 
                     boxprops=dict(linestyle="--", color="red"),
                     whiskerprops=dict(linestyle="--", color="red"))

    y = y2
    yy = [list(data[i][y]) for i in xi]
    p2 = plt.boxplot(yy, positions=center_positions - half_width, widths=width,
                     sym="",#patch_artist=True, 
                     boxprops=dict(linestyle="-", color="blue"),
                     whiskerprops=dict(linestyle="-", color="blue"))


    xtick = np.array(xi) / 17347.0 * 100
    xtick = np.around(xtick,1)
    xtick = ['{:g}'.format(i) for i in xtick]
    
    plt.xticks(center_positions, xtick)
    plt.ylabel(ylabel, fontsize=12)
    plt.xlabel("Percentage of deployed non-stub ASes", fontsize=12)
    plt.legend([p2['boxes'][0], p1['boxes'][0]], ['FRIEND', 'FlowSpec'], loc='upper left')

    plt.grid(axis='y',linestyle='-', linewidth=0.1)
    if ylim:
        plt.ylim(ylim)
    plt.xlim([0.60,19.4])
    if save:
        fig.savefig("result/" + name + ".pdf", dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    

    print("plot done!")


import json
import random

import pandas as pd
import numpy as np

from eval_ddos_block_sim import block_traffic_sim_both, block_sim_both_plot
from eval_ddos_route_sim import route_sim
from eval_ddos_utils import load_as_graph, get_stub_as_list, get_as_country, asn_lookup, get_vaild_dns_lists, \
    get_non_stub_as_list


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
        count = 0
        while count < dns_server_num:
            ip = dns_ip_list[i]
            asn = asn_lookup(ip)
            if asn and asn in g.nodes:
                a[ip] = {"vol": 1.0, "as":asn}
                count += 1
            i+=1
            if i>=len(dns_ip_list):
                break
        print("select dns list length",len(a))

    vaild_dns_lists = get_vaild_dns_lists()
    for k,v in stat.items():
        vaild_dns_list = vaild_dns_lists.get(k,[])
        for dns in vaild_dns_list:
            if dns in v:
                v[dns]["inwhitelist"] = True
                print("inwhitelist", dns)

    json.dump(stat, open(stat_file, 'w'), indent=4)
    print("dumped")


def main():
    common = "gen-stat-50World-5000World-01291553"

    stat_file = "result/%s.json" % common
    sim_route_file = 'result/%s-sim-route.json' % common
    sim_block_file_both = 'result/%s-sim-block.csv' % common

    generate_stat(stat_file, 50, 5000, None, None)
    route_sim(stat_file, sim_route_file)
    block_traffic_sim_both(sim_route_file, sim_block_file_both, np.linspace(0.05, 1.0, 20) , 50, incremental=200)
    block_sim_both_plot(sim_block_file_both, fig_save=True, name_prefix=common + "-")
    # print(len(get_non_stub_as_list()))

if __name__ == "__main__":
    main()


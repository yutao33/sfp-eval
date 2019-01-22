#!/usr/bin/env python{}{}
# from sfp_eval.correctness.flow import read_flows
from sfp_eval.bin.announcement_sim import read_flows
from sfp_eval.correctness.advertise import initiate_ribs, fp_bgp_advertise, correct_bgp_advertise, sfp_advertise
from sfp_eval.correctness.advertise import report_rib, report_local_policy, read_local_rib
from sfp_eval.correctness.policies import generate_local_policies
from sfp_eval.correctness.policies import manual_policy
from sfp_eval.correctness.policies import dump_tables
from sfp_eval.correctness.route import check_reachability
from sfp_eval.correctness.topology import read_topo
from sfp_eval.correctness.verify_triangles import read_triangle


def session_start(topo_filepath,
                  flow_filepath,
                  algorithm_type='1',
                  triangle=None,
                  **kwargs):

    if triangle:
        triangle = read_triangle(triangle)

    G = read_topo(topo_filepath)
    F = read_flows(flow_filepath)
    # print(len(F))
    # ASRelationsReader(relationship_filepath).augment_to_topology(G)
    generate_local_policies(G, triangle=triangle, **kwargs)
    # manual_policy(G)

    # dump_topo(G, 'results.yaml')

    # Find common reachable flows
    # H = G.copy()
    # H.ip_prefixes = G.ip_prefixes
    # initiate_ribs(H)
    # for i in range(10):
    #     fp_bgp_advertise(H)
    # F, _ = check_reachability(H, F, display=False)
    # H = G.copy()
    # H.ip_prefixes = G.ip_prefixes
    # initiate_ribs(H)
    # for i in range(10):
    #     correct_bgp_advertise(H)
    # F, _ = check_reachability(H, F, display=False)
    # H = G.copy()
    # H.ip_prefixes = G.ip_prefixes
    # initiate_ribs(H)
    # print('\t'.join(['hops'] + [str(i) for i in range(2, 11)] + ['loop', 'drop', 'transferred/bytes', 'failed/bytes']))

    if '1' in algorithm_type:
        # print("CGFP-BGP Evaluation")
        # cgfp_bgp_eval(G.copy(), F)
        H = G.copy()
        H.ip_prefixes = G.ip_prefixes
        initiate_ribs(H)
        for i in range(10):
            fp_bgp_advertise(H)
            # correct_bgp_advertise(H)
        # print('============================== RIB ============================')
        # report_rib(H, 23)
        # print('============================== LOCAL ============================')
        # report_local_policy(H, 29)
        # report_local_policy(H, 30)
        # print('CGFP', end='\t')
        check_reachability(H, F)
        # dump_tables(H, 'cgfp-bgp-tables.json')
    if '2' in algorithm_type:
        # print("CGC-BGP Evaluation")
        # cgc_bgp_eval(G.copy(), F)
        # manual_policy(G)
        H = G.copy()
        H.ip_prefixes = G.ip_prefixes
        initiate_ribs(H)
        for i in range(10):
            correct_bgp_advertise(H)
        # print('============================== RIB ============================')
        # report_rib(H, 23)
        # print('CGC', end='\t')
        R_F, UR_F = check_reachability(H, F)
        # dump_tables(H, 'cgc-bgp-tables.json')
        # for f in UR_F[:20]:
        #     src = H.ip_prefixes[f['src_ip']]
        #     dst = H.ip_prefixes[f['dst_ip']]
        #     print(f, src, dst)
    if '3' in algorithm_type:
        # print("SFP Evaluation")
        # fg_sfp_eval(G.copy(), F)
        H = G.copy()
        H.ip_prefixes = G.ip_prefixes
        # report_rib(G, 29)
        initiate_ribs(H)
        # report_rib(H, 29)
        for i in range(10):
            sfp_advertise(H)
        # print('============================== RIB ============================')
        # report_rib(H, 23)
        # report_rib(H, 45)
        # report_rib(H, 68)
        # print('============================== Adj-RIBs-In ============================')
        # report_rib(H, 23, table='adj-ribs-in', neigh=48)
        # report_rib(H, 23, table='adj-ribs-in', neigh=45)
        # report_rib(H, 45, table='adj-ribs-in', neigh=68)
        # report_rib(H, 68, table='adj-ribs-in', neigh=45)
        # report_rib(H, 30, table='adj-ribs-in', neigh=29)
        # print('============================== AS 29 Read Local ============================')
        # print(read_local_rib(H, 29, '128.211.128.0/19', 80))
        # print('============================== AS 30 Read Local ============================')
        # print(read_local_rib(H, 30, '128.211.128.0/19', 80))
        # print('============================== LOCAL ============================')
        # report_local_policy(H)
        # print('SFP', end='\t')
        _, UR_F = check_reachability(H, F)
        dump_tables(H, 'sfp-bgp-tables.json')
        # for f in UR_F[:20]:
        #     src = H.ip_prefixes[f['src_ip']]
        #     dst = H.ip_prefixes[f['dst_ip']]
        #     print(f, src, dst)
    if '4' in algorithm_type:
        # print("SFP Evaluation on CGC-BGP Reachable Flows")
        H = G.copy()
        H.ip_prefixes = G.ip_prefixes
        initiate_ribs(H)
        for i in range(10):
            sfp_advertise(H)
        _, UR_F = check_reachability(H, R_F)

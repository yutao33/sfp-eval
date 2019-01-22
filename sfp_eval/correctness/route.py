import math
from sfp_eval.correctness.advertise import get_last_hop


def default_routing_policy(node,
                           dst_ip,
                           dst_port=None,
                           src_ip=None,
                           src_port=None,
                           protocol='tcp',
                           **args):
    """
    Default routing policy for networks.

    Args:
        node: node id for the network.
        dst_ip: destination ip address.
        dst_port: optional.
        src_ip: optional.
        src_port: optional.
        protocol: optional.
        args: additional flow spec.

    Returns:
        The next hop of the give flow spec from this node.
    """
    if dst_ip not in node['rib']:
        return None
    else:
        prefix_actions = node['rib'][dst_ip]
        # print(dst_ip, dst_port, prefix_actions)
        return prefix_actions.get(dst_port, prefix_actions.get(0, None)) or None


def check_path(flow, G, routing_policy=default_routing_policy, debug=False):
    """
    Check the path of a given flow in the topology.

    Args:
        flow: The flow spec to check.
        G: The topology object.

    Returns:
        the AS-PATH length of the route.
        nan - no route
        inf - there is a loop
    """
    if debug:
        path = []
    loop_remover = {}
    src = G.ip_prefixes[flow['src_ip']]
    dst = G.ip_prefixes[flow['dst_ip']]
    if src == dst:
        if debug:
            return 1, [src]
        return 1
    d = src
    if debug:
        path = [src]
    dn = routing_policy(G.node[src], **flow)
    path_len = 1
    while dn:
        loop_remover[d] = loop_remover.get(d, 0) + 1
        # print d, p, loop_remover
        if loop_remover[d] > 1:
            # print(loop_remover)
            if debug:
                return math.inf, []
            return math.inf
        d = dn
        if debug:
            path.append(dn)
        dn = routing_policy(G.node[d], **flow)
        path_len += 1
    #  if loop_remover.get(8, 0) and loop_remover.get(57, 0):
        #  return 10
    #  if loop_remover.get(23, 0) and loop_remover.get(27, 0):
        #  return 10
    # if loop_remover.get(23, 0) and loop_remover.get(24, 0):
    #     return 10
    if d != dst:
        if debug:
            return math.nan, []
        return math.nan
    if debug:
        return path_len, path
    return path_len


debug_dict = {}


def check_reachability(G, F, max_len=10, debug=False, debug_num=None, display=True):
    as_length_dist = {}
    success_volume = 0
    unsuccess_volume = 0
    affected_volume = 0
    R_F = []
    UR_F = []
    # cnt = 0
    for f in F:
        if debug:
            global debug_dict
            result, path = check_path(f, G, debug=True)
            if debug_num not in debug_dict:
                debug_dict[debug_num] = dict()
            debug_dict[debug_num][(f["src_ip"], f["dst_ip"], f["start_time"],
                                   f["end_time"], f["volume"])] = (result, path)
        else:
            result = check_path(f, G)
        as_length_dist[result] = as_length_dist.get(result, 0) + 1
        if type(result) == float:
            unsuccess_volume += f['volume']
            UR_F.append(f)
            # if result == math.inf:
            #     src = G.ip_prefixes[f['src_ip']]
            #     dst = G.ip_prefixes[f['dst_ip']]
            #     print(f, src, dst)
            # if cnt < 200:
            #     src = G.ip_prefixes[f['src_ip']]
            #     dst = G.ip_prefixes[f['dst_ip']]
            #     print(f, src, dst)
            #     cnt += 1
        elif result > 1:
            success_volume += f['volume']
            R_F.append(f)
            if result == 10:
                affected_volume += f['volume']
    # print 'block_policies', 'deflection_policies'
    # print '%d\t%d' % policy_summary(G)
    if debug:
        as_len_nan = as_length_dist.pop(math.nan) if math.nan in as_length_dist else 0
        as_lens = sorted(as_length_dist.keys())
        as_lens.append(math.nan)
        as_length_dist[math.nan] = as_len_nan
        print('\t'.join([str(l) for l in as_lens]))
        print('\t'.join([str(as_length_dist[l]) for l in as_lens]))
    as_len_pdf = []
    for al in range(max_len - 1):
        as_len_pdf.append(as_length_dist.get(al + 2, 0))
    as_len_pdf.append(as_length_dist.get(math.inf, 0))
    as_len_pdf.append(as_length_dist.get(math.nan, 0))
    as_len_pdf.append(success_volume)
    as_len_pdf.append(unsuccess_volume)
    as_len_pdf.append(affected_volume)
    # Format: flow_num from 2 to max_len, inf, nan, success_volume, unsuccess_volume
    # print(as_length_dist)
    if display:
        print('\t'.join([str(a) for a in as_len_pdf]))
    return R_F, UR_F

import json

import numpy as np

DEFAULT_SERVICE_TYPES = {21: 0.1, 80: 0.1, 2801: 0.2, 8444: 0.3, 8445: 0.3}


class Flow(object):
    def __init__(self, obj):
        super(Flow, self).__init__()
        # TODO

    @property
    def src_ip(self):
        return self._src_ip

    @property
    def dst_ip(self):
        return self._dst_ip

    @property
    def volume(self):
        return self._volume

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def src_port(self):
        return self._src_port

    @property
    def dst_port(self):
        return self._dst_port

    @property
    def protocol(self):
        return self._protocol

    def from_dict(self, flow):
        self.src_ip = flow['src_ip']
        self.dst_ip = flow['dst_ip']
        self.start_time = flow['start_time']
        self.end_time = flow['end_time']
        self.volume = flow['volume']


def read_flows(file_path, port_dist=DEFAULT_SERVICE_TYPES):
    """
    Examples:
        [{
            "src_ip": "10.0.0.1",
            "src_port": 22,
            "dst_ip": "10.0.10.1",
            "dst_port": 80,
            "protocol": "tcp",
            "start_time": 1516292713,
            "end_time": 1516313885,
            "volume": 4089456904
        }]

        required: src_ip, dst_ip, start_time, end_time, volume
        optional: src_port, dst_port, protocol
    """
    data = json.load(open(file_path))
    flows = []
    for d in data:
        flow = Flow()
        flow.from_dict(d)
        if not d.get('dst_port', None):
            flow.dst_port = np.random.choice(
                list(port_dist.keys()), p=list(port_dist.values()))
        flows.append(flow)
    return flows

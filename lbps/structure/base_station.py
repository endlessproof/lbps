import logging
import random
import math
import sys

sys.path.append('../..')
from . import device
from src import bearer
from itertools import count


class BaseStation(device.OneHopDevice):
    count = count(0)

    def __init__(self, name=None):
        super(BaseStation, self).__init__()
        self.name = (
            name or '_'.join(
                [self.__class__.__name__, str(next(self.count))]
            )
        )

    def connect_to(self, dest, CQI, flow):
        assert (
            isinstance(dest, device.OneHopDevice) or
            isinstance(dest, device.TwoHopDevice)
            )

        self.append_bearer(bearer.Bearer(self, dest, CQI, flow))

        if isinstance(dest, device.OneHopDevice):
            dest.append_bearer(bearer.Bearer(dest, self, CQI, flow))
            logging.debug('Build direct bearer (%s, %s)' % (self.name, dest.name))
        elif isinstance(dest, device.TwoHopDevice):
            dest.backhaul.append_bearer(bearer.Bearer(dest, self, CQI, flow))
            logging.debug('Build backhaul bearer (%s, %s)' % (self.name, dest.name))

    def simulate_timeline(self, simulation_time):
        users = [ue for rn in self.target_device for ue in rn.access.target_device]
        timeline = { i: [] for i in range(simulation_time)}

        for ue in users:
            for b in ue.bearer:

                # generate packet arrival time in exponential distribution
                arrival_time = [0]
                while arrival_time[-1] < simulation_time-1 and ue.lambd:
                    variant = random.expovariate(ue.lambd)
                    arrival_time.append(arrival_time[-1]+variant)
                arrival_time[-1] >= simulation_time-1 and arrival_time.pop()
                arrival_time.pop(0)
                logging.debug(
                    'Generate %d packets for %s' % (len(arrival_time), ue.name))

                # generate packet
                for t in arrival_time:
                    timeline[math.ceil(t)].append({
                        'device': ue,
                        'flow': b.flow,
                        'size': b.flow.packet_size,
                        'delay_budget': b.flow.delay_budget,
                        'bitrate': b.flow.bitrate,
                        'arrival_time': t
                    })

        for i in timeline.values():
            i = sorted(i, key=lambda x: x['arrival_time'])

        return timeline

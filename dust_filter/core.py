#!/usr/bin/python3

import sys
import time
import csv

import pigpio

from .PPD42NS import Sensor
from .mdsutils.datefile import DateFile
from .control import DFControl
from .motor import Motor
from .config import ArgumentParser

DEFAULT_CONFIG = """
sensor_gpio: null
motor_gpios: [null, null, null]
poll: 5 # seconds
thresholds: [0.01, 0.02, 0.04, 0.08]
mode: Auto  # Auto, Off, Low, Med, High
data_prefix: data/dust_
dummy = false
"""

CONFIG_PATH=['./dfconfig.yaml']

#    config = {'sensor_gpio': 25,
#              'motor_gpios': [21, 26, 20],
#              'poll': 5,# seconds
#              'thresholds': [0.01, 0.02, 0.04, 0.08]

MODEMAP={0: 'Off',
         1: 'Low',
         2: 'Med',
         3: 'High',
         'Auto': 'Auto'}
for k, v in MODEMAP.items(): MODEMAP[v] = k




class DustFilter(object):
    def __init__(self, plot_conn, web_conn):
        self.last_r = 0 # this is a brute-force hack to reject outliers... I
                   # should make it cleaner at some point
        self.config()
        self.plot_conn = plot_conn
        self.web_conn = web_conn
        self.mode = 'Auto'

        c = self.conf
        if c.dummy:
            from dust_filter.motor import _DummyPi
            self.pi = _DummyPi()
        else:
            try: import pigpio
            except ImportError:
                print('Failed to import pigpio - running on a pi?')
                print('Use -D')
                sys.exit(1)
            self.pi = pigpio.pi()

        self.sensor = Sensor(self.pi, c.sensor_gpio)
        self.datalog = DateFile(c.data_prefix, '%Y-%m-%d')
        self.control = DFControl(c.thresholds)
        motor = Motor(self.pi, c.motor_gpios)
        writer = csv.writer(self.datalog)

    def config(self):
        p = ArgumentParser()
        a = p.parse_args()
        a('-D', '--dummy', action='store_true',
          help='use a dummy pigio instance for testing')
        args = p.parse_args()
        c_cl = convert_command_line_args(p.parse_args)
        c_files = load_config_files(CONFIG_PATH)
        c_default = load_config(DEFAULT_CONFIG, source='<default>')
        configs = [c_default] + c_files + [c_cl]
        self.conf = merge_configs(configs)

    def dump_config(self):
        # save mode and thresholds
        pass

    def read_sensor(self):
        t = self._time()
        r = self.sensor.read()
        if r > 0.8:
            r = self.last_r # log... log it!
        else:
            self.last_r = r
        level = self.control.update(r, t)
        self.writer.writerow( (t, r, level) )
        self.datalog.flush()
        if self.mode == 'Auto':
            self.motor.set(level)
        else:
            self.motor.set(self.conf.mode)

        datapoint = (t, level, r, self.control._sv)
        self.send_plot_data( datapoint )

    def send_plot_data(self, datapoint=None):
        dp = self.datapoints
        if datapoint is not None: dp.append(datapoint)
        now = self._time()
        while dp[0][0] < now - self.plot_length:
            dp.pop(0)
        t, l, rr, ra = tuple(zip(*dp))
        thresh = self.conf.thresholds
        self.plot_conn.send( (t, l, rr, ra, thresh) )
        
    def select_helpers(self, until):
        timeout = until - self._time()
        if timeout < 0: timeout = 0

        r, w, x = select.select([self.web_conn, self.plot_conn],
                                [], [], timeout/self.speedup)
        if not r: return
        # we have something to do!
        if self.plot_conn in r:
            self.plot_response()
        if self.web_conn in r:
            self.web_request()

    def plot_response(self):
        self._plot_data = self.plot_conn.recv()
        self._plot_time = self._time()

    def web_request(self):
        meth, args, kwargs = self.web_conn.recv()
        resp = getattr(self, '_web_'+meth)(*args, **kwargs)
        self.web_conn.send(resp)

    def _web_index(self):
        r = {'selected': MODEMAP[self.mode],
             'active': MODEMAP[self.motor.get()]}
        return r

    def _web_image(self):
        return self._plot_data
    
    def _web_mode(self, mode):
        self.conf.mode = MODEMAP[mode]
        if self.conf.mode == 'Auto': self.motor.set(level)
        else:                        self.motor.set(self.conf.mode)
        self.dump_config()

    def _web_thresholds(self, thresholds):
        self.conf.thresholds = thresholds
        level = self.control.set_thresholds(thresholds)
        self.send_plot_data()
        if self.conf.mode == 'Auto': self.motor.set(level)
        else:                        self.motor.set(self.conf.mode)
        self.dump_config()
    
    def loop(self):
        next_read_time = math.ceil(self._time())
        while True:
            self.select_helpers(next_read_time)
            if self._time() > next_read_time:
                self.read_sensor()
                next_read_time = next_read_time + self.config.poll
        self.pi.stop() # Disconnect from Pi.

    speedup = 1.0
    def _time(self):
        return time.time()



def start_helpers():
    multiprocessing.set_start_method('forkserver')

    # for the plotting process
    plot_conn, plot_child_conn = multiprocessing.Pipe()
    multiprocessing.Process(target=plots.plotproc,
                            args=(plot_child_conn,)).start()

    # for the web server process
    web_conn, web_child_conn = multiprocessing.Pipe()
    multiprocessing.Process(target=dfserver.main,
                            args=(web_child_conn,)).start()

    return plot_conn, web_conn

def main():
    pass

if __name__ == '__main__':
    main()

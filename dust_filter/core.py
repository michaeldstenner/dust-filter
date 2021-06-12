
#!/usr/bin/python3

import sys
import time
import csv
import multiprocessing
import logging
import math
import select
import pprint

from . import plots
from . import dfserver

from .PPD42NS import Sensor
from .mdsutils.datefile import DateFile
from .control import DFControl
from .motor import Motor
from .mdsutils import config

DEFAULT_CONFIG = """
sensor_gpio: 25
motor_gpios: [21, 26, 20]
poll: 5 # seconds
thresholds: [0.02, 0.04, 0.08, 0.16]
mode: Auto  # Auto, Off, Low, Med, High
data_prefix: log/dust_
log_prefix: log/dust.log
mock: false
mock_start: 1589722589.97081
mock_speed: 1.0
"""

CONFIG_PATH=['/etc/df2000.yaml', './df2000.yaml']

#    config = {'sensor_gpio': 25,
#              'motor_gpios': [21, 26, 20],
#              'poll': 5,# seconds
#              'thresholds': [0.01, 0.02, 0.04, 0.08]

MODEMAP={0: 'Off',
         1: 'Low',
         2: 'Med',
         3: 'High',
         'Auto': 'Auto'}
for k, v in list(MODEMAP.items()): MODEMAP[v] = k

class DustFilter(object):
    def __init__(self, plot_conn, web_conn):
        self.last_r = 0 # this is a brute-force hack to reject outliers... I
                   # should make it cleaner at some point
        self.config()
        self.plot_conn = plot_conn
        self.web_conn = web_conn
        self.speedup = 1.0
        self.datapoints = []
        self.plot_length = 5*60
        self._plot_data = None
        self.level = 0

        c = self.conf
        if c.mock:
            from .mock_classes import MockPi, MockSensor
            self._time = self._mock_time
            self.pi = MockPi()
            self.sensor = MockSensor(self._time)
            self.speedup = c.mock_speed
        else:
            try:
                import pigpio
            except ImportError:
                print('Failed to import pigpio - running on a pi?')
                print('Use -M to run with mock hardware')
                sys.exit(1)
            self.pi = pigpio.pi()
            self.sensor = Sensor(self.pi, c.sensor_gpio)

        self.motor = Motor(self.pi, c.motor_gpios)
        self.datalog = DateFile(c.data_prefix, '%Y-%m-%d')
        self.control = DFControl(c.thresholds)
        self.writer = csv.writer(self.datalog)

    def config(self):
        p = config.ArgumentParser()
        a = p.add_argument
        a('-M', '--mock', action='store_true',
          help='use mock hardware and data for testing')
        a('-C', '--conf',
          help='append FILE to the config file path')
        a('--dump-config', action='store_true',
          help='dump the config and exit')
        args = p.parse_args()
        c_cl = config.convert_command_line_args(args)
        if c_cl.conf: CONFIG_PATH.append(c_cl.conf)
        c_files = config.load_config_files(CONFIG_PATH)
        c_default = config.load_config(DEFAULT_CONFIG, source='<default>')
        configs = [c_default] + c_files + [c_cl]
        self.conf = config.merge_configs(configs)
        self.conf._configs = configs
        if self.conf.dump_config:
            pprint.pprint(self.conf)
            self.exit()


    def exit(self):
        for c in multiprocessing.active_children():
            c.terminate()
        sys.exit()

    def dump_config(self):
        # save mode and thresholds
        pass

    def read_sensor(self):
        t = self._time()
        r = self.sensor.read()
        if r > 0.8:
            logging.warn('HIGH READING: read r = %0.5f, suppressing', r)
            r = self.last_r # log... log it!
        else:
            self.last_r = r
        self.level = self.control.update(r, t)
        logging.debug('read r=%0.4f from sensor, level=%d', r, self.level)
        self.writer.writerow( (t, r, self.level) )
        self.datalog.flush()
        if self.conf.mode == 'Auto':
            self.motor.set(self.level)
        else:
            self.motor.set(self.conf.mode)

        datapoint = (t, self.level, r, self.control._sv)
        self.send_plot_data( datapoint )

    def send_plot_data(self, datapoint=None):
        dp = self.datapoints
        if datapoint is not None: dp.append(datapoint)
        now = self._time()
        while dp[0][0] < now - self.plot_length:
            dp.pop(0)
        t, l, rr, ra = tuple(zip(*dp))
        thresh = self.conf.thresholds
        if len(t) < 4: return
        logging.debug('sending plot data (%d points)', len(t))
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
        logging.debug('receiving plot image')
        self._plot_data = self.plot_conn.recv()
        self._plot_time = self._time()

    def web_request(self):
        try:
            meth, args, kwargs = self.web_conn.recv()
        except EOFError:
            logging.exception('EOF received from web server process')
            self.exit()
        except Exception as e:
            logging.exception('exception raised in web_request')
            return None
        logging.debug('handling web request: (%s, %s, %s)',
                      meth, args, kwargs)
        try:
            resp = getattr(self, '_web_'+meth)(*args, **kwargs)
            self.web_conn.send(resp)
        except Exception as e:
            logging.exception('exception raised in web_request: (%s, %s, %s)',
                              meth, args, kwargs)
            return None

        logging.debug('web request: (%s, %s, %s) -> %20.20s',
                      meth, args, kwargs, resp)

    def _web_index(self):
        r = {'selected': MODEMAP[self.conf.mode],
             'active': MODEMAP[self.motor.get()],
             'average': self.control._sv * 100,
             'thresholds': [ 100 * t for t in self.conf.thresholds] }
        return r

    def _web_image(self):
        logging.debug('sending plot image to web server')        
        return self._plot_data
    
    def _web_mode(self, mode):
        oldmode = self.conf.mode
        self.conf.mode = MODEMAP[mode]
        logging.info('setting mode from %s to %s at user command',
                     oldmode, self.conf.mode)
        if self.conf.mode == 'Auto': self.motor.set(self.level)
        else:                        self.motor.set(self.conf.mode)

    def _web_settings(self, settings=None):
        if settings is not None:
            self._apply_settings(settings)
        th = [ t * 100 for t in self.conf.thresholds ]
        ret = {'thresholds': th}
        return ret

    def _apply_settings(self, settings):
        logging.info('settings: %s', settings)
        thresholds = settings.get('thresholds')
        if not thresholds: return
        thresholds = [ t / 100.0 for t in thresholds ]
        self.conf.thresholds = thresholds
        self.level = self.control.set_thresholds(thresholds)
        self.send_plot_data()
        if self.conf.mode == 'Auto': self.motor.set(self.level)
        else:                        self.motor.set(self.conf.mode)
        
        self.dump_config()
        
    def loop(self):
        next_read_time = math.ceil(self._time())
        while True:
            self.select_helpers(next_read_time)
            if self._time() > next_read_time:
                self.read_sensor()
                next_read_time = next_read_time + self.conf.poll
        self.pi.stop() # Disconnect from Pi.

    def _time(self):
        return time.time()

    def _mock_time(self):
        now = time.time()
        if not hasattr(self, '_real_start_time'):
            self._real_start_time = now
        t = (now - self._real_start_time) \
            * self.speedup + self.conf.mock_start
        #print('%f -> %f' % (now, t))
        return t

def log_process(logq):
    root = logging.getLogger()
    hf = logging.handlers.TimedRotatingFileHandler
    logfile = logq.get()
    h = hf(logfile, 'midnight', backupCount=7)
    fmt = '%(asctime)s %(processName)-6s %(name)-5.5s ' \
        '%(levelname)-5.5s %(message)s'
    f = logging.Formatter(fmt)
    h.setFormatter(f)
    root.addHandler(h)
    root.setLevel(logging.DEBUG)

    logging.info('================================')
    logging.info('================================')
    logging.info('starting logger process')
    while True:
        try:
            record = logq.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys, traceback
            print('Exception in log process:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def start_helpers():
    multiprocessing.set_start_method('forkserver')

    logq = multiprocessing.Queue(-1)
    h = logging.handlers.QueueHandler(logq)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)

    multiprocessing.current_process().name = 'core'
    
    # for the logging process
    multiprocessing.Process(target=log_process, name='logger',
                            args=(logq,)).start()

    # for the plotting process
    plot_conn, plot_child_conn = multiprocessing.Pipe()
    multiprocessing.Process(target=plots.plotproc, name='plot',
                            args=(logq, plot_child_conn)).start()

    # for the web server process
    web_conn, web_child_conn = multiprocessing.Pipe()
    multiprocessing.Process(target=dfserver.main, name='web',
                            args=(logq, web_child_conn)).start()

    return logq, plot_conn, web_conn

def main():
    logq, plot_conn, web_conn = start_helpers()
    df = DustFilter(plot_conn, web_conn)
    logq.put(df.conf.log_prefix)
    logging.info('starting DustFilter instance')
    df.loop()

if __name__ == '__main__':
    main()

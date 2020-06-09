import pathlib
import time
import csv

class MockPi(object):
    def __init__(self):
        self.gpios = {}
    def read(self, gpio):
        return self.gpios.get(gpio, 0)
    def write(self, gpio, val):
        self.gpios[gpio] = val

class FileInterpolator(object):
    def __init__(self, fn):
        #print('opening %s' % fn)
        self.fo = open(fn)
        self.lines = csv.reader(self.fo, delimiter=',')
        self.t1, self.v1, _ = map(float, next(self.lines))
        self.t2, self.v2, _ = map(float, next(self.lines))

    def get(self, t):
        #print(t)
        while t > self.t2:
            self.t1, self.v1,   = self.t2, self.v2
            self.t2, self.v2, _ = map(float, next(self.lines))
        v = self.v1 + (self.v2 - self.v1) * \
            (t - self.t1) / (self.t2 - self.t1)
        #print('1:  %10f %10f' % (self.t1, self.v1))
        #print('2:  %10f %10f' % (self.t2, self.v2))
        #print('    %10f %10f' % (t, v))
        return v

class MockSensor(object):
    def __init__(self, timefunc, datafile=None):
        self._time = timefunc
        if datafile is None:
            datafile = pathlib.Path(__file__).parent.joinpath('dustlog.csv')
        self.datafile = datafile
        self.fi = FileInterpolator(self.datafile)
        
    def read(self):
        return self.fi.get(self._time())

if __name__ == '__main__':
    start = time.time()
    def timefunc():
        return time.time() - start + 1589722589.97081
    ms = MockSensor(timefunc)
    while True:
        print(ms.read())
        time.sleep(1)

import time

class Motor(object):
    def __init__(self, pi, gpios=None, limit=1):
        self.pi = pi
        self.gpios = gpios
        self.limit = limit
        self._last = 0

    def set(self, val):
        now = time.time()
        diff = now - self._last
        if diff < self.limit:
            msg = 'rate limit: last set %f seconds ago. limit is %f'
            raise Exception(msg % (diff, self.limit))
        self._last = now

        old_val = self.get()

        if old_val is None:
            # error... turn everything off
            for g in self.gpios:
                pi.write(g, 0)
            old_val = self.get() # check again
            if old_val is None: # uh-oh... double-problem
                raise ValueError('cannot turn off GPIOs')

        # if there is no change, just return
        if val == old_val:
            return

        if old_val: # if something is on, we need to turn it off
            self.pi.write(self.gpios[old_val-1], 0)
        if val: # if we need to turn something on, do that
            self.pi.write(self.gpios[val-1], 1)

    def get(self):
        state = [ self.pi.read(g) for g in self.gpios ]
        print(state)
        s = sum(state)
        if s == 0:
            return 0
        elif s == 1:
            return 1 + state.index(1)
        else:
            # this is an error - only one should be on at a time
            print('error state: %s', (str(state),))
            return None

class _DummyPi(object):
    def __init__(self):
        self.gpios = {}
    def read(self, gpio):
        return self.gpios.get(gpio, 0)
    def write(self, gpio, val):
        self.gpios[gpio] = val

if __name__ == '__main__':
    # test
    gpios = [4, 5, 6]
    pi = _DummyPi()
    import random
    mc = Motor(pi, gpios, limit=0)
    for i in range(100):
        v = random.randrange(len(gpios)+1)
        mc.set(v)
        vg = mc.get()
        if not v == vg:
            raise ValueError
        print('%s %s' % (v, vg))

    print('test rate limit')
    mc.limit = 1
    mc.set(v)

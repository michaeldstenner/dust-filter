import time

class DFControl(object):
    """control loop manager

    Change rules:
    INCREASE level i -> i+1 when:
        60-second ave > TH[i+1]
    DECREASE level i -> i-1 when:
        60-second ave < TH[i-1] for 5 minutes
    """

    def __init__(self, thresholds, smooth_win=60, min_run=300):
        self.thresholds = thresholds
        self.smooth_win = smooth_win
        self.min_run = min_run
        self._buf = []
        self._buf_len = smooth_win + min_run
        self.level = 0
        self._last_above = [ 0.0 for t in thresholds ]
        self._sv = None

    def _update_buf(self, v, t=None):
        if t is None: t = time.time()

        while self._buf and self._buf[0][0] < t - self._buf_len:
            self._buf.pop(0)
        raw = [ a[1] for a in self._buf if a[0] > t - self.smooth_win ]
        raw.append(v)
        sv = sum(raw)/len(raw)
        self._buf.append( (t, v, sv) )
        self._sv = sv

    def _update_level(self, t=None):
        if t is None: t = time.time()
        sv = self._sv # last smoothed value
        for i in range(len(self.thresholds)):
            if sv > self.thresholds[i]:
                self._last_above[i] = t
                self.level = max(self.level, i)
            elif t - self._last_above[i] > self.min_run:
                self.level = min(self.level, i)
                break

    def set_thresholds(self, thresholds):
        la = []
        for t in thresholds:
            above = [0.0] + [ t for (t, v, sv) in self._buf if sv > t ]
            la.append(above[-1])
        self._last_above = la
        self.thresholds = thresholds
        self._update_level
        return self.level

    def update(self, v, t=None):
        if t is None: t = time.time()
        self._update_buf(v, t)
        self._update_level(t)
        return self.level

    def _old_update(self, v, t=None):
        if t is None: t = time.time()

        self._smooth_buf.append((t, v))
        while self._smooth_buf[0][0] < t - self.smooth_win:
            self._smooth_buf.pop(0)
        sv = sum([a[1] for a in self._smooth_buf]) / len(self._smooth_buf)

        for i in range(len(self.thresholds)):
            if sv > self.thresholds[i]:
                self._last_above[i] = t
                self.level = max(self.level, i)
            elif t - self._last_above[i] > self.min_run:
                self.level = min(self.level, i)
                break
        self._sv = sv
        return self.level

    def poll(self):
        pass        

if __name__ == '__main__':
    pass

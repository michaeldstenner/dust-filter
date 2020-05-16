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
        self._smooth_buf = []
        self.level = 0
        self._last_above = [ 0.0 for t in thresholds ]
        self._sv = None

    def update(self, v, t=None):
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


if __name__ == '__main__':
    pass

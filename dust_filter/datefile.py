import time

class DateFile(object):
    def __init__(self, base, fmt, mode='a'):
        self.base = base
        self.fmt = fmt
        self.mode = mode

        self._ext = time.strftime(fmt)
        self._fo = open(self.base + self._ext, self.mode)

    def _rotate(self):
        now_ext = time.strftime(self.fmt)
        if not self._ext == now_ext:
            self._ext = now_ext
            self._fo.close()
            self._fo = open(self.base + self._ext, self.mode)

    def write(self, s):
        self._rotate()
        return self._fo.write(s)

    def flush(self):
        self._fo.flush()

    def close(self):
        return self._fo.close()


if __name__ == '__main__':
    # test
    fmt = '%Y-%m-%d_%H-%M-%S'
    fo = DateFile('test-', fmt)
    for i in range(15):
        fo.write(time.strftime(fmt)+'\n')
        time.sleep(0.3)
    fo.close()

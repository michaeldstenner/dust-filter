class multiprocessing


class FWrap(object):
    def __init__(self, func):
        self.func = func
        self.cp, self.pp = self.pipe = multiprocessing.Pipe()
        self.clock = multiprocssing.Lock()
        self.rlock = multiprocssing.Lock()
        self.proc = multiprocessing.Process(target=self.watch_loop)
        self.proc.start()

    def call_wait(self, *args, **kwargs):
        with self.clock:
            print('parent writing to pipe')
            self.pp.send(args, kwargs)
            print('parent waiting for response')

        resp = self.pp.recv()
        print('parent got response')
        return resp
            
        
    def watch_loop(self):
        while True:
            with self.lock:
                print('child reading from pipe ...')
                args, kwargs = self.cp.recv()
                print('child calling target process')
            resp = self.func(*args, **kwargs)
            print('child sending response back over pipe')
            self.cp.send(resp)
        
        
        

class PWrap(object):
    def __init__(self, conn):
        self.conn = conn

    def __call__(self, *args, **kwargs):
        self.conn.send(args, kwargs)
        resp = self.conn.recv()
        return resp
    

    

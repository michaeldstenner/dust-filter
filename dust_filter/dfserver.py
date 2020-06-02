import multiprocessing
import threading
import time

import werkzeug
import flask
from flask import Flask, render_template, request, g

import plots

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    fd = dict(labels   = ['Auto', 'High', 'Med', 'Low', 'Off'],
              selected = DFOBJ.get_selected(),
              active   = DFOBJ.get_active())
    td = plots._test_data()
    PLOTPIPE.send(td)
    PLOTPIPE.poll(5)
    return render_template('index.html',**fd)

@app.route('/images/plot.png', methods=['GET'])
def images_plot():
    resp = flask.make_response(PLOTPIPE.recv())
    resp.content_type = "image/png"
    return resp
    
@app.route('/mode', methods=['POST'])
def mode():
    DFOBJ.set_selected(request.form['selected'])
    return render_template('mode.html')


################################################################

class _dummyDFObj(object):
    def __init__(self):
        self.active = 'Off'
        self.selected = 'Off'
    def get_active(self):
        return self.active
    def get_selected(self):
        return self.selected
    def set_selected(self, val):
        self.selected = val
        if val == 'Auto':
            self.active = 'Med'
        else:
            self.active = val

def main(dfobj):
    global DFOBJ
    DFOBJ = dfobj
    global PLOTPIPE
    
    if werkzeug.serving.is_running_from_reloader():
        print('running in reloader')
        multiprocessing.set_start_method('forkserver')
        parent_conn, child_conn = multiprocessing.Pipe()        
        multiprocessing.Process(target=plots.plotproc,
                                args=(child_conn,)).start()
        PLOTPIPE = parent_conn
        
        lt = threading.Thread(target=bg_loop)
        lt.start()
    app.run(debug=True, host="0.0.0.0")

DATA = {}
def bg_loop():
    global DATA
    while True:
        #print(threading.current_thread())
        DATA['time'] = time.time()
        #print(DATA['value'], DATA['time'])
        time.sleep(3)
    
if __name__ == '__main__':
    ddfo = _dummyDFObj()
    main(ddfo)


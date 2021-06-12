import logging
import threading


import werkzeug
import flask
from flask import Flask, render_template, request, g, abort

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/', methods=['GET'])
def index():
    r = PWC.index()
    ave_p, thresh_p = _barplot_data(r['average'], r['thresholds'])

    fd = dict(labels   = ['Auto', 'High', 'Med', 'Low', 'Off'],
              selected = r['selected'],
              active   = r['active'],
              average  = r['average'],
              ave_p    = ave_p,
              thresh_p = thresh_p)
    
    return render_template('index.html',**fd)

def _barplot_data(average, thresholds):
    pmax = 1.2 * max( thresholds + [average] )
    tp = [ int(100 * t / pmax) for t in thresholds ]
    ap = int(100 * average / pmax)
    return ap, tp

@app.route('/images/plot.png', methods=['GET'])
def images_plot():
    data = PWC.image()
    if data is None:
        logging.error('failed to get image (not enough data yet?)')
        abort(404)
    resp = flask.make_response(data)
    resp.content_type = "image/png"
    return resp
    
@app.route('/mode', methods=['POST'])
def mode():
    logging.info('POST mode: %s', request.form)
    PWC.mode(request.form['selected'])
    return render_template('redir-index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        logging.info('GET settings')
        settings = PWC.settings()
        return render_template('settings.html', **settings)
    else: # POST
        logging.info('POST settings: %s', request.form)
        f = request.form
        thresholds = [ float(f[k]) for k in ('t1', 't2', 't3', 't4') ]
        settings = {'thresholds': thresholds}
        
        settings = PWC.settings(settings)
        return render_template('settings.html', **settings)
        


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


################################################################

class PipeWrapCaller(object):
    def __init__(self, pipe):
        self.lock = threading.Lock()
        logging.debug('initiating PipeWrapCaller')
        self.pipe = pipe
    def __getattr__(self, attr):
        logging.debug('PipeWrapCaller getting: %s', attr)
        def _lambda(*args, **kwargs):
            logging.debug('PipeWrapCaller (%s, %s, %s)', attr, args, kwargs)
            with self.lock:
                self.pipe.send( (attr, args, kwargs) )
                ret = self.pipe.recv()
            logging.debug('PipeWrapCaller %s --> %10.10s...', attr, ret)
            return ret
        return _lambda

def main(logq, pipe):
    h = logging.handlers.QueueHandler(logq)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)

    logging.info('starting web server')
    global PWC
    PWC = PipeWrapCaller(pipe)
    #if werkzeug.serving.is_running_from_reloader():
    #    logging.info('flask running in reloader')
    app.run(debug=False, host="0.0.0.0")

if __name__ == '__main__':
    pass


import logging

import werkzeug
import flask
from flask import Flask, render_template, request, g, abort

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    r = PWC.index()
    fd = dict(labels   = ['Auto', 'High', 'Med', 'Low', 'Off'],
              selected = r['selected'],
              active   = r['active'])
    return render_template('index.html',**fd)

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
    logging.info('POST mode: %s', request.form['selected'])
    PWC.mode(request.form['selected'])
    return render_template('mode.html')

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
        logging.debug('initiating PipeWrapCaller')
        self.pipe = pipe
    def __getattr__(self, attr):
        logging.debug('PipeWrapCaller getting: %s', attr)
        def _lambda(*args, **kwargs):
            logging.debug('PipeWrapCaller (%s, %s, %s)', attr, args, kwargs)
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
    if werkzeug.serving.is_running_from_reloader():
        logging.info('flask running in reloader')
    app.run(debug=False, host="0.0.0.0")
    
if __name__ == '__main__':
    pass


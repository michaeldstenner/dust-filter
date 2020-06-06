import werkzeug
import flask
from flask import Flask, render_template, request, g

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
    resp = flask.make_response(data)
    resp.content_type = "image/png"
    return resp
    
@app.route('/mode', methods=['POST'])
def mode():
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
        self.pipe = pipe
    def __getattr__(self, attr):
        def _lambda(*args, **kwargs):
            self.pipe.send( (attr, args, kwargs) )

def main(pipe):
    global PWC
    PWC = PipeWrapCaller(pipe)
    if werkzeug.serving.is_running_from_reloader():
        print('running in reloader')
    app.run(debug=False, host="0.0.0.0")
    
if __name__ == '__main__':
    pass


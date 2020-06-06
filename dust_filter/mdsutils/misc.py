"""Common routines and supporting classes"""

import json
import time
import datetime
import re
import sys
import os.path
from os import makedirs
import inspect

def deep_in(key_tup, dict_obj):
    """this provides a "deep" version of "if key in dict_obj" where
    key_tup is a tuple of keys.  It will return True if dict_obj is a
    nested dictionary and all of the keys exist along the way.

    dict_obj = {'a': {'b': {'c': 123}}}
    deep_in(('a', 'b', 'c'), dict_obj) --> True
    """
    d = dict_obj
    for k in key_tup:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return False
    else:
        return True

def deep_del(key_tup, dict_obj):
    """this provides a "deep" version of "del dict_obj[key]" where
    key_tup is a tuple of keys.  It will delete the key/val pair from
    the nested dict.

    dict_obj = {'a': {'b': {'c': 123}}}
    deep_del(('a', 'b', 'c'), dict_obj)  --> dict_obj = {'a': {'b': {}}}
    """
    d = dict_obj
    for i, k in enumerate(key_tup, 1):
        if isinstance(d, dict) and k in d:
            if i < len(key_tup):
                d = d[k]
        else:
            raise KeyError('keys %s not found in nested dict' % repr(key_tup))
    else:
        del d[k]

def indent(indent_string, text_string):
    """Add the indentation string to the beginning of each line of text.

    Keyword arguments:
    indent_string -- String to append to each line
    text_string -- Text to split by line and append the indentation string to

    Returns a string where every line has the indentation string appended."""
    return ''.join([ indent_string + s for s in text_string.splitlines(True) ])

def combine_dockertag(registry, name, tag):
    """Assemble the three parts of a docker image name into a string"""
    if tag is None: tag = 'latest'
    if registry is None:
        return '%s:%s' % (name, tag)
    else:
        return '%s/%s:%s' % (registry, name, tag)

def parse_dockertag(image_name):
    """Splits the docker tag string name into parts and returns them.

    Returns a tuple with the registry host/IP, the image name, and the tag.
    """
    # split on the first /
    cl = image_name.split('/', 1)
    if '.' in cl[0] or ':' in cl[0]:
        # first chunk is a registry
        registry = cl[0]
        name = cl[1]
    else:
        registry = None
        name = image_name

    if ':' in name:
        name, tag = name.split(':')
    else:
        tag = None

    return (registry, name, tag)

def makedirsp(dirname):
    """make a directory tree, don't complain if parts already exist"""
    try:
        makedirs(dirname)
    except OSError as e:
        if e.errno == 17:
            pass
        else:
            raise

class sopen(object):
    """a context wrapper for open that interprets '-' as stdin or stdout

    fn = 'foo'  # or foo = '-'
    with open(foo) as fo:
        data = fo.read()

    This works for regular filenames or '-' for stdin.  If the mode is
    'a' or 'w', then it will interpret '-' as stdout.
    """
    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args
        self.fo = None

    def __enter__(self):
        if self.args:
            mode = self.args[0]
        else:
            mode = 'r'

        if self.fn == '-':
            if mode[0] in 'aw':
                return sys.stdout
            else:
                return sys.stdin
        else:
            self.fo = open(self.fn, *self.args)
            return self.fo

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.fn == '-':
            self.fo.close()

def tta(job, exc, t0=0.01, a=1.5, b=0, maxtime=5):
    """If at first you don't succeed...

    This function tries to execute the job repeatedly until it works
    or times out.

    Keyword arguments:
    job = (cmd, args, kwargs)
    exc      - an exception class or tuple thereof to catch and retry
    t0       - the amount of time to wait between first and second try
    a, b     - at each iteration,   t -> a * t + b
    maxtime  - if one of the expected exceptions occurs after this amount
               of time, re-raise it.
    """

    cmd, args, kwargs = job
    starttime = time.time()
    t = t0
    while True:
        try:
            return cmd(*args, **kwargs)
        except exc:
            dt = time.time() - starttime
            if dt > maxtime:
                raise
            #print '%6.4fs: got %s, waiting %f seconds' % (dt, e, t)
            time.sleep(t)
            t = a * t + b

json_split_re = re.compile(r'}\s*{')
def json_split(mjson):
    """split concatenated json objects

    This function will accept concatenated json objects which have
    been simply joined together.  It splits on '}\\s*{' so it may
    incorrectly split if that pattern appears in a string within one
    of the json objects.

    In this context, "object" specifically means the mapping data
    stuctures bounded by {}.

    It returns a list of strings, where each string is a json object.
    """

    # one mitigation for incorrect splits is to try and parse every
    # chunk as json.  If it fails to parse, add the following chunk to
    # it and try again.  This is not yet implemented.

    r = json_split_re.split(mjson)
    if len(r) > 1:
        r[0] = r[0] + '}\n'
        r[-1] = '{' + r[-1]
        for ind in range(1, len(r)-1):
            r[ind] = '{' + r[ind] + '}\n'
    return r

def timestamp(local=False):
    """Creates a timestamp string."""
    fmt = "%a, %d %b %Y %H:%M:%S"
    utcnow = datetime.datetime.utcnow()
    if not local:
        return utcnow.strftime(fmt) + ' UTC+0000'
    now = datetime.datetime.now()
    mindiff = round((now - utcnow).total_seconds())/60
    zh = mindiff / 60
    zm = mindiff % 60
    tzname = time.strftime('%Z', time.localtime())
    return now.strftime(fmt) + ' %s%+03d%02d' % (tzname, zh, zm)

def int2base(x,alphabet='0123456789abcdefghijklmnopqrstuvwxyz',b=None):
    'convert an integer to its string representation in a given base'
    if b is None:
        b = len(alphabet)
    if b<2 or b>len(alphabet):
        if b==64: # assume base64 rather than raise error
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                "abcdefghijklmnopqrstuvwxyz0123456789+/"
        else:
            raise AssertionError("int2base base out of range")
    if isinstance(x,complex): # return a tuple
        return ( int2base(x.real,b,alphabet) , int2base(x.imag,b,alphabet) )
    if x<=0:
        if x==0:
            return alphabet[0]
        else:
            return  '-' + int2base(-x,b,alphabet)
    # else x is non-negative real
    rets=''
    while x>0:
        x,idx = divmod(x,b)
        rets = alphabet[idx] + rets
    return rets

#############################################################################

def test_tta():
    """Simple test for tta function."""
    def raise_until_time(raise_time):
        """Raise an exception if the current time is less than the given raise
        time."""
        if time.time() < raise_time:
            raise KeyError('not the right choice... I know')
        else:
            return 42
    job = (raise_until_time, (time.time() + 3, ), {})
    print(tta(job, KeyError))
    job = (raise_until_time, (time.time() + 3, ), {})
    print(tta(job, KeyError, maxtime = 2))

def test_json_split():
    """Simple test for json_split function."""
    print('reading multi-json from stdin')
    mjson = sys.stdin.read()
    r = json_split(mjson)
    print('read %s chunks' % len(r))
    for i, d in enumerate(r, 1):
        print('='*70)
        for j, l in enumerate(d.splitlines(), 1):
            print('%3d %s' % (j,l))
        try:
            a = AttrDict.from_json(d, True)
        except Exception as e:
            print('exception:', e)
        else:
            print('%2d: %d keys' % (i, len(list(a.keys()))))

if __name__ == '__main__':
    print('running as script for testing')
    #test_tta()
    #test_rconvert()
    #test_json_split()

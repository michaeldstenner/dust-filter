import os
import logging
import logging.config
import argparse
from os.path import exists, dirname
import argparse

from attrdict import AttrDict

DEBUG = False

class ArgumentParser(argparse.ArgumentParser):
    """sub-classed version of ArgumentParser to allow nested/dotted dest
    
    This subclass makes to substantive changes:
      1) it allows dots in 'dest' values, such as: dest='network.port'
      2) it returns parsed arguments in dict rather than a namespace

    This significance is that options can be directly dumped into a
    nested options structure

    """

    def __init__(self, *args, **kwargs):
        super(ArgumentParser, self).__init__(*args, **kwargs)
        self._dest_map = {}

    def add_argument(self, *args, **kwargs):
        if 'dest' in kwargs and '.' in kwargs['dest']:
            deep_dest = kwargs['dest']
            us_dest = deep_dest.replace('.', '_')
            self._dest_map[us_dest] = deep_dest
            kwargs['dest'] = us_dest
        return super(ArgumentParser, self).add_argument(*args, **kwargs)
        
    def parse_known_args(self, *args, **kwargs):
        spka = super(ArgumentParser, self).parse_known_args
        ns, args = spka(*args, **kwargs)
        d = {}
        for k, v in vars(ns).items():
            key = self._dest_map.get(k, k)
            d[key] = v
        return d, args

def load_config(y, source=None):
    config = AttrDict.from_yaml(y)
    if source is False:
        pass
    elif source is None:
        if hasattr(y, 'name'):
            config._source = y.name
        elif isinstance(y, str):
            config._source = '<string>'
        else:
            config._source = '<unknown>'
    else:
        config._source = source
    return config
        
def load_config_file(fn, source=None):
    """load a YAML config file from a file name"""
    with open(fn) as fo:
        config = load_config(fo, source)
    return config

def load_config_files(searchpath, prune=True, source=None):
    """load multiple config files and create separate config objects

    For each location in searchpath, read the config file there and
    load it.  A list of the resulting objects is returned.  If no file
    is found at some location, it will be skipped and nothing will be
    entered into the returned list UNLESS prune=False, in which case
    None will be included.  If prune=False, then there is a simple
    mapping between searchpath and the output list of config objects.
    """
    configs = []
    errors = {}
    for fn in searchpath:
        if exists(fn):
            try:
                configs.append(load_config_file(fn, source=source))
            except Exception as e:
                raise
        elif prune is False:
            configs.append(None)
    return configs
            
def convert_command_line_args(args, trans=None, prefix=None):
    """convert command line arguments (from argparse) to an 
    AttrDict-based config.

    If 'trans' is provided, it is a map from the 'dest' to the deep
    key for the config dict.  For example, 
       {'hostname': 'network.host'}

    If 'prefix' is provided, it is prepended to all keys that are NOT represent    ed in 'trans'.  For example, for prefix='cl.':
       'debug' -->  'cl.debug'
    """
    config = AttrDict()
    if trans is None: trans = {}
    if isinstance(args, argparse.Namespace): args = vars(args)
    for k, v in args.items():
        if k in trans: key = trans[k]
        elif prefix is not None: key = prefix + k
        else: key = k
        config.deepset(key, v)
    return config

def merge_configs(config_list, sections=None):
    config = AttrDict()
    if sections is None: sections = ()
    for c in config_list:
        if c is None: continue
        for s in sections:
            if c.deepin(s) and config.deepin(s):
                #print('removing', s)
                config.deepdel(s)
        config.deepupdate(c, copy=True)
    return config

def configure_logging(config):
    lc = config.logging
    if 'version' not in lc:
        lc.version = 1
    if 'disable_existing_loggers' not in lc:
        lc.disable_existing_loggers = False
    for h in lc.handlers.values():
        if 'filename' in h:
            if not exists(dirname(h.filename)):
                os.makedirs(dirname(h.filename))
    obj = logging.config.dictConfig(lc)

if __name__ == '__main__':
    DEBUG=True
    

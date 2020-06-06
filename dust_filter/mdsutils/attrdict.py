"""AttrDict class"""

import json
import re
from collections import OrderedDict
import sys
import os.path
import copy as copymod

import yaml

DEBUG = False

class AttrDict(dict):
    """Class exposing both a dict and attribute interface. Any elements added
    as a dictionary are available as attributes, and vice versa."""

    def __init__(self, *args, **kwargs):
        """Constructor. Initialize internal dictionary structure."""
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def deepget(self, key):
        """get values from nested dict.  Key is of the form 'a.b.c'"""
        if DEBUG: print(repr(self))
        if '.' in key:
            top, rest = key.split('.', 1)
            #if DEBUG: print(top, rest)
            return self[top].deepget(rest)
        else:
            return self[key]

    def deepset(self, key, val):
        """set values in a nested dict.  Key is of the form 'a.b.c'

        If intermediate layers do not exist, they will be created.  If
        intermediate objects are of the wrong type, an exception will
        naturally be generated and it will simply be passed up.
        """
        if DEBUG:
            print(repr(self))
        if '.' in key:
            top, rest = key.split('.', 1)
            topd = self.setdefault(top, self.__class__())
            topd.deepset(rest, val)
        else:
            self[key] = val

    def deepdel(self, key):
        """del values in a nested dict.  Key is of the form 'a.b.c'

        Only the leaf node is removed.
        """
        if DEBUG:
            print(repr(self))
        if '.' in key:
            top, rest = key.split('.', 1)
            self[top].deepdel(rest)
        else:
            del self[key]

    def deepin(self, key):
        """Test whether the "deep key" (of the form 'a.b.c') exists in a
        nested structure
        """
        
        if DEBUG:
            print(repr(self))
        if '.' in key:
            top, rest = key.split('.', 1)
            return self[top].deepin(rest)
        else:
            return key in self

    def deepupdate(self, other, copy=False):
        """fold 'other' into 'self', but do it recursively.  All data present
        in 'other' will be entered into 'self', overwriting data from
        'self' if necessary.

        By default, instances of AttrDict will be copied, but other
        objects will bin included as references.  If you want to copy
        deeply, set copy=False
        """
        for k in other:
            if isinstance(other[k], self.__class__):
                if not k in self:
                    self[k] = self.__class__()
                elif isinstance(self[k], self.__class__):
                    pass
                elif isinstance(self[k], dict):
                    self[k] = self.__class__(self[k]).rconvert()
                else:
                    self[k] = self.__class__()
                self[k].deepupdate(other[k])
            else:
                if copy: self[k] = copymod.deepcopy(other[k])
                else: self[k] = other[k]
        return self

    def deepcopy(self):
        """create and return a deep copy of this object"""
        return copymod.deepcopy(self)

    def __copy__(self):
        cls = self.__class__
        new = cls.__new__(cls)
        new.__dict__ = new
        new.update(self)
        return new

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        new.__dict__ = new
        for k, v in self.items():
            new[k] = copymod.deepcopy(v, memo)
        return new

    def __setstate__(self, state):
        self.__dict__ = self
        self.update(state)
    
    @classmethod
    def from_yaml(cls, y):
        """Build an instance from YAML data.

        Keyword arguments:
        y -- YAML string or file object

        Returns an instance of AttrDict with the attributes described
        in the input YAML.
        """
        return cls(yaml.load(y, AttrLoader))

    def to_yaml(self, stream=None, **kwargs):
        """Return a YAML representation of the object."""
        return yaml.dump(self, stream, AttrDumper, **kwargs)

    @classmethod
    def from_json(cls, j, allow_comments=False):
        """Build an instance from JSON data.

        Keyword arguments:
        j -- JSON string
        allow_comments -- if true, permit comments (see below)

        If "allow_comments" is True, then any line starting with zero
        or more whitespace characters and a '#' will be removed.  More
        specifically, it will be replaced with spaces so that any
        parse-error reporting will still have the correct line, row, and
        character counts.

        Returns an instance of AttrDict with the attributes described
        in the input JSON.
        """
        if allow_comments:
            lines = j.splitlines()
            newlines = []
            for line in lines:
                if line.lstrip().startswith('#'):
                    newlines.append(' ' * len(line)) # keep char count OK
                else:
                    newlines.append(line)
            j = '\n'.join(newlines)
        return cls(json.loads(j, cls=AttrDecoder))

    def to_json(self, *args, **kwargs):
        """Return a JSON string representation of the object.

        Any arguments will be passed to json.dumps().

        In addition to the json.dumps arguments, this accepts the
        kwarg 'sortorder', which should be a list of keys.  The keys
        in the sortorder list will be printed first (in order).  Any
        other keys will then be printed in natural sort order.
        """
        if 'sortorder' in kwargs:
            kwargs['sort_keys'] = False
            sortorder = kwargs['sortorder']
            del kwargs['sortorder']
            obj = OrderedDict()
            for k in sortorder:
                if k in self:
                    obj[k] = self[k]
            for k in sorted(self.keys()):
                if k not in sortorder:
                    obj[k] = self[k]
        else:
            obj = self
        return json.dumps(obj, *args, **kwargs)

    pprint_args = {'sort_keys': True,
                   'indent': 4,
                   'separators': (',', ': ')}
    def pprint(self, *args, **kwargs):
        """A wrapper for self.to_json that pretty-prints.

        Returns a string, but more readable!"""
        kw = dict(self.pprint_args)
        kw.update(kwargs)
        return self.to_json(*args, **kw)

    def rconvert(self):
        """recursively convert dicts within self to AttrDicts
        This is particularly useful in the following scenario:
        a = {'foo': {'bar': 'baz'}}
        b = AttrDict(a).rconvert()

        print a.foo.bar
        >>> baz
        """
        for k in self:
            if isinstance(self[k], dict):
                if not isinstance(self[k], AttrDict):
                    self[k] = AttrDict(self[k])
                self[k].rconvert()
        return self

class AttrDecoder(json.JSONDecoder):
    """Class for decoding JSON - not intended for direct use"""
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, *args, **kwargs)
        self.object_hook = AttrDict

class AttrLoader(yaml.Loader):
    """Class for decoding YAML - not intended for direct use"""
    def __init__(self, stream):
        if isinstance(stream, str):
            self._root = os.getcwd()
        else:
            self._root = os.path.split(stream.name)[0]
        super(AttrLoader, self).__init__(stream)

    def include(self, node):
        """Load the include YAML node and return the node pointed by it."""
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, AttrLoader)

def attrdict_constructor(loader, node):
    """Build a new AttrDict based on the given YAML node."""
    return AttrDict(loader.construct_mapping(node))
AttrLoader.add_constructor('!include', AttrLoader.include)
AttrLoader.add_constructor('tag:yaml.org,2002:map', attrdict_constructor)

class AttrDumper(yaml.Dumper):
    """YAML dumper for AttrDict."""
    pass

def attrdict_representer(dumper, data):
    """Return the YAML representation of the given AttrDict."""
    return dumper.represent_dict(data)
AttrDumper.add_representer(AttrDict, attrdict_representer)


#############################################################################

def test_AttrDict():
    """Test AttrDicts conversions to JSON and YAML."""
    obj1 = AttrDict()
    obj1.test = 'abc'
    print(obj1)

    obj2 = AttrDict({'foo': 'bar'})
    print(obj2)

    obj2.update(obj1)
    j = obj2.to_json()
    print('json:\n', j)
    y = obj2.to_yaml()
    print('yaml:\n', y)

    obj3 = AttrDict.from_json(j)
    print('from json:', obj3)
    obj3 = AttrDict.from_yaml(y)
    print('from yaml:', obj3)

def test_rconvert():
    """Test conversion from JSON/dict to AttrDict."""
    d = {'foo': 'bar',
         'baz': {'this': 'that',
                 'here': 'there',
                 'everywhere': {'answer': 42}}}

    a = AttrDict(d)
    print(a.foo)
    try:
        print(a.baz.this)
    except AttributeError:
        print('got AttributeError as expected')

    a = AttrDict(d).rconvert()
    print(a.foo)
    print(a.baz.this)

def test_deep_getset():
    a = AttrDict()
    a.b = AttrDict()
    a.b.c = AttrDict()
    a.b.c.d1 = 1
    print('starting:         ', repr(a))
    print('get b.c.d1 =', a.deepget('b.c.d1'))

    print('set b.c.d2 = 2 --> ', end='')
    a.deepset('b.c.d2', 2)
    print(repr(a))

    print('del b.c.d1     --> ', end='')
    a.deepdel('b.c.d1')
    print(repr(a))
    
    print('set b2.c2.d3 = 3 --> ', end='')
    a.deepset('b2.c2.d3', 3)
    print(repr(a))

    print('get b.c.d4 = ', end='')
    try: a.deepget('b.c.d4')
    except Exception as e: print(repr(e))

    print('get b.c3.d5 = ', end='')
    try: a.deepget('b.c3.d5')
    except Exception as e: print(repr(e))

    print('a = ', repr(a))
    print('"b.c.d2" in a -->', a.deepin('b.c.d2'))
    print('"b.c.d1" in a -->', a.deepin('b.c.d1'))
    print('"b.c"    in a -->', a.deepin('b.c'))
    print('"b.f"    in a -->', a.deepin('b.f'))

    print('============== test .deepupdate')    
    a2 = AttrDict()
    a2.b = AttrDict()
    a2.b.c = AttrDict()
    a2.b.c.d1 = 1
    print('a  = ', repr(a))
    print('a2 = ', repr(a2))
    print('a.deepupdate(a2) -->', repr(a.deepupdate(a2)))


    print('============== test .deepcopy')    
    a3 = a2.deepcopy()
    print('a2 =                  ', repr(a2))
    print('a3 = a2.deepcopy() -->', repr(a3))
    print("a3['b3'] = 3"); a3['b3'] = 3
    print("a3.b4 = 4");    a3.b4 = 4
    print('a3.b.c.d3 = 3'); a3.b.c.d3 = 3
    print('a3 =                  ', repr(a3))
    print('a2 =                  ', repr(a2))
    
    print('============== test pickle')
    import pickle
    a3 = pickle.loads(pickle.dumps(a2))
    print('a2 =                  ', repr(a2))
    print('a2 --> pickle --> a3 =', repr(a3))
    print("a3['b3'] = 3"); a3['b3'] = 3
    print("a3.b4 = 4");    a3.b4 = 4
    print('a3.b.c.d3 = 3'); a3.b.c.d3 = 3
    print('a3 =                  ', repr(a3))
    print('a2 =                  ', repr(a2))
    
    print('============== test .copy')    
    a3 = copymod.copy(a2)
    print('a2 =                  ', repr(a2))
    print('a3 = a2.copy() -->    ', repr(a3))
    print("a3['b3'] = 3"); a3['b3'] = 3
    print("a3.b4 = 4");    a3.b4 = 4
    print('a3.b.c.d3 = 3'); a3.b.c.d3 = 3
    print('a3 =                  ', repr(a3))
    print('a2 =                  ', repr(a2))
    
    
    
if __name__ == '__main__':
    #DEBUG = True
    print('running as script for testing')
    #test_AttrDict()
    test_deep_getset()

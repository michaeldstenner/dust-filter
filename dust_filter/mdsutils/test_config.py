import os
import sys
import tempfile
import argparse

import munittest as unittest
import config
import attrdict
"""config.py tests"""

_config_str = """
# comment
this:
  that: val1
  there: 23
sec:
  one: 1
  two: 2
list: [1, 2, 3]
"""
_config_val = attrdict.AttrDict.from_yaml(_config_str)

class ConfigFIleTest(unittest.TestCase):
    """config file loading tests"""
    def setUp(self):
        (fd, fn) = tempfile.mkstemp()
        fo = os.fdopen(fd, 'w')
        fo.write(_config_str)
        fo.close()
        self.fn = fn

    def tearDown(self):
        os.remove(self.fn)

    def test_load_config_string(self):
        c = config.load_config(_config_str)
        self.assertIn('_source', c)
        self.assertEqual(c._source, '<string>')
        del c['_source']        
        self.assertEqual(c, _config_val)

    def test_load_config_fo(self):
        fo = open(self.fn)

        c = config.load_config(fo)
        self.assertIn('_source', c)
        self.assertEqual(c._source, self.fn)
        del c['_source']        
        self.assertEqual(c, _config_val)

        fo.close()
        
    def test_load_config_fn(self):
        c = config.load_config_file(self.fn)
        self.assertIn('_source', c)
        self.assertEqual(c._source, self.fn)
        del c['_source']        
        self.assertEqual(c, _config_val)

class LoadConfigFilesTests(unittest.TestCase):
    def setUp(self):
        (fd, fn) = tempfile.mkstemp()
        fo = os.fdopen(fd, 'w')
        fo.write(_config_str)
        fo.close()
        self.fn = fn

    def tearDown(self):
        os.remove(self.fn)

    def test_load_files(self):
        searchpath = [self.fn, '/NON-EXISTENT-FILE', self.fn]
        c = config.load_config_files(searchpath, source=False)
        self.assertEqual(c, [_config_val, _config_val])
        c = config.load_config_files(searchpath, source=False, prune=False)
        self.assertEqual(c, [_config_val, None, _config_val])

class MergeConfigsTests(unittest.TestCase):
    """merge_configs tests"""
    def setUp(self):
        self.c1 = _config_val.deepcopy()
        self.c2 = _config_val.deepcopy()

    def test_merge(self):
        self.c2.new = 'val'
        m = config.merge_configs([self.c1, self.c2])
        self.assertEqual(self.c2, m)

    def test_merge_section(self):
        del self.c2.sec['one']
        m = config.merge_configs([self.c1, self.c2], sections=['sec'])
        self.assertEqual(m.sec, {'two': 2})
        
class CommandLineArgsTests(unittest.TestCase):
    """convert_command_line_args tests"""
    def setUp(self):
        self.p = argparse.ArgumentParser()
        a = self.p.add_argument
        a('-a', action='store_true', help='arg a')
        a('-b', metavar='VAL', help='arg b')

    def test_parsing(self):
        """command line arg conversion"""
        argv = ['-a', '-b', '12']
        args = self.p.parse_args(argv)
        c = config.convert_command_line_args(args)
        self.assertEqual(c, {'a': True, 'b': '12'})

    def test_mapping(self):
        """test key translation"""
        argv = ['-a', '-b', '12']
        args = self.p.parse_args(argv)
        trans = {'b': 'cl.b'}
        c = config.convert_command_line_args(args, trans=trans)
        self.assertEqual(c, {'a': True, 'cl':{'b': '12'}})

    def test_prefix(self):
        """test prefix"""
        argv = ['-a', '-b', '12']
        args = self.p.parse_args(argv)
        trans = {'b': 'cl.b'}
        c = config.convert_command_line_args(args, trans=trans, prefix='p.')
        self.assertEqual(c, {'p':{'a': True}, 'cl':{'b': '12'}})


class ArgParseTests(unittest.TestCase):
    """ArgumentParser subclass tests"""
    def setUp(self):
        self.p = config.ArgumentParser()
        a = self.p.add_argument
        a('-a', dest='cl.a', action='store_true', help='arg a')
        a('-b', dest='cl.b', metavar='VAL', help='arg b')

    def test_parsing(self):
        """command line arg conversion"""
        argv = ['-a', '-b', '12']
        args = self.p.parse_args(argv)
        self.assertEqual(args, {'cl.a': True, 'cl.b': '12'})
        c = config.convert_command_line_args(args)
        self.assertEqual(c, {'cl': {'a': True, 'b': '12'}})
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
    

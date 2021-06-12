import dust_filter as _package
import re as _re
import sys as _sys

name = "DF2000"
description = "Dust Filter 2000"

##########################################################################
long_description = getattr(_package, '__doc__', '(none)')
license = getattr(_package, '__license__', '(unspecified)')
for _i, _a in enumerate(_sys.argv):
    if _a.startswith('--version='):
        version = _a[10:]
        del _sys.argv[_i]
        break
else:
    version = getattr(_package, '__version__', '0')
_authors = _re.split(r',\s+', getattr(_package, '__author__', ''))
author       = ', '.join([_re.sub(r'\s+<.*',        r'', _) for _ in _authors])
author_email = ', '.join([_re.sub(r'(^.*<)|(>.*$)', r'', _) for _ in _authors])
url = getattr(_package, '__url__', '(none)')
##########################################################################

packages = ['dust_filter', 'dust_filter.mdsutils']
package_dir = {'dust_filter':'dust_filter',
               'dust_filter.mdsutils':'dust_filter/mdsutils'}
package_data= {'dust_filter': ['VERSION', 'DATE']}
scripts = ['df2000']
data_files = [
    #('share/doc/' + name + '-' + version, ['README', 'TODO', 'ChangeLog']),
    ('share/man/man1/', ['docs/df2000.1.gz']),
    ('/var/log/df2000/', []),
    ('/etc/', ['config/df2000.yaml']),
    ('/usr/lib/systemd/system/', ['config/df2000.service'])
]
options = { 'clean' : { 'all' : 1 } }
classifiers = [
        'Programming Language :: Python',
      ]

from distutils.command.bdist_rpm import bdist_rpm as _orig_bdist_rpm
class _bdist_rpm(_orig_bdist_rpm):
    user_options = list(_orig_bdist_rpm.user_options)
    user_options.append( ('config-files=', None,
          'list of configuration files (space or comma-separated)') )

    def initialize_options(self):
        _orig_bdist_rpm.initialize_options(self)
        self.config_files = None

    def finalize_package_data(self):
        _orig_bdist_rpm.finalize_package_data(self)
        self.ensure_string_list('config_files')

    def _make_spec_file(self):
        spec_file = _orig_bdist_rpm._make_spec_file(self)
        if self.config_files:
            for config_file in self.config_files:
                spec_file.append('%config(noreplace) ' + config_file)
        return spec_file

cmdclass = {
    'bdist_rpm': _bdist_rpm
    }

# load up distutils
if __name__ == '__main__':
    config = globals().copy()
    keys = list(config)
    for k in keys:
    #print '%-20s -> %s' % (k, config[k])
        if k.startswith('_'): del config[k]

    from distutils.core import setup
    setup(**config)

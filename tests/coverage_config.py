import configparser
import os.path
from collections.abc import Iterable
from copy import deepcopy

__all__ = [
    'CoverageConfiguration',
    'TEST_DIR'
]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.abspath(os.path.join(BASE_DIR, '../tests'))

STATIC_CONF = {
    'run': {
        'branch': True,
        'command_line': f'-m pytest {TEST_DIR}',
        'source': ['src']
    },
    'report': {
        'fail_under': 91,
        'precision': 2,
        'show_missing': True,
        'skip_covered': True,
        'skip_empty': True,
        'sort': '-Miss',
        'exclude_also': [
            'raise NotImplementedError',
            'pass',
            'except KeyboardInterrupt:',
        ],
        'omit': []
    }
}


class CoverageConfiguration:
    ins = None

    def __new__(cls):
        if cls.ins is None:
            cls.ins = super().__new__(cls)
            cls.ins.conf = deepcopy(STATIC_CONF)
        return cls.ins

    @staticmethod
    def _merge(arr, to_add):
        return list(set(arr).union(to_add))

    def append_exclusion(self, exclude_also=None, omit=None):
        if exclude_also is None:
            exclude_also = []
        if omit is None:
            omit = []
        self.conf['report']['exclude_also'] = self._merge(self.conf['report'].get('exclude_also', []), exclude_also)
        self.conf['report']['omit'] = self._merge(self.conf['report'].get('omit', []), omit)

    @staticmethod
    def convert_value(value):
        if isinstance(value, Iterable) and not isinstance(value, str):
            return "\n" + "\n".join(map(str, sorted(value)))
        return str(value)

    def write(self, filepath):
        config = configparser.ConfigParser()
        for section, payloads in self.conf.items():
            config.add_section(section)
            for option, value in payloads.items():
                config[section][option] = self.convert_value(value)
        with open(filepath, 'w') as configfile:
            config.write(configfile)

import os.path
import unittest

from tests.coverage_config import CoverageConfiguration, TEST_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

__all__ = []

COVERAGERC_PATH = os.path.abspath(os.path.join(BASE_DIR, '../.coveragerc'))

if __name__ == '__main__':
    unittest.defaultTestLoader.discover(TEST_DIR)
    CoverageConfiguration().write(COVERAGERC_PATH)

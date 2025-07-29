"""A python package to dump any HLS stream as it is"""
import os.path
import sys

# It imports release module this way because if it tried to import the whole package
# and some required dependencies were not installed, that would fail
# This is the only way to access the release module without needing all
# dependencies.
sys.path.insert(0, os.path.dirname(__file__))
import release

__author__ = release.author
__version__ = release.version

# List of all modules that contain classes needed to be registered with the registry (via a Class.register decorator)
# This code ensures that the modules are imported and hence the decorators are
# executed and the classes/functions registered.
__modules_to_register = []

for m in [None] + __modules_to_register:
    # This try/catch is needed to support reload(dump_hls)
    if m is not None:
        try:
            exec('import %s' % m)
            exec('del %s' % m)
        except AttributeError:
            pass
else:
    if m is not None:
        del m

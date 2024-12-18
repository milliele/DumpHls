import os
import sys

from setuptools import setup

# It imports release module this way because if it tried to import the whole package
# and some required dependencies were not installed, that would fail
# This is the only way to access the release module without needing all
# dependencies.
sys.path.insert(0, 'src/dump_hls')
import release

sys.path.pop(0)

with open('README.md', 'r') as f:
    long_description = f.read()

with open('LICENSE', 'r') as f:
    license = f.read()

DEV_DEPENDENCIES = [
    'coverage',
    'twine',
    'pytest',
]


def parse_requirements_txt(file):
    with open('requirements.txt', "r") as f:
        lines = list(map(str.strip, f.readlines()))
    # remove comment
    lines = [l[:l.find('#')].strip() if '#' in l else l for l in lines if not l.startswith('#')]
    return lines


requirements_dev = parse_requirements_txt('requirements.txt')
requirements_prod = [r for r in requirements_dev if all(not r.startswith(p) for p in DEV_DEPENDENCIES)]

prefix = os.getenv("PYPI_PREFIX", '')
if prefix:
    prefix += '.'

setup(
    name=f'{prefix}{release.name}',
    version=release.version,
    author=release.author,
    author_email=release.author_email,
    description=release.description_short,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=release.url,
    include_package_data=True,
    package_dir={'': 'src'},
    packages=['dump_hls'],
    license=license,
    install_requires=requirements_prod,
    entry_points={
        'console_scripts': [
            "dumphls = src.dump_hls.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)

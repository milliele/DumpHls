""""""
import os.path

import pytest
from click.testing import CliRunner

import src.dump_hls.cli as m
from src.dump_hls.release import version

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture()
def runner():
    yield CliRunner()


def test_main(runner):
    res = runner.invoke(m.main, ['--version'])
    assert version == res.output.split(' ')[-1].strip()
    assert 0 == res.exit_code
    res = runner.invoke(m.main, ['-h'])
    assert 0 == res.exit_code

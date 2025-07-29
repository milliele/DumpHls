""""""
import os.path
from unittest.mock import patch, MagicMock

import click
import pytest
from click.testing import CliRunner

import src.dump_hls.cli as m
from src.dump_hls.release import version

BASE_DIR = os.path.dirname(__file__)


@pytest.fixture()
def runner():
    yield CliRunner()


def test_dumphls_misc(runner):
    # version
    res = runner.invoke(m.dumphls, ['--version'])
    assert version == res.output.split(' ')[-1].strip()
    assert 0 == res.exit_code

    # help
    res = runner.invoke(m.dumphls, ['-h'])
    assert 0 == res.exit_code


@pytest.fixture
def mock_stream_dumper():
    with patch('src.dump_hls.cli.StreamDumper') as MockDumper:
        yield MockDumper


def test_valid_url_and_server(monkeypatch, mock_stream_dumper):
    runner = click.testing.CliRunner()
    mock_instance = MagicMock()
    mock_stream_dumper.return_value = mock_instance

    result = runner.invoke(
        m.dumphls,
        ['--server', '/tmp', 'https://example.com/playlist.m3u8']
    )
    assert result.exit_code == 0
    assert "Server directory: /tmp" in result.output
    assert "URL: https://example.com/playlist.m3u8" in result.output
    mock_stream_dumper.assert_called_once_with('/tmp')
    mock_instance.dump.assert_called_once_with('https://example.com/playlist.m3u8')


@pytest.mark.parametrize("url,prefix", [
    ("ftp://example.com/playlist.m3u8", 'URL must be an absolute URL with a domain name'),
    ("http:///playlist.m3u8", "URL must be an absolute URL with a domain name"),
    ('not_a_url', "URL must be an absolute URL with a domain name"),
    ("https://example.com/playlist.txt", "URL must point to a multi-variant playlist (M3U8) file"),
])
def test_invalid_url_failed_to_be_parsed(url, prefix):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        m.dumphls,
        ['--server', '/tmp', url]
    )
    assert result.exit_code != 0
    assert prefix in result.output
    assert url in result.output

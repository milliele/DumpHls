"""Run the Dump HLS.

This script defines the CLI of Dump HLS.

Check the instructions: ::

    dumphls -h
"""
import os.path
import sys
from urllib.parse import urlparse

import click

from main import StreamDumper
from . import __version__

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.version_option(__version__)
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--server', type=click.Path(exists=True, file_okay=False), help='Directory path for server')
@click.argument('multivariant_url')
def dumphls(server: str, multivariant_url: str):
    """Dump HLS content from a given URL, optionally using a local server directory.

    Args:
        server: the directory path for the server where the files will be stored
        multivariant_url: URL to the multi-variant playlist (M3U8) file
    """
    click.echo(f"Server directory: {server}")
    click.echo(f"URL: {multivariant_url}")

    try:
        parsed_url = urlparse(multivariant_url)
    except Exception:
        click.echo(f"Invalid URL: {multivariant_url}", err=True)
        sys.exit(1)
    if not all([parsed_url.scheme in ('http', 'https'), parsed_url.netloc]):
        click.echo(f"URL must be an absolute URL with a domain name: {multivariant_url}", err=True)
        sys.exit(1)
    _, ext = os.path.splitext(parsed_url.path)
    if ext.lower() not in ('.m3u8', '.m3u'):
        click.echo(f"URL must point to a multi-variant playlist (M3U8) file: {multivariant_url}", err=True)
        sys.exit(1)
    d = StreamDumper(server)
    d.dump(multivariant_url)


if __name__ == '__main__':
    dumphls()

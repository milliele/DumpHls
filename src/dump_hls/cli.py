"""Run the Dump HLS.

This script defines the CLI of Dump HLS.

Check the instructions: ::

    dumphls -h
"""

import click

from src.dump_hls import __version__

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
def main():
    pass


if __name__ == '__main__':
    main()
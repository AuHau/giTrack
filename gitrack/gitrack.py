import sys

from . import cli

def main(args=None):
    cli.entrypoint(args or sys.argv[1:])

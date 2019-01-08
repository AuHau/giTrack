import sys

from gitrack import cli


def main(args=None):
    cli.entrypoint(args or sys.argv[1:])


if __name__ == '__main__':
    main()

"""
Entry point for klystrctl.

    python -m cli.main get nodes
"""

import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(prog='klystrctl', description='Klystr cluster client')
    parser.add_argument('--api-url', default=None, help='Control plane URL (env: KLYSTR_API_URL)')
    parser.add_argument('-o', '--output', choices=['table', 'json', 'yaml'], default='table')
    parser.add_subparsers(dest='command', required=True)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    parser.error(f'command not implemented: {args.command}')
    return 1


if __name__ == '__main__':
    sys.exit(main())

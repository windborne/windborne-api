"""Argument types shared by the CLI command groups."""

import argparse


def boolean(value):
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    raise argparse.ArgumentTypeError('Expected true or false')

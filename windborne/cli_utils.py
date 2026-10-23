"""Argument parsing shared by the CLI command groups."""

import argparse
import sys


class IntermixedArgumentParser(argparse.ArgumentParser):
    """Allow options between positionals, including in nested commands.

    Use argparse's two-pass approach at leaf parsers so it also works on
    Python 3.6, which has no parse_intermixed_args. Keep the ``--`` tail out
    of the first pass; otherwise it can be mistaken for options on pass two.
    This uses argparse's private action/group lists, so retain cross-version
    parsing tests when changing the supported Python versions.
    """

    def parse_known_args(self, args=None, namespace=None):
        positionals = self._get_positional_actions()
        if not positionals or any(
                action.nargs in (argparse.PARSER, argparse.REMAINDER)
                for action in positionals):
            # Parent parsers select the command normally. Their leaf parsers
            # inherit this class and handle that command's options/positionals.
            return super().parse_known_args(args, namespace)

        args = list(sys.argv[1:] if args is None else args)
        separator = args.index('--') if '--' in args else len(args)
        before_separator, after_separator = args[:separator], args[separator:]
        saved_positionals = [(action, action.nargs, action.default)
                             for action in positionals]
        saved_usage = self.usage
        try:
            # Keep complete usage text in errors even while positionals are
            # temporarily disabled to collect all the options in one pass.
            if self.usage is None:
                self.usage = self.format_usage()[7:]
            try:
                for action in positionals:
                    action.nargs = argparse.SUPPRESS
                    action.default = argparse.SUPPRESS
                namespace, remaining = super().parse_known_args(before_separator, namespace)
            finally:
                for action, nargs, default in saved_positionals:
                    action.nargs = nargs
                    action.default = default

            # Required options and mutually exclusive groups were validated
            # above; the second pass assigns positionals in their original order.
            required = [(action, action.required) for action in self._get_optional_actions()]
            required.extend((group, group.required) for group in self._mutually_exclusive_groups)
            try:
                for action, _ in required:
                    action.required = False
                return super().parse_known_args(remaining + after_separator, namespace)
            finally:
                for action, value in required:
                    action.required = value
        finally:
            self.usage = saved_usage


def boolean(value):
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    raise argparse.ArgumentTypeError('Expected true or false')

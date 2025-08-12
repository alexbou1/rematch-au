#!/usr/bin/env python3
"""CLI tool for running address matching and related processes."""

from __future__ import annotations

import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from .commands import CliCommand
from ..common import setup_logging
from ..version import __version__

PROG = Path(__file__).stem.replace("_", "-")
LOG = setup_logging(PROG, fresh=True)
LOG.setLevel(os.getenv("LOG_LEVEL", logging.INFO))


# ------------------------------------------------------------------------------
def process_cli_args() -> Namespace:
    """Process the command line arguments."""

    argp = ArgumentParser(
        prog=PROG,
        description="Find the closest matching addresses in the Australian GNAF dataset.",
    )

    argp.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{PROG} v{__version__}",
        help="show program's version number and exit",
    )

    subps = argp.add_subparsers(title="subcommand", dest="subcommand")

    for name, cli_command in CliCommand.subcommands.items():
        subp = subps.add_parser(name, help=cli_command.description)
        cli_command.add_cli_arguments(subp)

    if len(sys.argv) == 1:
        argp.print_help()
    args = argp.parse_args()

    return args


# ------------------------------------------------------------------------------
def main() -> int:
    """Main CLI entrypoint."""
    args = process_cli_args()

    if not hasattr(args, "subcommand") or args.subcommand is None:
        LOG.error("No subcommand chosen, use '%s --help' for usage", PROG)
        return 1

    # Run subcommand
    try:
        command = CliCommand.subcommands.get(args.subcommand)
        command(args)
    except InterruptedError:
        LOG.error("Keyboard interrupt. exiting...")
        return 1
    except Exception as e:
        LOG.error(e)
        return 1

    return 0


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    exit(main())

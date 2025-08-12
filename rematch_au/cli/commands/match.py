"""CLI subcommand for generating DuckDB address data set."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import duckdb

from .__common__ import CliCommand
from rematch_au.address_matcher import match_address
from ...models import SearchAddress

DUCKDB_FILENAME = "gnaf.db"


# ------------------------------------------------------------------------------
@CliCommand.register("match")
class InitDataCommand(CliCommand):
    """Match a single address with extra information useful for debugging."""

    # --------------------------------------------------------------------------
    def add_cli_arguments(self, argp: ArgumentParser) -> None:
        """Define command line arguments."""
        argp.add_argument(
            "-a",
            "--address",
            action="store",
            metavar="'ADDRESS'",
            help="The address to search for.",
        )

        argp.add_argument(
            "-s",
            "--suburb",
            "--locality",
            action="store",
            metavar="'SUBURB'",
            help="The suburb to address resides.",
        )

        argp.add_argument(
            "-j",
            "--state",
            "--jurisdiction",
            action="store",
            metavar="'STATE'",
            help="The state the address resides.",
        )

        argp.add_argument(
            "-p",
            "--postcode",
            action="store",
            metavar="'ADDRESS'",
            help="The address to search for.",
        )

        argp.add_argument(
            "-g",
            "--gnaf-db",
            action="store",
            metavar="GNAF.DB",
            default=DUCKDB_FILENAME,
            help="The DuckDB file containing the address lookup information.",
        )

    # --------------------------------------------------------------------------
    def __call__(self, args: Namespace) -> None:
        """Execute the command."""
        conn = duckdb.connect(args.gnaf_db, read_only=True)
        search_address = SearchAddress(
            "match", args.address, args.suburb, args.state, args.postcode
        )
        highest_address, highest_score, match_confidence = match_address(
            conn, search_address
        )
        print(f"Matched address:  {highest_address.address}")
        print(f"Highest score:    {highest_score:.3f}")
        print(f"Match confidence: {match_confidence:.3f}")

"""CLI subcommand for generating DuckDB address data set."""

from argparse import ArgumentParser, Namespace
from pathlib import Path


from .__common__ import CliCommand
from rematch_au.gnaf import (
    download_most_recent_gnaf_file,
    generate_temp_db_file,
    generate_rematch_db_file,
)

DUCKDB_FILENAME = "gnaf.db"
PROGRESS_BARS = True


# ------------------------------------------------------------------------------
@CliCommand.register("init_data")
class InitDataCommand(CliCommand):
    """Initialize DuckDB address data file."""

    # --------------------------------------------------------------------------
    def add_cli_arguments(self, argp: ArgumentParser) -> None:
        """Define command line arguments."""
        argp.add_argument(
            "-o",
            "--output-file",
            action="store",
            metavar="FILE",
            default=DUCKDB_FILENAME,
            help=f"The output DuckDB file name. Default is '{DUCKDB_FILENAME}'",
        )

        argp.add_argument(
            "-p",
            "--progress-bars",
            action="store_" + str(not PROGRESS_BARS).lower(),
            help=f"Whether to display progress bars. Default is '{PROGRESS_BARS}'",
        )

        argp.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="Force overwrite of output file. Default is 'False'",
        )

    # --------------------------------------------------------------------------
    def __call__(self, args: Namespace) -> None:
        """Define command line arguments."""
        gnaf_file = download_most_recent_gnaf_file(args.progress_bars)

        output_file = Path(args.output_file)
        if output_file.is_file() and not args.force:
            raise FileExistsError(
                f"Output file already exists: '{output_file}'. Use --force to overwrite."
            )

        tmp_db_file = generate_temp_db_file(
            gnaf_file, args.output_file, args.progress_bars
        )
        generate_rematch_db_file(
            tmp_db_file, args.output_file, args.progress_bars
        )

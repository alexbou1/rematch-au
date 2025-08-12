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
@CliCommand.register("init-db")
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

        if PROGRESS_BARS:
            argp.add_argument(
                "-np",
                "--no-progress-bars",
                action="store_false",
                dest="progress_bars",
                help="Do not render progress bars during 'init-db'",
            )
        else:
            argp.add_argument(
                "-p",
                "--progress-bars",
                action="store_true",
                help="Render progress bars during 'init-db'",
            )

        argp.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="Force overwrite of output file",
        )

        argp.add_argument(
            "--not-optimised",
            action="store_false",
            dest="optimised",
            help="Do not optimise the GNAF data, better for debugging but worse "
            "for performance",
        )

    # --------------------------------------------------------------------------
    def __call__(self, args: Namespace) -> None:
        """Execute the command."""
        gnaf_file = download_most_recent_gnaf_file(args.progress_bars)

        output_file = Path(args.output_file)
        if output_file.is_file() and not args.force:
            raise FileExistsError(
                f"Output file already exists: '{output_file}'. Use --force to overwrite."
            )
        elif output_file.is_file():
            output_file.unlink()

        tmp_db_file = generate_temp_db_file(
            gnaf_file, args.output_file, args.progress_bars
        )
        generate_rematch_db_file(
            tmp_db_file,
            args.output_file,
            optimised=args.optimised,
            progress_bars=args.progress_bars,
        )

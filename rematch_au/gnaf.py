"""Module for downloading and handling the Australian GNAF dataset."""

import logging
import os
from pathlib import Path
from typing import Optional, Union
from zipfile import ZipFile, Path as ZipPath

import duckdb
import requests

from .common import setup_logging
from .utils import ProgressBar

PROG = Path(__file__).stem
LOG = setup_logging(PROG, fresh=True)
LOG.setLevel(os.getenv("LOG_LEVEL", logging.INFO))

GNAF_INFO_URL = "https://data.gov.au/data/api/3/action/package_show?id=19432f89-dc3a-4ef3-b943-5326ef1dbecc"
DB_FILENAME = "gnaf.db"
SQL_PATH = Path(__file__).parent / "sql"


# ------------------------------------------------------------------------------
def download_most_recent_gnaf_file(progress_bar: bool = True) -> Optional[Path]:
    """
    Download the most recent G-NAF file if not already present.

    :param progress_bar: If True, show a progress bar for the download.
    :returns: The path to the downloaded G-NAF zip file, or None on failure.
    """
    gnaf_data = requests.get(GNAF_INFO_URL).json()
    files = gnaf_data.get("result", {}).get("resources", [])

    # Look for the GDA2020 file
    found_file = None
    for file in files:
        if file.get("description") == "GDA2020":
            found_file = file
            break

    if found_file is None:
        LOG.error("No GDA2020 GNAF file found")
        return None

    gnaf_file = Path(Path(found_file.get("url")).name)

    # Download the file if it doesn't already exist
    if not gnaf_file.is_file():

        # Download GNAF file is not already downloaded
        with ProgressBar(
            remaining_time=True, disable=not progress_bar
        ) as progress:
            logger = progress.log if progress_bar else LOG.info
            logger(f"Downloading newest GNAF file to '{gnaf_file}'")

            task = progress.add_task(
                "[green]Downloading",
                total=found_file.get("size") // 1024 + 1,
            )
            res = requests.get(found_file.get("url"), stream=True)
            with open(gnaf_file, "wb") as f:
                for chunk in res.iter_content(1024):
                    f.write(chunk)
                    progress.update(task, advance=1)

            logger("Completed download")
    else:
        LOG.info("'%s' already downloaded. Skipping...", gnaf_file)

    return gnaf_file


# ------------------------------------------------------------------------------
def generate_temp_db_file(
    gnaf_file: Path,
    file_name: Union[str, Path] = DB_FILENAME,
    progress_bars: bool = True,
) -> Path:
    """
    Generate a temporary DuckDB database from the G-NAF zip file.

    :param gnaf_file: Path to the downloaded G-NAF zip file.
    :param file_name: The base name for the output database file.
    :param progress_bars: If True, display progress bars during creation.
    :returns: The path to the generated temporary DuckDB database file.
    """
    file_path = Path(file_name)
    tmp_address_file = file_path.parent / f"tmp_{file_path.name}"

    # If file already exists, skip creating
    if tmp_address_file.is_file():
        LOG.info("'%s' already exists. Skipping...", tmp_address_file)
        return tmp_address_file

    conn = duckdb.connect(tmp_address_file)

    # Split up relevant files
    zip_file = ZipFile(gnaf_file)
    sql_files = {
        f.split("/")[-1].split(".")[0]: ZipPath(zip_file, f)
        for f in zip_file.namelist()
        if f.endswith(".sql") and "sqlserver" not in f
    }
    std_files = [
        ZipPath(zip_file, f)
        for f in zip_file.namelist()
        if f.endswith(".psv") and "Standard" in f
    ]
    auth_code_files = [
        ZipPath(zip_file, f)
        for f in zip_file.namelist()
        if f.endswith(".psv") and "Authority" in f
    ]

    with (
        conn.cursor() as cursor,
        ProgressBar(disable=not progress_bars) as progress,
    ):
        logger = progress.log if progress_bars else LOG.info

        # Run create tables script
        for query in (
            sql_files["create_tables_ansi"].open().read().lower().split(";")
        ):
            cursor.execute(query)
        logger("Created GNAF tables from provided script")

        # Install DuckDB extension that allows for reading from ZIPs
        cursor.install_extension("zipfs", repository="community")
        cursor.load_extension("zipfs")
        logger("Installed zipfs module in DuckDB")

        # Load all the Standard files from PSV into corresponding tables
        std_task = progress.add_task("[yellow]STD Files", total=len(std_files))
        for file in std_files:
            table_name = "_".join(file.name.split("_")[1:-1]).lower()
            cursor.execute(
                f"COPY {table_name} FROM 'zip://{file}' (DELIMITER '|');"
            )
            logger(f"Inserted '{file.name}' in '{table_name}'")
            progress.update(std_task, advance=1)

        # Load all the Authority Code files from PSV into corresponding tables
        auth_code_task = progress.add_task(
            "[green]Auth Code Files", total=len(auth_code_files)
        )
        for file in auth_code_files:
            table_name = "_".join(file.name.split("_")[2:-1]).lower()
            cursor.execute(
                f"COPY {table_name} FROM 'zip://{file}' (DELIMITER '|');"
            )
            progress.update(auth_code_task, advance=1)
            logger(f"Inserted '{file.name}' in '{table_name}'")

        # Execute primary key queries to create primary keys in tables
        pk_queries = [
            q.lower()
            for q in sql_files["add_fk_constraints"].open().read().split(";")
            if "PRIMARY KEY" in q
        ]
        pk_task = progress.add_task("[red]Primary keys", total=len(pk_queries))
        for query in pk_queries:
            cursor.execute(query)
            progress.update(pk_task, advance=1)
        logger("Added primary keys to all tables")

        # Create address summary table, not a view as they are slower
        aus_addresses_task = progress.add_task("[cyan]Address table", total=4)
        address_table = (
            sql_files["address_view"]
            .open()
            .read()
            .lower()
            .replace(
                "create or replace view address_view",
                "create table australian_addresses",
            )
        )
        cursor.execute(address_table)
        progress.update(aus_addresses_task, advance=1)
        logger("Created 'australian_addresses' table from data tables")

        cursor.execute(
            (SQL_PATH / "australian_full_addresses.sql").open().read()
        )
        progress.update(aus_addresses_task, advance=1)
        logger(
            "Created 'australian_full_addresses' from 'australian_addresses'"
        )

        cursor.execute(
            "alter table australian_full_addresses add primary key (address_detail_pid);"
        )
        progress.update(aus_addresses_task, advance=1)
        logger(
            "Created primary key on 'australian_full_addresses' as 'address_detail_pid'"
        )

        cursor.execute(
            "create index idx_australian_full_addresses_state "
            "on australian_full_addresses (state_abbreviation);"
        )
        progress.update(aus_addresses_task, advance=1)
        logger(
            "Created index 'idx_australian_full_addresses_state' on 'australian_full_addresses'"
        )
        logger(f"Complete, written to '{tmp_address_file}'")

    return tmp_address_file


# ------------------------------------------------------------------------------
def generate_rematch_db_file(
    tmp_db_path: Path,
    output_file: Union[str, Path] = DB_FILENAME,
    optimised: bool = True,
    progress_bars: bool = True,
) -> None:
    """
    Generate the final, optimised rematch-au lookup database.

    :param tmp_db_path: Path to the temporary GNAF database file.
    :param output_file: The path for the final, optimised database file.
    :param optimised: If True, use optimised SQL scripts for table creation.
    :param progress_bars: If True, display a progress bar during creation.
    """
    conn = duckdb.connect(tmp_db_path)
    with (
        conn.cursor() as cursor,
        ProgressBar(disable=not progress_bars) as progress,
    ):
        logger = progress.log if progress_bars else LOG.info
        cursor.execute(f"attach '{output_file}' as gnaf;")

        sql_file = SQL_PATH / (
            "custom_rematch_tables_optimised.sql"
            if optimised
            else "custom_rematch_tables.sql"
        )
        queries = sql_file.open().read().split(";\n")
        query_count = len([q for q in queries if not q.startswith("--")])

        rematch_task = progress.add_task(
            "[cyan]rematch-au tables", total=query_count
        )
        for query in queries:
            if query.startswith("--"):
                logger(query.strip("- ;"))
                continue

            cursor.execute(query)
            progress.update(rematch_task, advance=1)

        logger(f"Complete, written to '{output_file}'")

"""File reader mddule that handles reading multiple input types."""

from pathlib import Path
from typing import Union, Iterator

import duckdb

from rematch_au.models import SearchAddress
from rematch_au.utils import fetch_from_cursor

REQUIRED_INPUT_COLUMNS = {
    "identifier",
    "address",
    "suburb",
    "state",
    "postcode",
}

FILE_TYPE_MAPPING = {
    ".csv": "read_csv",
    ".psv": "read_csv",
    ".json": "read_json",
    ".jsonl": "read_json",
    ".parquet": "read_parquet",
    ".xlsx": "read_xlsx",
}


# ------------------------------------------------------------------------------
class FileReaderError(Exception):
    """File reader module error."""


# ------------------------------------------------------------------------------
def read_data_file(path: Union[str, Path]) -> Iterator[SearchAddress]:
    """
    Read data file and return an iterator of SearchAddress objects.

    :param path: path to data file, allowed types are .csv, .psv, .json,
                 .jsonl, .parquet and .xlsx
    :return:     iterator of SearchAddress objects
    """
    # Prevent overwriting the input path argument
    file_path = path
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check file exists
    if not file_path.is_file():
        raise FileReaderError(f"File '{file_path}' not found")

    try:
        # Use DuckDB's excellent file reading capabilities
        with duckdb.connect(":memory:") as conn:
            suffix = file_path.suffix

            # Handle if the file is GZIPPED
            supported_types = (
                "Only supports '"
                + "', '".join(FILE_TYPE_MAPPING.keys())
                + "' and some gzipped variants"
            )
            if suffix == ".gz":
                suffix = Path(file_path.stem).suffix
                if suffix in (".parquet", ".xlsx"):
                    raise FileReaderError(
                        f"Unsupported file type '{suffix}.gz'. {supported_types}"
                    )

            # If not a supported type
            if suffix not in FILE_TYPE_MAPPING:
                raise FileReaderError(
                    f"Unsupported file type '{suffix}'. {supported_types}"
                )

            # Read file in DuckDB
            file_path = str(file_path)
            reader = FILE_TYPE_MAPPING[suffix]
            query = f"SELECT * FROM {reader}(?);"

            cursor = conn.cursor()
            cursor.execute(query, (file_path,))

            # Check columns in file match required columns
            data_columns = set(c[0] for c in cursor.description)
            missing_cols = REQUIRED_INPUT_COLUMNS - data_columns
            if missing_cols:
                raise FileReaderError(
                    f"Input file '{file_path}' is missing columns '"
                    + "', '".join(missing_cols)
                    + "'"
                )

            # Yield SearchAddresses until the input file is out
            for row in fetch_from_cursor(cursor):
                yield SearchAddress(**row)

    except Exception as e:
        if isinstance(e, FileReaderError):
            raise e

        raise FileReaderError(f"Error occurred whilst reading '{path}'") from e

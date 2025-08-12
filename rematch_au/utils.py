"""Util functions used in address validation process."""

from types import TracebackType
from typing import Iterator, Any, List, Optional, Type

from duckdb import DuckDBPyConnection
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from rematch_au.models import GNAFAddress, SearchAddress


# ------------------------------------------------------------------------------
class ProgressBar:
    """Progress bar handler using rich."""

    # --------------------------------------------------------------------------
    def __init__(
        self,
        elapsed_time: bool = True,
        remaining_time: bool = False,
        disable: bool = False,
    ) -> None:
        """Initialize a progress bar."""
        columns: List[ProgressColumn] = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ]
        if elapsed_time:
            columns.append(TimeElapsedColumn())

        if remaining_time:
            columns.append(TimeRemainingColumn())

        self.progress = Progress(
            *columns,
            transient=False,
            disable=disable,
        )

    # --------------------------------------------------------------------------
    def __enter__(self) -> Progress:
        self.progress.start()
        return self.progress

    # --------------------------------------------------------------------------
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.progress.stop()


# ------------------------------------------------------------------------------
def fetch_from_cursor(cursor: DuckDBPyConnection) -> Iterator[dict[str, Any]]:
    """
    Consume the data from a cursor on which a query has been executed.

    :param cursor:    DBAPI 2.0 cursor. The query must have already been executed.
    """
    columns = [f[0] for f in cursor.description]

    while True:
        row = cursor.fetchone()
        if not row:
            break

        r = dict(zip(columns, row, strict=True))
        yield r


# ------------------------------------------------------------------------------
def fetch_gnaf_address_from_cursor(
    cursor: DuckDBPyConnection,
) -> Iterator[GNAFAddress]:
    """
    Consume the GNAFAddresses from a cursor on which a query has been executed.

    :param cursor:    DBAPI 2.0 cursor. The query must have already been executed.
    """
    for row in fetch_from_cursor(cursor):
        yield GNAFAddress.from_dict(**row)

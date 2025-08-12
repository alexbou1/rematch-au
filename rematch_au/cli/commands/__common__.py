"""Shared functionality between CLI subcommands."""

from __future__ import annotations

from abc import ABC
from argparse import ArgumentParser, Namespace
from types import TracebackType
from typing import Callable, Dict, Type, List, Optional

from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    ProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Column


# ------------------------------------------------------------------------------
class CliCommand(ABC):
    """CLI command class for adding subcommands."""

    subcommands: Dict[str, CliCommand] = {}

    # Fields used by subclasses
    name: str = None
    description: str = None

    # --------------------------------------------------------------------------
    @classmethod
    def register(cls, name: str) -> Callable:
        """Register a subcommand."""

        def wrapper(command: Type[CliCommand]) -> CliCommand:
            """Decorate a subcommand."""
            description = command.__doc__.splitlines()[0].strip().rstrip(".")
            description = description[0].lower() + description[1:]
            cli_command = command(name, description)
            cls.subcommands[name] = cli_command
            return cli_command

        return wrapper

    # --------------------------------------------------------------------------
    def __init__(self, name: str, description: str) -> None:
        """Initialize a cli command."""
        self.name = name
        self.description = description

    # --------------------------------------------------------------------------
    def add_cli_arguments(self, argp: ArgumentParser) -> None:
        """Defines command line arguments."""
        raise NotImplementedError()

    # --------------------------------------------------------------------------
    def __call__(self, args: Namespace) -> None:
        """Execute CLI subcommand."""
        raise NotImplementedError()

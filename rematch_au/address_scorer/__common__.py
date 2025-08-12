"""Module for handling the scoring process for potential address matches."""

import re
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Tuple, Type

from rich.table import Column, Table

from rematch_au.models import SearchAddress, GNAFAddress

NUMBER_ONLY_REGEX = re.compile(r"\b[A-Z]{0,2}(\d+)[A-Z]{0,2}\b")
ALPHA_NUMERIC_REGEX = re.compile(r"\b([A-Z]{0,2}\d+[A-Z]{0,2})\b")


# ------------------------------------------------------------------------------
class AttributeScorer(ABC):
    """An abstract base class for individual attribute scorers."""

    name: str = None
    short_name: str = None
    weight: float = None
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __init__(self):
        """Initialise the scorer."""
        self.score: float = 0.0

    # --------------------------------------------------------------------------
    @property
    def weighted_score(self):
        """Return the weighted score."""
        return self.weight * self.score

    # --------------------------------------------------------------------------
    @abstractmethod
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the similarity score for a specific attribute.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score for the attribute.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.score() not implemented"
        )


# ------------------------------------------------------------------------------
class AddressScorer:
    """Score GNAF addresses compared to a search string."""

    scorers: Dict[str, Type[AttributeScorer]] = {}

    # --------------------------------------------------------------------------
    @classmethod
    def register(cls) -> Callable:
        """Register a new attribute scorer class."""

        def wrapper(scorer: Type[AttributeScorer]) -> Type[AttributeScorer]:
            """Add the scorer to the registry."""
            cls.scorers[scorer.short_name] = scorer
            return scorer

        return wrapper

    # --------------------------------------------------------------------------
    def score_table(self) -> Table:
        """Generate a rich Table for displaying score breakdowns."""
        table_columns = [
            Column("Score", no_wrap=True),
            Column("GNAF ID", style="yellow", no_wrap=True),
            Column("Address", style="gold1"),
        ]
        for scorer in self.score_methods:
            colour = "green"
            if scorer.weight >= 1:
                colour = "magenta"
            elif scorer.weight >= 0.5:
                colour = "cyan"
            column = Column(scorer.short_name, style=colour, no_wrap=True)
            table_columns.append(column)

        return Table(*table_columns, box=None)

    # --------------------------------------------------------------------------
    def __init__(self, address: SearchAddress) -> None:
        """Initialise the address scorer with a search address."""
        self._address = address
        self._search_address = address.address

        # Sort scorers in descending order by weight
        self.score_methods = sorted(
            self.scorers.values(), key=lambda s: -s.weight
        )

    # --------------------------------------------------------------------------
    def score(
        self, comp_address: GNAFAddress
    ) -> Tuple[float, List[AttributeScorer]]:
        """
        Calculate the total similarity score for a G-NAF address.

        :param comp_address: The G-NAF address to compare against.
        :returns: A tuple containing the total score and a list of individual
            scorer instances.
        """
        scores = []
        total_score = 0.0

        for scorer in self.score_methods:
            if not scorer.enabled:
                continue

            scorer_instance = scorer()
            score = scorer_instance(self._address, comp_address)
            total_score += score
            scores.append(scorer_instance)

        return total_score, scores

"""Scorer that calculates the partial fuzzy similarity of potential addresses."""

from rapidfuzz.fuzz import ratio

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class FuzzyDistanceScorer(AttributeScorer):
    """Calculate the fuzzy distance between two addresses."""

    name: str = "Fuzzy Distance"
    short_name: str = "FZD"
    weight: float = 0.6
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the fuzzy similarity score between two full address strings.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """

        # Full ratio to compare overall difference in strings
        fuzzy_distance = ratio(search_address.address, comp_address.address)
        if fuzzy_distance is None:
            return 0

        self.score = fuzzy_distance / 100
        return self.weighted_score

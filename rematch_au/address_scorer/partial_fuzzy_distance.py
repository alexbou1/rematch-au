"""Scorer that calculates the partial fuzzy similarity of potential addresses."""

from rapidfuzz.fuzz import partial_ratio_alignment

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class PartialFuzzyDistanceScorer(AttributeScorer):
    """Calculate the partial fuzzy similarity between two addresses."""

    name: str = "Partial Fuzzy Distance"
    short_name: str = "PFD"
    weight: float = 0.4
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the partial fuzzy similarity score between two addresses.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """

        # Partial comparison to offset string length difference affecting scores
        alignment = partial_ratio_alignment(
            search_address.address, comp_address.address
        )
        if alignment is None:
            return 0

        partial_distance = alignment.dest_end - alignment.dest_start
        partial_distance_ratio = partial_distance / len(search_address.address)

        self.score = alignment.score / 100 - ((1 - partial_distance_ratio) / 3)
        return self.weighted_score

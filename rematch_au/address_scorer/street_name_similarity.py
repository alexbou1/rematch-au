"""Scorer that calculates the fuzzy similarity of street names from potential addresses."""

from rapidfuzz.fuzz import partial_ratio_alignment

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class StreetNameSimilarityScorer(AttributeScorer):
    """Calculate the fuzzy similarity between street names."""

    name: str = "Street Name Similarity"
    short_name: str = "SNS"
    weight: float = 0.5
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the partial fuzzy similarity for the street name.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """
        street_part = " ".join(search_address.street_tokens)

        alignment = partial_ratio_alignment(
            comp_address.full_street_name, street_part
        )

        if alignment is None:
            return 0

        partial_match_length = alignment.src_end - alignment.src_start
        if partial_match_length < len(comp_address.street_name):
            self.score = (
                alignment.score
                / 100
                * 0.5
                * partial_match_length
                / len(comp_address.street_name)
            )
        else:
            self.score = alignment.score / 100

        return self.weighted_score

"""Scorer that calculates the fuzzy similarity of postcodes from potential addresses."""

from rapidfuzz.fuzz import ratio

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class PostcodeSimilarityScorer(AttributeScorer):
    """Calculate the similarity between postcodes."""

    name: str = "Postcode Similarity"
    short_name: str = "PSM"
    weight: float = 0.3
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the similarity score based on the postcode.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """

        # Effectively a boost for matching postcodes to help tie-break equal matches
        fuzzy_distance = ratio(search_address.postcode, comp_address.postcode)
        if fuzzy_distance is None:
            return 0

        self.score = fuzzy_distance / 100
        return self.weighted_score

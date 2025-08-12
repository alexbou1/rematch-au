"""Scorer that calculates the fuzzy similarity of number prefixes in potential addresses."""

import re

from rapidfuzz.fuzz import token_sort_ratio

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


NUMBER_PREFIX_REGEX = re.compile(r"([A-Z]+)\s([A-Z]{0,2}\d+[A-Z]{0,2})\b")


# ------------------------------------------------------------------------------
@AddressScorer.register()
class NumberPrefixSimilarityScorer(AttributeScorer):
    """Calculate the similarity of number prefixes (e.g., UNIT, LOT)."""

    name: str = "Number Prefix Similarity"
    short_name: str = "NPS"
    weight: float = 0.5
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the similarity score for number prefixes.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """
        comp_address_prefixes = (
            (comp_address.flat_type, comp_address.full_flat_number),
            (comp_address.level_type, comp_address.full_level_number),
            (
                ("LOT", comp_address.full_lot_number)
                if comp_address.full_lot_number
                and not comp_address.full_flat_number
                else (None, None)
            ),
        )
        comp_address_prefixes = " ".join(
            [f"{p}---{n}" for p, n in comp_address_prefixes if p]
        )
        search_address_prefixes = re.findall(
            NUMBER_PREFIX_REGEX, " ".join(search_address.street_tokens)
        )

        if "/" in search_address.original_address:
            search_address_prefixes.append("UNIT")
        search_address_prefixes = " ".join(
            [f"{p}---{n}" for p, n in search_address_prefixes if p]
        )

        if (
            len(comp_address_prefixes) == 0
            and len(search_address_prefixes) == 0
        ):
            return 0.4

        fuzzy_distance = token_sort_ratio(
            comp_address_prefixes, search_address_prefixes
        )
        self.score = fuzzy_distance / 100
        return self.weighted_score

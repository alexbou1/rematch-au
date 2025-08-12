"""Scorer that gives a boost to addresses to tiebreak principals and aliases."""

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class AddressPrincipalTiebreakScorer(AttributeScorer):
    """Calculate the tiebreak of the address based on address principals."""

    name: str = "Address Principal Tiebreak"
    short_name: str = "APT"
    weight: float = 0.05
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Give a score boost if the candidate address is a principal address.

        :param search_address: The user-provided address (unused in this scorer).
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """
        self.score = int(comp_address.alias_principal == "P")
        return self.weighted_score

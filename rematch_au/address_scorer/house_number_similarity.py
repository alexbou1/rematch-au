"""Scorer that calculates the similarity of house numbers to the search address."""

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class HouseNumberSimilarityScorer(AttributeScorer):
    """Calculate the similarity of the house numbers in addresses."""

    name: str = "House Number Similarity"
    short_name: str = "HNS"
    weight: float = 0.5
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the raw similarity score for house numbers.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The raw similarity score (0.0 to 1.0).
        """

        self.score = self._calculate_score(search_address, comp_address)
        return self.weighted_score

    # --------------------------------------------------------------------------
    @staticmethod
    def _calculate_score(
        search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the raw similarity score for house numbers.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The raw similarity score (0.0 to 1.0).
        """

        # Get the predicted house numbers from the address
        search_address_last_numbers = search_address.numbers[-2:]

        if len(search_address_last_numbers) == 0:
            return 0

        search_num_last, search_num_first = None, None
        if len(search_address_last_numbers) >= 1:
            search_num_last = int(search_address_last_numbers[-1])
        if len(search_address_last_numbers) == 2:
            search_num_first = int(search_address_last_numbers[0])

        if (
            len(search_address_last_numbers) == 2
            and comp_address.number_first == search_num_first
            and comp_address.number_last == search_num_last
        ):
            return 1

        if comp_address.number_last == search_num_last:
            return 0.75

        if comp_address.number_first == search_num_last:
            return 0.75

        if (
            not comp_address.number_last
            and not comp_address.number_first
            and comp_address.lot_number == search_address_last_numbers[-1]
        ):
            return 0.5

        if (
            comp_address.number_first
            and comp_address.number_last
            and comp_address.number_first
            <= search_num_last
            <= comp_address.number_last
        ):
            return 0.3

        return 0

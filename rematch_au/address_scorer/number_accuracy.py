"""Scorer that calculates the similarity and order of number in potential addresses."""

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress


# ------------------------------------------------------------------------------
@AddressScorer.register()
class NumberAccuracyScorer(AttributeScorer):
    """Calculate similarity based on the value and order of all numbers."""

    name: str = "Number Accuracy"
    short_name: str = "NAC"
    weight: float = 1
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate a score based on number matches and their relative order.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """

        # Get numbers from comp addresses
        comp_address_numbers = [str(n) for n in comp_address.get_numbers()]
        comp_address_numbers_tmp = [str(n) for n in comp_address.get_numbers()]

        # Find matching numbers and their indexes
        matched_search_indexes = []
        matched_comp_indexes = []
        for search_index, number in enumerate(search_address.numbers):
            if number in comp_address_numbers_tmp:
                matched_search_indexes.append(search_index)

                comp_index = comp_address_numbers.index(number)
                matched_comp_indexes.append(comp_index)
                comp_address_numbers_tmp.remove(number)

        if not matched_search_indexes:
            return 0

        # Calculate the score from the number of matches and their positioning
        increment = 1 / (len(comp_address_numbers) * 2 + 1)
        score = len(matched_search_indexes) / len(search_address.numbers)

        offset_matched_comp_indexes = [None] + matched_comp_indexes
        matched_comp_indexes_tmp = matched_comp_indexes + [None]
        for index, next_index in zip(
            offset_matched_comp_indexes, matched_comp_indexes_tmp
        ):
            if index is None or next_index is None:
                continue

            # If a number is in the wrong order penalise it, otherwise reward it
            if next_index < index:
                score -= increment
            else:
                # When all numbers match, sometimes the score can equal since
                # we truncate over 1, so penalties should be higher than rewards
                score += increment * 0.9

        # If only a house number is provided, also penalise non house numbers
        if len(search_address.numbers) == 1 and len(matched_comp_indexes) == 1:
            if search_address.numbers[0] == str(comp_address.number_first):
                pass
            elif search_address.numbers[0] == str(comp_address.number_last):
                pass
            else:
                score -= increment

        self.score = max(0, min(score, 1))
        return self.weighted_score

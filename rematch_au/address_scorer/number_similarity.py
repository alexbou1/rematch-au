"""Scorer that calculates the fuzzy similarity of numbers in potential addresses."""

from rapidfuzz.fuzz import token_sort_ratio

from .__common__ import AddressScorer, AttributeScorer
from ..models import SearchAddress, GNAFAddress
from ..number_converter import convert_number_to_string


# ------------------------------------------------------------------------------
@AddressScorer.register()
class NumberSimilarityScorer(AttributeScorer):
    """Calculate the fuzzy similarity between all numbers in addresses."""

    name: str = "Number Similarity"
    short_name: str = "NSM"
    weight: float = 1
    enabled: bool = True

    # --------------------------------------------------------------------------
    def __call__(
        self, search_address: SearchAddress, comp_address: GNAFAddress
    ) -> float:
        """
        Calculate the fuzzy similarity score for all numbers in the addresses.

        :param search_address: The user-provided address.
        :param comp_address: The G-NAF address to score.
        :returns: The weighted score.
        """

        # Get numbers from both addresses including prefixes and suffixes
        search_address_numbers = [n for n in search_address.alpha_nums]
        comp_address_numbers = comp_address.get_full_numbers()

        # Handle cases where a unit, level or lot is only a letter
        for number in comp_address_numbers:
            if (
                not number.isalpha()
                or number not in search_address.street_tokens
            ):
                continue

            num_index = search_address.street_tokens.index(number)
            if num_index >= len(search_address.street_tokens) - 2:
                continue

            next_token = search_address.street_tokens[num_index + 1]
            if next_token not in search_address_numbers:
                continue

            next_index = search_address_numbers.index(next_token)
            search_address_numbers.insert(next_index, number)

        # Pad numbers to be the same length for comparison
        search_address_count = len(search_address_numbers)
        comp_address_count = len(comp_address_numbers)

        longest_seq = max(search_address_count, comp_address_count)

        search_address_numbers.extend(
            ["#" * 5] * (longest_seq - search_address_count)
        )
        comp_address_numbers.extend(
            ["#" * 5] * (longest_seq - comp_address_count)
        )

        # Convert all numbers to words
        search_address_wordnums = [
            (convert_number_to_string(num) or num)
            for num in search_address_numbers
        ]
        comp_address_wordnums = [
            (convert_number_to_string(num) or num)
            for num in comp_address_numbers
        ]

        # Token set comparison to compare numbers individually
        fuzzy_distance = token_sort_ratio(
            " ".join(search_address_wordnums), " ".join(comp_address_wordnums)
        )
        if comp_address.number_last is not None:
            fuzzy_first = token_sort_ratio(
                " ".join(search_address_wordnums),
                " ".join(comp_address_wordnums[:-1]),
            )
            if fuzzy_first > fuzzy_distance:
                fuzzy_distance = fuzzy_first
            del comp_address_wordnums[-2]
            fuzzy_second = token_sort_ratio(
                " ".join(search_address_wordnums),
                " ".join(comp_address_wordnums),
            )
            if fuzzy_second > fuzzy_distance:
                fuzzy_distance = fuzzy_second

        if fuzzy_distance is None:
            return 0

        self.score = fuzzy_distance / 100
        return self.weighted_score

"""Module for converting numbers into words."""

import math
import re
from enum import Enum
from functools import lru_cache
from typing import Optional, Union


# ------------------------------------------------------------------------------
class Numbers(Enum):
    """Key numbers between 1 and 99."""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12
    THIRTEEN = 13
    FOURTEEN = 14
    FIFTEEN = 15
    SIXTEEN = 16
    SEVENTEEN = 17
    EIGHTEEN = 18
    NINETEEN = 19
    TWENTY = 20
    THIRTY = 30
    FORTY = 40
    FIFTY = 50
    SIXTY = 60
    SEVENTY = 70
    EIGHTY = 80
    NINETY = 90

    # --------------------------------------------------------------------------
    @classmethod
    def get(cls, number: int) -> Optional["Numbers"]:
        """Find a number by number."""
        try:
            return cls(number)
        except ValueError:
            return None


# ------------------------------------------------------------------------------
@lru_cache
def convert_number_to_string(number: Union[int, str]) -> Optional[str]:
    """Convert number to string."""

    if not number:
        return None

    prefix = None
    suffix = None
    if isinstance(number, str):
        try:
            number = int(number)
        except ValueError:
            try:
                prefix, number, suffix = re.split(r"(\d+)", number)
                number = int(number)
            except ValueError:
                return None

    if number >= 10**15:
        return None

    labels = (None, "THOUSAND", "MILLION", "BILLION", "TRILLION")
    magnitude = math.log10(number) if number != 0 else 1

    iterations = int(magnitude // 3) + 1
    unused_number = number

    output = []
    for i in range(iterations):
        cur_value = unused_number % 1000
        unused_number = (unused_number - cur_value) / 1000

        hundreds, remainder = divmod(cur_value, 100)
        tens, remainder = divmod(remainder, 10)

        if tens == 1:
            tens = 0
            remainder += 10
        tens *= 10

        filtered_values = filter(
            lambda t: t[0],
            [
                (Numbers.get(hundreds), "HUNDRED"),
                (Numbers.get(tens), None),
                (Numbers.get(remainder), None),
            ],
        )

        output_values = [
            v.name + (f"-{w}" if w else "") for v, w in filtered_values
        ]
        if not output_values:
            continue

        converted_number = "-".join(output_values) + (
            f"-{labels[i]}" if labels[i] else ""
        )
        if converted_number:
            output.append(converted_number)

    if not output:
        return None

    reversed_number = list(reversed(output))
    if prefix:
        reversed_number = [prefix] + reversed_number
    if suffix:
        reversed_number = reversed_number + [suffix]

    return "-".join(reversed_number)


# ------------------------------------------------------------------------------
def convert_address_numbers_to_words(address: str) -> str:
    """"""

    numbers = re.findall(r"(\d+)", address)
    numbers_as_words = [convert_number_to_string(int(n)) for n in numbers]
    biggest_to_smallest = sorted(
        zip(numbers, numbers_as_words),
        key=lambda x: int(x[0]),
        reverse=True,
    )

    output_address = address
    for num, word in biggest_to_smallest:
        if word is not None:
            output_address = output_address.replace(num, f"-{word}-")

    return re.sub(r"-\s-|-\s|\s-|^-|-$", " ", output_address)

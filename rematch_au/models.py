"""Module for handling addresses."""

from __future__ import annotations

import re
from dataclasses import dataclass
from string import punctuation
from typing import Optional, List, Union

NUMBER_ONLY_REGEX = re.compile(r"\b[A-Z]{0,2}(\d+)[A-Z]{0,2}\b")
ALPHA_NUMERIC_REGEX = re.compile(r"\b([A-Z]{0,2}\d+[A-Z]{0,2})\b")


# ------------------------------------------------------------------------------
class SearchAddress:
    """Address class to hold search criteria."""

    # --------------------------------------------------------------------------
    def __init__(
        self,
        identifier: str,
        address: str,
        suburb: str,
        state: str,
        postcode: Union[str, int],
        **kwargs,
    ) -> None:
        """Initialize SearchAddress class."""
        self.identifier = identifier
        self.address = address
        self.suburb = suburb
        self.state = state
        self.postcode = postcode

        # In case postcode was read in as an int from data file
        if isinstance(postcode, int):
            self.postcode = f"{postcode:04d}"

        # Store extra information and process input text for matching
        self._metadata = kwargs
        self.__post_init__()

        # For storing matched information
        self.matched_address: Optional[GNAFAddress] = None
        self.confidence: Optional[float] = None

    # --------------------------------------------------------------------------
    def __post_init__(self) -> None:
        """Post initialisation processing."""

        # Capitalise and remove any punctuation from string
        self.original_address = self.address
        removal_chars = "".join(punctuation.replace("-", "").replace("'", ""))
        replacement = " " * len(removal_chars)
        self.address = (
            self.address.upper()
            .translate(str.maketrans(removal_chars, replacement))
            .strip()
        )
        self.address = re.sub(r"(\s{2,})", " ", self.address)
        self.suburb = (
            self.suburb.upper()
            .translate(str.maketrans(removal_chars, replacement))
            .strip()
            if self.suburb
            else None
        )
        self.state = (
            self.state.upper()
            .translate(str.maketrans(removal_chars, replacement))
            .strip()
            if self.state
            else None
        )
        self.postcode = self.postcode.strip() if self.postcode else None

        # Calculate the likely street name once
        self.street_tokens = None
        self._likely_street_name_tokens = self._likely_street_name()

        # For searching numbers the postcode needs to be removed
        # This step prevents recalculation every time the scorer runs
        self.numeric_search_address = " ".join(
            self.address.rsplit(self.postcode, maxsplit=1)
        )

        # Find number tokens excluding any prefixes or suffixes
        self.numbers = re.findall(
            NUMBER_ONLY_REGEX, self.numeric_search_address
        )

        # Find number tokens including any prefixes or suffixes
        self.alpha_nums = re.findall(
            ALPHA_NUMERIC_REGEX, self.numeric_search_address
        )

    # --------------------------------------------------------------------------
    def likely_street_name(self, start_token: int = 0) -> Optional[str]:
        """Return likely street name."""

        if start_token >= len(self._likely_street_name_tokens):
            return None

        return " ".join(self._likely_street_name_tokens[start_token:])

    # --------------------------------------------------------------------------
    def _likely_street_name(self) -> List[str]:
        """Find the most likely substring containing the street name."""

        search_address = self.address

        suburb_index = self.address.rfind(self.suburb) if self.suburb else -1
        state_index = self.address.rfind(self.state) if self.state else -1
        postcode_index = (
            self.address.rfind(self.postcode) if self.postcode else -1
        )

        indexes = [
            i for i in [suburb_index, state_index, postcode_index] if i != -1
        ]

        if len(indexes) > 0:
            remove_index = min(indexes)
            search_address = search_address[:remove_index].rstrip()

        self.street_tokens = search_address.split(" ")
        last_number = -1
        for i, token in enumerate(self.street_tokens):
            # If the token contains numbers (not alphabetical characters)
            if not token.isalpha():
                last_number = i

        street_name_tokens = self.street_tokens[last_number + 1 :]

        # Handle case where the street name has a number
        if len(street_name_tokens) <= 1:
            tokens_to_remove_from_start = -1
            for i, token in enumerate(self.street_tokens):
                if token.isalpha():
                    tokens_to_remove_from_start = i
                    continue

                break

            street_name_tokens = self.street_tokens[
                tokens_to_remove_from_start + 1 :
            ]
            if len(street_name_tokens) <= 1:
                return self.street_tokens

        return street_name_tokens

    # --------------------------------------------------------------------------
    @property
    def address_suffix(self) -> str:
        """Address suffix is the street name, suburb, state and postcode."""
        return " ".join(
            (self.likely_street_name, self.suburb, self.state, self.postcode)
        )


# ------------------------------------------------------------------------------
@dataclass
class GNAFAddress:
    """GNAF address class."""

    address_detail_pid = None
    lot_number_prefix = None
    lot_number = None
    lot_number_suffix = None
    flat_type = None
    flat_number_prefix = None
    flat_number = None
    flat_number_suffix = None
    level_type = None
    level_number_prefix = None
    level_number = None
    level_number_suffix = None
    number_first_prefix = None
    number_first = None
    number_first_suffix = None
    number_last_prefix = None
    number_last = None
    number_last_suffix = None
    street_name = None
    street_type_code = None
    street_suffix_type = None
    locality_name = None
    state_abbreviation = None
    postcode = None
    address = None
    alias_principal = None

    # --------------------------------------------------------------------------
    @classmethod
    def from_dict(cls, **kwargs) -> GNAFAddress:
        """Initialize address from dictionary."""
        new_instance = cls()
        for key, value in kwargs.items():
            if hasattr(new_instance, key):
                setattr(new_instance, key, value)

        new_instance.__post_init__()
        return new_instance

    # --------------------------------------------------------------------------
    def get_full_number(self, key: str) -> Optional[str]:
        """Get full number including prefix and suffix."""
        prefix = getattr(self, key + "_prefix")
        number = getattr(self, key)
        suffix = getattr(self, key + "_suffix")
        if prefix or number or suffix:
            return f"{prefix or ''}{number or ''}{suffix or ''}"

        return None

    # --------------------------------------------------------------------------
    def __post_init__(self):
        """Compute some calculated fields post init."""
        self.full_lot_number = self.get_full_number("lot_number")
        self.full_level_number = self.get_full_number("level_number")
        self.full_flat_number = self.get_full_number("flat_number")
        self.full_number_first = self.get_full_number("number_first")
        self.full_number_last = self.get_full_number("number_last")

    # --------------------------------------------------------------------------
    @property
    def full_street_name(self) -> Optional[str]:
        """Full street name with type and suffix."""
        return " ".join(
            t
            for t in [
                self.street_name,
                self.street_type_code,
                self.street_suffix_type,
            ]
            if t
        )

    # --------------------------------------------------------------------------
    def get_numbers(self) -> List[str]:
        """Get numbers from address including excluding prefixes and suffixes."""
        numbers = [
            self.flat_number or self.lot_number,
            self.level_number,
            self.number_first,
            self.number_last,
        ]

        return [num for num in numbers if num]

    # --------------------------------------------------------------------------
    def get_full_numbers(self) -> List[str]:
        """Get numbers from address including prefixes and suffixes."""
        numbers = [
            self.full_flat_number or self.full_lot_number,
            self.full_level_number,
            self.full_number_first,
            self.full_number_last,
        ]

        return [num for num in numbers if num]

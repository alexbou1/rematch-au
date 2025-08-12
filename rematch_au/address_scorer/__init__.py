"""Module for handling the scoring of addresses."""

__author__ = "Alex Boul"

import pkgutil
from importlib import import_module

from .__common__ import (
    AddressScorer as AddressScorer,
    AttributeScorer as AttributeScorer,
)

# Auto import our handler classes
for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name.startswith("_"):
        continue
    import_module(f".{module_name}", package=__name__)

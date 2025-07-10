"""
EustatsPy - A Python wrapper for Eurostat APIs

This package provides easy access to Eurostat's Statistics and Catalogue APIs,
allowing users to search for datasets, retrieve metadata, and download data
as pandas DataFrames.
"""

from .client import EurostatClient
from .exceptions import EurostatAPIError, DatasetNotFoundError, InvalidParameterError
from .models import Dataset, TableOfContents, DatasetInfo

__version__ = "0.1.0"
__author__ = "Emanuel Raptis"

# Make the main client easily accessible
__all__ = [
    "EurostatClient",
    "Dataset", 
    "TableOfContents",
    "DatasetInfo",
    "EurostatAPIError",
    "DatasetNotFoundError", 
    "InvalidParameterError"
]
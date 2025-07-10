"""Custom exceptions for the EustatsPy package."""

class EurostatAPIError(Exception):
    """Base exception for Eurostat API errors."""
    pass

class DatasetNotFoundError(EurostatAPIError):
    """Raised when a requested dataset is not found."""
    pass

class InvalidParameterError(EurostatAPIError):
    """Raised when invalid parameters are provided to API calls."""
    pass

class CacheError(EurostatAPIError):
    """Raised when there are issues with caching operations."""
    pass

class DataParsingError(EurostatAPIError):
    """Raised when there are issues parsing API response data."""
    pass

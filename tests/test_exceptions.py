"""Tests for custom exceptions."""

import pytest
from eustatspy.exceptions import (
    EurostatAPIError,
    DatasetNotFoundError,
    InvalidParameterError,
    CacheError,
    DataParsingError
)


class TestEurostatAPIError:
    """Test cases for EurostatAPIError base exception."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        error = EurostatAPIError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_empty_message(self):
        """Test exception with empty message."""
        error = EurostatAPIError("")
        assert str(error) == ""
    
    def test_none_message(self):
        """Test exception with None message."""
        error = EurostatAPIError(None)
        assert str(error) == "None"
    
    def test_exception_inheritance(self):
        """Test that EurostatAPIError is a proper Exception."""
        error = EurostatAPIError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, EurostatAPIError)
    
    def test_raising_and_catching(self):
        """Test raising and catching the exception."""
        with pytest.raises(EurostatAPIError, match="Test error"):
            raise EurostatAPIError("Test error")
    
    def test_exception_with_complex_message(self):
        """Test exception with complex message."""
        message = "API Error 500: Internal server error occurred while processing dataset 'nama_10_gdp'"
        error = EurostatAPIError(message)
        assert str(error) == message


class TestDatasetNotFoundError:
    """Test cases for DatasetNotFoundError."""
    
    def test_inheritance(self):
        """Test proper inheritance from EurostatAPIError."""
        error = DatasetNotFoundError("Dataset not found")
        assert isinstance(error, DatasetNotFoundError)
        assert isinstance(error, EurostatAPIError)
        assert isinstance(error, Exception)
    
    def test_specific_error_message(self):
        """Test with dataset-specific error message."""
        dataset_code = "invalid_dataset_123"
        error = DatasetNotFoundError(f"Dataset '{dataset_code}' not found")
        assert dataset_code in str(error)
    
    def test_raising_and_catching_specific(self):
        """Test raising and catching DatasetNotFoundError specifically."""
        with pytest.raises(DatasetNotFoundError):
            raise DatasetNotFoundError("Dataset not found")
    
    def test_catching_as_base_class(self):
        """Test that DatasetNotFoundError can be caught as EurostatAPIError."""
        with pytest.raises(EurostatAPIError):
            raise DatasetNotFoundError("Dataset not found")


class TestInvalidParameterError:
    """Test cases for InvalidParameterError."""
    
    def test_inheritance(self):
        """Test proper inheritance from EurostatAPIError."""
        error = InvalidParameterError("Invalid parameter")
        assert isinstance(error, InvalidParameterError)
        assert isinstance(error, EurostatAPIError)
        assert isinstance(error, Exception)
    
    def test_parameter_specific_message(self):
        """Test with parameter-specific error message."""
        param_name = "geoLevel"
        param_value = "invalid_level"
        error = InvalidParameterError(f"Invalid parameter '{param_name}': {param_value}")
        
        assert param_name in str(error)
        assert param_value in str(error)
    
    def test_multiple_parameters_error(self):
        """Test error message with multiple parameters."""
        message = "Invalid combination of parameters: time and lastTimePeriod cannot be used together"
        error = InvalidParameterError(message)
        assert "time" in str(error)
        assert "lastTimePeriod" in str(error)


class TestCacheError:
    """Test cases for CacheError."""
    
    def test_inheritance(self):
        """Test proper inheritance from EurostatAPIError."""
        error = CacheError("Cache error")
        assert isinstance(error, CacheError)
        assert isinstance(error, EurostatAPIError)
        assert isinstance(error, Exception)
    
    def test_cache_operation_errors(self):
        """Test cache-specific error messages."""
        error_messages = [
            "Error writing to cache: Permission denied",
            "Error reading from cache: File not found",
            "Error clearing cache: Disk full"
        ]
        
        for message in error_messages:
            error = CacheError(message)
            assert str(error) == message
    
    def test_cache_error_with_exception_details(self):
        """Test cache error that includes underlying exception details."""
        underlying_error = PermissionError("Access denied")
        cache_error = CacheError(f"Cache operation failed: {underlying_error}")
        
        assert "Cache operation failed" in str(cache_error)
        assert "Access denied" in str(cache_error)


class TestDataParsingError:
    """Test cases for DataParsingError."""
    
    def test_inheritance(self):
        """Test proper inheritance from EurostatAPIError."""
        error = DataParsingError("Parsing error")
        assert isinstance(error, DataParsingError)
        assert isinstance(error, EurostatAPIError)
        assert isinstance(error, Exception)
    
    def test_json_parsing_error(self):
        """Test JSON parsing error message."""
        error = DataParsingError("Failed to parse JSON response: Invalid JSON format")
        assert "JSON" in str(error)
        assert "Invalid JSON format" in str(error)
    
    def test_jsonstat_parsing_error(self):
        """Test JSON-stat parsing error message."""
        error = DataParsingError("Failed to convert JSON-stat to DataFrame: Missing dimension data")
        assert "JSON-stat" in str(error)
        assert "DataFrame" in str(error)
        assert "dimension data" in str(error)
    
    def test_csv_parsing_error(self):
        """Test CSV parsing error message."""
        error = DataParsingError("Failed to parse CSV data: Malformed header row")
        assert "CSV" in str(error)
        assert "header row" in str(error)


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance behavior."""
    
    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from EurostatAPIError."""
        exceptions = [
            DatasetNotFoundError("test"),
            InvalidParameterError("test"),
            CacheError("test"),
            DataParsingError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, EurostatAPIError)
    
    def test_catching_base_exception(self):
        """Test that base exception can catch all derived exceptions."""
        derived_exceptions = [
            DatasetNotFoundError("Dataset not found"),
            InvalidParameterError("Invalid parameter"),
            CacheError("Cache error"),
            DataParsingError("Parsing error")
        ]
        
        for exc in derived_exceptions:
            with pytest.raises(EurostatAPIError):
                raise exc
    
    def test_specific_exception_catching(self):
        """Test catching specific exception types."""
        # Test that we can catch specific exceptions without catching others
        with pytest.raises(DatasetNotFoundError):
            try:
                raise DatasetNotFoundError("Not found")
            except InvalidParameterError:
                pytest.fail("Should not catch InvalidParameterError")
            except DatasetNotFoundError:
                raise  # Re-raise for pytest to catch
    
    def test_exception_type_checking(self):
        """Test isinstance checks work correctly."""
        dataset_error = DatasetNotFoundError("Not found")
        param_error = InvalidParameterError("Invalid")
        cache_error = CacheError("Cache issue")
        parsing_error = DataParsingError("Parse failed")
        
        # Positive checks
        assert isinstance(dataset_error, DatasetNotFoundError)
        assert isinstance(param_error, InvalidParameterError)
        assert isinstance(cache_error, CacheError)
        assert isinstance(parsing_error, DataParsingError)
        
        # Cross checks (should be False)
        assert not isinstance(dataset_error, InvalidParameterError)
        assert not isinstance(param_error, DatasetNotFoundError)
        assert not isinstance(cache_error, DataParsingError)
        assert not isinstance(parsing_error, CacheError)
        
        # Base class checks (should all be True)
        for exc in [dataset_error, param_error, cache_error, parsing_error]:
            assert isinstance(exc, EurostatAPIError)
            assert isinstance(exc, Exception)


class TestExceptionUsageScenarios:
    """Test realistic usage scenarios for exceptions."""
    
    def test_api_error_chain(self):
        """Test chaining of API errors."""
        def level3():
            raise DatasetNotFoundError("Dataset 'invalid_code' not found")
        
        def level2():
            try:
                level3()
            except DatasetNotFoundError as e:
                raise EurostatAPIError(f"Failed to retrieve data: {e}") from e
        
        def level1():
            try:
                level2()
            except EurostatAPIError as e:
                raise EurostatAPIError(f"API call failed: {e}") from e
        
        with pytest.raises(EurostatAPIError) as exc_info:
            level1()
        
        # Check the exception chain
        assert "API call failed" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
    
    def test_multiple_error_handling(self):
        """Test handling multiple types of errors in sequence."""
        errors_to_test = [
            (DatasetNotFoundError, "Dataset not found"),
            (InvalidParameterError, "Invalid geo level"),
            (CacheError, "Cache write failed"),
            (DataParsingError, "JSON parsing failed"),
            (EurostatAPIError, "Generic API error")
        ]
        
        for error_class, message in errors_to_test:
            with pytest.raises(EurostatAPIError):  # All should be catchable as base
                raise error_class(message)
    
    def test_error_message_formatting(self):
        """Test that error messages are properly formatted and informative."""
        # Test various realistic error scenarios
        scenarios = [
            (
                DatasetNotFoundError,
                "Dataset 'nama_10_gdp_invalid' not found. Check the dataset code and try again."
            ),
            (
                InvalidParameterError,
                "Invalid geo level 'invalid_level'. Must be one of: aggregate, country, nuts1, nuts2, nuts3, city."
            ),
            (
                CacheError,
                "Error writing to cache file '/tmp/.eustatspy_cache/abc123.pkl': Permission denied"
            ),
            (
                DataParsingError,
                "Failed to convert JSON-stat to DataFrame: Missing 'value' field in response data"
            )
        ]
        
        for error_class, message in scenarios:
            error = error_class(message)
            assert str(error) == message
            assert len(str(error)) > 10  # Ensure messages are substantive
    
    def test_exception_context_preservation(self):
        """Test that exception context is preserved through the stack."""
        def simulate_api_call():
            # Create a mock ConnectionError since we might not have requests available
            class MockConnectionError(Exception):
                pass
            raise MockConnectionError("Network unreachable")
        
        def handle_api_call():
            try:
                simulate_api_call()
            except Exception as e:
                raise EurostatAPIError(f"Failed to connect to Eurostat API: {e}") from e
        
        with pytest.raises(EurostatAPIError) as exc_info:
            handle_api_call()
        
        assert "Failed to connect to Eurostat API" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
        assert "Network unreachable" in str(exc_info.value.__cause__)


class TestExceptionDocumentation:
    """Test that exceptions have proper documentation and are usable."""
    
    def test_exception_docstrings(self):
        """Test that exceptions have docstrings (basic check)."""
        exceptions = [
            EurostatAPIError,
            DatasetNotFoundError,
            InvalidParameterError,
            CacheError,
            DataParsingError
        ]
        
        for exc_class in exceptions:
            # Just verify they have some form of documentation
            assert exc_class.__doc__ is not None
            assert len(exc_class.__doc__.strip()) > 0
    
    def test_exception_names_are_descriptive(self):
        """Test that exception names clearly indicate their purpose."""
        exception_names = [
            "EurostatAPIError",
            "DatasetNotFoundError", 
            "InvalidParameterError",
            "CacheError",
            "DataParsingError"
        ]
        
        # Names should be descriptive and follow naming conventions
        for name in exception_names:
            assert name.endswith("Error")
            assert len(name) > 5  # Not too short
            assert name[0].isupper()  # Proper case
    
    def test_exceptions_are_importable(self):
        """Test that all exceptions can be imported from the main module."""
        import eustatspy as est
        
        # All exceptions should be accessible from the main module
        assert hasattr(est, 'EurostatAPIError')
        assert hasattr(est, 'DatasetNotFoundError')
        assert hasattr(est, 'InvalidParameterError')
        
        # Test they're the same classes
        assert est.EurostatAPIError is EurostatAPIError
        assert est.DatasetNotFoundError is DatasetNotFoundError
        assert est.InvalidParameterError is InvalidParameterError
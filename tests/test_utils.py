"""Tests for utility functions and classes."""

import pytest
import json
import pickle
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import requests

from eustatspy.utils import Cache, parse_datetime, handle_api_errors, validate_geo_level
from eustatspy.exceptions import (
    CacheError, EurostatAPIError, DatasetNotFoundError, InvalidParameterError
)


class TestCache:
    """Test cases for the Cache class."""
    
    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization."""
        cache = Cache(temp_cache_dir, expire_hours=12)
        
        assert cache.cache_dir == Path(temp_cache_dir)
        assert cache.expire_hours == 12
        assert cache.cache_dir.exists()
    
    def test_cache_initialization_creates_directory(self):
        """Test that cache initialization creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "new_cache_dir"
            assert not cache_dir.exists()
            
            cache = Cache(str(cache_dir))
            assert cache_dir.exists()
    
    def test_get_cache_key_simple(self, cache_instance):
        """Test cache key generation with simple parameters."""
        key1 = cache_instance._get_cache_key("http://test.com")
        key2 = cache_instance._get_cache_key("http://test.com")
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
    
    def test_get_cache_key_with_params(self, cache_instance):
        """Test cache key generation with parameters."""
        params1 = {"geo": "SE", "time": "2020"}
        params2 = {"time": "2020", "geo": "SE"}  # Different order
        
        key1 = cache_instance._get_cache_key("http://test.com", params1)
        key2 = cache_instance._get_cache_key("http://test.com", params2)
        
        assert key1 == key2  # Order shouldn't matter
    
    def test_cache_set_and_get(self, cache_instance):
        """Test setting and getting cache data."""
        url = "http://test.com/data"
        data = {"test": "data", "number": 123}
        
        # Initially no cache
        assert cache_instance.get(url) is None
        
        # Set cache
        cache_instance.set(url, data)
        
        # Get from cache
        cached_data = cache_instance.get(url)
        assert cached_data == data
    
    def test_cache_with_parameters(self, cache_instance):
        """Test caching with URL parameters."""
        url = "http://test.com/data"
        params = {"geo": "SE", "time": "2020"}
        data = {"result": "test"}
        
        # Set cache with params
        cache_instance.set(url, data, params)
        
        # Get with same params
        cached_data = cache_instance.get(url, params)
        assert cached_data == data
        
        # Get with different params should return None
        different_params = {"geo": "NO", "time": "2020"}
        assert cache_instance.get(url, different_params) is None
    
    def test_cache_expiration(self, temp_cache_dir):
        """Test cache expiration functionality."""
        # Create cache with very short expiration
        cache = Cache(temp_cache_dir, expire_hours=0.001)  # ~3.6 seconds
        
        url = "http://test.com"
        data = {"test": "data"}
        
        # Set cache
        cache.set(url, data)
        
        # Should get data immediately
        assert cache.get(url) == data
        
        # Manually modify file timestamp to simulate expiration
        cache_key = cache._get_cache_key(url)
        cache_file = cache.cache_dir / f"{cache_key}.pkl"
        
        # Set modification time to 2 hours ago using os.utime
        old_time = datetime.now().timestamp() - 7200  # 2 hours ago
        os.utime(cache_file, (old_time, old_time))
        
        # Should return None (expired)
        assert cache.get(url) is None
        
        # Cache file should be deleted
        assert not cache_file.exists()
    
    def test_cache_clear(self, cache_instance):
        """Test clearing all cache files."""
        # Set multiple cache entries
        cache_instance.set("http://test1.com", {"data": 1})
        cache_instance.set("http://test2.com", {"data": 2})
        cache_instance.set("http://test3.com", {"data": 3})
        
        # Verify they exist
        assert cache_instance.get("http://test1.com") is not None
        assert cache_instance.get("http://test2.com") is not None
        assert cache_instance.get("http://test3.com") is not None
        
        # Clear cache
        cache_instance.clear()
        
        # Verify all are gone
        assert cache_instance.get("http://test1.com") is None
        assert cache_instance.get("http://test2.com") is None
        assert cache_instance.get("http://test3.com") is None
    
    def test_cache_error_handling(self, temp_cache_dir):
        """Test cache error handling."""
        cache = Cache(temp_cache_dir)
        
        # Test error in set operation (simulate permission error)
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(CacheError, match="Error writing to cache"):
                cache.set("http://test.com", {"data": "test"})
        
        # Test error in get operation
        cache.set("http://test.com", {"data": "test"})  # Set valid data first
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(CacheError, match="Error reading from cache"):
                cache.get("http://test.com")
        
        # Test error in clear operation
        with patch.object(Path, 'glob', side_effect=OSError("Filesystem error")):
            with pytest.raises(CacheError, match="Error clearing cache"):
                cache.clear()
    
    def test_cache_complex_data(self, cache_instance):
        """Test caching complex data structures."""
        complex_data = {
            "nested": {
                "dict": {"value": 123},
                "list": [1, 2, 3, {"inner": "value"}]
            },
            "datetime": datetime.now(),
            "none_value": None,
            "boolean": True
        }
        
        url = "http://test.com/complex"
        cache_instance.set(url, complex_data)
        cached_data = cache_instance.get(url)
        
        assert cached_data == complex_data
        assert isinstance(cached_data["datetime"], datetime)


class TestParseDatetime:
    """Test cases for parse_datetime function."""
    
    def test_parse_iso_format(self):
        """Test parsing ISO format datetime."""
        result = parse_datetime("2025-06-26T23:00:00+0200")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 26
    
    def test_parse_date_only(self):
        """Test parsing date-only format."""
        result = parse_datetime("2025-06-26")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 26
    
    def test_parse_european_format(self):
        """Test parsing European date format."""
        result = parse_datetime("26.06.2025")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 26
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        assert parse_datetime("") is None
        assert parse_datetime(" ") is None
    
    def test_parse_none(self):
        """Test parsing None value."""
        assert parse_datetime(None) is None
    
    def test_parse_invalid_format(self):
        """Test parsing invalid date format."""
        assert parse_datetime("invalid-date") is None
        assert parse_datetime("2025-13-40") is None
        assert parse_datetime("not-a-date") is None


class TestHandleApiErrors:
    """Test cases for handle_api_errors function."""
    
    def test_handle_success_response(self):
        """Test handling successful response (200)."""
        response = Mock()
        response.status_code = 200
        
        # Should not raise any exception
        handle_api_errors(response)
    
    def test_handle_404_with_json_error(self):
        """Test handling 404 error with JSON error message."""
        response = Mock()
        response.status_code = 404
        response.json.return_value = {
            "error": {
                "status": 404,
                "label": "Dataset not found"
            }
        }
        
        with pytest.raises(DatasetNotFoundError, match="Dataset not found"):
            handle_api_errors(response)
    
    def test_handle_400_with_json_error(self):
        """Test handling 400 error with JSON error message."""
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "error": {
                "status": 400,
                "label": "Invalid parameters"
            }
        }
        
        with pytest.raises(InvalidParameterError, match="Invalid parameters"):
            handle_api_errors(response)
    
    def test_handle_500_with_json_error(self):
        """Test handling 500 error with JSON error message."""
        response = Mock()
        response.status_code = 500
        response.json.return_value = {
            "error": {
                "status": 500,
                "label": "Internal server error"
            }
        }
        
        with pytest.raises(EurostatAPIError, match="API Error 500"):
            handle_api_errors(response)
    
    def test_handle_404_without_json(self):
        """Test handling 404 error without JSON response."""
        response = Mock()
        response.status_code = 404
        response.json.side_effect = requests.exceptions.JSONDecodeError("", "", 0)
        
        with pytest.raises(DatasetNotFoundError, match="Dataset not found"):
            handle_api_errors(response)
    
    def test_handle_400_without_json(self):
        """Test handling 400 error without JSON response."""
        response = Mock()
        response.status_code = 400
        response.json.side_effect = requests.exceptions.JSONDecodeError("", "", 0)
        
        with pytest.raises(InvalidParameterError, match="Invalid request parameters"):
            handle_api_errors(response)
    
    def test_handle_generic_error_without_json(self):
        """Test handling generic error without JSON response."""
        response = Mock()
        response.status_code = 503
        response.text = "Service unavailable"
        response.json.side_effect = requests.exceptions.JSONDecodeError("", "", 0)
        
        with pytest.raises(EurostatAPIError, match="HTTP 503"):
            handle_api_errors(response)
    
    def test_handle_error_malformed_json(self):
        """Test handling error with malformed JSON error structure."""
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "not_error": "different structure"
        }
        response.text = "Bad request"
        
        with pytest.raises(InvalidParameterError, match="Invalid request parameters"):
            handle_api_errors(response)


class TestValidateGeoLevel:
    """Test cases for validate_geo_level function."""
    
    def test_valid_geo_levels(self):
        """Test validation of valid geo levels."""
        valid_levels = ["aggregate", "country", "nuts1", "nuts2", "nuts3", "city"]
        
        for level in valid_levels:
            result = validate_geo_level(level)
            assert result == level
    
    def test_invalid_geo_level(self):
        """Test validation of invalid geo level."""
        with pytest.raises(InvalidParameterError, match="Invalid geo level"):
            validate_geo_level("invalid_level")
    
    def test_case_sensitive_geo_level(self):
        """Test that geo level validation is case sensitive."""
        with pytest.raises(InvalidParameterError):
            validate_geo_level("COUNTRY")  # Should be "country"
        
        with pytest.raises(InvalidParameterError):
            validate_geo_level("Country")  # Should be "country"


class TestUtilsIntegration:
    """Integration tests for utility functions."""
    
    def test_cache_with_datetime_serialization(self, cache_instance):
        """Test that cache can handle datetime objects properly."""
        data_with_datetime = {
            "timestamp": datetime(2025, 6, 26, 12, 30, 45),
            "values": [1, 2, 3]
        }
        
        url = "http://test.com/datetime"
        cache_instance.set(url, data_with_datetime)
        cached_data = cache_instance.get(url)
        
        assert cached_data == data_with_datetime
        assert isinstance(cached_data["timestamp"], datetime)
    
    def test_parse_datetime_with_various_formats(self):
        """Test parse_datetime with various real-world formats."""
        test_cases = [
            ("2025-06-26T23:00:00+0200", datetime(2025, 6, 26, 23, 0, 0)),
            ("2025-06-26", datetime(2025, 6, 26, 0, 0, 0)),
            ("26.06.2025", datetime(2025, 6, 26, 0, 0, 0)),
            ("", None),
            (" ", None),
            (None, None),
            ("invalid", None)
        ]
        
        for input_str, expected in test_cases:
            result = parse_datetime(input_str)
            if expected is None:
                assert result is None
            else:
                assert result.year == expected.year
                assert result.month == expected.month
                assert result.day == expected.day
    
    def test_error_handling_integration(self):
        """Test error handling functions with various response scenarios."""
        # Test successful response
        success_response = Mock()
        success_response.status_code = 200
        handle_api_errors(success_response)  # Should not raise
        
        # Test various error scenarios
        error_scenarios = [
            (404, DatasetNotFoundError),
            (400, InvalidParameterError),
            (500, EurostatAPIError),
            (503, EurostatAPIError)
        ]
        
        for status_code, expected_exception in error_scenarios:
            response = Mock()
            response.status_code = status_code
            response.json.side_effect = requests.exceptions.JSONDecodeError("", "", 0)
            response.text = f"HTTP {status_code} error"
            
            with pytest.raises(expected_exception):
                handle_api_errors(response)
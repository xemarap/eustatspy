"""Utility functions for the EustatsPy package."""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import requests
from .exceptions import CacheError

class Cache:
    """Simple file-based cache for API responses."""
    
    def __init__(self, cache_dir: str = ".eustatspy_cache", expire_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.expire_hours = expire_hours
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key from URL and parameters."""
        cache_string = url
        if params:
            cache_string += json.dumps(params, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached response if available and not expired."""
        try:
            cache_key = self._get_cache_key(url, params)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if not cache_file.exists():
                return None
            
            # Check if cache has expired
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age > timedelta(hours=self.expire_hours):
                cache_file.unlink()  # Remove expired cache
                return None
            
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            raise CacheError(f"Error reading from cache: {e}")
    
    def set(self, url: str, data: Any, params: Optional[Dict] = None) -> None:
        """Cache a response."""
        try:
            cache_key = self._get_cache_key(url, params)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            raise CacheError(f"Error writing to cache: {e}")
    
    def clear(self) -> None:
        """Clear all cached files."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
        except Exception as e:
            raise CacheError(f"Error clearing cache: {e}")

def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse various datetime formats used by Eurostat API."""
    if not date_string:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
        "%Y-%m-%d",             # Date only
        "%d.%m.%Y",            # European date format
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None

def handle_api_errors(response: requests.Response) -> None:
    """Handle common API error responses."""
    from .exceptions import EurostatAPIError, DatasetNotFoundError, InvalidParameterError
    
    if response.status_code == 200:
        return
    
    try:
        error_data = response.json()
        if "error" in error_data:
            error_info = error_data["error"]
            
            # Handle case where error is a list
            if isinstance(error_info, list):
                if len(error_info) > 0:
                    error_info = error_info[0]  # Take first error
                else:
                    error_info = {}
            
            # Handle case where error_info is still not a dict
            if not isinstance(error_info, dict):
                error_info = {}
            
            status = error_info.get("status", response.status_code)
            message = error_info.get("label", "Unknown error")
            
            if status == 404:
                raise DatasetNotFoundError(f"Dataset not found: {message}")
            elif status == 400:
                raise InvalidParameterError(f"Bad request: {message}")
            else:
                raise EurostatAPIError(f"API Error {status}: {message}")
    except (json.JSONDecodeError, KeyError, AttributeError):
        pass
    
    # Fallback for non-JSON error responses
    if response.status_code == 404:
        raise DatasetNotFoundError("Dataset not found")
    elif response.status_code == 400:
        raise InvalidParameterError("Invalid request parameters")
    else:
        raise EurostatAPIError(f"HTTP {response.status_code}: {response.text}")

def validate_geo_level(geo_level: str) -> str:
    """Validate geo level parameter."""
    from .exceptions import InvalidParameterError
    
    valid_levels = {"aggregate", "country", "nuts1", "nuts2", "nuts3", "city"}
    if geo_level not in valid_levels:
        raise InvalidParameterError(f"Invalid geo level '{geo_level}'. Must be one of: {valid_levels}")
    return geo_level
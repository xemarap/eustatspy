"""Statistics API functionality for retrieving actual data."""

import itertools
from typing import Dict, List, Optional, Any, Union, Tuple
import requests
import pandas as pd
import numpy as np
from .models import Dataset, DatasetInfo
from .utils import Cache, handle_api_errors, validate_geo_level
from .exceptions import EurostatAPIError, DataParsingError, InvalidParameterError

class StatisticsAPI:
    """Handler for Eurostat Statistics API operations."""
    
    def __init__(self, base_url: str = "https://ec.europa.eu/eurostat/api/dissemination", 
                 cache: Optional[Cache] = None):
        self.base_url = base_url
        self.cache = cache
        # Reference to catalogue API will be set by parent client
        self.catalogue = None
    
    def set_catalogue_reference(self, catalogue):
        """Set reference to catalogue API for metabase access."""
        self.catalogue = catalogue
    
    def get_data(self, dataset_code: str, **kwargs) -> Dict[str, Any]:
        """
        Get raw JSON-stat data from Eurostat.
        
        Args:
            dataset_code: The dataset code to retrieve
            **kwargs: Filter parameters and options
            
        Returns:
            Raw JSON-stat response as dictionary
        """
        url = f"{self.base_url}/statistics/1.0/data/{dataset_code}"
        
        # Build parameters - now returns list of tuples to handle multiple values
        params = self._build_params(**kwargs)
        
        # Create cache key from the final URL with parameters
        cache_key = self._create_cache_key(url, params)
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            # Handle both dictionary and list of tuples parameters
            if isinstance(params, list):
                response = requests.get(url, params=params)
            else:
                response = requests.get(url, params=params)
            
            handle_api_errors(response)
            
            data = response.json()
            
            # Handle asynchronous response
            if 'warning' in data and data['warning'].get('status') == 413:
                raise EurostatAPIError(
                    "Request too large. Data will be processed asynchronously. "
                    "Please try again later or use more specific filters."
                )
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, data)
            
            return data
            
        except requests.exceptions.JSONDecodeError as e:
            raise DataParsingError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise EurostatAPIError(f"Failed to get data: {e}")
    
    def get_data_as_dataframe(self, dataset_code: str, **kwargs) -> pd.DataFrame:
        """
        Get data as a pandas DataFrame.
        
        Args:
            dataset_code: The dataset code to retrieve
            **kwargs: Filter parameters and options
            
        Returns:
            pandas DataFrame with the data
        """
        json_data = self.get_data(dataset_code, **kwargs)
        return self._jsonstat_to_dataframe(json_data)
    
    def get_available_filters(self, dataset_code: str) -> Dict[str, List[str]]:
        """
        Get available filter values for each dimension using Metabase.
        
        This method now always uses the Metabase for consistency and performance.
        
        Args:
            dataset_code: The dataset code
            
        Returns:
            Dictionary mapping dimension names to available values
        """
        if self.catalogue:
            return self.catalogue.get_dataset_dimensions_from_metabase(dataset_code)
        
    
    def _build_params(self, **kwargs) -> List[Tuple[str, str]]:
        """
        Build API parameters from keyword arguments.
        Returns list of tuples to handle multiple values for same parameter.
        """
        params = []
        
        # Handle format parameter
        params.append(('format', 'JSON'))  # Only supported format
        
        # Always use English language
        params.append(('lang', 'EN'))
        
        # Handle geo level parameter
        if 'geoLevel' in kwargs:
            validate_geo_level(kwargs['geoLevel'])
            params.append(('geoLevel', kwargs['geoLevel']))
        
        # Handle time parameters - these are special and mutually exclusive
        time_params = ['time', 'sinceTimePeriod', 'untilTimePeriod', 'lastTimePeriod']
        time_param_found = []
        
        for param in time_params:
            if param in kwargs:
                time_param_found.append(param)
        
        # Check for valid time parameter combinations
        if len(time_param_found) > 1:
            # Only sinceTimePeriod + untilTimePeriod is allowed as combination
            if not (len(time_param_found) == 2 and 
                   'sinceTimePeriod' in time_param_found and 
                   'untilTimePeriod' in time_param_found):
                raise InvalidParameterError(
                    "Only one time parameter allowed, except sinceTimePeriod and untilTimePeriod can be used together. "
                    f"Found: {time_param_found}"
                )
        
        # Add time parameters
        for param in time_params:
            if param in kwargs:
                value = kwargs[param]
                if isinstance(value, list):
                    # Handle multiple time values (e.g., time=['2020', '2021'])
                    for v in value:
                        params.append((param, str(v)))
                else:
                    params.append((param, str(value)))
        
        # Handle other filter parameters (any dimension)
        reserved_params = {
            'format', 'lang', 'language', 'geoLevel', 
            'time', 'sinceTimePeriod', 'untilTimePeriod', 'lastTimePeriod'
        }
        
        for key, value in kwargs.items():
            if key not in reserved_params:
                if isinstance(value, list):
                    # Handle multiple values for the same dimension
                    # e.g., geo=['SE11', 'DK01'] becomes [('geo', 'SE11'), ('geo', 'DK01')]
                    for v in value:
                        params.append((key, str(v)))
                else:
                    params.append((key, str(value)))
        
        return params
    
    def _create_cache_key(self, url: str, params: List[Tuple[str, str]]) -> str:
        """Create a consistent cache key from URL and parameters."""
        # Sort parameters to ensure consistent caching
        sorted_params = sorted(params)
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        return f"{url}?{param_string}"
    
    def _jsonstat_to_dataframe(self, json_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert JSON-stat format to pandas DataFrame.
        
        Args:
            json_data: JSON-stat response data
            
        Returns:
            pandas DataFrame
        """
        try:
            # Extract basic info
            if 'value' not in json_data:
                raise DataParsingError("No value data found in JSON-stat response")
            
            values = json_data['value']
            dimensions = json_data.get('dimension', {})
            dimension_ids = json_data.get('id', [])
            dimension_sizes = json_data.get('size', [])
            
            if not dimension_ids or not dimension_sizes:
                raise DataParsingError("Missing dimension information in JSON-stat response")
            
            # Create index arrays for each dimension
            dimension_indices = []
            dimension_labels = []
            
            for i, dim_id in enumerate(dimension_ids):
                dim_size = dimension_sizes[i]
                dim_info = dimensions.get(dim_id, {})
                
                # Get category information
                category = dim_info.get('category', {})
                index_map = category.get('index', {})
                label_map = category.get('label', {})
                
                # Create ordered list of codes
                if index_map:
                    # Sort by index values to get correct order
                    sorted_items = sorted(index_map.items(), key=lambda x: x[1])
                    codes = [item[0] for item in sorted_items]
                else:
                    # Fallback to numeric indices
                    codes = [str(j) for j in range(dim_size)]
                
                # Get labels for these codes
                labels = [label_map.get(code, code) for code in codes]
                
                dimension_indices.append(codes)
                dimension_labels.append(labels)
            
            # Create MultiIndex from cartesian product of all dimensions
            if len(dimension_indices) > 1:
                index_tuples = list(itertools.product(*dimension_indices))
                label_tuples = list(itertools.product(*dimension_labels))
                
                # Create MultiIndex
                index = pd.MultiIndex.from_tuples(
                    index_tuples,
                    names=dimension_ids
                )
                
                # Create label MultiIndex for display
                label_index = pd.MultiIndex.from_tuples(
                    label_tuples,
                    names=dimension_ids
                )
            else:
                index = pd.Index(dimension_indices[0], name=dimension_ids[0])
                label_index = pd.Index(dimension_labels[0], name=dimension_ids[0])
            
            # Create array for values
            total_size = np.prod(dimension_sizes)
            value_array = np.full(total_size, np.nan)
            
            # Fill in the values
            for key, val in values.items():
                try:
                    idx = int(key)
                    if idx < len(value_array):
                        value_array[idx] = float(val) if val is not None else np.nan
                except (ValueError, TypeError):
                    continue
            
            # Create DataFrame
            df = pd.DataFrame({
                'value': value_array
            }, index=index)
            
            # Add status information if available
            if 'status' in json_data:
                status_array = np.full(total_size, '', dtype=object)
                for key, status in json_data['status'].items():
                    try:
                        idx = int(key)
                        if idx < len(status_array):
                            status_array[idx] = status
                    except (ValueError, TypeError):
                        continue
                df['status'] = status_array
            
            # Reset index to make dimensions into columns for easier use
            df = df.reset_index()
            
            # Replace dimension codes with labels for better readability
            for i, dim_id in enumerate(dimension_ids):
                dim_info = dimensions.get(dim_id, {})
                category = dim_info.get('category', {})
                label_map = category.get('label', {})
                
                if label_map:
                    # Add a column with labels
                    df[f'{dim_id}_label'] = df[dim_id].map(label_map)
            
            return df
            
        except Exception as e:
            raise DataParsingError(f"Failed to convert JSON-stat to DataFrame: {e}")
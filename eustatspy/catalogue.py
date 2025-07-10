"""Catalogue API functionality for browsing datasets and metadata."""

from typing import Dict, List, Optional, Tuple
import requests
import pandas as pd
import csv
import io
import gzip
from collections import defaultdict
from .models import DatasetInfo, TableOfContents
from .utils import Cache, handle_api_errors, parse_datetime
from .exceptions import EurostatAPIError, DataParsingError, InvalidParameterError

class CatalogueAPI:
    """Handler for Eurostat Catalogue API operations."""
    
    def __init__(self, base_url: str = "https://ec.europa.eu/eurostat/api/dissemination", 
                 cache: Optional[Cache] = None):
        self.base_url = base_url
        self.cache = cache
        self._metabase_cache = None
    
    def get_table_of_contents(self) -> TableOfContents:
        """
        Get the table of contents from Eurostat in English using TXT format.
        
        Returns:
            TableOfContents object with dataset information
        """
        return self._get_toc_txt()
    
    def get_metabase(self, refresh: bool = False) -> Dict[str, Dict[str, List[str]]]:
        """
        Get the metabase containing all dataset dimensions and available values.
        
        Args:
            refresh: Whether to refresh cached metabase data
            
        Returns:
            Dictionary with structure: {dataset_code: {dimension: [values]}}
        """
        if refresh:
            self._metabase_cache = None
        
        if self._metabase_cache is not None:
            return self._metabase_cache
        
        url = f"{self.base_url}/catalogue/metabase.txt.gz"
        
        # Check cache first
        if self.cache:
            cached_data = self.cache.get(url)
            if cached_data:
                self._metabase_cache = cached_data
                return cached_data
        
        try:
            print("Downloading metabase (this may take a moment)...")
            response = requests.get(url, stream=True)
            handle_api_errors(response)
            
            # Parse the gzipped content
            metabase = defaultdict(lambda: defaultdict(list))
            
            with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        dataset_code = parts[0]
                        dimension = parts[1]
                        value = parts[2]
                        
                        metabase[dataset_code][dimension].append(value)
            
            # Convert defaultdict to regular dict for JSON serialization
            metabase_dict = {}
            for dataset_code, dimensions in metabase.items():
                metabase_dict[dataset_code] = {}
                for dimension, values in dimensions.items():
                    metabase_dict[dataset_code][dimension] = values
            
            self._metabase_cache = metabase_dict
            
            # Cache the result
            if self.cache:
                self.cache.set(url, metabase_dict)
            
            print(f"Metabase loaded: {len(metabase_dict):,} datasets")
            return metabase_dict
            
        except Exception as e:
            raise EurostatAPIError(f"Failed to get metabase: {e}")
    
    def get_dataset_dimensions_from_metabase(self, dataset_code: str) -> Dict[str, List[str]]:
        """
        Get available dimensions and their values for a dataset from metabase.
        
        Args:
            dataset_code: The dataset code
            
        Returns:
            Dictionary mapping dimension names to available values
        """
        metabase = self.get_metabase()
        
        if dataset_code not in metabase:
            return {}
        
        return metabase[dataset_code]
    
    def get_all_dataset_codes(self) -> List[str]:
        """
        Get all dataset codes available in the metabase.
        
        Returns:
            List of dataset codes
        """
        metabase = self.get_metabase()
        return list(metabase.keys())
    
    def search_datasets_in_metabase(self, query: str) -> List[str]:
        """
        Search for dataset codes in metabase that match the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching dataset codes
        """
        query = query.lower()
        metabase = self.get_metabase()
        
        matching_codes = []
        for dataset_code in metabase.keys():
            if query in dataset_code.lower():
                matching_codes.append(dataset_code)
        
        return matching_codes
    
    def _get_toc_txt(self) -> TableOfContents:
        """Get table of contents in text format (English only)."""
        url = f"{self.base_url}/catalogue/toc/txt"
        params = {"lang": "en"}  # Always use English
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(url, params)
            if cached_data:
                return cached_data
        
        try:
            response = requests.get(url, params=params)
            handle_api_errors(response)
            
            # Parse TXT format using CSV reader
            datasets = []
            hierarchy = {}
            current_path = []
            
            # Use CSV reader to handle tab-separated values with proper quoting
            csv_reader = csv.reader(io.StringIO(response.text), delimiter='\t', quotechar='"')
            
            # Skip header row
            header = next(csv_reader, None)
            if not header:
                raise DataParsingError("Empty TXT response or missing header")
            
            for row in csv_reader:
                if len(row) < 8:  # Ensure we have all expected columns
                    continue
                
                title, code, item_type, last_update_str, last_modified_str, data_start, data_end, values_str = row[:8]
                
                # Skip empty rows
                if not title.strip() or not code.strip():
                    continue
                
                # Calculate indentation level (4 spaces per level)
                indent_level = (len(title) - len(title.lstrip())) // 4
                clean_title = title.strip()
                
                # Adjust current path based on indentation
                current_path = current_path[:indent_level]
                current_path.append(code)
                
                # Parse dates
                last_update = None
                if last_update_str.strip() and last_update_str.strip() != " ":
                    last_update = parse_datetime(last_update_str.strip())
                
                last_modified = None
                if last_modified_str.strip() and last_modified_str.strip() != " ":
                    last_modified = parse_datetime(last_modified_str.strip())
                
                # Parse data periods
                data_start_clean = data_start.strip() if data_start.strip() != " " else None
                data_end_clean = data_end.strip() if data_end.strip() != " " else None
                
                # Parse values count
                values_count = None
                if values_str.strip() and values_str.strip() != " ":
                    try:
                        values_count = int(values_str.strip())
                    except ValueError:
                        pass
                
                # Create DatasetInfo object
                dataset_info = DatasetInfo(
                    code=code,
                    title=clean_title,
                    type=item_type,
                    last_update=last_update,
                    last_modified=last_modified,
                    data_start=data_start_clean,
                    data_end=data_end_clean,
                    values_count=values_count
                )
                
                datasets.append(dataset_info)
                
                # Build hierarchy
                if indent_level > 0 and len(current_path) > 1:
                    parent_code = current_path[indent_level - 1]
                    if parent_code not in hierarchy:
                        hierarchy[parent_code] = []
                    if code not in hierarchy[parent_code]:
                        hierarchy[parent_code].append(code)
            
            toc = TableOfContents(
                datasets=datasets,
                hierarchy=hierarchy
            )
            
            # Cache result
            if self.cache:
                self.cache.set(url, toc, params)
            
            return toc
            
        except Exception as e:
            raise EurostatAPIError(f"Failed to get table of contents: {e}")
    
    def search_datasets(self, 
               query: str, 
               max_results: int = 50,
               updated_since: Optional[str] = None) -> pd.DataFrame:
        """
        Search for datasets by title, description, or code.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            updated_since: Only include datasets updated since this date (format: YYYY-MM-DD, inclusive)
            
        Returns:
            pandas DataFrame with search results, sorted by last update (most recent first)
        """
        from datetime import datetime
        
        # Validate updated_since parameter if provided
        updated_since_date = None
        if updated_since is not None:
            try:
                updated_since_date = datetime.strptime(updated_since, '%Y-%m-%d')
            except ValueError:
                raise InvalidParameterError(f"Invalid date format '{updated_since}'. Use YYYY-MM-DD format.")
        
        # Get table of contents
        toc = self.get_table_of_contents()
        
        query = query.lower()
        
        # Search for matching datasets
        results = []
        for dataset in toc.datasets:
            # First check if dataset matches search criteria
            matches_search = False
            
            # Search in title
            if query in dataset.title.lower():
                matches_search = True
            # Search in description
            elif dataset.short_description and query in dataset.short_description.lower():
                matches_search = True
            # Search in code
            elif query in dataset.code.lower():
                matches_search = True
            
            if not matches_search:
                continue
            
            # Then check date filter if specified
            if updated_since_date is not None:
                if dataset.last_update is None:
                    # Skip datasets with no update date when filter is specified
                    continue
                if dataset.last_update.date() < updated_since_date.date():
                    continue
            
            results.append(dataset)
        
        # Convert to DataFrame
        data = []
        for dataset in results:
            row = {
                'code': dataset.code,
                'title': dataset.title,
                'type': dataset.type,
                'last_update': dataset.last_update,
                'last_modified': dataset.last_modified,
                'data_start': dataset.data_start,
                'data_end': dataset.data_end,
                'values_count': dataset.values_count,
                'short_description': dataset.short_description or '',
                'unit': dataset.unit or '',
                'source': dataset.source or ''
            }
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by last_update descending (most recent first), handling None values
        if not df.empty:
            df = df.sort_values('last_update', ascending=False, na_position='last')
        
        # Limit results
        df = df.head(max_results)
        
        return df.reset_index(drop=True)
    
    def get_dataset_info(self, dataset_code: str) -> Optional[DatasetInfo]:
        """
        Get information about a specific dataset.
        
        Args:
            dataset_code: The dataset code to look up
            
        Returns:
            DatasetInfo object if found, None otherwise
        """
        toc = self.get_table_of_contents()
        
        for dataset in toc.datasets:
            if dataset.code == dataset_code:
                return dataset
        
        return None
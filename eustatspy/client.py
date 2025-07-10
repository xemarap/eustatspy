"""Main client class for the EustatsPy package."""

from typing import Dict, List, Optional, Union, Any
import pandas as pd
import warnings
import time
from .catalogue import CatalogueAPI
from .statistics import StatisticsAPI
from .models import Dataset, DatasetInfo, TableOfContents
from .utils import Cache
from .exceptions import EurostatAPIError, InvalidParameterError

class EurostatClient:
    """
    Main client for accessing Eurostat APIs.
    
    This class provides a unified interface for browsing datasets via the Catalogue API
    and retrieving data via the Statistics API. All content is returned in English.
    """
    
    def __init__(self, 
                 base_url: str = "https://ec.europa.eu/eurostat/api/dissemination",
                 cache_enabled: bool = False,
                 cache_dir: str = ".eustatspy_cache",
                 cache_expire_hours: int = 24):
        """
        Initialize the Eurostat client.
        
        Args:
            base_url: Base URL for Eurostat APIs
            cache_enabled: Whether to enable caching
            cache_dir: Directory for cache files
            cache_expire_hours: Hours after which cache expires
        """
        self.base_url = base_url
        
        # Initialize cache
        self.cache = Cache(cache_dir, cache_expire_hours) if cache_enabled else None
        
        # Initialize API handlers
        self.catalogue = CatalogueAPI(base_url, self.cache)
        self.statistics = StatisticsAPI(base_url, self.cache)
        
        # Set catalogue reference in statistics API for metabase access
        self.statistics.set_catalogue_reference(self.catalogue)
        
        # Cache for table of contents
        self._toc_cache = None
    
    def get_table_of_contents(self, refresh: bool = False) -> TableOfContents:
        """
        Get the table of contents showing all available datasets in English.
        
        Args:
            refresh: Whether to refresh cached data
            
        Returns:
            TableOfContents object
        """
        if refresh:
            self._toc_cache = None
        
        if self._toc_cache is None:
            self._toc_cache = self.catalogue.get_table_of_contents()
        
        return self._toc_cache
    
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
            
        Examples:
            # Search for GDP datasets
            df = client.search_datasets("GDP")
            
            # Search for datasets updated since July 1, 2025
            df = client.search_datasets("employment", updated_since="2025-07-01")
            
            # Search for recent population datasets
            df = client.search_datasets("population", max_results=10, updated_since="2025-06-01")
        """
        return self.catalogue.search_datasets(query, max_results, updated_since)
    
    def get_dataset_info(self, dataset_code: str) -> Optional[DatasetInfo]:
        """
        Get detailed information about a specific dataset.
        
        Args:
            dataset_code: The dataset code
            
        Returns:
            DatasetInfo object if found, None otherwise
        """
        return self.catalogue.get_dataset_info(dataset_code)
    
    def get_data_as_dataframe(self, 
                            dataset_code: str, 
                            **filters) -> pd.DataFrame:
        """
        Get dataset as a pandas DataFrame with comprehensive filtering support.
        
        This is the main method for data retrieval. It supports:
        - Multiple values for any dimension (geo, time, etc.)
        - Time range filtering
        - Latest data retrieval
        - All standard Eurostat API filters
        
        Args:
            dataset_code: The dataset code to retrieve
            **filters: Filter parameters for the API
            
        Common filter parameters:
            geo: Geographic area(s) - single value, list, or 'all'
                Examples: geo='FR', geo=['FR', 'DE'], geo='all'
            time: Time period(s) - single value or list
                Examples: time='2020', time=['2020', '2021'], time=['2020-Q1', '2020-Q2']
            sinceTimePeriod: Start time period (use with untilTimePeriod)
                Example: sinceTimePeriod='2015'
            untilTimePeriod: End time period (use with sinceTimePeriod)
                Example: untilTimePeriod='2020'
            lastTimePeriod: Number of latest periods to include
                Example: lastTimePeriod=5
            geoLevel: Geographic level filter
                Options: 'aggregate', 'country', 'nuts1', 'nuts2', 'nuts3', 'city'
            
        Dataset-specific dimensions can also be filtered:
            unit, na_item, sex, age, indic_na, etc.
            
        Returns:
            pandas DataFrame with the data
            
        Examples:
            # Basic usage - single country, latest data
            df = client.get_data_as_dataframe('nama_10_gdp', geo='FR', lastTimePeriod=3)
            
            # Multiple countries and years
            df = client.get_data_as_dataframe(
                'nama_10_gdp',
                geo=['FR', 'DE', 'IT'],
                time=['2020', '2021', '2022'],
                unit='CP_MEUR',
                na_item='B1GQ'
            )
            
            # Time range
            df = client.get_data_as_dataframe(
                'nama_10_gdp',
                geo='SE',
                sinceTimePeriod='2015',
                untilTimePeriod='2020'
            )
            
            # Geographic level filtering
            df = client.get_data_as_dataframe(
                'nama_10r_3gdp',
                geoLevel='nuts2',
                lastTimePeriod=1
            )
        """
        return self.statistics.get_data_as_dataframe(dataset_code, **filters)
    
    def get_raw_data(self, dataset_code: str, **filters) -> Dict[str, Any]:
        """
        Get raw JSON-stat data from Eurostat.
        
        Args:
            dataset_code: The dataset code to retrieve
            **filters: Filter parameters for the API
            
        Returns:
            Raw JSON-stat response as dictionary
        """
        return self.statistics.get_data(dataset_code, **filters)
    
    def get_available_filters(self, dataset_code: str) -> Dict[str, List[str]]:
        """
        Get available filter values for each dimension of a dataset using Metabase.
        
        Args:
            dataset_code: The dataset code
            
        Returns:
            Dictionary mapping dimension names to available values
        """
        return self.catalogue.get_dataset_dimensions_from_metabase(dataset_code)
    
    def describe_dataset(self, 
                     dataset_code: str, 
                     show_all_for_dimension: Optional[str] = None,
                     max_values_per_dimension: int = 10) -> None:
        """
        Print a detailed description of a dataset including metadata and available filters.
        
        This method always uses the Metabase for dimension information, which is faster
        and more comprehensive than API calls.
        
        Args:
            dataset_code: The dataset code
            show_all_for_dimension: Dimension name to show all available values for
            max_values_per_dimension: Maximum values to show per dimension (default: 10)
        """
        # Get basic info from table of contents
        info = self.get_dataset_info(dataset_code)
        
        # Get dimension information from metabase
        try:
            metabase_filters = self.catalogue.get_dataset_dimensions_from_metabase(dataset_code)
        except Exception as e:
            print(f"Error loading dataset '{dataset_code}': {e}")
            return
        
        # If dataset not found in TOC but exists in metabase
        if info is None and metabase_filters:
            print(f"Dataset '{dataset_code}' found in metabase but not in table of contents.")
            print("This may be a valid dataset code that's not publicly listed.")
            # Create a minimal info object
            info = DatasetInfo(code=dataset_code, title=dataset_code, type="dataset")
        elif info is None and not metabase_filters:
            print(f"Dataset '{dataset_code}' not found.")
            return
        
        # Display basic information
        print(f"Dataset: {dataset_code}")
        print("=" * 50)
        print(f"Title: {info.title}")
        
        if info.short_description:
            print(f"Description: {info.short_description}")
        
        print(f"Type: {info.type}")
        
        if info.last_update:
            print(f"Last Updated: {info.last_update}")
        if info.data_start and info.data_end:
            print(f"Data Period: {info.data_start} - {info.data_end}")
        if info.values_count:
            print(f"Number of Values: {info.values_count:,}")
        if info.unit:
            print(f"Unit: {info.unit}")
        if info.source:
            print(f"Source: {info.source}")
        
        # Display dimensions and filters
        if not metabase_filters:
            print("\nNo dimension information available.")
            return
        
        print(f"\nAvailable Dimensions and Filters:")
        print("-" * 35)
        print(f"(Found {len(metabase_filters)} dimensions in metabase)")
        
        for dim_name, available_values in metabase_filters.items():
            print(f"\n{dim_name}:")
            
            # Determine if we should show all values for this dimension
            show_all = (
                show_all_for_dimension == dim_name or  # User specifically requested this dimension
                len(available_values) <= max_values_per_dimension  # Small enough to show all
            )
            
            if show_all:
                # Show all values
                for value in available_values:
                    print(f"  - {value}")
                
                if len(available_values) > max_values_per_dimension:
                    print(f"  (Showing all {len(available_values)} values)")
            else:
                # Show limited values with option to see all
                for value in available_values[:max_values_per_dimension]:
                    print(f"  - {value}")
                
                remaining = len(available_values) - max_values_per_dimension
                if remaining > 0:
                    print(f"  ... and {remaining} more values")
                    print(f"  (Use show_all_for_dimension='{dim_name}' to see all {len(available_values)} values)")
        
        # Display metadata URLs if available
        if info and info.metadata_urls:
            print(f"\nMetadata URLs:")
            for format_type, url in info.metadata_urls.items():
                print(f"  {format_type}: {url}")
        
        # Usage tips
        if show_all_for_dimension:
            print(f"\nNote: Showing all values for dimension '{show_all_for_dimension}' as requested.")
        else:
            print(f"\nTip: Use show_all_for_dimension='dimension_name' to see all available values for a specific dimension.")
            print(f"     Example: client.describe_dataset('{dataset_code}', show_all_for_dimension='geo')")
        
        print("\nNote: Dimension information from metabase (comprehensive, fast, no labels).")
    
    def preload_metabase(self, show_progress: bool = True) -> Dict[str, Dict[str, List[str]]]:
        """
        Pre-load the metabase for optimal performance.
        
        This downloads and caches the complete Eurostat metabase, making all subsequent
        dataset exploration operations lightning fast.
        
        Args:
            show_progress: Whether to show progress messages
            
        Returns:
            The loaded metabase dictionary
            
        Example:
            >>> client = est.EurostatClient(cache_enabled=True)
            >>> metabase = client.preload_metabase()  # One-time cost
            >>> # Now all describe_dataset() calls are instant!
            >>> client.describe_dataset('nama_10_gdp')  # ⚡ Fast!
        """
        if show_progress:
            print("🚀 Pre-loading Eurostat metabase...")
        
        try:
            metabase = self.catalogue.get_metabase()
            
            if show_progress:
                print(f"✅ Metabase loaded successfully!")
                print(f"   📊 {len(metabase):,} datasets available")
                
            return metabase
            
        except Exception as e:
            if show_progress:
                print(f"❌ Failed to pre-load metabase: {e}")
            raise
    
    def is_metabase_loaded(self) -> bool:
        """
        Check if metabase is already loaded in memory.
        
        Returns:
            True if metabase is loaded, False otherwise
        """
        return self.catalogue._metabase_cache is not None
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        if self.cache:
            self.cache.clear()
        self._toc_cache = None
        # Clear metabase cache
        self.catalogue._metabase_cache = None
        print("Cache cleared successfully.")
    
    def browse_database(self, parent_code: Optional[str] = None, max_items: int = 20) -> None:
        """
        Browse the dataset hierarchy one level at a time.
        
        Args:
            parent_code: Parent folder code (None for root, which starts at 'data')
            max_items: Maximum number of items to display
        """
        toc = self.get_table_of_contents()
        
        # If no parent_code specified, start at 'data' folder
        if parent_code is None:
            parent_code = "data"
        
        # Show specific folder contents
        parent_dataset = next((d for d in toc.datasets if d.code == parent_code), None)
        if parent_dataset is None:
            print(f"Folder '{parent_code}' not found.")
            return
        
        parent_title = parent_dataset.title
        
        # Special display for data folder (root)
        if parent_code == "data":
            print(f"Eurostat Database - Main Themes:")
            print("=" * 50)
        else:
            print(f"📁 {parent_code}: {parent_title}")
            print("=" * 60)
        
        if parent_code not in toc.hierarchy:
            print("This folder has no subfolders or datasets.")
            return
        
        # Show direct children only
        children = toc.hierarchy[parent_code][:max_items]
        
        folders = []
        datasets = []
        
        for child_code in children:
            child_dataset = next((d for d in toc.datasets if d.code == child_code), None)
            if child_dataset:
                if child_dataset.type == "folder":
                    folders.append(child_dataset)
                else:
                    datasets.append(child_dataset)
        
        # Show folders first
        if folders:
            folder_icon = "📊" if parent_code == "data" else "📁"
            folder_label = "Themes" if parent_code == "data" else "Folders"
            print(f"{folder_icon} {folder_label}:")
            for folder in folders:
                title = folder.title
                child_count = len(toc.hierarchy.get(folder.code, []))
                print(f"  📁 {folder.code}: {title} ({child_count} items)")
        
        # Then show datasets/tables
        if datasets:
            print(f"\n📄 Datasets and Tables:")
            for dataset in datasets:
                title = dataset.title
                # Add some metadata if available
                metadata = []
                if dataset.last_update:
                    metadata.append(f"Updated: {dataset.last_update.strftime('%Y-%m-%d')}")
                if dataset.values_count:
                    metadata.append(f"{dataset.values_count:,} values")
                
                meta_str = f" ({', '.join(metadata)})" if metadata else ""
                print(f"  📄 {dataset.code}: {title}{meta_str}")
        
        total_shown = len(folders) + len(datasets)
        total_available = len(children)
        
        if total_available > max_items:
            print(f"\nShowing {total_shown} of {total_available} items. Use max_items parameter to see more.")
        else:
            print(f"\nShowing all {total_shown} items in this folder.")
        
        print(f"\nUse browse_database('folder_code') to explore subfolders or describe_dataset('dataset_code') for dataset details.")

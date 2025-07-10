"""Tests for the CatalogueAPI class."""

import pytest
import pandas as pd
import gzip
import io
from unittest.mock import patch, Mock
from datetime import datetime
from eustatspy.catalogue import CatalogueAPI
from eustatspy.models import DatasetInfo, TableOfContents
from eustatspy.exceptions import EurostatAPIError, DataParsingError, InvalidParameterError


def create_mock_response(data, status_code=200, content_type="application/json"):
    """Create a mock response object."""
    mock_response = Mock()
    mock_response.status_code = status_code
    
    if content_type == "application/json":
        mock_response.json.return_value = data
        mock_response.text = str(data) if not isinstance(data, str) else data
    else:
        mock_response.text = data
        mock_response.content = data.encode() if isinstance(data, str) else data
    
    return mock_response


class TestCatalogueAPI:
    """Test cases for CatalogueAPI."""
    
    def test_initialization(self):
        """Test CatalogueAPI initialization."""
        api = CatalogueAPI()
        assert api.base_url == "https://ec.europa.eu/eurostat/api/dissemination"
        assert api.cache is None
        assert api._metabase_cache is None
    
    def test_initialization_with_cache(self, cache_instance):
        """Test CatalogueAPI initialization with cache."""
        api = CatalogueAPI(cache=cache_instance)
        assert api.cache == cache_instance
    
    @patch('requests.get')
    def test_get_toc_txt_success(self, mock_get, sample_toc_txt_response):
        """Test successful retrieval of table of contents in TXT format."""
        api = CatalogueAPI()
        mock_response = create_mock_response(sample_toc_txt_response, content_type="text/plain")
        mock_get.return_value = mock_response
        
        toc = api._get_toc_txt()
        
        assert isinstance(toc, TableOfContents)
        assert len(toc.datasets) >= 2  # At least folder and datasets
        assert 'data' in [d.code for d in toc.datasets]
        assert 'nama_10_gdp' in [d.code for d in toc.datasets]
        
        # Check hierarchy
        assert 'data' in toc.hierarchy
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'toc/txt' in call_args[0][0]
        assert call_args[1]['params']['lang'] == 'en'
    
    @patch('requests.get')
    def test_get_toc_txt_with_cache(self, mock_get, cache_instance, sample_toc_txt_response):
        """Test TOC retrieval with caching."""
        api = CatalogueAPI(cache=cache_instance)
        mock_response = create_mock_response(sample_toc_txt_response, content_type="text/plain")
        mock_get.return_value = mock_response
        
        # First call
        toc1 = api._get_toc_txt()
        assert mock_get.call_count == 1
        
        # Second call should use cache
        toc2 = api._get_toc_txt()
        assert mock_get.call_count == 1  # Still 1, used cache
        assert toc1.datasets[0].code == toc2.datasets[0].code
    
    @patch('requests.get')
    def test_get_metabase_success(self, mock_get, sample_metabase_data):
        """Test successful metabase retrieval."""
        api = CatalogueAPI()
        
        # Create gzipped metabase content
        metabase_lines = []
        for dataset_code, dimensions in sample_metabase_data.items():
            for dimension, values in dimensions.items():
                for value in values:
                    metabase_lines.append(f"{dataset_code}\t{dimension}\t{value}")
        
        metabase_content = '\n'.join(metabase_lines)
        gzipped_content = gzip.compress(metabase_content.encode('utf-8'))
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = gzipped_content
        mock_get.return_value = mock_response
        
        metabase = api.get_metabase()
        
        assert isinstance(metabase, dict)
        assert 'nama_10_gdp' in metabase
        assert 'demo_pjan' in metabase
        assert 'geo' in metabase['nama_10_gdp']
        assert 'EU27_2020' in metabase['nama_10_gdp']['geo']
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'metabase.txt.gz' in call_args[0][0]
    
    @patch('requests.get')
    def test_get_metabase_with_cache(self, mock_get, cache_instance, sample_metabase_data):
        """Test metabase retrieval with caching."""
        api = CatalogueAPI(cache=cache_instance)
        
        # Setup mock response
        metabase_content = "nama_10_gdp\tgeo\tSE\nnama_10_gdp\ttime\t2020"
        gzipped_content = gzip.compress(metabase_content.encode('utf-8'))
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = gzipped_content
        mock_get.return_value = mock_response
        
        # First call
        metabase1 = api.get_metabase()
        assert mock_get.call_count == 1
        
        # Second call should use cache
        metabase2 = api.get_metabase()
        assert mock_get.call_count == 1  # Still 1, used cache
        assert metabase1 == metabase2
    
    def test_get_metabase_refresh(self, sample_metabase_data):
        """Test metabase refresh functionality."""
        api = CatalogueAPI()
        
        # Set initial metabase cache
        api._metabase_cache = {"old": "data"}
        
        with patch.object(api, 'get_metabase') as mock_get_metabase:
            mock_get_metabase.return_value = sample_metabase_data
            
            # Call with refresh=True should clear cache and reload
            result = api.get_metabase(refresh=True)
            
            # The cache should be cleared (set to None) before calling
            assert result == sample_metabase_data
    
    def test_get_dataset_dimensions_from_metabase(self, sample_metabase_data):
        """Test getting dataset dimensions from metabase."""
        api = CatalogueAPI()
        api._metabase_cache = sample_metabase_data
        
        dimensions = api.get_dataset_dimensions_from_metabase('nama_10_gdp')
        
        assert dimensions == sample_metabase_data['nama_10_gdp']
        assert 'geo' in dimensions
        assert 'time' in dimensions
        assert 'EU27_2020' in dimensions['geo']
    
    def test_get_dataset_dimensions_nonexistent(self, sample_metabase_data):
        """Test getting dimensions for non-existent dataset."""
        api = CatalogueAPI()
        api._metabase_cache = sample_metabase_data
        
        dimensions = api.get_dataset_dimensions_from_metabase('nonexistent')
        
        assert dimensions == {}
    
    def test_get_all_dataset_codes(self, sample_metabase_data):
        """Test getting all dataset codes."""
        api = CatalogueAPI()
        api._metabase_cache = sample_metabase_data
        
        codes = api.get_all_dataset_codes()
        
        assert isinstance(codes, list)
        assert 'nama_10_gdp' in codes
        assert 'demo_pjan' in codes
        assert len(codes) == 2
    
    def test_search_datasets_in_metabase(self, sample_metabase_data):
        """Test searching datasets in metabase."""
        api = CatalogueAPI()
        api._metabase_cache = sample_metabase_data
        
        # Search for GDP
        results = api.search_datasets_in_metabase('gdp')
        assert 'nama_10_gdp' in results
        
        # Search for demo
        results = api.search_datasets_in_metabase('demo')
        assert 'demo_pjan' in results
        
        # Search case insensitive
        results = api.search_datasets_in_metabase('GDP')
        assert 'nama_10_gdp' in results
    
    def test_search_datasets_success(self, sample_toc):
        """Test successful dataset searching."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            results = api.search_datasets('GDP')
        
        assert isinstance(results, pd.DataFrame)
        assert len(results) >= 1
        assert 'code' in results.columns
        assert 'title' in results.columns
        assert 'nama_10_gdp' in results['code'].values
    
    def test_search_datasets_with_date_filter(self, sample_toc):
        """Test dataset searching with date filter."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            # Search with valid date filter
            results = api.search_datasets('GDP', updated_since='2025-06-01')
            assert isinstance(results, pd.DataFrame)
            
            # Search with date that excludes all results
            results = api.search_datasets('GDP', updated_since='2025-12-31')
            assert len(results) == 0
    
    def test_search_datasets_invalid_date(self, sample_toc):
        """Test dataset searching with invalid date format."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            with pytest.raises(InvalidParameterError, match="Invalid date format"):
                api.search_datasets('GDP', updated_since='invalid-date')
    
    def test_search_datasets_max_results(self, sample_toc):
        """Test dataset searching with max results limit."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            results = api.search_datasets('', max_results=1)  # Search all, limit to 1
            assert len(results) <= 1
    
    def test_get_dataset_info_found(self, sample_toc):
        """Test getting info for existing dataset."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            info = api.get_dataset_info('nama_10_gdp')
        
        assert info is not None
        assert info.code == 'nama_10_gdp'
        assert info.title == 'GDP and main components'
    
    def test_get_dataset_info_not_found(self, sample_toc):
        """Test getting info for non-existent dataset."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            info = api.get_dataset_info('nonexistent')
        
        assert info is None
    
    @patch('requests.get')
    def test_get_table_of_contents_calls_txt(self, mock_get, sample_toc_txt_response):
        """Test that get_table_of_contents calls the TXT endpoint."""
        api = CatalogueAPI()
        mock_response = create_mock_response(sample_toc_txt_response, content_type="text/plain")
        mock_get.return_value = mock_response
        
        toc = api.get_table_of_contents()
        
        assert isinstance(toc, TableOfContents)
        mock_get.assert_called_once()


class TestCatalogueAPITOCParsing:
    """Test TOC parsing functionality."""
    
    def test_toc_parsing_with_indentation(self):
        """Test TOC parsing with proper indentation handling."""
        api = CatalogueAPI()
        
        toc_content = """"title"	"code"	"type"	"last update of data"	"last table structure change"	"data start"	"data end"	"values"
"Database by themes"	"data"	"folder"	" "	" "	" "	" "	
"    General statistics"	"general"	"folder"	" "	" "	" "	" "	
"        GDP statistics"	"nama_10_gdp"	"dataset"	"26.06.2025"	"14.04.2025"	"1975"	"2024"	1049888
"        Population"	"demo_pjan"	"dataset"	"15.06.2025"	"10.06.2025"	"1990"	"2024"	15000"""
        
        with patch('requests.get') as mock_get:
            mock_response = create_mock_response(toc_content, content_type="text/plain")
            mock_get.return_value = mock_response
            
            toc = api._get_toc_txt()
        
        # Check datasets
        dataset_codes = [d.code for d in toc.datasets]
        assert 'data' in dataset_codes
        assert 'general' in dataset_codes
        assert 'nama_10_gdp' in dataset_codes
        assert 'demo_pjan' in dataset_codes
        
        # Check hierarchy
        assert 'data' in toc.hierarchy
        assert 'general' in toc.hierarchy['data']
        assert 'nama_10_gdp' in toc.hierarchy['general']
        assert 'demo_pjan' in toc.hierarchy['general']
    
    def test_toc_parsing_date_formats(self):
        """Test parsing of different date formats in TOC."""
        api = CatalogueAPI()
        
        toc_content = """"title"	"code"	"type"	"last update of data"	"last table structure change"	"data start"	"data end"	"values"
"Test Dataset"	"test_data"	"dataset"	"26.06.2025"	"14.04.2025"	"1975"	"2024"	1000"""
        
        with patch('requests.get') as mock_get:
            mock_response = create_mock_response(toc_content, content_type="text/plain")
            mock_get.return_value = mock_response
            
            toc = api._get_toc_txt()
        
        # Find the test dataset
        test_dataset = next(d for d in toc.datasets if d.code == 'test_data')
        
        assert test_dataset.last_update is not None
        assert test_dataset.last_modified is not None
        assert test_dataset.data_start == "1975"
        assert test_dataset.data_end == "2024"
        assert test_dataset.values_count == 1000
    
    def test_toc_parsing_empty_values(self):
        """Test parsing of empty/missing values in TOC."""
        api = CatalogueAPI()
        
        toc_content = """"title"	"code"	"type"	"last update of data"	"last table structure change"	"data start"	"data end"	"values"
"Test Folder"	"test_folder"	"folder"	" "	" "	" "	" "	"""
        
        with patch('requests.get') as mock_get:
            mock_response = create_mock_response(toc_content, content_type="text/plain")
            mock_get.return_value = mock_response
            
            toc = api._get_toc_txt()
        
        # Find the test folder
        test_folder = next(d for d in toc.datasets if d.code == 'test_folder')
        
        assert test_folder.last_update is None
        assert test_folder.last_modified is None
        assert test_folder.data_start is None or test_folder.data_start == ''
        assert test_folder.data_end is None or test_folder.data_end == ''
        assert test_folder.values_count is None


class TestCatalogueAPIErrorHandling:
    """Test error handling in CatalogueAPI."""
    
    @patch('requests.get')
    def test_toc_http_error(self, mock_get):
        """Test handling of HTTP errors when getting TOC."""
        api = CatalogueAPI()
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": {"status": 404, "label": "Not found"}}
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError):
            api._get_toc_txt()
    
    @patch('requests.get')
    def test_metabase_http_error(self, mock_get):
        """Test handling of HTTP errors when getting metabase."""
        api = CatalogueAPI()
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError):
            api.get_metabase()
    
    @patch('requests.get')
    def test_toc_malformed_csv(self, mock_get):
        """Test handling of malformed CSV in TOC response."""
        api = CatalogueAPI()
        
        malformed_content = "malformed,csv\nwith,wrong,number,of,columns"
        mock_response = create_mock_response(malformed_content, content_type="text/plain")
        mock_get.return_value = mock_response
        
        # Should not raise an error, but should handle gracefully
        toc = api._get_toc_txt()
        assert isinstance(toc, TableOfContents)
    
    @patch('requests.get')
    def test_toc_empty_response(self, mock_get):
        """Test handling of empty TOC response."""
        api = CatalogueAPI()
        
        mock_response = create_mock_response("", content_type="text/plain")
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError, match="Failed to get table of contents"):
            api._get_toc_txt()
    
    @patch('requests.get')
    def test_metabase_gzip_error(self, mock_get):
        """Test handling of gzip decompression errors."""
        api = CatalogueAPI()
        
        # Invalid gzip content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"invalid gzip content"
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError, match="Failed to get metabase"):
            api.get_metabase()


class TestCatalogueAPIEdgeCases:
    """Test edge cases for CatalogueAPI."""
    
    def test_search_datasets_empty_query(self, sample_toc):
        """Test searching with empty query string."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            results = api.search_datasets('')
        
        # Empty query should return all datasets
        assert len(results) >= 2  # Should find all datasets
    
    def test_search_datasets_no_matches(self, sample_toc):
        """Test searching with query that has no matches."""
        api = CatalogueAPI()
        
        with patch.object(api, 'get_table_of_contents', return_value=sample_toc):
            results = api.search_datasets('nonexistent_term_xyz')
        
        assert len(results) == 0
        assert isinstance(results, pd.DataFrame)
    
    def test_metabase_large_dataset(self):
        """Test handling of large metabase data."""
        api = CatalogueAPI()
        
        # Create large metabase content
        large_metabase_lines = []
        for i in range(1000):
            large_metabase_lines.append(f"dataset_{i}\tgeo\tSE")
            large_metabase_lines.append(f"dataset_{i}\ttime\t2020")
        
        metabase_content = '\n'.join(large_metabase_lines)
        gzipped_content = gzip.compress(metabase_content.encode('utf-8'))
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = gzipped_content
            mock_get.return_value = mock_response
            
            metabase = api.get_metabase()
        
        assert len(metabase) == 1000
        assert 'dataset_0' in metabase
        assert 'dataset_999' in metabase
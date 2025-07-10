"""Tests for the main EurostatClient class."""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
import eustatspy as est
from eustatspy.exceptions import EurostatAPIError, DatasetNotFoundError


class TestEurostatClient:
    """Test cases for EurostatClient."""
    
    def test_client_initialization_default(self):
        """Test client initialization with default parameters."""
        client = est.EurostatClient()
        
        assert client.base_url == "https://ec.europa.eu/eurostat/api/dissemination"
        assert client.cache is None
        assert client.catalogue is not None
        assert client.statistics is not None
        assert client._toc_cache is None
    
    def test_client_initialization_with_cache(self, temp_cache_dir):
        """Test client initialization with caching enabled."""
        client = est.EurostatClient(
            cache_enabled=True,
            cache_dir=temp_cache_dir,
            cache_expire_hours=12
        )
        
        assert client.cache is not None
        assert str(client.cache.cache_dir) == temp_cache_dir
        assert client.cache.expire_hours == 12
    
    def test_client_initialization_custom_url(self):
        """Test client initialization with custom base URL."""
        custom_url = "https://custom.eurostat.api"
        client = est.EurostatClient(base_url=custom_url)
        
        assert client.base_url == custom_url
        assert client.catalogue.base_url == custom_url
        assert client.statistics.base_url == custom_url
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_table_of_contents')
    def test_get_table_of_contents(self, mock_get_toc, client_no_cache, sample_toc):
        """Test getting table of contents."""
        mock_get_toc.return_value = sample_toc
        
        # First call
        toc = client_no_cache.get_table_of_contents()
        assert toc == sample_toc
        assert mock_get_toc.call_count == 1
        
        # Second call should use cache
        toc2 = client_no_cache.get_table_of_contents()
        assert toc2 == sample_toc
        assert mock_get_toc.call_count == 1  # Still 1, used cache
        
        # Force refresh
        toc3 = client_no_cache.get_table_of_contents(refresh=True)
        assert toc3 == sample_toc
        assert mock_get_toc.call_count == 2  # Called again
    
    @patch('eustatspy.catalogue.CatalogueAPI.search_datasets')
    def test_search_datasets(self, mock_search, client_no_cache):
        """Test dataset searching."""
        # Create mock search results
        mock_df = pd.DataFrame({
            'code': ['nama_10_gdp', 'demo_pjan'],
            'title': ['GDP data', 'Population data'],
            'type': ['dataset', 'dataset']
        })
        mock_search.return_value = mock_df
        
        # Test basic search
        results = client_no_cache.search_datasets("GDP")
        assert len(results) == 2
        assert 'nama_10_gdp' in results['code'].values
        mock_search.assert_called_once_with("GDP", 50, None)
        
        # Test search with parameters
        client_no_cache.search_datasets("population", max_results=10, updated_since="2025-01-01")
        mock_search.assert_called_with("population", 10, "2025-01-01")
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_dataset_info')
    def test_get_dataset_info(self, mock_get_info, client_no_cache, sample_dataset_info):
        """Test getting dataset information."""
        mock_get_info.return_value = sample_dataset_info
        
        info = client_no_cache.get_dataset_info("nama_10_gdp")
        assert info == sample_dataset_info
        mock_get_info.assert_called_once_with("nama_10_gdp")
        
        # Test non-existent dataset
        mock_get_info.return_value = None
        info = client_no_cache.get_dataset_info("nonexistent")
        assert info is None
    
    @patch('eustatspy.statistics.StatisticsAPI.get_data_as_dataframe')
    def test_get_data_as_dataframe(self, mock_get_data, client_no_cache):
        """Test getting data as DataFrame."""
        # Create mock DataFrame
        mock_df = pd.DataFrame({
            'geo': ['SE', 'NO'],
            'time': ['2020', '2020'],
            'value': [1000.5, 1100.2]
        })
        mock_get_data.return_value = mock_df
        
        # Test basic call
        df = client_no_cache.get_data_as_dataframe('nama_10_gdp', geo='SE')
        assert len(df) == 2
        assert 'value' in df.columns
        mock_get_data.assert_called_once_with('nama_10_gdp', geo='SE')
        
        # Test with multiple filters
        client_no_cache.get_data_as_dataframe(
            'nama_10_gdp',
            geo=['SE', 'NO'],
            time='2020',
            unit='CP_MEUR'
        )
        mock_get_data.assert_called_with(
            'nama_10_gdp',
            geo=['SE', 'NO'],
            time='2020',
            unit='CP_MEUR'
        )
    
    @patch('eustatspy.statistics.StatisticsAPI.get_data')
    def test_get_raw_data(self, mock_get_data, client_no_cache, sample_jsonstat_response):
        """Test getting raw JSON-stat data."""
        mock_get_data.return_value = sample_jsonstat_response
        
        data = client_no_cache.get_raw_data('nama_10_gdp', geo='SE')
        assert data == sample_jsonstat_response
        mock_get_data.assert_called_once_with('nama_10_gdp', geo='SE')
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_dataset_dimensions_from_metabase')
    def test_get_available_filters(self, mock_get_dimensions, client_no_cache, sample_metabase_data):
        """Test getting available filters."""
        mock_get_dimensions.return_value = sample_metabase_data['nama_10_gdp']
        
        filters = client_no_cache.get_available_filters('nama_10_gdp')
        assert 'geo' in filters
        assert 'time' in filters
        assert 'SE' in filters['geo']
        mock_get_dimensions.assert_called_once_with('nama_10_gdp')
    
    @patch('eustatspy.statistics.StatisticsAPI.get_geo_categorical')
    def test_get_geo_data(self, mock_get_geo, client_no_cache, sample_geo_response):
        """Test getting geographic data."""
        mock_get_geo.return_value = sample_geo_response
        
        geo_data = client_no_cache.get_geo_data('country')
        assert geo_data == sample_geo_response
        assert 'SE' in geo_data
        assert geo_data['SE'] == 'Sweden'
        mock_get_geo.assert_called_once_with('country')
    
    @patch('eustatspy.statistics.StatisticsAPI.get_country_label')
    def test_get_country_name(self, mock_get_label, client_no_cache):
        """Test getting country name."""
        mock_get_label.return_value = "Sweden"
        
        name = client_no_cache.get_country_name('SE')
        assert name == "Sweden"
        mock_get_label.assert_called_once_with('SE')
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_metabase')
    def test_preload_metabase(self, mock_get_metabase, client_no_cache, sample_metabase_data):
        """Test preloading metabase."""
        mock_get_metabase.return_value = sample_metabase_data
        
        # Test with progress
        metabase = client_no_cache.preload_metabase(show_progress=True)
        assert metabase == sample_metabase_data
        mock_get_metabase.assert_called_once()
        
        # Test without progress  
        client_no_cache.preload_metabase(show_progress=False)
        assert mock_get_metabase.call_count == 2
    
    def test_is_metabase_loaded(self, client_no_cache):
        """Test checking if metabase is loaded."""
        # Initially not loaded
        assert not client_no_cache.is_metabase_loaded()
        
        # Set metabase cache manually
        client_no_cache.catalogue._metabase_cache = {"test": {}}
        assert client_no_cache.is_metabase_loaded()
    
    @patch('eustatspy.utils.Cache.clear')
    def test_clear_cache(self, mock_cache_clear, client_with_cache):
        """Test clearing cache."""
        # Set some cached data
        client_with_cache._toc_cache = Mock()
        client_with_cache.catalogue._metabase_cache = Mock()
        
        client_with_cache.clear_cache()
        
        mock_cache_clear.assert_called_once()
        assert client_with_cache._toc_cache is None
        assert client_with_cache.catalogue._metabase_cache is None
    
    def test_clear_cache_no_cache(self, client_no_cache):
        """Test clearing cache when no cache is enabled."""
        # Should not raise an error
        client_no_cache.clear_cache()
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_table_of_contents')
    @patch('eustatspy.catalogue.CatalogueAPI.get_dataset_info')
    @patch('eustatspy.catalogue.CatalogueAPI.get_dataset_dimensions_from_metabase')
    def test_describe_dataset(self, mock_get_dimensions, mock_get_info, mock_get_toc, 
                            client_no_cache, sample_dataset_info, sample_metabase_data, 
                            capsys):
        """Test describing a dataset."""
        mock_get_info.return_value = sample_dataset_info
        mock_get_dimensions.return_value = sample_metabase_data['nama_10_gdp']
        
        client_no_cache.describe_dataset('nama_10_gdp')
        
        captured = capsys.readouterr()
        assert "Dataset: nama_10_gdp" in captured.out
        assert "Title: Gross domestic product (GDP) and main components" in captured.out
        assert "geo:" in captured.out
        assert "time:" in captured.out
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_table_of_contents')
    def test_browse_database_root(self, mock_get_toc, client_no_cache, sample_toc, capsys):
        """Test browsing database at root level."""
        mock_get_toc.return_value = sample_toc
        
        client_no_cache.browse_database()
        
        captured = capsys.readouterr()
        assert "Eurostat Database - Main Themes:" in captured.out
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_table_of_contents')
    def test_browse_database_specific_folder(self, mock_get_toc, client_no_cache, sample_toc, capsys):
        """Test browsing specific folder in database."""
        mock_get_toc.return_value = sample_toc
        
        client_no_cache.browse_database("data")
        
        captured = capsys.readouterr()
        # The browse function shows "Eurostat Database - Main Themes:" for the data folder
        assert "Eurostat Database - Main Themes:" in captured.out


class TestClientErrorHandling:
    """Test error handling in EurostatClient."""
    
    @patch('eustatspy.statistics.StatisticsAPI.get_data_as_dataframe')
    def test_data_retrieval_error(self, mock_get_data, client_no_cache):
        """Test handling of data retrieval errors."""
        mock_get_data.side_effect = EurostatAPIError("API Error")
        
        with pytest.raises(EurostatAPIError):
            client_no_cache.get_data_as_dataframe('invalid_dataset')
    
    @patch('eustatspy.catalogue.CatalogueAPI.get_metabase')
    def test_preload_metabase_error(self, mock_get_metabase, client_no_cache):
        """Test handling of metabase loading errors."""
        mock_get_metabase.side_effect = EurostatAPIError("Download failed")
        
        with pytest.raises(EurostatAPIError):
            client_no_cache.preload_metabase()


class TestClientWithRealishData:
    """Test client with more realistic data scenarios."""
    
    @patch('eustatspy.statistics.StatisticsAPI.get_data_as_dataframe')
    def test_multiple_filters(self, mock_get_data, client_no_cache):
        """Test data retrieval with multiple complex filters."""
        # Create realistic DataFrame
        df_data = []
        for geo in ['SE', 'NO', 'DK']:
            for time in ['2020', '2021', '2022']:
                for unit in ['CP_MEUR', 'CLV20_MEUR']:
                    df_data.append({
                        'geo': geo,
                        'geo_label': {'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark'}[geo],
                        'time': time,
                        'unit': unit,
                        'value': 1000 + len(df_data)
                    })
        
        mock_df = pd.DataFrame(df_data)
        mock_get_data.return_value = mock_df
        
        df = client_no_cache.get_data_as_dataframe(
            'nama_10_gdp',
            geo=['SE', 'NO', 'DK'],
            time=['2020', '2021', '2022'],
            unit=['CP_MEUR', 'CLV20_MEUR'],
            na_item='B1GQ'
        )
        
        assert len(df) == 18  # 3 countries × 3 years × 2 units
        assert 'geo_label' in df.columns
        assert set(df['geo'].unique()) == {'SE', 'NO', 'DK'}
        
        mock_get_data.assert_called_once_with(
            'nama_10_gdp',
            geo=['SE', 'NO', 'DK'],
            time=['2020', '2021', '2022'],
            unit=['CP_MEUR', 'CLV20_MEUR'],
            na_item='B1GQ'
        )
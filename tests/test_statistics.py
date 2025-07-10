"""Tests for the StatisticsAPI class."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
import requests
from eustatspy.statistics import StatisticsAPI
from eustatspy.exceptions import EurostatAPIError, InvalidParameterError, DataParsingError


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


class TestStatisticsAPI:
    """Test cases for StatisticsAPI."""
    
    def test_initialization(self):
        """Test StatisticsAPI initialization."""
        api = StatisticsAPI()
        assert api.base_url == "https://ec.europa.eu/eurostat/api/dissemination"
        assert api.cache is None
        assert api.catalogue is None
    
    def test_initialization_with_cache(self, cache_instance):
        """Test StatisticsAPI initialization with cache."""
        api = StatisticsAPI(cache=cache_instance)
        assert api.cache == cache_instance
    
    def test_set_catalogue_reference(self):
        """Test setting catalogue reference."""
        api = StatisticsAPI()
        mock_catalogue = Mock()
        
        api.set_catalogue_reference(mock_catalogue)
        assert api.catalogue == mock_catalogue
    
    @patch('requests.get')
    def test_get_data_success(self, mock_get, sample_jsonstat_response):
        """Test successful data retrieval."""
        api = StatisticsAPI()
        mock_response = create_mock_response(sample_jsonstat_response)
        mock_get.return_value = mock_response
        
        data = api.get_data('nama_10_gdp', geo='SE', time='2020')
        
        assert data == sample_jsonstat_response
        mock_get.assert_called_once()
        
        # Check URL construction
        call_args = mock_get.call_args
        assert 'nama_10_gdp' in call_args[0][0]
        
        # Check parameters (as list of tuples)
        params = call_args[1]['params']
        assert ('format', 'JSON') in params
        assert ('lang', 'EN') in params
        assert ('geo', 'SE') in params
        assert ('time', '2020') in params
    
    @patch('requests.get')
    def test_get_data_with_cache(self, mock_get, cache_instance, sample_jsonstat_response):
        """Test data retrieval with caching."""
        api = StatisticsAPI(cache=cache_instance)
        mock_response = create_mock_response(sample_jsonstat_response)
        mock_get.return_value = mock_response
        
        # First call
        data1 = api.get_data('nama_10_gdp', geo='SE')
        assert mock_get.call_count == 1
        
        # Second call should use cache
        data2 = api.get_data('nama_10_gdp', geo='SE')
        assert mock_get.call_count == 1  # Still 1, used cache
        assert data1 == data2
    
    @patch('requests.get')
    def test_get_data_asynchronous_response(self, mock_get):
        """Test handling of asynchronous response."""
        api = StatisticsAPI()
        async_response = {
            "warning": {
                "status": 413,
                "label": "ASYNCHRONOUS_RESPONSE. Your request will be treated asynchronously."
            }
        }
        mock_response = create_mock_response(async_response)
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError, match="asynchronously"):
            api.get_data('nama_10_gdp')
    
    @patch('requests.get')
    def test_get_data_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        api = StatisticsAPI()
        
        # Test 404 error
        error_response = {
            "error": {
                "status": 404,
                "label": "Dataset not found"
            }
        }
        mock_response = create_mock_response(error_response, status_code=404)
        mock_get.return_value = mock_response
        
        with pytest.raises(EurostatAPIError):
            api.get_data('invalid_dataset')
    
    def test_get_data_as_dataframe(self, sample_jsonstat_response):
        """Test converting JSON-stat to DataFrame."""
        api = StatisticsAPI()
        
        with patch.object(api, 'get_data', return_value=sample_jsonstat_response):
            df = api.get_data_as_dataframe('nama_10_gdp', geo='SE')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4  # 2 geo × 2 time = 4 rows
        assert 'value' in df.columns
        assert 'geo' in df.columns
        assert 'time' in df.columns
        assert 'geo_label' in df.columns
        assert 'time_label' in df.columns
        
        # Check values
        assert 1000.5 in df['value'].values
        assert 'Sweden' in df['geo_label'].values
        assert '2020' in df['time'].values
    
    def test_build_params_basic(self):
        """Test building basic parameters."""
        api = StatisticsAPI()
        
        params = api._build_params(geo='SE', time='2020')
        
        # Convert to dict for easier testing
        params_dict = dict(params)
        assert params_dict['format'] == 'JSON'
        assert params_dict['lang'] == 'EN'
        assert params_dict['geo'] == 'SE'
        assert params_dict['time'] == '2020'
    
    def test_build_params_multiple_values(self):
        """Test building parameters with multiple values."""
        api = StatisticsAPI()
        
        params = api._build_params(geo=['SE', 'NO'], time=['2020', '2021'])
        
        # Check that we have multiple geo and time entries
        geo_values = [v for k, v in params if k == 'geo']
        time_values = [v for k, v in params if k == 'time']
        
        assert 'SE' in geo_values
        assert 'NO' in geo_values
        assert '2020' in time_values
        assert '2021' in time_values
    
    def test_build_params_geo_level(self):
        """Test building parameters with geoLevel."""
        api = StatisticsAPI()
        
        params = api._build_params(geoLevel='country')
        
        params_dict = dict(params)
        assert params_dict['geoLevel'] == 'country'
    
    def test_build_params_time_parameters(self):
        """Test building time parameters."""
        api = StatisticsAPI()
        
        # Test lastTimePeriod
        params = api._build_params(lastTimePeriod=5)
        params_dict = dict(params)
        assert params_dict['lastTimePeriod'] == '5'
        
        # Test sinceTimePeriod and untilTimePeriod together
        params = api._build_params(sinceTimePeriod='2015', untilTimePeriod='2020')
        params_dict = dict(params)
        assert params_dict['sinceTimePeriod'] == '2015'
        assert params_dict['untilTimePeriod'] == '2020'
    
    def test_build_params_invalid_time_combination(self):
        """Test invalid time parameter combinations."""
        api = StatisticsAPI()
        
        with pytest.raises(InvalidParameterError):
            api._build_params(time='2020', lastTimePeriod=5)
        
        with pytest.raises(InvalidParameterError):
            api._build_params(time='2020', sinceTimePeriod='2015')
    
    def test_build_params_invalid_geo_level(self):
        """Test invalid geoLevel parameter."""
        api = StatisticsAPI()
        
        with pytest.raises(InvalidParameterError):
            api._build_params(geoLevel='invalid_level')
    
    def test_jsonstat_to_dataframe_simple(self):
        """Test JSON-stat to DataFrame conversion with simple data."""
        api = StatisticsAPI()
        
        simple_jsonstat = {
            "value": {"0": 100, "1": 200},
            "id": ["geo"],
            "size": [2],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"SE": 0, "NO": 1},
                        "label": {"SE": "Sweden", "NO": "Norway"}
                    }
                }
            }
        }
        
        df = api._jsonstat_to_dataframe(simple_jsonstat)
        
        assert len(df) == 2
        assert 'geo' in df.columns
        assert 'value' in df.columns
        assert 'geo_label' in df.columns
        assert df.loc[0, 'geo'] == 'SE'
        assert df.loc[0, 'value'] == 100
        assert df.loc[0, 'geo_label'] == 'Sweden'
    
    def test_jsonstat_to_dataframe_with_status(self):
        """Test JSON-stat conversion including status information."""
        api = StatisticsAPI()
        
        jsonstat_with_status = {
            "value": {"0": 100, "1": 200},
            "status": {"0": "", "1": "p"},
            "id": ["geo"],
            "size": [2],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"SE": 0, "NO": 1},
                        "label": {"SE": "Sweden", "NO": "Norway"}
                    }
                }
            }
        }
        
        df = api._jsonstat_to_dataframe(jsonstat_with_status)
        
        assert 'status' in df.columns
        assert df.loc[0, 'status'] == ''
        assert df.loc[1, 'status'] == 'p'
    
    def test_jsonstat_to_dataframe_missing_values(self):
        """Test JSON-stat conversion with missing values."""
        api = StatisticsAPI()
        
        jsonstat_missing = {
            "value": {"0": 100, "2": 200},  # Missing index 1
            "id": ["geo"],
            "size": [3],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"SE": 0, "NO": 1, "DK": 2},
                        "label": {"SE": "Sweden", "NO": "Norway", "DK": "Denmark"}
                    }
                }
            }
        }
        
        df = api._jsonstat_to_dataframe(jsonstat_missing)
        
        assert len(df) == 3
        assert pd.isna(df.loc[1, 'value'])  # Missing value should be NaN
        assert df.loc[0, 'value'] == 100
        assert df.loc[2, 'value'] == 200
    
    def test_jsonstat_to_dataframe_error_handling(self):
        """Test error handling in JSON-stat conversion."""
        api = StatisticsAPI()
        
        # Test with invalid data
        invalid_jsonstat = {"invalid": "data"}
        
        with pytest.raises(DataParsingError):
            api._jsonstat_to_dataframe(invalid_jsonstat)
    
    @patch('requests.get')
    def test_get_geo_categorical(self, mock_get, sample_geo_response):
        """Test getting geographical categorical data."""
        api = StatisticsAPI()
        mock_response = create_mock_response(sample_geo_response)
        mock_get.return_value = mock_response
        
        geo_data = api.get_geo_categorical('country')
        
        assert geo_data == sample_geo_response
        mock_get.assert_called_once()
        
        # Check URL construction
        call_args = mock_get.call_args
        assert 'geo_categorical' in call_args[0][0]
        assert 'country' in call_args[0][0]
    
    @patch('requests.get')
    def test_get_country_label(self, mock_get):
        """Test getting country label."""
        api = StatisticsAPI()
        label_response = {"label": "Sweden"}
        mock_response = create_mock_response(label_response)
        mock_get.return_value = mock_response
        
        label = api.get_country_label('SE')
        
        assert label == "Sweden"
        mock_get.assert_called_once()
        
        # Check URL construction
        call_args = mock_get.call_args
        assert 'country_label' in call_args[0][0]
        assert 'SE' in call_args[0][0]
    
    def test_get_available_filters_with_catalogue(self, sample_metabase_data):
        """Test getting available filters when catalogue is set."""
        api = StatisticsAPI()
        mock_catalogue = Mock()
        mock_catalogue.get_dataset_dimensions_from_metabase.return_value = sample_metabase_data['nama_10_gdp']
        
        api.set_catalogue_reference(mock_catalogue)
        
        filters = api.get_available_filters('nama_10_gdp')
        
        assert filters == sample_metabase_data['nama_10_gdp']
        mock_catalogue.get_dataset_dimensions_from_metabase.assert_called_once_with('nama_10_gdp')
    
    def test_get_available_filters_no_catalogue(self):
        """Test getting available filters when no catalogue is set."""
        api = StatisticsAPI()
        
        filters = api.get_available_filters('nama_10_gdp')
        
        # Should return None when no catalogue is available
        assert filters is None
    
    def test_create_cache_key(self):
        """Test cache key creation."""
        api = StatisticsAPI()
        
        params = [('geo', 'SE'), ('time', '2020'), ('format', 'JSON')]
        key = api._create_cache_key('http://test.com', params)
        
        assert 'http://test.com' in key
        assert 'geo=SE' in key
        assert 'time=2020' in key
        assert 'format=JSON' in key
    
    def test_create_cache_key_consistency(self):
        """Test that cache key creation is consistent regardless of parameter order."""
        api = StatisticsAPI()
        
        params1 = [('geo', 'SE'), ('time', '2020')]
        params2 = [('time', '2020'), ('geo', 'SE')]
        
        key1 = api._create_cache_key('http://test.com', params1)
        key2 = api._create_cache_key('http://test.com', params2)
        
        assert key1 == key2


class TestStatisticsAPIEdgeCases:
    """Test edge cases and error scenarios for StatisticsAPI."""
    
    def test_large_multidimensional_data(self):
        """Test conversion of large multidimensional JSON-stat data."""
        api = StatisticsAPI()
        
        # Create a 3D dataset: geo (3) × time (3) × unit (2) = 18 values
        jsonstat_3d = {
            "value": {str(i): float(i * 100) for i in range(18)},
            "id": ["geo", "time", "unit"],
            "size": [3, 3, 2],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"SE": 0, "NO": 1, "DK": 2},
                        "label": {"SE": "Sweden", "NO": "Norway", "DK": "Denmark"}
                    }
                },
                "time": {
                    "category": {
                        "index": {"2020": 0, "2021": 1, "2022": 2},
                        "label": {"2020": "2020", "2021": "2021", "2022": "2022"}
                    }
                },
                "unit": {
                    "category": {
                        "index": {"EUR": 0, "USD": 1},
                        "label": {"EUR": "Euro", "USD": "US Dollar"}
                    }
                }
            }
        }
        
        df = api._jsonstat_to_dataframe(jsonstat_3d)
        
        assert len(df) == 18
        assert set(df.columns) >= {'geo', 'time', 'unit', 'value', 'geo_label', 'time_label', 'unit_label'}
        assert set(df['geo'].unique()) == {'SE', 'NO', 'DK'}
        assert set(df['time'].unique()) == {'2020', '2021', '2022'}
        assert set(df['unit'].unique()) == {'EUR', 'USD'}
    
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors."""
        api = StatisticsAPI()
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with pytest.raises(EurostatAPIError, match="Failed to get data"):
            api.get_data('nama_10_gdp')
    
    @patch('requests.get')
    def test_json_decode_error(self, mock_get):
        """Test handling of JSON decode errors."""
        api = StatisticsAPI()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        with pytest.raises(DataParsingError, match="Failed to parse JSON"):
            api.get_data('nama_10_gdp')
    
    def test_empty_dimension_data(self):
        """Test handling of empty dimension data."""
        api = StatisticsAPI()
        
        jsonstat_empty = {
            "value": {},
            "id": [],
            "size": [],
            "dimension": {}
        }
        
        with pytest.raises(DataParsingError):
            api._jsonstat_to_dataframe(jsonstat_empty)
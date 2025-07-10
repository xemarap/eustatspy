"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch
import tempfile
import shutil

# Import the package modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import eustatspy as est
from eustatspy.models import DatasetInfo, TableOfContents
from eustatspy.utils import Cache


@pytest.fixture
def sample_dataset_info():
    """Sample DatasetInfo object for testing."""
    return DatasetInfo(
        code="nama_10_gdp",
        title="Gross domestic product (GDP) and main components",
        type="dataset",
        last_update=datetime(2025, 6, 26),
        last_modified=datetime(2025, 4, 14),
        data_start="1975",
        data_end="2024",
        values_count=1049888,
        short_description="GDP statistics for EU countries",
        unit="Million EUR",
        source="Eurostat"
    )


@pytest.fixture
def sample_toc():
    """Sample TableOfContents for testing."""
    datasets = [
        DatasetInfo(
            code="data",
            title="Database by themes",
            type="folder"
        ),
        DatasetInfo(
            code="nama_10_gdp",
            title="GDP and main components",
            type="dataset",
            last_update=datetime(2025, 6, 26),
            values_count=1049888
        ),
        DatasetInfo(
            code="demo_pjan",
            title="Population on 1 January",
            type="dataset",
            last_update=datetime(2025, 6, 15),
            values_count=15000
        )
    ]
    
    hierarchy = {
        "data": ["nama_10_gdp", "demo_pjan"]
    }
    
    return TableOfContents(
        datasets=datasets,
        hierarchy=hierarchy,
        creation_date=datetime.now()
    )


@pytest.fixture
def sample_jsonstat_response():
    """Sample JSON-stat response for testing."""
    return {
        "version": "2.0",
        "class": "dataset",
        "label": "GDP Test Data",
        "source": "ESTAT",
        "updated": "2025-06-26T23:00:00+0200",
        "value": {
            "0": 1000.5,
            "1": 1100.2,
            "2": 1200.8,
            "3": 1050.1
        },
        "status": {
            "0": "",
            "1": "p",
            "2": "",
            "3": "e"
        },
        "id": ["geo", "time"],
        "size": [2, 2],
        "dimension": {
            "geo": {
                "label": "Geography",
                "category": {
                    "index": {
                        "SE": 0,
                        "NO": 1
                    },
                    "label": {
                        "SE": "Sweden",
                        "NO": "Norway"
                    }
                }
            },
            "time": {
                "label": "Time",
                "category": {
                    "index": {
                        "2020": 0,
                        "2021": 1
                    },
                    "label": {
                        "2020": "2020",
                        "2021": "2021"
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_metabase_data():
    """Sample metabase data for testing."""
    return {
        "nama_10_gdp": {
            "geo": ["EU27_2020", "SE", "NO", "DK", "FI"],
            "time": ["2020", "2021", "2022", "2023", "2024"],
            "unit": ["CP_MEUR", "CLV20_MEUR"],
            "na_item": ["B1GQ", "P3", "P5G"]
        },
        "demo_pjan": {
            "geo": ["EU27_2020", "SE", "NO"],
            "time": ["2020", "2021", "2022"],
            "sex": ["T", "M", "F"],
            "age": ["TOTAL", "Y_LT5", "Y5-9"]
        }
    }


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for testing."""
    with patch('requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def mock_successful_response():
    """Mock successful HTTP response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    mock_response.text = "test response text"
    return mock_response


@pytest.fixture
def temp_cache_dir():
    """Temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_instance(temp_cache_dir):
    """Cache instance for testing."""
    return Cache(temp_cache_dir, expire_hours=1)


@pytest.fixture
def client_no_cache():
    """EurostatClient without caching."""
    return est.EurostatClient(cache_enabled=False)


@pytest.fixture
def client_with_cache(temp_cache_dir):
    """EurostatClient with caching enabled."""
    return est.EurostatClient(
        cache_enabled=True,
        cache_dir=temp_cache_dir,
        cache_expire_hours=1
    )


@pytest.fixture
def sample_toc_txt_response():
    """Sample TOC TXT response for testing."""
    return """"title"	"code"	"type"	"last update of data"	"last table structure change"	"data start"	"data end"	"values"
"Database by themes"	"data"	"folder"	" "	" "	" "	" "	
"    Gross domestic product"	"nama_10_gdp"	"dataset"	"26.06.2025"	"14.04.2025"	"1975"	"2024"	1049888
"    Population statistics"	"demo_pjan"	"dataset"	"15.06.2025"	"10.06.2025"	"1990"	"2024"	15000"""


@pytest.fixture 
def sample_geo_response():
    """Sample geographic data response."""
    return {
        "SE": "Sweden",
        "NO": "Norway", 
        "DK": "Denmark",
        "FI": "Finland"
    }
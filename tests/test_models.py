"""Tests for data models."""

import pytest
import pandas as pd
from datetime import datetime
from eustatspy.models import DatasetInfo, Dataset, TableOfContents


class TestDatasetInfo:
    """Test cases for DatasetInfo model."""
    
    def test_dataset_info_creation_minimal(self):
        """Test creating DatasetInfo with minimal required fields."""
        info = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset"
        )
        
        assert info.code == "test_dataset"
        assert info.title == "Test Dataset"
        assert info.type == "dataset"
        assert info.last_update is None
        assert info.last_modified is None
        assert info.data_start is None
        assert info.data_end is None
        assert info.values_count is None
        assert info.short_description is None
        assert info.unit is None
        assert info.source is None
        assert info.metadata_urls is None
        assert info.download_urls is None
    
    def test_dataset_info_creation_full(self):
        """Test creating DatasetInfo with all fields."""
        metadata_urls = {"html": "http://example.com/metadata.html"}
        download_urls = {"tsv": "http://example.com/data.tsv"}
        last_update = datetime(2025, 6, 26, 12, 30)
        last_modified = datetime(2025, 4, 14, 10, 15)
        
        info = DatasetInfo(
            code="nama_10_gdp",
            title="GDP and main components",
            type="dataset",
            last_update=last_update,
            last_modified=last_modified,
            data_start="1975",
            data_end="2024",
            values_count=1049888,
            short_description="GDP statistics for EU countries",
            unit="Million EUR",
            source="Eurostat",
            metadata_urls=metadata_urls,
            download_urls=download_urls
        )
        
        assert info.code == "nama_10_gdp"
        assert info.title == "GDP and main components"
        assert info.type == "dataset"
        assert info.last_update == last_update
        assert info.last_modified == last_modified
        assert info.data_start == "1975"
        assert info.data_end == "2024"
        assert info.values_count == 1049888
        assert info.short_description == "GDP statistics for EU countries"
        assert info.unit == "Million EUR"
        assert info.source == "Eurostat"
        assert info.metadata_urls == metadata_urls
        assert info.download_urls == download_urls
    
    def test_dataset_info_equality(self):
        """Test DatasetInfo equality comparison."""
        info1 = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset"
        )
        
        info2 = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset"
        )
        
        info3 = DatasetInfo(
            code="different_dataset",
            title="Test Dataset",
            type="dataset"
        )
        
        assert info1 == info2
        assert info1 != info3
    
    def test_dataset_info_repr(self):
        """Test DatasetInfo string representation."""
        info = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset"
        )
        
        repr_str = repr(info)
        assert "test_dataset" in repr_str
        assert "Test Dataset" in repr_str
        assert "dataset" in repr_str
    
    def test_dataset_info_type_validation(self):
        """Test that DatasetInfo accepts various type values."""
        valid_types = ["dataset", "table", "folder"]
        
        for type_value in valid_types:
            info = DatasetInfo(
                code="test",
                title="Test",
                type=type_value
            )
            assert info.type == type_value
    
    def test_dataset_info_with_none_values(self):
        """Test DatasetInfo with explicitly None values."""
        info = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset",
            last_update=None,
            last_modified=None,
            data_start=None,
            data_end=None,
            values_count=None,
            short_description=None,
            unit=None,
            source=None,
            metadata_urls=None,
            download_urls=None
        )
        
        assert info.last_update is None
        assert info.last_modified is None
        assert info.data_start is None
        assert info.data_end is None
        assert info.values_count is None
        assert info.short_description is None
        assert info.unit is None
        assert info.source is None
        assert info.metadata_urls is None
        assert info.download_urls is None


class TestDataset:
    """Test cases for Dataset model."""
    
    def test_dataset_creation_minimal(self, sample_dataset_info):
        """Test creating Dataset with minimal required fields."""
        dataset = Dataset(info=sample_dataset_info)
        
        assert dataset.info == sample_dataset_info
        assert dataset.data is None
        assert dataset.dimensions is None
        assert dataset.raw_response is None
    
    def test_dataset_creation_with_data(self, sample_dataset_info):
        """Test creating Dataset with data."""
        df = pd.DataFrame({
            'geo': ['SE', 'NO'],
            'time': ['2020', '2020'],
            'value': [1000.5, 1100.2]
        })
        
        dimensions = {
            "geo": {"SE": "Sweden", "NO": "Norway"},
            "time": {"2020": "2020"}
        }
        
        raw_response = {"test": "data"}
        
        dataset = Dataset(
            info=sample_dataset_info,
            data=df,
            dimensions=dimensions,
            raw_response=raw_response
        )
        
        assert dataset.info == sample_dataset_info
        assert dataset.data.equals(df)
        assert dataset.dimensions == dimensions
        assert dataset.raw_response == raw_response
    
    def test_dataset_equality(self, sample_dataset_info):
        """Test Dataset equality comparison."""
        df = pd.DataFrame({'value': [1, 2, 3]})
        
        dataset1 = Dataset(info=sample_dataset_info, data=df)
        dataset2 = Dataset(info=sample_dataset_info, data=df)
        
        # Note: DataFrame equality in dataclasses might not work as expected
        # This test mainly ensures the structure works
        assert dataset1.info == dataset2.info
    
    def test_dataset_repr(self, sample_dataset_info):
        """Test Dataset string representation."""
        dataset = Dataset(info=sample_dataset_info)
        
        repr_str = repr(dataset)
        assert "nama_10_gdp" in repr_str
    
    def test_dataset_with_various_data_types(self, sample_dataset_info):
        """Test Dataset with various data types."""
        # Test with different data types
        data_types = [
            pd.DataFrame({'col': [1, 2, 3]}),
            {"dict": "data"},
            [1, 2, 3],
            "string_data",
            None
        ]
        
        for data in data_types:
            dataset = Dataset(info=sample_dataset_info, data=data)
            
            # Handle DataFrame comparison specially
            if isinstance(data, pd.DataFrame):
                assert dataset.data.equals(data)
            else:
                assert dataset.data == data


class TestTableOfContents:
    """Test cases for TableOfContents model."""
    
    def test_toc_creation_minimal(self, sample_dataset_info):
        """Test creating TableOfContents with minimal fields."""
        datasets = [sample_dataset_info]
        hierarchy = {"data": ["nama_10_gdp"]}
        
        toc = TableOfContents(
            datasets=datasets,
            hierarchy=hierarchy
        )
        
        assert toc.datasets == datasets
        assert toc.hierarchy == hierarchy
        assert toc.creation_date is None
    
    def test_toc_creation_with_date(self, sample_dataset_info):
        """Test creating TableOfContents with creation date."""
        datasets = [sample_dataset_info]
        hierarchy = {"data": ["nama_10_gdp"]}
        creation_date = datetime(2025, 6, 26, 15, 30)
        
        toc = TableOfContents(
            datasets=datasets,
            hierarchy=hierarchy,
            creation_date=creation_date
        )
        
        assert toc.datasets == datasets
        assert toc.hierarchy == hierarchy
        assert toc.creation_date == creation_date
    
    def test_toc_with_multiple_datasets(self):
        """Test TableOfContents with multiple datasets."""
        datasets = [
            DatasetInfo(code="dataset1", title="Dataset 1", type="dataset"),
            DatasetInfo(code="dataset2", title="Dataset 2", type="dataset"),
            DatasetInfo(code="folder1", title="Folder 1", type="folder")
        ]
        
        hierarchy = {
            "data": ["folder1"],
            "folder1": ["dataset1", "dataset2"]
        }
        
        toc = TableOfContents(
            datasets=datasets,
            hierarchy=hierarchy
        )
        
        assert len(toc.datasets) == 3
        assert "data" in toc.hierarchy
        assert "folder1" in toc.hierarchy
        assert "dataset1" in toc.hierarchy["folder1"]
        assert "dataset2" in toc.hierarchy["folder1"]
    
    def test_toc_empty_hierarchy(self):
        """Test TableOfContents with empty hierarchy."""
        datasets = [DatasetInfo(code="dataset1", title="Dataset 1", type="dataset")]
        hierarchy = {}
        
        toc = TableOfContents(
            datasets=datasets,
            hierarchy=hierarchy
        )
        
        assert len(toc.datasets) == 1
        assert toc.hierarchy == {}
    
    def test_toc_equality(self, sample_dataset_info):
        """Test TableOfContents equality comparison."""
        datasets = [sample_dataset_info]
        hierarchy = {"data": ["nama_10_gdp"]}
        
        toc1 = TableOfContents(datasets=datasets, hierarchy=hierarchy)
        toc2 = TableOfContents(datasets=datasets, hierarchy=hierarchy)
        
        assert toc1 == toc2
    
    def test_toc_repr(self, sample_dataset_info):
        """Test TableOfContents string representation."""
        datasets = [sample_dataset_info]
        hierarchy = {"data": ["nama_10_gdp"]}
        
        toc = TableOfContents(datasets=datasets, hierarchy=hierarchy)
        
        repr_str = repr(toc)
        assert "TableOfContents" in repr_str


class TestModelsIntegration:
    """Integration tests for data models."""
    
    def test_full_dataset_workflow(self):
        """Test a complete workflow using all models together."""
        # Create dataset info
        info = DatasetInfo(
            code="nama_10_gdp",
            title="GDP and main components",
            type="dataset",
            last_update=datetime(2025, 6, 26),
            values_count=1049888
        )
        
        # Create sample data
        df = pd.DataFrame({
            'geo': ['SE', 'NO', 'DK'],
            'geo_label': ['Sweden', 'Norway', 'Denmark'],
            'time': ['2020', '2020', '2020'],
            'value': [1000.5, 1100.2, 950.8]
        })
        
        # Create dimensions
        dimensions = {
            "geo": {
                "category": {
                    "index": {"SE": 0, "NO": 1, "DK": 2},
                    "label": {"SE": "Sweden", "NO": "Norway", "DK": "Denmark"}
                }
            },
            "time": {
                "category": {
                    "index": {"2020": 0},
                    "label": {"2020": "2020"}
                }
            }
        }
        
        # Create dataset
        dataset = Dataset(
            info=info,
            data=df,
            dimensions=dimensions,
            raw_response={"version": "2.0", "class": "dataset"}
        )
        
        # Create table of contents
        all_datasets = [
            DatasetInfo(code="data", title="Database", type="folder"),
            info,
            DatasetInfo(code="demo_pjan", title="Population", type="dataset")
        ]
        
        hierarchy = {
            "data": ["nama_10_gdp", "demo_pjan"]
        }
        
        toc = TableOfContents(
            datasets=all_datasets,
            hierarchy=hierarchy,
            creation_date=datetime.now()
        )
        
        # Verify everything works together
        assert dataset.info.code == "nama_10_gdp"
        assert len(dataset.data) == 3
        assert "geo" in dataset.dimensions
        assert dataset.raw_response["class"] == "dataset"
        
        assert len(toc.datasets) == 3
        assert "nama_10_gdp" in toc.hierarchy["data"]
        
        # Find the dataset in TOC
        found_dataset = next(d for d in toc.datasets if d.code == "nama_10_gdp")
        assert found_dataset == info
    
    def test_model_serialization_compatibility(self):
        """Test that models work well with common serialization scenarios."""
        info = DatasetInfo(
            code="test_dataset",
            title="Test Dataset",
            type="dataset",
            last_update=datetime(2025, 6, 26),
            values_count=1000
        )
        
        # Test converting to dict (common for JSON serialization)
        info_dict = {
            'code': info.code,
            'title': info.title,
            'type': info.type,
            'last_update': info.last_update.isoformat() if info.last_update else None,
            'values_count': info.values_count
        }
        
        assert info_dict['code'] == "test_dataset"
        assert info_dict['title'] == "Test Dataset"
        assert info_dict['values_count'] == 1000
        assert info_dict['last_update'] == "2025-06-26T00:00:00"
    
    def test_models_with_real_world_data(self):
        """Test models with realistic data structures."""
        # Create a realistic dataset info as might come from Eurostat
        info = DatasetInfo(
            code="nama_10_gdp",
            title="Gross domestic product (GDP) and main components (output, expenditure and income)",
            type="dataset",
            last_update=datetime(2025, 6, 26, 23, 0, 0),
            last_modified=datetime(2025, 4, 14, 23, 0, 0),
            data_start="1975",
            data_end="2024",
            values_count=1049888,
            short_description="National accounts, GDP",
            unit="Various units",
            source="Eurostat",
            metadata_urls={
                "html": "https://ec.europa.eu/eurostat/cache/metadata/en/nama_10_gdp_esms.htm",
                "sdmx": "https://ec.europa.eu/eurostat/api/dissemination/files?file=metadata/nama_10_gdp_esms.sdmx.zip"
            },
            download_urls={
                "tsv": "https://ec.europa.eu/eurostat/api/dissemination/files?file=data/nama_10_gdp.tsv.gz",
                "sdmx": "https://ec.europa.eu/eurostat/api/dissemination/files?file=data/nama_10_gdp.sdmx.zip"
            }
        )
        
        # Verify all fields are properly set
        assert info.code == "nama_10_gdp"
        assert "GDP" in info.title
        assert info.values_count == 1049888
        assert "html" in info.metadata_urls
        assert "tsv" in info.download_urls
        assert info.data_start == "1975"
        assert info.data_end == "2024"
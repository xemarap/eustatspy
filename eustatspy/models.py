"""Data models for the EustatsPy package."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class DatasetInfo:
    """Information about a Eurostat dataset."""
    code: str
    title: str  # English title only
    type: str  # 'dataset' or 'table'
    last_update: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    data_start: Optional[str] = None
    data_end: Optional[str] = None
    values_count: Optional[int] = None
    short_description: Optional[str] = None  # English description only
    unit: Optional[str] = None  # English unit only
    source: Optional[str] = None  # English source only
    metadata_urls: Optional[Dict[str, str]] = None
    download_urls: Optional[Dict[str, str]] = None

@dataclass 
class Dataset:
    """A complete dataset with metadata and data."""
    info: DatasetInfo
    data: Optional[Any] = None  # pandas DataFrame when loaded
    dimensions: Optional[Dict[str, Any]] = None
    raw_response: Optional[Dict] = None

@dataclass
class TableOfContents:
    """Table of contents structure."""
    datasets: List[DatasetInfo]
    hierarchy: Dict[str, List[str]]  # folder -> list of child codes
    creation_date: Optional[datetime] = None
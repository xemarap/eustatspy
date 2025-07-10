# EustatsPy

A Python wrapper for the Eurostat APIs, providing easy access to European statistical data.

[![Python Versions](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Note:** This is an independent project and is not associated with Eurostat.

## Installation

```bash
pip install git+https://github.com/xemarap/eustatspy.git
```

## Requirements
EuStatsPy requires Python 3.7+ and the following dependencies:

- requests (≥2.25.0) - HTTP library for API communication
- pandas (≥1.0.0) - Data manipulation and analysis

These dependencies are automatically installed when you install EuStatsPy.


## Quick Start

```python
import eustatspy as est

# Initialize the client with caching enabled
client = est.EurostatClient(cache_enabled=True)

# Pre-load metabase for optimal performance (one-time cost)
client.preload_metabase()
```

## Core Functionality

EuStatsPy provides four essential functions for working with Eurostat data:

### 1. Browse Database Structure

Navigate through the Eurostat database hierarchy to discover datasets:

```python
# Start at the root to see main themes
client.browse_database()

# Explore specific themes
client.browse_database('general')  # General statistics
client.browse_database('euroind')  # European indicators
```

### 2. Search Datasets

Find datasets by keyword, with optional date filtering:

```python
# Basic search
results = client.search_datasets("GDP")

# Search with date filter (datasets updated since specific date)
recent_data = client.search_datasets(
    query="unemployment", 
    updated_since="2025-06-01",
    max_results=20
)

# Search for today's updates
today_updates = client.search_datasets(
    query="",  # Empty query = all datasets
    updated_since="2025-07-09",
    max_results=100
)
```

### 3. Explore Dataset Details

Understand dataset dimensions and available filters:

```python
# Get comprehensive dataset information
client.describe_dataset("lfst_r_lfsd2pop")

# See all values for a specific dimension
client.describe_dataset("nama_10_gdp", show_all_for_dimension='geo')

# Limit displayed values per dimension
client.describe_dataset("ei_isbr_m", max_values_per_dimension=5)
```

### 4. Get Data as DataFrame

Retrieve data with flexible filtering options:

#### Geographic Filtering
```python
# Single country
df = client.get_data_as_dataframe('nama_10_gdp', geo='SE')

# Multiple countries
df = client.get_data_as_dataframe(
    'lfst_r_lfsd2pop',
    geo=['SE11', 'DK01']
)

# By geographic level
df = client.get_data_as_dataframe(
    'tour_occ_nin2m',
    geoLevel='country',
    lastTimePeriod=1
)
```

#### Time Filtering
```python
# Specific years
df = client.get_data_as_dataframe(
    'lfst_r_lfsd2pop',
    geo='SE',
    time=['2022', '2023']
)

# Latest periods
df = client.get_data_as_dataframe(
    'nama_10_gdp',
    geo='SE',
    lastTimePeriod=5
)

# Time ranges
df = client.get_data_as_dataframe(
    'ei_isbr_m',
    geo='SE',
    sinceTimePeriod='2024-01',
    untilTimePeriod='2024-12'
)

# Data from specific time
df = client.get_data_as_dataframe(
    'nama_10_gdp',
    geo='SE',
    sinceTimePeriod='2020'
    )
```

#### Multi-dimensional Filtering
```python
# Complex filtering with multiple dimensions
df = client.get_data_as_dataframe(
    'lfst_r_lfsd2pop',
    geo=['SE11', 'SE12'],
    age='Y25-64',
    isced11=['ED0-2', 'ED3_4', 'ED5-8'],
    sex=['M', 'F'],
    lastTimePeriod=3
)
```

## Common Filter Parameters

- **geo**: Geographic areas - `'SE'`, `['SE', 'DK']`, or `'all'`
- **time**: Time periods - `'2020'`, `['2020', '2021']`, `'2020-Q1'`
- **geoLevel**: Geographic level - `'country'`, `'nuts1'`, `'nuts2'`, `'nuts3'`, `'city'`, `'aggregate'`
- **lastTimePeriod**: Number of latest periods - `1`, `5`, `10`
- **sinceTimePeriod**: Start period - `'2020'`, `'2020-Q1'`, `'2020-01'`
- **untilTimePeriod**: End period - `'2023'`, `'2023-Q4'`, `'2023-12'`

Plus dataset-specific dimensions like `unit`, `na_item`, `sex`, `age` etc.

## Performance Tips

1. **Enable caching** for faster repeated queries:
   ```python
   client = est.EurostatClient(cache_enabled=True)
   ```

2. **Pre-load metabase** for instant dataset exploration:
   ```python
   client.preload_metabase()  # One-time cost
   # Now all describe_dataset() calls are instant!
   ```

3. **Use specific filters** to reduce data size:
   ```python
   # Instead of getting all data
   df = client.get_data_as_dataframe('nama_10_gdp')
   
   # Filter to what you need
   df = client.get_data_as_dataframe(
       'nama_10_gdp',
       geo='SE',
       unit='CP_MEUR',
       lastTimePeriod=5
   )
   ```

## Data Frequency Examples

- **Annual data**: `nama_10_gdp` (GDP), `lfst_r_lfsd2pop` (Population)
- **Quarterly data**: `tipsbp53` (Balance of payments), `namq_10_gdp` (GDP quarterly)
- **Monthly data**: `ei_isbr_m` (Industrial production), `tour_occ_nin2m` (Tourism)

## Error Handling

```python
try:
    df = client.get_data_as_dataframe('invalid_dataset')
except est.DatasetNotFoundError:
    print("Dataset not found")
except est.InvalidParameterError as e:
    print(f"Invalid parameters: {e}")
except est.EurostatAPIError as e:
    print(f"API error: {e}")
```

## Cache Management

```python
# Clear cache when needed
client.clear_cache()

# Check if metabase is loaded
if not client.is_metabase_loaded():
    client.preload_metabase()
```

## Example Workflow

```python
import eustatspy as est

# 1. Initialize and setup
client = est.EurostatClient(cache_enabled=True)
client.preload_metabase()

# 2. Discover data
client.browse_database()  # Explore themes
results = client.search_datasets("employment")  # Find datasets

# 3. Understand dataset
client.describe_dataset("lfst_r_lfsd2pop")  # Explore dimensions

# 4. Get data
df = client.get_data_as_dataframe(
    'lfst_r_lfsd2pop',
    geo=['SE11', 'DK01'],
    age='Y25-64',
    lastTimePeriod=5
)

print(df.head())
```

## Language Support

This package returns all data and metadata in English only for consistency and simplicity.

## Contributing

Contributions are welcome! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Dependency Licenses
EuStatsPy includes the following dependencies:

**Runtime Dependencies:**
- requests
- pandas

**Development/Testing Dependencies (not distributed):**
- pytest
- pytest-cov
- pytest-mock

All dependency licenses are available in the `LICENSES/` directory.

## Acknowledgments

- Data provided by [Eurostat](https://ec.europa.eu/eurostat)
- Built using the official Eurostat APIs
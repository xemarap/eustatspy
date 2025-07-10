# EuStatsPy Test Suite

This directory contains a comprehensive test suite for the EuStatsPy package. The tests are designed to be maintainable, fast, and provide good coverage of the codebase.

## Test Structure

### Test Files

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_client.py`** - Tests for the main `EurostatClient` class
- **`test_statistics.py`** - Tests for the `StatisticsAPI` class
- **`test_catalogue.py`** - Tests for the `CatalogueAPI` class
- **`test_utils.py`** - Tests for utility functions and the `Cache` class
- **`test_models.py`** - Tests for data model classes
- **`test_exceptions.py`** - Tests for custom exception classes
- **`test_integration.py`** - Integration tests for complete workflows

### Configuration Files

- **`pytest.ini`** - Pytest configuration with markers and settings
- **`requirements-test.txt`** - Test dependencies
- **`run_tests.py`** - Test runner script with various options

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Or use the test runner (run directly, not as module)
python run_tests.py
```

### Test Categories

Tests are organized with pytest markers:

```bash
# Unit tests (fast, isolated)
pytest -m unit

# Integration tests (test multiple components)
pytest -m integration

# Fast tests only (exclude slow tests)
pytest -m "not slow"

# Specific test categories
pytest -m api          # API interaction tests
pytest -m cache        # Caching tests
pytest -m parsing      # Data parsing tests
pytest -m models       # Data model tests
```

### Using the Test Runner

The `run_tests.py` script provides convenient options:

```bash
# Basic usage
python run_tests.py                    # All tests
python run_tests.py --unit             # Unit tests only
python run_tests.py --integration      # Integration tests only
python run_tests.py --fast             # Fast tests only

# Coverage reporting
python run_tests.py --coverage         # Detailed coverage
python run_tests.py --html             # HTML coverage report
python run_tests.py --no-cov           # Disable coverage

# Parallel execution
python run_tests.py --parallel         # Run tests in parallel

# Specific tests
python run_tests.py --file client      # Run test_client.py
python run_tests.py --test test_search # Run specific test function
python run_tests.py -k "search"        # Run tests matching keyword

# Debug options
python run_tests.py --pdb              # Drop into debugger on failure
python run_tests.py --lf               # Run last failed tests only
python run_tests.py --failed-first     # Run failed tests first
```

## Test Design Principles

### 1. Fast and Reliable

- Most tests are unit tests that run quickly
- External dependencies are mocked
- No real network calls in tests
- Deterministic test behavior

### 2. Good Coverage

- Aims for >85% code coverage
- Tests both happy paths and error cases
- Covers edge cases and boundary conditions

### 3. Maintainable

- Clear test names that describe what's being tested
- Shared fixtures in `conftest.py`
- Minimal test duplication
- Easy to understand test structure

### 4. Realistic

- Tests use realistic data structures
- Integration tests simulate real workflows
- Mock responses match actual API responses

## Test Fixtures

### Common Fixtures (from `conftest.py`)

- **`sample_dataset_info`** - Example `DatasetInfo` object
- **`sample_toc`** - Example `TableOfContents` object
- **`sample_jsonstat_response`** - Example JSON-stat API response
- **`sample_metabase_data`** - Example metabase data structure
- **`temp_cache_dir`** - Temporary directory for cache testing
- **`cache_instance`** - Pre-configured `Cache` instance
- **`client_no_cache`** - Client without caching
- **`client_with_cache`** - Client with caching enabled

### Creating Mock Responses

Use the `create_mock_response` utility function:

```python
from conftest import create_mock_response

# JSON response
mock_response = create_mock_response({"key": "value"})

# Text response
mock_response = create_mock_response("text content", content_type="text/plain")

# Error response
mock_response = create_mock_response({"error": "Not found"}, status_code=404)
```

## Writing New Tests

### Test File Structure

```python
"""Tests for [module/functionality]."""

import pytest
from unittest.mock import patch, Mock
from eustatspy.[module] import [Class]
from eustatspy.exceptions import [ExceptionClass]


class Test[ClassName]:
    """Test cases for [ClassName]."""
    
    def test_basic_functionality(self):
        """Test basic functionality works."""
        # Arrange
        instance = Class()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ExceptionClass):
            # Code that should raise exception
            pass


class Test[ClassName]EdgeCases:
    """Test edge cases for [ClassName]."""
    
    def test_edge_case(self):
        """Test specific edge case."""
        pass
```

### Test Naming Convention

- Test files: `test_[module].py`
- Test classes: `Test[ClassName]` or `Test[Functionality]`
- Test methods: `test_[what_is_being_tested]`

Examples:
- `test_client_initialization`
- `test_search_datasets_with_filters`
- `test_error_handling_invalid_dataset`

### Mocking Guidelines

1. **Mock external dependencies**: Always mock HTTP requests, file system operations, etc.
2. **Use appropriate mock scope**: Use `@patch` decorator or context manager as appropriate
3. **Verify mock calls**: Assert that mocks were called with expected parameters
4. **Create realistic mocks**: Mock responses should match real API responses

### Assertions

Use descriptive assertions:

```python
# Good
assert result.code == "nama_10_gdp"
assert len(dataframe) == 100
assert "error" in response

# Better with custom messages
assert result.code == "nama_10_gdp", f"Expected nama_10_gdp, got {result.code}"
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- Tests are deterministic and don't depend on external services
- Parallel execution is supported
- Coverage reporting is configured
- Test results can be exported in various formats

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e .
        pip install -r requirements-test.txt
    - name: Run tests
      run: python run_tests.py --coverage --parallel
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Debugging Tests

### Running Individual Tests

```bash
# Specific test file
pytest tests/test_client.py

# Specific test class
pytest tests/test_client.py::TestEurostatClient

# Specific test method
pytest tests/test_client.py::TestEurostatClient::test_initialization

# With debugger
pytest --pdb tests/test_client.py::TestEurostatClient::test_initialization
```

### Verbose Output

```bash
# Show more details
pytest -v

# Show print statements
pytest -s

# Show local variables on failure
pytest --tb=long
```

### Common Issues

1. **Import errors**: Make sure the package is installed in development mode (`pip install -e .`)
2. **Mock not working**: Check that you're patching the right import path
3. **Flaky tests**: Often due to time dependencies or race conditions
4. **Slow tests**: Make sure you're mocking external dependencies

## Performance

### Running Tests Quickly

```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Exit on first failure
pytest -x

# Rerun only failed tests
pytest --lf
```

### Test Performance Monitoring

The test suite includes performance monitoring:

- `--durations=10` shows the 10 slowest tests
- Tests taking longer than 5 minutes will timeout
- Use the `@pytest.mark.slow` marker for tests that take >1 second

## Contributing

When adding new functionality:

1. **Write tests first** (TDD approach recommended)
2. **Ensure good coverage** - aim for >90% on new code
3. **Add appropriate markers** - use `@pytest.mark.[category]`
4. **Update this README** if adding new test patterns or conventions
5. **Run the full test suite** before submitting PR

### Test Review Checklist

- [ ] Tests cover both happy path and error cases
- [ ] External dependencies are properly mocked
- [ ] Test names clearly describe what's being tested
- [ ] Tests are fast and reliable
- [ ] Coverage is maintained or improved
- [ ] No real network calls or file system dependencies
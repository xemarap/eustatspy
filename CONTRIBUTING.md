# Contributing to EuStatsPy

Thank you for your interest in contributing to EuStatsPy! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/xemarap/eustatspy.git
   cd eustatspy
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest tests/ -v --cov=eustatspy
```

## Code Style

We use Black for code formatting:
```bash
black eustatspy/
```

And flake8 for linting:
```bash
flake8 eustatspy/
```

## Type Checking

We use mypy for type checking:
```bash
mypy eustatspy/
```

## Submitting Changes

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature-name
   ```

2. Make your changes and add tests
3. Ensure all tests pass and code follows style guidelines
4. Commit your changes with a clear message
5. Push to your fork and submit a pull request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features. Include:
- Python version
- EustatsPy version
- Detailed description of the issue
- Code to reproduce the problem (if applicable)

## Code of Conduct

Please be respectful and constructive in all interactions with the project and community.
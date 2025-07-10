"""Setup configuration for the eustatspy package."""

from setuptools import setup, find_packages

# Read the contents of README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eustatspy",
    version="0.1.0",
    author="Emanuel Raptis",
    description="A Python wrapper for Eurostat APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xemarap/eustatspy",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pandas>=1.3.0"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Data/Statistics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="eurostat statistics api data economics",
    project_urls={
        "Bug Reports": "https://github.com/xemarap/eustatspy/issues",
        "Source": "https://github.com/xemarap/eustatspy"
    },
)
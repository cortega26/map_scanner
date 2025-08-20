"""
Setup script for the Map Scanner package.

Professional package setup following modern Python packaging standards.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements from requirements.txt


def read_requirements():
    """Read requirements from requirements.txt file."""
    requirements_path = this_directory / "requirements.txt"
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            # Filter out comments and empty lines
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith('#')
            ]
    return []


# Package metadata
setup(
    name="map-scanner",
    version="3.0.0",
    author="Professional Development Team",
    author_email="dev@mapscanner.com",
    description="Enhanced Professional Map Scanner with Advanced OCR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/map-scanner",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/map-scanner/issues",
        "Documentation": "https://map-scanner.readthedocs.io/",
        "Source Code": "https://github.com/your-org/map-scanner",
    },

    # Package configuration
    packages=find_packages(),
    include_package_data=True,

    # Dependencies
    install_requires=read_requirements(),

    # Python version requirement
    python_requires=">=3.8",

    # Package classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Typing :: Typed",
    ],

    # Keywords for discoverability
    keywords=[
        "ocr", "automation", "game", "scanner", "image-processing",
        "tesseract", "opencv", "gui-automation", "map-scanning"
    ],

    # Entry points for command-line interface
    entry_points={
        "console_scripts": [
            "map-scanner=map_scanner.main:main",
        ],
    },

    # Additional package data
    package_data={
        "map_scanner": [
            "py.typed",  # Indicates this package supports type hints
        ],
    },

    # Development dependencies (optional)
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },

    # Zip safety
    zip_safe=False,
)

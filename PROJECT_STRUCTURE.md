# Project Structure Guide

This document outlines the complete project structure for the refactored Map Scanner application, following professional Python packaging standards and best practices.

## 📁 Complete Directory Structure

```text

map-scanner/
├── map_scanner/                    # Main package directory
│   ├── __init__.py                # Package initialization and public API
│   ├── main.py                    # Application entry point and CLI
│   ├── config.py                  # Configuration classes and constants
│   ├── exceptions.py              # Custom exception hierarchy
│   ├── logger_config.py           # Centralized logging configuration
│   ├── utils.py                   # Reusable utility functions
│   ├── window_manager.py          # Window detection and management
│   ├── screen_capture.py          # Screen capture operations
│   ├── mouse_controller.py        # Mouse movement and interactions
│   ├── ocr_engine.py             # OCR processing and preprocessing
│   ├── map_scanner.py            # Main scanner orchestration logic
│   └── py.typed                  # Type hints support marker
│
├── tests/                         # Test suite (to be implemented)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_utils.py
│   ├── test_window_manager.py
│   ├── test_screen_capture.py
│   ├── test_mouse_controller.py
│   ├── test_ocr_engine.py
│   ├── test_map_scanner.py
│   └── fixtures/                  # Test data and fixtures
│
├── docs/                          # Documentation
│   ├── source/
│   │   ├── conf.py               # Sphinx configuration
│   │   ├── index.rst             # Main documentation index
│   │   ├── api.rst               # API documentation
│   │   ├── installation.rst      # Installation guide
│   │   ├── usage.rst             # Usage examples
│   │   └── development.rst       # Development guide
│   └── build/                    # Built documentation
│
├── examples/                      # Usage examples
│   ├── basic_usage.py            # Basic usage example
│   ├── advanced_usage.py         # Advanced configuration example
│   └── custom_integration.py     # Custom integration example
│
├── scripts/                       # Utility scripts
│   ├── setup_dev_env.py         # Development environment setup
│   ├── run_tests.py              # Test runner script
│   └── build_docs.py             # Documentation builder
│
├── .github/                       # GitHub specific files
│   ├── workflows/
│   │   ├── ci.yml                # Continuous Integration
│   │   ├── release.yml           # Release automation
│   │   └── docs.yml              # Documentation building
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── requirements.txt               # Core dependencies
├── requirements-dev.txt           # Development dependencies
├── setup.py                      # Setup script for pip installation
├── pyproject.toml                # Modern Python project configuration
├── README.md                     # Main project documentation
├── LICENSE                       # License file
├── CHANGELOG.md                  # Version history and changes
├── CONTRIBUTING.md               # Contribution guidelines
├── .gitignore                    # Git ignore rules
├── .editorconfig                 # Editor configuration
├── .pre-commit-config.yaml       # Pre-commit hooks configuration
└── Makefile                      # Common development tasks
```

## 📋 File Descriptions

### Core Package (`map_scanner/`)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `__init__.py` | Package API and exports | `create_scanner()`, version info |
| `main.py` | CLI entry point | `main()`, argument parsing |
| `config.py` | Configuration management | `WindowConfig`, `OCRConfig`, etc. |
| `exceptions.py` | Exception hierarchy | `MapScannerError`, `SafetyExit` |
| `logger_config.py` | Logging setup | `setup_logging()`, `get_logger()` |
| `utils.py` | Utility functions | Helper functions, text processing |
| `window_manager.py` | Window operations | `WindowManager` class |
| `screen_capture.py` | Screen capture | `ScreenCapture` class |
| `mouse_controller.py` | Mouse control | `MouseController` class |
| `ocr_engine.py` | OCR processing | `OCREngine`, `ImagePreprocessor` |
| `map_scanner.py` | Main orchestration | `MapScanner` class |

### Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Core runtime dependencies |
| `requirements-dev.txt` | Development dependencies |
| `setup.py` | Traditional package setup |
| `pyproject.toml` | Modern package configuration |

### Development Files

| File | Purpose |
|------|---------|
| `.gitignore` | Git ignore patterns |
| `.editorconfig` | Editor settings consistency |
| `.pre-commit-config.yaml` | Code quality hooks |
| `Makefile` | Development automation |

## 🔧 Development Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd map-scanner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]
```

### 2. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 3. Run Development Tools

```bash
# Code formatting
make format

# Linting
make lint

# Type checking
make typecheck

# Run tests
make test

# Build documentation
make docs
```

## 📦 Package Installation Options

### For End Users

```bash
pip install map-scanner
```

### For Development

```bash
git clone <repository-url>
cd map-scanner
pip install -e .[dev]
```

### From Source

```bash
python setup.py install
```

## 🎯 Key Architectural Benefits

### 1. **Modularity**

- Each module has a single, clear responsibility
- Components can be tested and developed independently
- Easy to add new features without affecting existing code

### 2. **Maintainability**

- Clear separation of concerns
- Consistent error handling patterns
- Comprehensive logging and debugging support

### 3. **Extensibility**

- Plugin-like architecture for OCR strategies
- Configurable parameters for different use cases
- Easy to add new preprocessing techniques

### 4. **Reliability**

- Comprehensive exception handling
- Safety checks and boundaries
- Graceful degradation on errors

### 5. **Professional Standards**

- Type hints throughout
- Comprehensive documentation
- Code quality tools integration
- CI/CD ready structure

## 🧪 Testing Strategy

### Unit Tests

- Test individual components in isolation
- Mock external dependencies (windows, mouse, etc.)
- Focus on business logic and edge cases

### Integration Tests

- Test component interactions
- Use test fixtures for predictable environments
- Validate end-to-end workflows

### Performance Tests

- OCR processing speed benchmarks
- Memory usage monitoring
- Movement accuracy validation

## 📚 Documentation Strategy

### API Documentation

- Automatically generated from docstrings
- Type hints provide clear interfaces
- Examples for each major function

### User Guide

- Installation instructions
- Basic and advanced usage examples
- Troubleshooting guide

### Developer Guide

- Architecture overview
- Contributing guidelines
- Code style requirements

## 🚀 Deployment Options

### Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile map_scanner/main.py
```

### Docker Container

```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install .
CMD ["map-scanner"]
```

### Package Distribution

```bash
python -m build
twine upload dist/*
```

This structure provides a solid foundation for professional development, maintenance, and distribution of the Map Scanner application.

# Contributing to Orby

Thank you for your interest in contributing to Orby! This document provides guidelines for contributing to this project.

## Development Setup

1. Fork and clone the repository
2. Install dependencies: `pip install -e .`
3. Run the CLI: `orby --help`

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return types
- Write docstrings for all public functions and classes
- Add tests for new functionality

## Pull Request Process

1. Create a feature branch from `main`
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation if necessary
5. Submit a pull request with a clear description

## Project Structure

- `orby/cli.py` - Main CLI entry point
- `orby/commands/` - Individual command implementations
- `orby/backend.py` - Backend interface definition
- `orby/backends.py` - Backend implementations (Ollama, LM Studio, etc.)
- `orby/config.py` - Configuration management
- `orby/tools/` - Tool implementations (for agentic features)

## Testing

Tests should be added for new functionality. Run the test suite with:

```bash
# Coming soon: pytest or similar
```

## Reporting Issues

When reporting issues, please include:
- Your operating system
- Python version
- Orby version
- Steps to reproduce the issue
- Expected vs actual behavior
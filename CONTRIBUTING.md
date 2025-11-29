# Contributing to MNMD Anki Sync

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive. We're all here to build something useful.

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Anki](https://apps.ankiweb.net/) with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) (for integration testing)

### Development Setup

1. Fork the repository on GitHub

2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mnmd-anki-sync.git
   cd mnmd-anki-sync
   ```

3. Install dependencies:
   ```bash
   uv sync --extra dev
   ```

4. Verify setup by running tests:
   ```bash
   uv run pytest
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_cloze_parser.py

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_parse"
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type check
uv run mypy src
```

### Pre-commit Checks

Before committing, ensure:
1. All tests pass: `uv run pytest`
2. Code is formatted: `uv run black src tests`
3. No lint errors: `uv run ruff check src tests`
4. Types check: `uv run mypy src`

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Write clear, concise commit messages:

```
Add support for image clozes

- Parse image markdown syntax within cloze brackets
- Convert to Anki media references
- Add tests for image handling
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

### PR Description Template

```markdown
## Summary
Brief description of changes

## Changes
- List of specific changes

## Testing
How to test these changes

## Checklist
- [ ] Tests pass locally
- [ ] Code is formatted
- [ ] Documentation updated (if applicable)
```

## Project Structure

```
mnmd-anki-sync/
├── src/mnmd_anki_sync/
│   ├── anki/           # Anki integration
│   │   ├── client.py   # AnkiConnect API client
│   │   ├── note_builder.py
│   │   └── note_type.py
│   ├── parser/         # Markdown parsing
│   │   ├── cloze_parser.py
│   │   ├── context_extractor.py
│   │   ├── prompt_generator.py
│   │   └── scope_resolver.py
│   ├── sync/           # Sync logic
│   │   ├── syncer.py
│   │   └── id_writer.py
│   ├── utils/          # Utilities
│   │   ├── base52.py
│   │   ├── file_id.py
│   │   ├── markdown_utils.py
│   │   └── exceptions.py
│   ├── cli.py          # CLI interface
│   ├── config.py       # Configuration
│   └── models.py       # Data models
├── tests/
│   └── unit/           # Unit tests
├── pyproject.toml
└── README.md
```

## Adding New Features

### Parser Changes

1. Update the relevant parser module
2. Add corresponding tests in `tests/unit/`
3. Update `models.py` if new data structures needed
4. Update documentation

### CLI Changes

1. Add commands/options in `cli.py`
2. Add tests in `tests/unit/test_cli.py`
3. Update README.md with usage examples

### Anki Integration Changes

1. Update `anki/client.py` for new API calls
2. Update `anki/note_type.py` for card template changes
3. Test with actual Anki instance

## Testing Guidelines

- Write tests for all new functionality
- Aim for high coverage (currently 96%)
- Use mocks for external services (AnkiConnect)
- Test edge cases and error conditions
- Use descriptive test names

## Documentation

- Update README.md for user-facing changes
- Update syntax-notes.md for syntax changes
- Add docstrings to new functions/classes
- Update CHANGELOG.md for releases

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

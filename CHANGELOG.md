# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX (Unreleased)

### Added - Core Feature
- **Clozes work ANYWHERE in markdown**: Place `{{clozes}}` directly in regular paragraphs
- **Automatic context extraction**: Paragraphs (separated by `\n\n`) become card contexts automatically
- **`> ?` blocks are optional**: Use only for custom context boundaries (special cases)

### Added - Other Features
- Basic cloze deletion syntax: `{{answer}}`
- Grouped cloze syntax: `{{id>answer}}`
- Sequence cloze syntax: `{{id.order>answer}}`
- Hint syntax: `{{answer|hint}}`
- Extra information syntax: `{{answer<extra}}`
- Combined syntax: `{{answer|hint<extra}}`
- Math support with LaTeX delimiters (`$inline$` and `$$block$$`)
- Image support via markdown syntax
- Scope control with `[-before,after]` notation
- Automatic Anki ID tracking to prevent duplicates
- Markdown to HTML conversion for rich formatting
- Card context blocks with `> ?` syntax
- CLI commands: `sync`, `validate`, `syntax`, `version`
- **`mnmd syntax` command**: View complete syntax guide in terminal (with pager support)
- **`agents-syntax.md`**: LLM-optimized syntax reference for programmatic generation
- Editor integration: VS Code, VSCodium, Neovim, Obsidian, File protocol
- `file` protocol option for generic file:// URLs (works with any editor)
- Comprehensive test suite (103 tests)

### Features
- Smart duplicate detection using base52-encoded Anki IDs
- Automatic ID write-back to markdown files
- Nested brace support for complex LaTeX expressions
- Paragraph-based context resolution
- Default list scope of `[-1]` (include paragraph before)
- Type-safe implementation with Pydantic

### Technical
- Built with Python 3.10+
- Uses Typer for CLI
- Pydantic v2 for data validation
- AnkiConnect integration via HTTP API
- Markdown rendering with python-markdown

## [Unreleased]

### Planned
- YAML front matter support for deck/tag configuration
- Batch processing of multiple files
- Watch mode for auto-sync
- Config file support (~/.mnmd/config.yaml)
- Export to standalone HTML/Quantum Country format

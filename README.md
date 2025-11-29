# MNMD Anki Sync

[![CI](https://github.com/am-campbell/mnmd-anki-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/am-campbell/mnmd-anki-sync/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/mnmd-anki-sync.svg)](https://badge.fury.io/py/mnmd-anki-sync)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Sync mnemonic markdown files to Anki with rich cloze deletion syntax.

## Features

- **Rich cloze syntax**: Basic, grouped, and sequence clozes
- **Hints and extras**: Add hints (`{{answer|hint}}`) and extra info (`{{answer<extra}}`)
- **Math support**: LaTeX equations (`$inline$` and `$$block$$`) automatically converted to Anki format
- **Markdown rendering**: Bold, italic, lists, images, code blocks, line breaks
- **Scope control**: Specify paragraph context for each cloze with `[-before,after]`
- **Smart updates**: Automatically tracks Anki IDs to prevent duplicates
- **Editor links**: Open source files from Anki in VS Code, VSCodium, Neovim, or Obsidian
- **Dry-run mode**: Preview changes before syncing with `--dry-run`
- **Type-safe**: Built with Pydantic for robust data validation
- **Well-tested**: 276 unit tests with 96% code coverage

## Installation

### For Users

**Recommended: Install with pipx** (installs in isolated environment)
```bash
pipx install mnmd-anki-sync
```

**Alternative: Install with pip**
```bash
pip install mnmd-anki-sync
```

**Or install with uv**
```bash
uv pip install mnmd-anki-sync
```

**Install from GitHub** (latest development version)
```bash
pip install git+https://github.com/am-campbell/mnmd-anki-sync.git
```

### For Developers

Clone the repository and install with uv:
```bash
git clone https://github.com/am-campbell/mnmd-anki-sync.git
cd mnmd-anki-sync
uv sync --extra dev
```

## Quick Start

1. Make sure Anki is running with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) installed

2. View the syntax guide:

```bash
mnmd syntax
```

3. Create a markdown file with cloze deletions:

```markdown
> ?
> The capital of France is {{Paris}}.

> ?
> My favorite languages are {{1>Python}} and {{1>Rust}}.
```

4. Sync to Anki:

```bash
mnmd sync myfile.md --deck "My Deck"
```

## Syntax Guide

See [syntax-notes.md](syntax-notes.md) for complete syntax documentation.

### Basic Cloze
```markdown
> ?
> The capital of France is {{Paris}}.
```
Creates one card with "The capital of France is [...]"

### Grouped Cloze
```markdown
> ?
> My favorite languages are {{1>Python}} and {{1>Rust}}.
```
Both items are hidden together on the same card: "My favorite languages are [...] and [...]"

### Sequence Cloze
```markdown
> ?
> My Haiku:
> {{1.1>I want to write an}}[-1]
> {{1.2>Example poem for you}}
> {{1.3>Hopefully helpful}}
```
Creates progressive reveal: first line hidden, then second, then third

### Hints and Extras
```markdown
> ?
> Python is a {{dynamically typed|type checking happens at runtime}} language.
> The package manager is {{pip<PyPI hosts over 400,000 packages}}.
```
- `|hint` adds hint text shown on card back
- `<extra` adds extra information (no closing `>`)
- Combine: `{{answer|hint<extra}}`

### Math Support
```markdown
> ?
> Einstein's equation: {{$E = mc^2$}}
> The quadratic formula: {{$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$|solves ax² + bx + c = 0}}
```
LaTeX math is automatically converted to Anki's format

### Images
```markdown
> ?
> The Python logo: ![Python](./images/python-logo.png)
```
Standard markdown images work in Anki cards

### Scope Control
```markdown
{{text}}[-1,2]
```
Include 1 paragraph before, 2 after. Default is current paragraph only.
- Negative numbers = paragraphs before
- Positive numbers = paragraphs after
- Lists default to `[-1]` (include paragraph before)

## CLI Commands

```bash
# Sync files
mnmd sync file.md --deck "Biology" --tags "chapter1"

# Sync with specific editor
mnmd sync file.md --editor nvim
mnmd sync file.md --editor vscode

# Validate syntax
mnmd validate file.md

# Show syntax guide (opens in pager)
mnmd syntax

# Show syntax guide without pager (direct output)
mnmd syntax --no-pager

# Show version
mnmd version
```

## Editor Configuration

Set your preferred editor for source links in Anki cards. Choose from:

- `vscode` - Visual Studio Code (default, works out of box)
- `vscodium` - VSCodium (works out of box)
- `obsidian` - Obsidian (works out of box)
- `file` - System default handler (works out of box)
- `nvim` - Neovim (requires setup, see [EDITOR_SETUP.md](EDITOR_SETUP.md))

**Config file (`~/.mnmdrc`):**
```yaml
editor_protocol: vscode  # or nvim, vscodium, obsidian, file
default_deck: My Deck
default_tags:
  - mnmd
```

**Command line:**
```bash
mnmd sync file.md --editor nvim
```

**For Neovim users:** The `nvim://` protocol requires custom setup. Either:
1. Use `file` protocol (easiest): `editor_protocol: file`
2. Register `nvim://` handler (see [EDITOR_SETUP.md](EDITOR_SETUP.md))

The `file` protocol opens files with your system's default markdown editor.

## Development

```bash
# Run tests
uv run pytest

# Type check
uv run mypy src
```

## For AI Agents & LLM Integration

If you're building tools that generate mnemonic markdown or integrating LLMs to create flashcards, see **[agents-syntax.md](agents-syntax.md)** for:

- Precise syntax specification optimized for LLM parsing
- Complete pattern reference with regex-like precision
- Common pitfalls and error prevention
- Validation checklist
- Quick reference table

This file provides unambiguous rules for programmatic generation of valid MNMD syntax.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass: `uv run pytest`
5. Submit a pull request

## Publishing & Distribution

See [DISTRIBUTION.md](DISTRIBUTION.md) for instructions on publishing releases to PyPI and GitHub.

## License

Apache 2.0 - See [LICENSE](LICENSE) file for details

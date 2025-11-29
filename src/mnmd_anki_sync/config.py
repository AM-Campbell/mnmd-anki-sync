"""Configuration management for mnmd-anki-sync."""

import html
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field

from .utils.exceptions import ConfigError


class EditorProtocol(str, Enum):
    """Supported editor protocols for source links."""

    VSCODE = "vscode"
    VSCODIUM = "vscodium"
    NVIM = "nvim"
    OBSIDIAN = "obsidian"
    FILE = "file"  # Generic file:// protocol (requires system handler)


class Config(BaseModel):
    """Application configuration."""

    editor_protocol: EditorProtocol = Field(
        default=EditorProtocol.VSCODE, description="Editor protocol for source links"
    )
    anki_url: str = Field(default="http://localhost:8765", description="AnkiConnect URL")
    default_deck: str = Field(default="Default", description="Default Anki deck name")
    default_tags: List[str] = Field(
        default_factory=lambda: ["mnmd"], description="Default tags for cards"
    )

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from a YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Config object

        Raises:
            ConfigError: If config file is invalid
        """
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            return cls(**data)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e
        except Exception as e:
            raise ConfigError(f"Error loading config: {e}") from e

    @classmethod
    def load_default(cls) -> "Config":
        """Load default configuration, optionally from ~/.mnmdrc.

        Returns:
            Config object
        """
        config_path = Path.home() / ".mnmdrc"
        if config_path.exists():
            try:
                return cls.load_from_file(config_path)
            except ConfigError as e:
                # Warn user that their config file is invalid
                print(
                    f"Warning: Invalid config file {config_path}: {e}\n"
                    "Using default configuration.",
                    file=sys.stderr
                )

        return cls()

    def build_source_link(self, file_path: Path, line_number: int) -> str:
        """Build a source link using the configured editor protocol.

        Args:
            file_path: Path to source file
            line_number: Line number in file

        Returns:
            HTML link to open file in editor
        """
        absolute_path = file_path.resolve()

        if self.editor_protocol == EditorProtocol.VSCODE:
            url = f"vscode://file{absolute_path}:{line_number}:1"
            text = "Open in VS Code"
        elif self.editor_protocol == EditorProtocol.VSCODIUM:
            url = f"vscodium://file{absolute_path}:{line_number}:1"
            text = "Open in VSCodium"
        elif self.editor_protocol == EditorProtocol.NVIM:
            # Note: nvim:// requires custom protocol handler setup
            # See EDITOR_SETUP.md for registration instructions
            url = f"nvim://open?file={absolute_path}&line={line_number}"
            text = "Open in Neovim"
        elif self.editor_protocol == EditorProtocol.OBSIDIAN:
            url = f"obsidian://open?path={absolute_path}"
            text = "Open in Obsidian"
        elif self.editor_protocol == EditorProtocol.FILE:
            # Generic file:// protocol - opens with system default handler
            url = f"file://{absolute_path}"
            text = "Open File"
        else:
            # Fallback
            url = f"file://{absolute_path}"
            text = "Open File"

        # HTML-escape the URL and text to prevent injection
        escaped_url = html.escape(url, quote=True)
        escaped_text = html.escape(text)

        return f'<a href="{escaped_url}">{escaped_text}</a>'

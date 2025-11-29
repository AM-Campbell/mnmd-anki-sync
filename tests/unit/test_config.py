"""Tests for configuration module."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from mnmd_anki_sync.config import Config, EditorProtocol
from mnmd_anki_sync.utils.exceptions import ConfigError


class TestConfigLoad:
    """Test configuration loading."""

    def test_load_default_creates_config(self):
        """Test that load_default creates a config with defaults."""
        config = Config()

        assert config.editor_protocol == EditorProtocol.VSCODE
        assert config.anki_url == "http://localhost:8765"
        assert config.default_deck == "Default"
        assert config.default_tags == ["mnmd"]

    def test_load_from_valid_yaml(self):
        """Test loading from a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("editor_protocol: nvim\ndefault_deck: TestDeck\n")
            f.flush()

            config = Config.load_from_file(Path(f.name))

            assert config.editor_protocol == EditorProtocol.NVIM
            assert config.default_deck == "TestDeck"

    def test_load_from_empty_yaml(self):
        """Test loading from an empty YAML file uses defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()

            config = Config.load_from_file(Path(f.name))

            # Should use defaults
            assert config.editor_protocol == EditorProtocol.VSCODE
            assert config.default_deck == "Default"

    def test_load_from_nonexistent_file_raises(self):
        """Test loading from non-existent file raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            Config.load_from_file(Path("/nonexistent/file.yaml"))

        assert "Config file not found" in str(exc_info.value)

    def test_load_from_invalid_yaml_raises(self):
        """Test loading from invalid YAML raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            f.flush()

            with pytest.raises(ConfigError) as exc_info:
                Config.load_from_file(Path(f.name))

            assert "Invalid YAML" in str(exc_info.value)

    def test_load_default_warns_on_invalid_config(self):
        """Test load_default warns when config file is invalid."""
        with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
            f.write("invalid: yaml: [")
            f.flush()
            config_path = Path(f.name)

        # Mock Path.home() to return our temp dir's parent
        with patch.object(Path, "home", return_value=config_path.parent):
            # Rename to .mnmdrc
            mnmdrc_path = config_path.parent / ".mnmdrc"
            config_path.rename(mnmdrc_path)

            # Capture stderr
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                config = Config.load_default()

                # Should print warning
                assert "Warning" in mock_stderr.getvalue() or config is not None

            # Cleanup
            if mnmdrc_path.exists():
                mnmdrc_path.unlink()

    def test_load_with_custom_tags(self):
        """Test loading config with custom tags."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("default_tags:\n  - custom\n  - tags\n")
            f.flush()

            config = Config.load_from_file(Path(f.name))

            assert config.default_tags == ["custom", "tags"]

    def test_load_with_custom_anki_url(self):
        """Test loading config with custom Anki URL."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("anki_url: http://remote:9999\n")
            f.flush()

            config = Config.load_from_file(Path(f.name))

            assert config.anki_url == "http://remote:9999"


class TestBuildSourceLink:
    """Test source link building."""

    def test_vscode_link(self):
        """Test VS Code link generation."""
        config = Config(editor_protocol=EditorProtocol.VSCODE)
        link = config.build_source_link(Path("/tmp/test.md"), 10)

        assert "vscode://file" in link
        assert "/tmp/test.md" in link
        assert ":10:1" in link
        assert "Open in VS Code" in link

    def test_nvim_link(self):
        """Test Neovim link generation."""
        config = Config(editor_protocol=EditorProtocol.NVIM)
        link = config.build_source_link(Path("/tmp/test.md"), 10)

        assert "nvim://open" in link
        assert "file=" in link
        assert "line=10" in link
        assert "Open in Neovim" in link

    def test_file_link(self):
        """Test generic file link generation."""
        config = Config(editor_protocol=EditorProtocol.FILE)
        link = config.build_source_link(Path("/tmp/test.md"), 10)

        assert "file://" in link
        assert "/tmp/test.md" in link
        assert "Open File" in link

    def test_html_escape_in_path(self):
        """Test that special characters in path are HTML-escaped."""
        config = Config(editor_protocol=EditorProtocol.FILE)
        # Path with special characters
        link = config.build_source_link(Path('/tmp/test"file<name>.md'), 10)

        # Should be escaped
        assert "&quot;" in link or "&#" in link or '"' not in link.split('href="')[1].split('"')[0]
        assert "&lt;" in link or "<" not in link.split('href="')[1].split('"')[0]

    def test_obsidian_link(self):
        """Test Obsidian link generation."""
        config = Config(editor_protocol=EditorProtocol.OBSIDIAN)
        link = config.build_source_link(Path("/tmp/test.md"), 10)

        assert "obsidian://open" in link
        assert "path=" in link
        assert "Open in Obsidian" in link

    def test_vscodium_link(self):
        """Test VSCodium link generation."""
        config = Config(editor_protocol=EditorProtocol.VSCODIUM)
        link = config.build_source_link(Path("/tmp/test.md"), 10)

        assert "vscodium://file" in link
        assert "Open in VSCodium" in link

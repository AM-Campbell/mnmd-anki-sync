"""Tests for CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mnmd_anki_sync import __version__
from mnmd_anki_sync.cli import app
from mnmd_anki_sync.config import EditorProtocol


runner = CliRunner()


class TestVersionCommand:
    """Test version command."""

    def test_version_shows_version(self):
        """Test version command shows version string."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert __version__ in result.output
        assert "mnmd-anki-sync" in result.output


class TestValidateCommand:
    """Test validate command."""

    def test_validate_file_with_clozes(self):
        """Test validating a file with valid clozes."""
        content = """> ?
The capital of France is {{Paris}}.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["validate", file_path])

        assert result.exit_code == 0
        assert "Validating" in result.output
        assert "Card Contexts" in result.output
        assert "Total Clozes" in result.output
        assert "valid" in result.output.lower()

    def test_validate_file_without_contexts(self):
        """Test validating a file without card contexts."""
        content = "Just regular markdown without > ? blocks."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["validate", file_path])

        assert result.exit_code == 0
        assert "No card contexts found" in result.output

    def test_validate_multiple_files(self):
        """Test validating multiple files."""
        content1 = """> ?
{{Answer1}}
"""
        content2 = """> ?
{{Answer2}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f1:
            f1.write(content1)
            f1.flush()
            file_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f2:
            f2.write(content2)
            f2.flush()
            file_path2 = f2.name

        result = runner.invoke(app, ["validate", file_path1, file_path2])

        assert result.exit_code == 0
        assert "Validating" in result.output

    def test_validate_nonexistent_file(self):
        """Test validating a nonexistent file."""
        result = runner.invoke(app, ["validate", "/nonexistent/file.md"])

        # Typer will catch this before our code runs
        assert result.exit_code != 0


class TestSyncCommand:
    """Test sync command."""

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_basic(self, mock_config, mock_syncer_class):
        """Test basic sync command."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 1, "updated": 0, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path])

        assert result.exit_code == 0
        assert "Sync complete" in result.output
        mock_syncer.sync_file.assert_called_once()

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_with_deck_option(self, mock_config, mock_syncer_class):
        """Test sync with deck override."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 1, "updated": 0, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--deck", "CustomDeck"])

        assert result.exit_code == 0
        call_args = mock_syncer.sync_file.call_args
        assert call_args[1]["deck_name"] == "CustomDeck"

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_with_tags_option(self, mock_config, mock_syncer_class):
        """Test sync with tags override."""
        config_obj = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_config.return_value = config_obj
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 0, "updated": 0, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--tags", "tag1, tag2"])

        assert result.exit_code == 0
        # Tags should be parsed and set on config
        assert config_obj.default_tags == ["tag1", "tag2"]

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_with_editor_option(self, mock_config, mock_syncer_class):
        """Test sync with editor protocol override."""
        config_obj = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_config.return_value = config_obj
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 0, "updated": 0, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--editor", "nvim"])

        assert result.exit_code == 0
        assert config_obj.editor_protocol == EditorProtocol.NVIM

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_with_anki_url_option(self, mock_config, mock_syncer_class):
        """Test sync with custom anki URL."""
        config_obj = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_config.return_value = config_obj
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 0, "updated": 0, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--anki-url", "http://remote:9999"])

        assert result.exit_code == 0
        assert config_obj.anki_url == "http://remote:9999"

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_error_handling(self, mock_config, mock_syncer_class):
        """Test sync handles errors gracefully."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_syncer = MagicMock()
        mock_syncer.sync_file.side_effect = Exception("Connection failed")
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path])

        assert result.exit_code == 1
        assert "Error" in result.output


class TestDryRunMode:
    """Test dry-run mode."""

    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_dry_run_shows_preview(self, mock_config):
        """Test dry run shows preview without syncing."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )

        content = """> ?
The capital of France is {{Paris}}.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Create" in result.output or "would be created" in result.output

    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_dry_run_shows_existing_notes(self, mock_config):
        """Test dry run shows existing notes as updates."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )

        # Content with an existing anki ID
        content = """> ?
The answer is {{abcdef>Paris}}.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Update" in result.output or "would be updated" in result.output

    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_dry_run_no_contexts(self, mock_config):
        """Test dry run with no card contexts."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )

        content = "Regular markdown without any clozes."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--dry-run"])

        assert result.exit_code == 0
        assert "No card contexts" in result.output

    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_dry_run_with_deck_option(self, mock_config):
        """Test dry run shows custom deck."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = f.name

        result = runner.invoke(app, ["sync", file_path, "--dry-run", "--deck", "MyDeck"])

        assert result.exit_code == 0
        assert "MyDeck" in result.output


class TestSyntaxCommand:
    """Test syntax command."""

    @patch("mnmd_anki_sync.cli.sys.stdout")
    def test_syntax_no_pager(self, mock_stdout):
        """Test syntax command without pager."""
        mock_stdout.isatty.return_value = False

        # Create a syntax file for the test
        syntax_content = "# Syntax Guide\n\nThis is the syntax guide."
        syntax_file = Path(__file__).parent.parent.parent / "src" / "mnmd_anki_sync" / "syntax-notes.md"

        # If file doesn't exist, test should handle gracefully
        if not syntax_file.exists():
            result = runner.invoke(app, ["syntax", "--no-pager"])
            # Should show error about missing file
            assert result.exit_code == 1 or "not found" in result.output.lower() or "Error" in result.output
        else:
            result = runner.invoke(app, ["syntax", "--no-pager"])
            # Should show content
            assert result.exit_code == 0


class TestMultipleFiles:
    """Test handling multiple files."""

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_multiple_files(self, mock_config, mock_syncer_class):
        """Test syncing multiple files."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_syncer = MagicMock()
        mock_syncer.sync_file.return_value = {"created": 1, "updated": 1, "skipped": 0}
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f1:
            f1.write(content)
            f1.flush()
            file_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f2:
            f2.write(content)
            f2.flush()
            file_path2 = f2.name

        result = runner.invoke(app, ["sync", file_path1, file_path2])

        assert result.exit_code == 0
        assert mock_syncer.sync_file.call_count == 2
        # Total should be aggregated
        assert "2 created" in result.output
        assert "2 updated" in result.output

    @patch("mnmd_anki_sync.cli.Syncer")
    @patch("mnmd_anki_sync.cli.Config.load_default")
    def test_sync_multiple_files_partial_failure(self, mock_config, mock_syncer_class):
        """Test syncing multiple files where one fails."""
        mock_config.return_value = MagicMock(
            editor_protocol=EditorProtocol.VSCODE,
            anki_url="http://localhost:8765",
            default_deck="Default",
            default_tags=["mnmd"],
        )
        mock_syncer = MagicMock()

        def sync_side_effect(path, deck_name=None):
            if "fail" in str(path):
                raise Exception("Sync failed")
            return {"created": 1, "updated": 0, "skipped": 0}

        mock_syncer.sync_file.side_effect = sync_side_effect
        mock_syncer_class.return_value = mock_syncer

        content = """> ?
{{Answer}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, prefix="ok_") as f1:
            f1.write(content)
            f1.flush()
            file_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, prefix="fail_") as f2:
            f2.write(content)
            f2.flush()
            file_path2 = f2.name

        result = runner.invoke(app, ["sync", file_path1, file_path2])

        # Should exit with error code when a file fails
        assert result.exit_code == 1 or "Error" in result.output


class TestHelpTexts:
    """Test help text display."""

    def test_main_help(self):
        """Test main help shows commands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "sync" in result.output
        assert "validate" in result.output
        assert "syntax" in result.output
        assert "version" in result.output

    def test_sync_help(self):
        """Test sync command help."""
        result = runner.invoke(app, ["sync", "--help"])

        assert result.exit_code == 0
        # Check for short flags (more reliable with rich formatting)
        assert "-d" in result.output or "deck" in result.output.lower()
        assert "-t" in result.output or "tags" in result.output.lower()
        assert "-e" in result.output or "editor" in result.output.lower()
        assert "dry-run" in result.output.lower()

    def test_validate_help(self):
        """Test validate command help."""
        result = runner.invoke(app, ["validate", "--help"])

        assert result.exit_code == 0
        assert "Markdown files" in result.output

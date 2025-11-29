"""Tests for syncer module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mnmd_anki_sync.config import Config
from mnmd_anki_sync.sync.syncer import Syncer


@pytest.fixture
def mock_client():
    """Create a mock AnkiConnect client."""
    client = MagicMock()
    client.model_names.return_value = ["MNMD Cloze"]
    client.model_templates.return_value = {"MNMD Cloze": {}}
    client.notes_info.return_value = []
    client.find_notes.return_value = []
    client.add_note.return_value = 1234567890
    return client


@pytest.fixture
def config():
    """Create a test config."""
    return Config(default_deck="TestDeck", default_tags=["test"])


@pytest.fixture
def sample_markdown():
    """Create a sample markdown file content."""
    return """> ?
The capital of France is {{Paris}}.
"""


@pytest.fixture
def sample_file(sample_markdown):
    """Create a temporary file with sample content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_markdown)
        f.flush()
        yield Path(f.name)


class TestSyncerInit:
    """Test Syncer initialization."""

    def test_init_with_config(self, config):
        """Test syncer initializes with config."""
        syncer = Syncer(config)

        assert syncer.config == config

    def test_init_creates_client(self, config):
        """Test syncer creates AnkiConnect client."""
        syncer = Syncer(config)

        assert syncer.client is not None
        assert syncer.client.url == config.anki_url


class TestSyncFile:
    """Test sync_file method."""

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_creates_notes(self, mock_write_ids, mock_client_class, config, sample_file):
        """Test syncing creates new notes."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        mock_client.find_notes.return_value = []
        mock_client.add_note.return_value = 1234567890
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(sample_file)

        assert stats["created"] >= 1
        mock_client.add_note.assert_called()

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_updates_existing_notes(self, mock_write_ids, mock_client_class, config):
        """Test syncing updates existing notes."""
        # Create file with existing Anki ID
        content = """> ?
The answer is {{abcdef>42}}.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        # Simulate note exists
        mock_client.notes_info.return_value = [{"noteId": 123}]
        mock_client.find_notes.return_value = []
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(file_path)

        assert stats["updated"] >= 1
        mock_client.update_note_fields.assert_called()

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_with_deck_override(self, mock_write_ids, mock_client_class, config, sample_file):
        """Test syncing with deck name override."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        mock_client.find_notes.return_value = []
        mock_client.add_note.return_value = 1234567890
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        syncer.sync_file(sample_file, deck_name="CustomDeck")

        call_args = mock_client.add_note.call_args
        assert call_args[1]["deck_name"] == "CustomDeck"

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_no_clozes_returns_zero_stats(self, mock_write_ids, mock_client_class, config):
        """Test syncing file with no clozes."""
        content = """> ?
No clozes here.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(file_path)

        assert stats["created"] == 0
        assert stats["updated"] == 0

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_no_contexts_returns_zero_stats(self, mock_write_ids, mock_client_class, config):
        """Test syncing file with no card contexts."""
        content = "Just regular markdown without > ? blocks."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(file_path)

        assert stats["created"] == 0
        assert stats["updated"] == 0

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_deletes_orphaned_notes(self, mock_write_ids, mock_client_class, config, sample_file):
        """Test syncing deletes orphaned notes."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        # Simulate orphaned note exists in Anki
        mock_client.find_notes.return_value = [999999]
        mock_client.add_note.return_value = 1234567890
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(sample_file)

        # Should delete the orphaned note
        assert stats["deleted"] == 1
        mock_client.delete_notes.assert_called_with([999999])

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_adds_file_tag(self, mock_write_ids, mock_client_class, config, sample_file):
        """Test syncing adds file tag to notes."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        mock_client.find_notes.return_value = []
        mock_client.add_note.return_value = 1234567890
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        syncer.sync_file(sample_file)

        # Check tags include file tag
        call_args = mock_client.add_note.call_args
        tags = call_args[1]["tags"]
        assert any(tag.startswith("mnmd-file-") for tag in tags)


class TestSyncerErrorHandling:
    """Test syncer error handling."""

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_handles_add_note_failure(self, mock_write_ids, mock_client_class, config, sample_file):
        """Test syncing handles note creation failure."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        mock_client.find_notes.return_value = []
        mock_client.add_note.side_effect = Exception("Failed to add note")
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        stats = syncer.sync_file(sample_file)

        # Should mark as skipped
        assert stats["skipped"] >= 1

    @patch("mnmd_anki_sync.sync.syncer.AnkiConnectClient")
    @patch("mnmd_anki_sync.sync.syncer.write_ids_to_file")
    def test_sync_handles_invalid_anki_id(self, mock_write_ids, mock_client_class, config):
        """Test syncing handles invalid Anki ID gracefully."""
        # Anki ID with numbers (invalid base52)
        content = """> ?
The answer is {{abc123>42}}.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}
        mock_client.notes_info.return_value = []
        mock_client.find_notes.return_value = []
        mock_client.add_note.return_value = 1234567890
        mock_client_class.return_value = mock_client

        syncer = Syncer(config)
        # Should not raise an error - invalid ID is ignored
        stats = syncer.sync_file(file_path)

        # Should create a new note since the ID is invalid
        assert stats["created"] >= 1

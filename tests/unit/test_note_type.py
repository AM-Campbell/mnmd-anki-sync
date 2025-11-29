"""Tests for note type module."""

from unittest.mock import MagicMock

import pytest

from mnmd_anki_sync.anki.note_type import (
    CARD_TEMPLATE,
    NOTE_TYPE_CSS,
    NOTE_TYPE_NAME,
    ensure_note_type_exists,
    get_note_type_fields,
)


class TestNoteTypeConstants:
    """Test note type constants."""

    def test_note_type_name(self):
        """Test note type name."""
        assert NOTE_TYPE_NAME == "MNMD Cloze"

    def test_note_type_css_not_empty(self):
        """Test CSS is not empty."""
        assert len(NOTE_TYPE_CSS) > 0
        assert ".card" in NOTE_TYPE_CSS

    def test_card_template_has_required_keys(self):
        """Test card template has required keys."""
        assert "Name" in CARD_TEMPLATE
        assert "Front" in CARD_TEMPLATE
        assert "Back" in CARD_TEMPLATE

    def test_card_template_has_cloze(self):
        """Test card template uses cloze syntax."""
        assert "{{cloze:Text}}" in CARD_TEMPLATE["Front"]
        assert "{{cloze:Text}}" in CARD_TEMPLATE["Back"]

    def test_card_template_has_source_on_back(self):
        """Test Source field is only on back."""
        assert "{{Source}}" in CARD_TEMPLATE["Back"]
        assert "{{Source}}" not in CARD_TEMPLATE["Front"]


class TestGetNoteTypeFields:
    """Test get_note_type_fields function."""

    def test_returns_correct_fields(self):
        """Test it returns the correct field names."""
        fields = get_note_type_fields()

        assert fields == ["Text", "Extra", "Source"]

    def test_returns_list(self):
        """Test it returns a list."""
        fields = get_note_type_fields()

        assert isinstance(fields, list)


class TestEnsureNoteTypeExists:
    """Test ensure_note_type_exists function."""

    def test_creates_model_when_not_exists(self):
        """Test model is created when it doesn't exist."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["Basic", "Cloze"]  # No MNMD Cloze

        ensure_note_type_exists(mock_client)

        mock_client.create_model.assert_called_once()
        call_args = mock_client.create_model.call_args
        assert call_args[1]["model_name"] == "MNMD Cloze"
        assert call_args[1]["in_order_fields"] == ["Text", "Extra", "Source"]

    def test_updates_styling_when_exists(self):
        """Test styling is updated when model exists."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["Basic", "MNMD Cloze"]
        mock_client.model_templates.return_value = {"MNMD Cloze": {}}

        ensure_note_type_exists(mock_client)

        mock_client.create_model.assert_not_called()
        mock_client.update_model_styling.assert_called_once_with("MNMD Cloze", NOTE_TYPE_CSS)

    def test_updates_templates_when_exists(self):
        """Test templates are updated when model exists."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {"Card 1": {"Front": "old", "Back": "old"}}

        ensure_note_type_exists(mock_client)

        mock_client.update_model_templates.assert_called_once()
        call_args = mock_client.update_model_templates.call_args
        assert call_args[0][0] == "MNMD Cloze"
        # Should use the actual template name from Anki
        assert "Card 1" in call_args[0][1]

    def test_handles_empty_templates(self):
        """Test handles empty templates dictionary gracefully."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = {}  # Empty

        ensure_note_type_exists(mock_client)

        # Should not call update_model_templates if no templates
        mock_client.update_model_templates.assert_not_called()

    def test_handles_none_templates(self):
        """Test handles None templates gracefully."""
        mock_client = MagicMock()
        mock_client.model_names.return_value = ["MNMD Cloze"]
        mock_client.model_templates.return_value = None

        ensure_note_type_exists(mock_client)

        # Should not call update_model_templates if templates is None
        mock_client.update_model_templates.assert_not_called()

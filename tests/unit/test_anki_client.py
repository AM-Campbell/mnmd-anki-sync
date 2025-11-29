"""Tests for AnkiConnect client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from mnmd_anki_sync.anki.client import AnkiConnectClient
from mnmd_anki_sync.utils.exceptions import AnkiAPIError, AnkiConnectionError


class TestAnkiConnectClientInit:
    """Test client initialization."""

    def test_default_url(self):
        """Test default URL is localhost:8765."""
        client = AnkiConnectClient()
        assert client.url == "http://localhost:8765"

    def test_custom_url(self):
        """Test custom URL."""
        client = AnkiConnectClient("http://custom:9999")
        assert client.url == "http://custom:9999"

    def test_version(self):
        """Test version is 6."""
        client = AnkiConnectClient()
        assert client.version == 6


class TestInvoke:
    """Test the invoke method."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_success(self, mock_post):
        """Test successful invoke."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": "success"}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.invoke("testAction", {"param": "value"})

        assert result == "success"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["action"] == "testAction"
        assert call_args[1]["json"]["params"] == {"param": "value"}
        assert call_args[1]["json"]["version"] == 6

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_no_params(self, mock_post):
        """Test invoke without params."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": "ok"}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.invoke("testAction")

        assert result == "ok"
        call_args = mock_post.call_args
        assert "params" not in call_args[1]["json"]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_connection_error(self, mock_post):
        """Test invoke raises AnkiConnectionError on connection failure."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed")

        client = AnkiConnectClient()

        with pytest.raises(AnkiConnectionError) as exc_info:
            client.invoke("testAction")

        assert "Cannot connect to AnkiConnect" in str(exc_info.value)

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_request_error(self, mock_post):
        """Test invoke raises AnkiConnectionError on request failure."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        client = AnkiConnectClient()

        with pytest.raises(AnkiConnectionError) as exc_info:
            client.invoke("testAction")

        assert "Request to AnkiConnect failed" in str(exc_info.value)

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_api_error(self, mock_post):
        """Test invoke raises AnkiAPIError on API error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Note was not found", "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()

        with pytest.raises(AnkiAPIError) as exc_info:
            client.invoke("testAction")

        assert "Note was not found" in str(exc_info.value)

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_invoke_invalid_response(self, mock_post):
        """Test invoke raises AnkiAPIError on invalid response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"only_one_key": "value"}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()

        with pytest.raises(AnkiAPIError) as exc_info:
            client.invoke("testAction")

        assert "Invalid response" in str(exc_info.value)


class TestAddNote:
    """Test add_note method."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_add_note(self, mock_post):
        """Test adding a note."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": 1234567890}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.add_note(
            deck_name="TestDeck",
            model_name="Basic",
            fields={"Front": "Question", "Back": "Answer"},
            tags=["test", "mnmd"],
        )

        assert result == 1234567890
        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "addNote"
        assert call_args["params"]["note"]["deckName"] == "TestDeck"
        assert call_args["params"]["note"]["modelName"] == "Basic"
        assert call_args["params"]["note"]["fields"]["Front"] == "Question"
        assert call_args["params"]["note"]["tags"] == ["test", "mnmd"]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_add_note_no_tags(self, mock_post):
        """Test adding a note without tags."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": 1234567890}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.add_note(
            deck_name="TestDeck",
            model_name="Basic",
            fields={"Front": "Question"},
        )

        call_args = mock_post.call_args[1]["json"]
        assert call_args["params"]["note"]["tags"] == []


class TestUpdateNoteFields:
    """Test update_note_fields method."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_update_note_fields(self, mock_post):
        """Test updating note fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.update_note_fields(1234567890, {"Front": "New Question"})

        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "updateNoteFields"
        assert call_args["params"]["note"]["id"] == 1234567890
        assert call_args["params"]["note"]["fields"]["Front"] == "New Question"


class TestNotesInfo:
    """Test notes_info method."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_notes_info(self, mock_post):
        """Test getting notes info."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": None,
            "result": [{"noteId": 123, "fields": {}}],
        }
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.notes_info([123])

        assert len(result) == 1
        assert result[0]["noteId"] == 123


class TestFindNotes:
    """Test find_notes method."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_find_notes(self, mock_post):
        """Test finding notes."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": [123, 456, 789]}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.find_notes("tag:test")

        assert result == [123, 456, 789]
        call_args = mock_post.call_args[1]["json"]
        assert call_args["params"]["query"] == "tag:test"


class TestModelMethods:
    """Test model-related methods."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_model_names(self, mock_post):
        """Test getting model names."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": ["Basic", "Cloze"]}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.model_names()

        assert result == ["Basic", "Cloze"]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_model_field_names(self, mock_post):
        """Test getting model field names."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": ["Front", "Back"]}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.model_field_names("Basic")

        assert result == ["Front", "Back"]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_create_model(self, mock_post):
        """Test creating a model."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": {"id": 123}}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.create_model(
            model_name="TestModel",
            in_order_fields=["Front", "Back"],
            card_templates=[{"Name": "Card 1", "Front": "{{Front}}", "Back": "{{Back}}"}],
            css=".card { color: blue; }",
        )

        assert result == {"id": 123}
        call_args = mock_post.call_args[1]["json"]
        assert call_args["params"]["modelName"] == "TestModel"

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_model_templates(self, mock_post):
        """Test getting model templates."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": None,
            "result": {"Card 1": {"Front": "{{Front}}", "Back": "{{Back}}"}},
        }
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.model_templates("Basic")

        assert "Card 1" in result

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_update_model_styling(self, mock_post):
        """Test updating model styling."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.update_model_styling("Basic", ".card { color: red; }")

        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "updateModelStyling"
        assert call_args["params"]["model"]["name"] == "Basic"

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_update_model_templates(self, mock_post):
        """Test updating model templates."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.update_model_templates(
            "Basic", {"Card 1": {"Front": "New {{Front}}", "Back": "New {{Back}}"}}
        )

        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "updateModelTemplates"


class TestDeckMethods:
    """Test deck-related methods."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_deck_names(self, mock_post):
        """Test getting deck names."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": ["Default", "Test"]}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.deck_names()

        assert result == ["Default", "Test"]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_create_deck(self, mock_post):
        """Test creating a deck."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": 1234567890}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        result = client.create_deck("NewDeck")

        assert result == 1234567890


class TestDeleteAndTagMethods:
    """Test delete and tag methods."""

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_delete_notes(self, mock_post):
        """Test deleting notes."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.delete_notes([123, 456])

        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "deleteNotes"
        assert call_args["params"]["notes"] == [123, 456]

    @patch("mnmd_anki_sync.anki.client.requests.post")
    def test_add_tags(self, mock_post):
        """Test adding tags."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": None, "result": None}
        mock_post.return_value = mock_response

        client = AnkiConnectClient()
        client.add_tags([123, 456], "test-tag")

        call_args = mock_post.call_args[1]["json"]
        assert call_args["action"] == "addTags"
        assert call_args["params"]["notes"] == [123, 456]
        assert call_args["params"]["tags"] == "test-tag"

"""AnkiConnect client for communicating with Anki."""

from typing import Any, Dict, List, Optional

import requests

from ..utils.exceptions import AnkiAPIError, AnkiConnectionError


class AnkiConnectClient:
    """Client for AnkiConnect API."""

    def __init__(self, url: str = "http://localhost:8765") -> None:
        """Initialize AnkiConnect client.

        Args:
            url: AnkiConnect URL
        """
        self.url = url
        self.version = 6

    def invoke(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Invoke an AnkiConnect action.

        Args:
            action: The action to invoke
            params: Parameters for the action

        Returns:
            The result from AnkiConnect

        Raises:
            AnkiConnectionError: Cannot connect to AnkiConnect
            AnkiAPIError: AnkiConnect returned an error
        """
        payload = {"action": action, "version": self.version}
        if params is not None:
            payload["params"] = params

        try:
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise AnkiConnectionError(
                f"Cannot connect to AnkiConnect at {self.url}. "
                "Make sure Anki is running with AnkiConnect installed."
            ) from e
        except requests.exceptions.RequestException as e:
            raise AnkiConnectionError(f"Request to AnkiConnect failed: {e}") from e

        result = response.json()

        if len(result) != 2:
            raise AnkiAPIError(f"Invalid response from AnkiConnect: {result}")

        if result["error"] is not None:
            raise AnkiAPIError(f"AnkiConnect error: {result['error']}")

        return result["result"]

    def add_note(
        self,
        deck_name: str,
        model_name: str,
        fields: Dict[str, str],
        tags: Optional[List[str]] = None,
    ) -> int:
        """Add a note to Anki.

        Args:
            deck_name: Target deck name
            model_name: Note type name
            fields: Field name to value mapping
            tags: Optional list of tags

        Returns:
            Note ID

        Raises:
            AnkiAPIError: If note creation fails
        """
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or [],
        }

        return self.invoke("addNote", {"note": note})

    def update_note_fields(self, note_id: int, fields: Dict[str, str]) -> None:
        """Update fields of an existing note.

        Args:
            note_id: The note ID to update
            fields: Field name to value mapping

        Raises:
            AnkiAPIError: If update fails
        """
        note = {"id": note_id, "fields": fields}
        self.invoke("updateNoteFields", {"note": note})

    def notes_info(self, note_ids: List[int]) -> List[Dict[str, Any]]:
        """Get information about notes.

        Args:
            note_ids: List of note IDs

        Returns:
            List of note info dictionaries

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("notesInfo", {"notes": note_ids})

    def find_notes(self, query: str) -> List[int]:
        """Find notes matching a query.

        Args:
            query: Anki search query

        Returns:
            List of note IDs

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("findNotes", {"query": query})

    def model_names(self) -> List[str]:
        """Get all model (note type) names.

        Returns:
            List of model names

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("modelNames")

    def model_field_names(self, model_name: str) -> List[str]:
        """Get field names for a model.

        Args:
            model_name: The model name

        Returns:
            List of field names

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("modelFieldNames", {"modelName": model_name})

    def create_model(
        self,
        model_name: str,
        in_order_fields: List[str],
        card_templates: List[Dict[str, str]],
        css: str = "",
    ) -> Dict[str, Any]:
        """Create a new model (note type).

        Args:
            model_name: Name for the new model
            in_order_fields: List of field names in order
            card_templates: List of card templates with 'Name', 'Front', 'Back'
            css: CSS styling for cards

        Returns:
            Model information

        Raises:
            AnkiAPIError: If creation fails
        """
        model = {
            "modelName": model_name,
            "inOrderFields": in_order_fields,
            "css": css,
            "cardTemplates": card_templates,
        }
        return self.invoke("createModel", model)

    def deck_names(self) -> List[str]:
        """Get all deck names.

        Returns:
            List of deck names

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("deckNames")

    def create_deck(self, deck_name: str) -> int:
        """Create a new deck.

        Args:
            deck_name: Name for the new deck

        Returns:
            Deck ID

        Raises:
            AnkiAPIError: If creation fails
        """
        return self.invoke("createDeck", {"deck": deck_name})

    def delete_notes(self, note_ids: List[int]) -> None:
        """Delete notes from Anki.

        Args:
            note_ids: List of note IDs to delete

        Raises:
            AnkiAPIError: If deletion fails
        """
        self.invoke("deleteNotes", {"notes": note_ids})

    def add_tags(self, note_ids: List[int], tags: str) -> None:
        """Add tags to notes.

        Args:
            note_ids: List of note IDs
            tags: Space-separated tag string

        Raises:
            AnkiAPIError: If operation fails
        """
        self.invoke("addTags", {"notes": note_ids, "tags": tags})

    def update_model_styling(self, model_name: str, css: str) -> None:
        """Update the CSS styling for a model.

        Args:
            model_name: The model name
            css: New CSS styling

        Raises:
            AnkiAPIError: If update fails
        """
        self.invoke("updateModelStyling", {"model": {"name": model_name, "css": css}})

    def update_model_templates(self, model_name: str, templates: Dict[str, Dict[str, str]]) -> None:
        """Update the card templates for a model.

        Args:
            model_name: The model name
            templates: Dict mapping template name to {"Front": ..., "Back": ...}

        Raises:
            AnkiAPIError: If update fails
        """
        self.invoke(
            "updateModelTemplates",
            {"model": {"name": model_name, "templates": templates}},
        )

    def model_templates(self, model_name: str) -> Dict[str, Any]:
        """Get the templates for a model.

        Args:
            model_name: The model name

        Returns:
            Dict with template information

        Raises:
            AnkiAPIError: If query fails
        """
        return self.invoke("modelTemplates", {"modelName": model_name})

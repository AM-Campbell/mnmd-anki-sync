"""MNMD Cloze note type for Anki."""

from typing import List

from .client import AnkiConnectClient

NOTE_TYPE_NAME = "MNMD Cloze"

# CSS for MNMD Cloze cards
NOTE_TYPE_CSS = """
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}

.cloze {
    font-weight: bold;
    color: blue;
}

.nightMode .card {
    color: white;
    background-color: #2f2f31;
}

.source {
    font-size: 12px;
    color: #888;
    margin-top: 20px;
}

.nightMode .source {
    color: #aaa;
}

.extra {
    font-size: 12px;
    color: #666;
    margin-top: 20px;
    border-top: 1px solid #ccc;
    padding-top: 15px;
}

.nightMode .extra {
    color: #999;
    border-top-color: #555;
}

/* Lists */
ul, ol {
    text-align: left;
    display: inline-block;
}

/* Code blocks */
code {
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: monospace;
}

.nightMode code {
    background-color: #444;
}

pre {
    background-color: #f4f4f4;
    padding: 10px;
    border-radius: 5px;
    text-align: left;
    overflow-x: auto;
}

.nightMode pre {
    background-color: #444;
}

/* Images */
img {
    max-width: 100%;
    height: auto;
}
"""

# Card template
CARD_TEMPLATE = {
    "Name": "MNMD Cloze",
    "Front": """
{{cloze:Text}}

{{#Extra}}
<div class="extra">{{Extra}}</div>
{{/Extra}}
""",
    "Back": """
{{cloze:Text}}

{{#Extra}}
<div class="extra">{{Extra}}</div>
{{/Extra}}

{{#Source}}
<div class="source">{{Source}}</div>
{{/Source}}
""",
}


def ensure_note_type_exists(client: AnkiConnectClient) -> None:
    """Ensure MNMD Cloze note type exists in Anki with correct styling.

    Creates the note type if it doesn't exist, or updates the styling
    and templates if it does exist.

    Args:
        client: AnkiConnect client

    Raises:
        AnkiAPIError: If note type creation/update fails
    """
    existing_models = client.model_names()

    if NOTE_TYPE_NAME not in existing_models:
        # Create the note type
        fields = ["Text", "Extra", "Source"]
        client.create_model(
            model_name=NOTE_TYPE_NAME,
            in_order_fields=fields,
            card_templates=[CARD_TEMPLATE],
            css=NOTE_TYPE_CSS,
        )
    else:
        # Update existing note type styling and templates
        client.update_model_styling(NOTE_TYPE_NAME, NOTE_TYPE_CSS)

        # Get the actual template name from Anki (may differ from what we wanted)
        existing_templates = client.model_templates(NOTE_TYPE_NAME)
        if existing_templates:
            # Use the first (and likely only) template name
            template_name = list(existing_templates.keys())[0]
            client.update_model_templates(
                NOTE_TYPE_NAME,
                {
                    template_name: {
                        "Front": CARD_TEMPLATE["Front"],
                        "Back": CARD_TEMPLATE["Back"],
                    }
                },
            )


def get_note_type_fields() -> List[str]:
    """Get the field names for MNMD Cloze note type.

    Returns:
        List of field names
    """
    return ["Text", "Extra", "Source"]

"""Build Anki notes from prompts."""

from typing import Dict

from ..config import Config
from ..models import Prompt


def build_note_fields(prompt: Prompt, config: Config) -> Dict[str, str]:
    """Build Anki note fields from a prompt.

    Args:
        prompt: The prompt to convert
        config: Configuration with editor protocol

    Returns:
        Dictionary of field names to values
    """
    # Convert prompt to Anki cloze format (includes HTML conversion)
    text_field = prompt.to_anki_cloze_text()

    # Build extra field if present
    extra_field = ""
    if prompt.cloze_match.extra:
        extra_field = prompt.cloze_match.extra

    # Build source link
    source_link = config.build_source_link(prompt.file_path, prompt.line_number)

    return {
        "Text": text_field,
        "Extra": extra_field,
        "Source": source_link,
    }

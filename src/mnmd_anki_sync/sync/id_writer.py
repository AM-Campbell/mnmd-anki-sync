"""Write Anki IDs back to markdown files."""

import re
from pathlib import Path
from typing import List, Tuple

from ..models import Prompt


def write_ids_to_file(file_path: Path, prompts: List[Prompt]) -> None:
    """Write Anki IDs back to markdown file.

    Updates cloze patterns in place with Anki IDs while preserving formatting.

    Args:
        file_path: Path to markdown file
        prompts: List of prompts with Anki IDs

    Example:
        {{answer}} -> {{abcXYZ>answer}}
        {{1>answer}} -> {{1,abcXYZ>answer}}
        {{1.2>answer}} -> {{1.2,abcXYZ>answer}}
    """
    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build updates list with positions: [(position, old_text, new_text), ...]
    updates: List[Tuple[int, str, str]] = []
    for prompt in prompts:
        # For grouped clozes, write IDs for all clozes in the group
        clozes_to_update = prompt.group_clozes if prompt.group_clozes else [prompt.cloze_match]

        for cloze in clozes_to_update:
            # Skip if no Anki ID
            if not cloze.anki_id:
                continue

            # Skip if Anki ID already written (check if it appears before '>')
            # Parse the IDs portion (everything between {{ and > if present)
            if ">" in cloze.full_text:
                ids_portion = cloze.full_text.split(">", 1)[0].replace("{{", "")
                if cloze.anki_id in ids_portion:
                    continue  # Already has this Anki ID
            else:
                # Basic cloze without group ID - check if ankiID is at start
                if cloze.full_text.startswith("{{" + cloze.anki_id + ">"):
                    continue  # Already has this Anki ID

            # Build new cloze text with Anki ID
            old_text = cloze.full_text

            # Parse the existing IDs part
            if cloze.cloze_id and cloze.sequence_order is not None:
                # Sequence cloze: {{id.order>text}} -> {{id.order,ankiID>text}}
                new_ids = f"{cloze.cloze_id}.{cloze.sequence_order},{cloze.anki_id}"
            elif cloze.cloze_id:
                # Grouped cloze: {{id>text}} -> {{id,ankiID>text}}
                new_ids = f"{cloze.cloze_id},{cloze.anki_id}"
            else:
                # Basic cloze: {{text}} -> {{ankiID>text}}
                new_ids = cloze.anki_id

            # Extract content after > (use DOTALL for reflowed clozes spanning lines)
            match = re.match(r"\{\{(?:[^>]+>)?(.+?)\}\}", old_text, re.DOTALL)
            if not match:
                continue

            content_part = match.group(1)

            # Build new text
            new_text = f"{{{{{new_ids}>{content_part}}}}}"

            # Check for scope specification
            scope_match = re.search(r"\}\}(\[-?\d+(?:,\s*-?\d+)?\])$", old_text)
            if scope_match:
                new_text += scope_match.group(1)

            # Store with position for proper ordering
            updates.append((cloze.start, old_text, new_text))

    # Apply updates
    if not updates:
        return

    # Sort by position in REVERSE order to preserve positions during replacement
    updates.sort(key=lambda x: x[0], reverse=True)

    # Apply replacements from end to start to preserve positions
    updated_content = content
    for _position, old_text, new_text in updates:
        updated_content = updated_content.replace(old_text, new_text, 1)

    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        # Atomic replace
        temp_path.replace(file_path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise

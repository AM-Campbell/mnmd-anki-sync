"""Generate and manage stable file IDs for tracking card ownership."""

import re
import secrets
from pathlib import Path
from typing import Optional, Tuple


def generate_file_id() -> str:
    """Generate a new random file ID.

    The file ID is used to tag Anki cards with their source file,
    enabling safe deletion when cards are removed from the markdown.

    Returns:
        A short, random identifier (8 alphanumeric characters)

    Example:
        >>> generate_file_id()
        'a3f4c2d1'
    """
    # Generate 8 character random ID using url-safe characters
    return secrets.token_urlsafe(6)[:8]


def extract_file_id(content: str) -> Optional[str]:
    """Extract file ID from markdown YAML frontmatter.

    Args:
        content: Markdown file content

    Returns:
        File ID if found, None otherwise

    Example:
        >>> extract_file_id("---\\nmnmd_file_id: abc123xy\\n---\\n# Content")
        'abc123xy'
    """
    # Match YAML frontmatter
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return None

    frontmatter = match.group(1)

    # Extract mnmd_file_id
    id_pattern = r"mnmd_file_id:\s*([a-zA-Z0-9_-]+)"
    id_match = re.search(id_pattern, frontmatter)

    if id_match:
        return id_match.group(1)

    return None


def ensure_file_id(file_path: Path) -> Tuple[str, bool]:
    """Ensure file has a stable ID in frontmatter.

    Reads the file, extracts or generates an ID, and writes it back if needed.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (file_id, was_modified)
        - file_id: The file's stable ID
        - was_modified: True if the file was updated with a new ID

    Example:
        >>> file_id, modified = ensure_file_id(Path("notes.md"))
        >>> print(f"ID: {file_id}, Modified: {modified}")
        ID: abc123xy, Modified: True
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Try to extract existing ID
    existing_id = extract_file_id(content)

    if existing_id:
        return existing_id, False

    # Generate new ID
    new_id = generate_file_id()

    # Add or update frontmatter
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        # Frontmatter exists, add ID to it
        frontmatter = match.group(1)
        updated_frontmatter = f"{frontmatter}\nmnmd_file_id: {new_id}\n"
        updated_content = re.sub(
            frontmatter_pattern,
            f"---\n{updated_frontmatter}---\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # No frontmatter, create it
        updated_content = f"---\nmnmd_file_id: {new_id}\n---\n\n{content}"

    # Write to temp file first, then atomic rename
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        # Atomic replace (POSIX) - on Windows this is best-effort
        temp_path.replace(file_path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise

    return new_id, True


def get_file_tag(file_id: str) -> str:
    """Get the Anki tag for a file ID.

    Args:
        file_id: The file's stable ID

    Returns:
        Tag string in format "mnmd-file-{fileID}"

    Example:
        >>> get_file_tag("abc123xy")
        'mnmd-file-abc123xy'
    """
    return f"mnmd-file-{file_id}"

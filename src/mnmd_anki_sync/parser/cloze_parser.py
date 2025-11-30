"""Parse cloze deletions from text with CORRECT MNMD syntax.

Syntax:
- Basic: {{answer}}
- With hint: {{answer|hint}}
- With extra: {{answer<extra}}
- Combined: {{answer|hint<extra}}
- With group ID: {{id>answer|hint<extra}}
- With sequence: {{id.order>answer|hint<extra}}
- With Anki ID: {{id,ankiID>answer}} or {{ankiID,id>answer}}  (either order)
- With scope: {{answer}}[-1,2]
"""

import re
from typing import List, Optional, Tuple

from ..models import ClozeMatch, ClozeType, ScopeSpec

# New regex pattern: capture structure, then parse content
CLOZE_PATTERN = re.compile(
    r"\{\{"
    r"(?:(?P<ids>[^>{}]+)>)?"  # Optional IDs before > (don't match { or })
    r"(?P<content>.+?)"  # Content (lazy match until }}) - allows nested braces
    r"\}\}"
    r"(?:\[(?P<scope>-?\d+(?:,\s*-?\d+)?)\])?",  # Optional scope
    re.MULTILINE | re.DOTALL,
)


def normalize_whitespace(text: str) -> str:
    """Normalize single newlines to spaces (handles reflowed text).

    Single newlines become spaces, multiple newlines are preserved.

    Args:
        text: Text that may contain single newlines from reflow

    Returns:
        Text with single newlines converted to spaces
    """
    # Replace single newlines (not followed/preceded by another newline) with space
    # First, protect double+ newlines by replacing them with a placeholder
    result = re.sub(r"\n{2,}", "\x00PARA\x00", text)
    # Replace remaining single newlines with space
    result = result.replace("\n", " ")
    # Restore paragraph breaks
    result = result.replace("\x00PARA\x00", "\n\n")
    # Collapse multiple spaces into one
    result = re.sub(r" {2,}", " ", result)
    return result


def parse_content(content_str: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse content into answer, hint, extra.

    Args:
        content_str: The content string (answer|hint<extra)

    Returns:
        (answer, hint, extra)

    Examples:
        "answer" -> ("answer", None, None)
        "answer|hint" -> ("answer", "hint", None)
        "answer<extra" -> ("answer", None, "extra")
        "answer|hint<extra" -> ("answer", "hint", "extra")
        "long\\nanswer" -> ("long answer", None, None)  # single newline normalized
    """
    # Normalize single newlines to spaces (handles reflowed text)
    content_str = normalize_whitespace(content_str)

    answer = content_str
    hint = None
    extra = None

    # Check for extra (after <, runs to end, NO closing >)
    if "<" in content_str:
        before_extra, extra = content_str.split("<", 1)
        content_str = before_extra

    # Check for hint (after |)
    if "|" in content_str:
        answer, hint = content_str.split("|", 1)
    else:
        answer = content_str

    return answer.strip(), hint.strip() if hint else None, extra.strip() if extra else None


def parse_cloze_ids(ids_str: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """Parse IDs into cloze_id, sequence_order, anki_id.

    Rules:
    - Numeric = cloze_id (group ID)
    - Numeric.Numeric = cloze_id.sequence_order
    - Alphabetic = anki_id (base52)
    - Can have comma-separated: id,ankiID or ankiID,id (either order!)

    Args:
        ids_str: The IDs string (e.g., "1", "1.2", "abc", "1,abc", "abc,1")

    Returns:
        (cloze_id, sequence_order, anki_id)

    Examples:
        "1" -> ("1", None, None)
        "1.2" -> ("1", 2, None)
        "abc" -> (None, None, "abc")
        "1,abc" -> ("1", None, "abc")
        "abc,1" -> ("1", None, "abc")
        "1.2,abc" -> ("1", 2, "abc")
    """
    if not ids_str:
        return None, None, None

    cloze_id = None
    sequence_order = None
    anki_id = None

    # Split by comma if present
    parts = [p.strip() for p in ids_str.split(",")]

    for part in parts:
        if "." in part:
            # Sequence: "1.2" -> cloze_id="1", sequence_order=2
            group, order = part.split(".", 1)
            cloze_id = group.strip()
            try:
                sequence_order = int(order.strip())
            except ValueError:
                # Invalid sequence order, skip this part
                sequence_order = None
        elif part.isdigit():
            # Numeric = cloze ID
            cloze_id = part
        elif part.isalpha():
            # Alphabetic = Anki ID
            anki_id = part
        # Ignore anything else (invalid)

    return cloze_id, sequence_order, anki_id


def parse_scope(scope_str: Optional[str], in_list: bool = False) -> ScopeSpec:
    """Parse scope specification.

    Args:
        scope_str: Scope string like "-1", "2", or "-1,2"
        in_list: Whether this cloze is in a list (default scope is [-1])

    Returns:
        ScopeSpec object (returns default on invalid input)

    Examples:
        None (in_list=False) -> ScopeSpec(before=0, after=0)
        None (in_list=True) -> ScopeSpec(before=-1, after=0)
        "-1" -> ScopeSpec(before=-1, after=0)
        "2" -> ScopeSpec(before=0, after=2)
        "-1,2" -> ScopeSpec(before=-1, after=2)
    """
    default = ScopeSpec.list_default() if in_list else ScopeSpec.default()

    if not scope_str:
        return default

    parts = [p.strip() for p in scope_str.split(",")]

    try:
        if len(parts) == 1:
            value = int(parts[0])
            if value < 0:
                # Negative = before
                return ScopeSpec(before=value, after=0)
            else:
                # Positive = after
                return ScopeSpec(before=0, after=value)
        else:
            # Two parts: before, after
            before = int(parts[0])
            after = int(parts[1])
            return ScopeSpec(before=before, after=after)
    except ValueError:
        # Invalid scope spec, return default
        return default


def find_closing_braces(text: str, start: int) -> Optional[int]:
    """Find the position of closing }} for a cloze starting at {{.

    Uses brace counting to handle nested braces in LaTeX math.
    Counts ALL braces (single and double) to properly handle LaTeX.

    Args:
        text: The text to search
        start: Position of the opening {{ (should point to first {)

    Returns:
        Position of the closing }}, or None if not found
    """
    depth = 0
    i = start

    while i < len(text):
        if text[i] == "{":
            depth += 1
            i += 1
        elif text[i] == "}":
            depth -= 1
            # Check if this is the closing }} (need depth 0 and next char is also })
            if depth == 1 and i + 1 < len(text) and text[i + 1] == "}":
                return i
            i += 1
        else:
            i += 1

    return None


def parse_clozes(text: str, start_line: int = 0, in_list: bool = False) -> List[ClozeMatch]:
    """Parse all cloze deletions from text.

    Args:
        text: Text to parse
        start_line: Starting line number (for line_number calculation)
        in_list: Whether text is in a list context (affects default scope)

    Returns:
        List of ClozeMatch objects
    """
    matches = []
    i = 0

    while i < len(text) - 1:
        # Look for opening {{
        if text[i : i + 2] != "{{":
            i += 1
            continue

        # Find matching }}
        start_pos = i
        end_pos = find_closing_braces(text, i)

        if end_pos is None:
            i += 1
            continue

        # Extract the full cloze text
        full_text = text[start_pos : end_pos + 2]
        content_with_ids = text[start_pos + 2 : end_pos]

        # Check for scope after }}
        scope_str = None
        scope_end = end_pos + 2
        if end_pos + 2 < len(text) and text[end_pos + 2] == "[":
            scope_match = re.match(r"\[(-?\d+(?:,\s*-?\d+)?)\]", text[end_pos + 2 :])
            if scope_match:
                scope_str = scope_match.group(1)
                scope_end = end_pos + 2 + len(scope_match.group(0))
                full_text = text[start_pos:scope_end]

        # Parse IDs (before >)
        ids = None
        content = content_with_ids
        if ">" in content_with_ids:
            # Split at first > only if it's not in nested braces
            # For simplicity, assume > always separates IDs
            parts = content_with_ids.split(">", 1)
            if len(parts) == 2:
                ids = parts[0]
                content = parts[1]

        # Parse content into answer, hint, extra
        answer, hint, extra = parse_content(content)

        # Skip clozes with empty answers
        if not answer:
            i = scope_end
            continue

        # Parse IDs
        cloze_id, sequence_order, anki_id = parse_cloze_ids(ids) if ids else (None, None, None)

        # Determine cloze type
        if sequence_order is not None:
            cloze_type = ClozeType.SEQUENCE
        elif cloze_id is not None:
            cloze_type = ClozeType.GROUPED
        else:
            cloze_type = ClozeType.BASIC

        # Parse scope
        scope = parse_scope(scope_str, in_list)

        # Calculate line number
        lines_before = text[:start_pos].count("\n")
        line_number = start_line + lines_before

        cloze_match = ClozeMatch(
            full_text=full_text,
            start=start_pos,
            end=scope_end,
            cloze_id=cloze_id,
            sequence_order=sequence_order,
            anki_id=anki_id,
            answer=answer,
            hint=hint,
            extra=extra,
            scope=scope,
            cloze_type=cloze_type,
            line_number=line_number,
        )

        matches.append(cloze_match)

        # Move past this cloze
        i = scope_end

    return matches

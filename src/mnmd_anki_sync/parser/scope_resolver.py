"""Resolve paragraph scope for cloze contexts."""

from typing import List, Tuple

from ..models import ScopeSpec


def get_paragraph_boundaries(text: str) -> List[Tuple[int, int]]:
    """Find all paragraph boundaries in text.

    A paragraph is a sequence of non-empty lines separated by empty lines.

    Args:
        text: The text to analyze

    Returns:
        List of (start_line, end_line) tuples for each paragraph

    Examples:
        >>> text = "Para 1.\\n\\nPara 2.\\n\\nPara 3."
        >>> boundaries = get_paragraph_boundaries(text)
        >>> len(boundaries)
        3
        >>> boundaries[0]
        (0, 0)
        >>> boundaries[1]
        (2, 2)
    """
    lines = text.split("\n")
    paragraphs = []
    current_para_start = None
    current_para_end = None

    for i, line in enumerate(lines):
        if line.strip():  # Non-empty line
            if current_para_start is None:
                current_para_start = i
            current_para_end = i
        else:  # Empty line
            if current_para_start is not None:
                paragraphs.append((current_para_start, current_para_end))
                current_para_start = None
                current_para_end = None

    # Handle last paragraph
    if current_para_start is not None:
        paragraphs.append((current_para_start, current_para_end))

    return paragraphs


def resolve_context_scope(text: str, cloze_line: int, scope: ScopeSpec) -> str:
    """Get the context text for a cloze based on its scope specification.

    Args:
        text: The full card context text
        cloze_line: Line number where the cloze appears (relative to text)
        scope: Scope specification

    Returns:
        Context text with appropriate paragraphs included

    Examples:
        >>> text = "Para 1.\\n\\nPara 2 with cloze.\\n\\nPara 3."
        >>> resolve_context_scope(text, 2, ScopeSpec(0, 0))
        'Para 2 with cloze.'
        >>> resolve_context_scope(text, 2, ScopeSpec(-1, 0))
        'Para 1.\\n\\nPara 2 with cloze.'
    """
    lines = text.split("\n")
    paragraphs = get_paragraph_boundaries(text)

    if not paragraphs:
        return text

    # Find which paragraph contains the cloze
    cloze_para_idx = None
    for i, (start, end) in enumerate(paragraphs):
        if start <= cloze_line <= end:
            cloze_para_idx = i
            break

    if cloze_para_idx is None:
        # Cloze not in a paragraph (shouldn't happen), return full text
        return text

    # Calculate paragraph range
    # scope.before is negative or 0, scope.after is positive or 0
    start_para = max(0, cloze_para_idx + scope.before)
    end_para = min(len(paragraphs) - 1, cloze_para_idx + scope.after)

    # Extract lines from paragraph range
    start_line = paragraphs[start_para][0]
    end_line = paragraphs[end_para][1]

    return "\n".join(lines[start_line : end_line + 1])

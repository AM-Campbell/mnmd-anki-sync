"""Extract card contexts from markdown.

Card contexts can be:
1. Explicit `> ?` blocks (custom context boundaries)
2. Regular paragraphs containing clozes (default: paragraph as context)
"""

import re
from typing import List, Set

from ..models import CardContext


def extract_card_contexts(markdown_text: str) -> List[CardContext]:
    """Extract all card contexts from markdown.

    Extracts two types of contexts:
    1. Explicit `> ?` blocks - custom context boundaries
    2. Regular paragraphs with clozes - automatic paragraph-based context

    Args:
        markdown_text: The markdown content to parse

    Returns:
        List of CardContext objects

    Examples:
        >>> text = "> ?\\n> My favorite is {{Python}}.\\n"
        >>> contexts = extract_card_contexts(text)
        >>> len(contexts)
        1

        >>> text = "The capital of France is {{Paris}}.\\n\\nThe capital of Spain is {{Madrid}}."
        >>> contexts = extract_card_contexts(text)
        >>> len(contexts)
        2
    """
    contexts = []

    # Step 1: Extract explicit > ? blocks
    explicit_contexts, explicit_line_ranges = _extract_explicit_contexts(markdown_text)
    contexts.extend(explicit_contexts)

    # Step 2: Extract paragraphs with clozes (excluding lines in explicit blocks)
    paragraph_contexts = _extract_paragraph_contexts(markdown_text, explicit_line_ranges)
    contexts.extend(paragraph_contexts)

    # Sort by line number to maintain document order
    contexts.sort(key=lambda c: c.start_line)

    return contexts


def _extract_explicit_contexts(markdown_text: str) -> tuple[List[CardContext], Set[int]]:
    """Extract > ? block contexts and return used line numbers."""
    lines = markdown_text.split("\n")
    contexts = []
    used_lines = set()
    in_context = False
    context_start = None
    context_lines = []
    line_numbers = []

    for i, line in enumerate(lines):
        if line.strip() == "> ?":
            # Start of card context
            in_context = True
            context_start = i
            context_lines = [line]
            line_numbers = [i]
            used_lines.add(i)
        elif in_context:
            if line.startswith(">"):
                # Continue card context
                context_lines.append(line)
                line_numbers.append(i)
                used_lines.add(i)
            else:
                # End of card context
                if context_lines:
                    context = _create_explicit_context(context_lines, context_start, i - 1, line_numbers)
                    contexts.append(context)
                in_context = False
                context_start = None
                context_lines = []
                line_numbers = []

    # Handle context at end of file
    if in_context and context_lines:
        context = _create_explicit_context(context_lines, context_start, len(lines) - 1, line_numbers)
        contexts.append(context)

    return contexts, used_lines


def _extract_paragraph_contexts(markdown_text: str, exclude_lines: Set[int]) -> List[CardContext]:
    """Extract paragraph contexts containing clozes.

    Paragraphs are separated by blank lines (\\n\\n).
    Only includes paragraphs that contain cloze syntax {{...}}.
    """
    contexts = []
    lines = markdown_text.split("\n")

    # Find paragraph boundaries
    paragraphs = []
    current_para = []
    current_start = 0

    for i, line in enumerate(lines):
        if i in exclude_lines:
            # Skip lines that are part of explicit > ? blocks
            if current_para:
                paragraphs.append((current_para, current_start, i - 1))
                current_para = []
            continue

        if line.strip() == "":
            # Blank line - end current paragraph
            if current_para:
                paragraphs.append((current_para, current_start, i - 1))
                current_para = []
        else:
            if not current_para:
                current_start = i
            current_para.append((line, i))

    # Handle final paragraph
    if current_para:
        paragraphs.append((current_para, current_start, len(lines) - 1))

    # Create contexts for paragraphs containing clozes
    # Use DOTALL to match clozes that span lines (from text reflow)
    cloze_pattern = re.compile(r'\{\{.+?\}\}', re.DOTALL)

    for para_lines, start, end in paragraphs:
        content = "\n".join(line for line, _ in para_lines)

        # Only create context if paragraph contains clozes
        if cloze_pattern.search(content):
            line_nums = [line_num for _, line_num in para_lines]
            context = CardContext(
                content=content,
                full_text=content,  # For paragraphs, content and full_text are same
                start_line=start,
                end_line=end,
                line_numbers=line_nums,
            )
            contexts.append(context)

    return contexts


def _create_explicit_context(lines: List[str], start: int, end: int, line_nums: List[int]) -> CardContext:
    """Create CardContext from > ? block lines.

    Args:
        lines: List of lines (with > prefixes)
        start: Starting line number
        end: Ending line number
        line_nums: List of all line numbers

    Returns:
        CardContext object
    """
    full_text = "\n".join(lines)

    # Strip leading '>' and whitespace from each line
    clean_lines = []
    for line in lines:
        if line.startswith(">"):
            clean_lines.append(line[1:].lstrip())
        else:
            clean_lines.append(line)

    clean_content = "\n".join(clean_lines)

    # Remove '?' marker from first line if present
    # Track how many lines were removed to adjust line number mapping
    lines_removed = 0
    if clean_content.startswith("?"):
        # If ? is on its own line (followed by newline), we're removing a full line
        if clean_content.startswith("?\n"):
            lines_removed = 1
        clean_content = clean_content[1:].lstrip()

    return CardContext(
        content=clean_content,
        full_text=full_text,
        start_line=start + lines_removed,  # Adjust for removed ? line
        end_line=end,
        line_numbers=line_nums,
    )

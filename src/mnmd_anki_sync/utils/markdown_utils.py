"""Markdown to HTML conversion utilities."""

import re

import markdown


def normalize_math_whitespace(math_content: str) -> str:
    """Remove single newlines from math content (handles reflowed text).

    In LaTeX math, single newlines should be removed entirely as they
    are just from text reflow, not intentional line breaks.

    Args:
        math_content: Math content that may contain newlines from reflow

    Returns:
        Math content with single newlines removed
    """
    # Replace single newlines with nothing (they're just reflow artifacts)
    # First, protect double+ newlines (though rare in math)
    result = re.sub(r"\n{2,}", "\x00PARA\x00", math_content)
    # Remove single newlines
    result = result.replace("\n", " ")
    # Restore any double newlines
    result = result.replace("\x00PARA\x00", "\n\n")
    # Collapse multiple spaces
    result = re.sub(r" {2,}", " ", result)
    return result.strip()


def convert_math_to_anki(text: str) -> str:
    """Convert LaTeX math delimiters to Anki format without markdown processing.

    Converts:
    - $$block math$$ → \\[block math\\]
    - $inline math$ → \\(inline math\\)

    Also normalizes single newlines in math (from text reflow).

    Args:
        text: Text with LaTeX math delimiters

    Returns:
        Text with Anki math delimiters

    Examples:
        >>> convert_math_to_anki("$E = mc^2$")
        '\\\\(E = mc^2\\\\)'
        >>> convert_math_to_anki("$E =\\nmc^2$")  # reflowed
        '\\\\(E = mc^2\\\\)'
    """

    def replace_block_math(match):
        content = normalize_math_whitespace(match.group(1))
        return f"\\[{content}\\]"

    def replace_inline_math(match):
        content = normalize_math_whitespace(match.group(1))
        return f"\\({content}\\)"

    # Convert block math first ($$...$$)
    text = re.sub(r"\$\$(.+?)\$\$", replace_block_math, text, flags=re.DOTALL)
    # Convert inline math ($...$) - now allow newlines since we normalize them
    text = re.sub(r"\$([^\$]+?)\$", replace_inline_math, text)
    return text


def markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML for Anki cards.

    Supports:
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    - Lists: ordered and unordered
    - Images: ![alt](url)
    - Code: inline `code` and blocks
    - Line breaks
    - Math: $inline$ and $$block$$ (converted to Anki format)

    Args:
        text: Markdown text to convert

    Returns:
        HTML string

    Examples:
        >>> markdown_to_html("**bold** and *italic*")
        '<strong>bold</strong> and <em>italic</em>'
        >>> markdown_to_html("Math: $E = mc^2$")
        'Math: \\\\(E = mc^2\\\\)'
    """
    # Step 1: Extract and protect math expressions from markdown
    math_placeholders = {}
    counter = [0]  # Use list to allow modification in nested function

    def save_math(match):
        placeholder = f"<span id='mnmd-math-{counter[0]}'></span>"

        if match.group(1) is not None:
            # Block math: $$...$$ → \[...\]
            content = normalize_math_whitespace(match.group(1))
            math_placeholders[placeholder] = f"\\[{content}\\]"
        else:
            # Inline math: $...$ → \(...\)
            content = normalize_math_whitespace(match.group(2))
            math_placeholders[placeholder] = f"\\({content}\\)"

        counter[0] += 1
        return placeholder

    # Match $$...$$ (block) or $...$ (inline) - allow newlines since we normalize them
    text = re.sub(r"\$\$(.+?)\$\$|\$([^\$]+?)\$", save_math, text, flags=re.DOTALL)

    # Step 2: Process markdown
    md = markdown.Markdown(
        extensions=[
            "extra",  # Tables, fenced code blocks, etc.
            "nl2br",  # Convert newlines to <br>
            "sane_lists",  # Better list handling
        ]
    )
    html = md.convert(text)

    # Step 3: Restore math expressions
    for placeholder, math_expr in math_placeholders.items():
        html = html.replace(placeholder, math_expr)

    # Strip wrapping <p> tags if it's just a simple paragraph
    if html.startswith("<p>") and html.endswith("</p>") and html.count("<p>") == 1:
        html = html[3:-4]

    return html

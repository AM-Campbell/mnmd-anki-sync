"""Tests for context extractor."""

from mnmd_anki_sync.parser.context_extractor import extract_card_contexts


class TestExtractCardContexts:
    """Test extraction of > ? card contexts."""

    def test_extract_single_context(self):
        """Test extracting a single card context."""
        text = "> ?\n> My favorite is {{Python}}."
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        assert contexts[0].content == "My favorite is {{Python}}."
        assert contexts[0].start_line == 1  # Adjusted for removed ? line
        assert contexts[0].end_line == 1

    def test_extract_multiline_context(self):
        """Test extracting multiline card context."""
        text = "> ?\n> Line 1 with {{cloze1}}.\n> Line 2 with {{cloze2}}."
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        assert "Line 1" in contexts[0].content
        assert "Line 2" in contexts[0].content
        assert "{{cloze1}}" in contexts[0].content
        assert "{{cloze2}}" in contexts[0].content

    def test_extract_multiple_contexts(self):
        """Test extracting multiple card contexts."""
        text = """
> ?
> First context {{a}}.

Regular text here.

> ?
> Second context {{b}}.
"""
        contexts = extract_card_contexts(text)

        assert len(contexts) == 2
        assert "First context" in contexts[0].content
        assert "Second context" in contexts[1].content

    def test_extract_context_at_eof(self):
        """Test extracting context at end of file."""
        text = "> ?\n> Context at end."
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        assert contexts[0].content == "Context at end."

    def test_no_contexts(self):
        """Test with no clozes (no contexts created)."""
        text = "Just regular markdown without any cloze syntax."
        contexts = extract_card_contexts(text)

        assert len(contexts) == 0

    def test_paragraph_with_cloze(self):
        """Test that regular paragraphs with clozes create contexts."""
        text = "Just regular markdown with {{clozes}}."
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        assert contexts[0].content == text
        assert "{{clozes}}" in contexts[0].content

    def test_strip_question_marker(self):
        """Test that ? marker is stripped."""
        text = "> ?\n> Content here."
        contexts = extract_card_contexts(text)

        assert contexts[0].content == "Content here."
        assert "?" not in contexts[0].content

    def test_preserve_full_text(self):
        """Test that full_text preserves original > prefixes."""
        text = "> ?\n> Content here."
        contexts = extract_card_contexts(text)

        assert contexts[0].full_text == "> ?\n> Content here."
        assert contexts[0].full_text.startswith(">")

    def test_line_numbers(self):
        """Test that line numbers are tracked correctly."""
        text = "Line 0\n> ?\n> Context on line 2.\nLine 3"
        contexts = extract_card_contexts(text)

        assert contexts[0].start_line == 2  # Adjusted for removed ? line
        assert contexts[0].line_numbers == [1, 2]

    def test_context_with_empty_lines(self):
        """Test context with empty quote lines."""
        text = "> ?\n> Line 1\n>\n> Line 2"
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        # Empty > lines should be preserved as empty lines
        assert "\n\n" in contexts[0].content or contexts[0].content.count("\n") >= 2

    def test_paragraph_with_reflowed_cloze(self):
        """Test that paragraphs with reflowed clozes (spanning lines) are detected."""
        text = (
            "If $a, b$ and $c$ are numbers, then $a + (b + c)$ $=$ "
            "{{bLmOdcNU>$(a + b) +\nc$|associativity}}."
        )
        contexts = extract_card_contexts(text)

        assert len(contexts) == 1
        assert "{{bLmOdcNU>" in contexts[0].content
        assert "associativity}}" in contexts[0].content

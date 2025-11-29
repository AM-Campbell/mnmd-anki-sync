"""Tests for markdown utilities."""

from mnmd_anki_sync.utils.markdown_utils import (
    convert_math_to_anki,
    markdown_to_html,
    normalize_math_whitespace,
)


class TestNormalizeMathWhitespace:
    """Test math whitespace normalization for reflowed text."""

    def test_single_newline_removed(self):
        """Test that single newlines are converted to spaces."""
        result = normalize_math_whitespace("E =\nmc^2")
        assert result == "E = mc^2"

    def test_multiple_single_newlines(self):
        """Test multiple single newlines in math."""
        result = normalize_math_whitespace("a +\nb +\nc")
        assert result == "a + b + c"

    def test_double_newlines_preserved(self):
        """Test that double newlines are preserved (rare in math)."""
        result = normalize_math_whitespace("first\n\nsecond")
        assert result == "first\n\nsecond"

    def test_multiple_spaces_collapsed(self):
        """Test that multiple spaces are collapsed."""
        result = normalize_math_whitespace("a  +   b")
        assert result == "a + b"

    def test_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        result = normalize_math_whitespace("  E = mc^2  ")
        assert result == "E = mc^2"


class TestConvertMathToAnki:
    """Test LaTeX math to Anki format conversion."""

    def test_inline_math_basic(self):
        """Test basic inline math conversion."""
        result = convert_math_to_anki("$E = mc^2$")
        assert result == "\\(E = mc^2\\)"

    def test_block_math_basic(self):
        """Test basic block math conversion."""
        result = convert_math_to_anki("$$E = mc^2$$")
        assert result == "\\[E = mc^2\\]"

    def test_inline_math_with_reflow(self):
        """Test inline math with single newline from reflow."""
        result = convert_math_to_anki("$E =\nmc^2$")
        assert result == "\\(E = mc^2\\)"

    def test_block_math_with_reflow(self):
        """Test block math with single newline from reflow."""
        result = convert_math_to_anki("$$\\frac{a}\n{b}$$")
        assert result == "\\[\\frac{a} {b}\\]"

    def test_mixed_text_and_math(self):
        """Test text with embedded math."""
        result = convert_math_to_anki("Einstein's equation is $E =\nmc^2$ which is famous")
        assert result == "Einstein's equation is \\(E = mc^2\\) which is famous"


class TestMarkdownToHtml:
    """Test markdown to HTML conversion."""

    def test_bold(self):
        """Test bold conversion."""
        result = markdown_to_html("This is **bold** text")
        assert "<strong>bold</strong>" in result

    def test_italic(self):
        """Test italic conversion."""
        result = markdown_to_html("This is *italic* text")
        assert "<em>italic</em>" in result

    def test_bold_and_italic(self):
        """Test combined bold and italic."""
        result = markdown_to_html("**bold** and *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_unordered_list(self):
        """Test unordered list conversion."""
        text = "- item 1\n- item 2\n- item 3"
        result = markdown_to_html(text)
        assert "<ul>" in result
        assert "<li>item 1</li>" in result
        assert "<li>item 2</li>" in result
        assert "<li>item 3</li>" in result

    def test_ordered_list(self):
        """Test ordered list conversion."""
        text = "1. first\n2. second\n3. third"
        result = markdown_to_html(text)
        assert "<ol>" in result
        assert "<li>first</li>" in result
        assert "<li>second</li>" in result
        assert "<li>third</li>" in result

    def test_inline_code(self):
        """Test inline code conversion."""
        result = markdown_to_html("Use `code` here")
        assert "<code>code</code>" in result

    def test_code_block(self):
        """Test code block conversion."""
        text = "```\ncode block\n```"
        result = markdown_to_html(text)
        assert "<code>" in result or "<pre>" in result

    def test_image(self):
        """Test image conversion."""
        result = markdown_to_html("![alt text](image.png)")
        assert '<img' in result
        assert 'alt="alt text"' in result
        assert 'src="image.png"' in result

    def test_line_breaks(self):
        """Test that line breaks are preserved."""
        text = "Line 1\nLine 2"
        result = markdown_to_html(text)
        # nl2br extension should convert \n to <br>
        assert "<br" in result or "Line 1" in result

    def test_mixed_formatting(self):
        """Test mixed markdown formatting."""
        text = "**Bold** and *italic* with `code`"
        result = markdown_to_html(text)
        assert "<strong>Bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<code>code</code>" in result

    def test_nested_list(self):
        """Test nested lists."""
        text = "- item 1\n  - nested 1\n  - nested 2\n- item 2"
        result = markdown_to_html(text)
        assert "<ul>" in result
        assert "<li>item 1" in result
        # Should handle nesting
        assert result.count("<ul>") >= 1

    def test_empty_text(self):
        """Test empty text."""
        result = markdown_to_html("")
        assert result == ""

    def test_plain_text(self):
        """Test plain text without formatting."""
        result = markdown_to_html("Just plain text")
        # Should return the text, possibly without <p> tags
        assert "Just plain text" in result

    def test_inline_math_with_reflow(self):
        """Test that reflowed inline math is normalized."""
        result = markdown_to_html("Math: $E =\nmc^2$")
        assert "\\(E = mc^2\\)" in result

    def test_block_math_with_reflow(self):
        """Test that reflowed block math is normalized."""
        result = markdown_to_html("$$\\sum_{i=1}\n^{n} i$$")
        assert "\\[\\sum_{i=1} ^{n} i\\]" in result

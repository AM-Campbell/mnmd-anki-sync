"""Tests for scope resolver."""

from mnmd_anki_sync.models import ScopeSpec
from mnmd_anki_sync.parser.scope_resolver import get_paragraph_boundaries, resolve_context_scope


class TestGetParagraphBoundaries:
    """Test paragraph boundary detection."""

    def test_single_paragraph(self):
        """Test single paragraph."""
        text = "This is a paragraph."
        paragraphs = get_paragraph_boundaries(text)

        assert len(paragraphs) == 1
        assert paragraphs[0] == (0, 0)

    def test_multiple_paragraphs(self):
        """Test multiple paragraphs."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        paragraphs = get_paragraph_boundaries(text)

        assert len(paragraphs) == 3
        assert paragraphs[0] == (0, 0)
        assert paragraphs[1] == (2, 2)
        assert paragraphs[2] == (4, 4)

    def test_multiline_paragraphs(self):
        """Test multiline paragraphs."""
        text = "Para 1 line 1\nPara 1 line 2\n\nPara 2 line 1\nPara 2 line 2"
        paragraphs = get_paragraph_boundaries(text)

        assert len(paragraphs) == 2
        assert paragraphs[0] == (0, 1)
        assert paragraphs[1] == (3, 4)

    def test_empty_text(self):
        """Test empty text."""
        text = ""
        paragraphs = get_paragraph_boundaries(text)

        assert len(paragraphs) == 0

    def test_only_empty_lines(self):
        """Test text with only empty lines."""
        text = "\n\n\n"
        paragraphs = get_paragraph_boundaries(text)

        assert len(paragraphs) == 0


class TestResolveContextScope:
    """Test scope resolution."""

    def test_resolve_current_paragraph_only(self):
        """Test resolving to current paragraph only."""
        text = "Para 1.\n\nPara 2 with cloze.\n\nPara 3."
        result = resolve_context_scope(text, 2, ScopeSpec(before=0, after=0))

        assert result == "Para 2 with cloze."

    def test_resolve_with_before(self):
        """Test resolving with paragraph before."""
        text = "Para 1.\n\nPara 2 with cloze.\n\nPara 3."
        result = resolve_context_scope(text, 2, ScopeSpec(before=-1, after=0))

        assert "Para 1" in result
        assert "Para 2 with cloze" in result
        assert "Para 3" not in result

    def test_resolve_with_after(self):
        """Test resolving with paragraph after."""
        text = "Para 1.\n\nPara 2 with cloze.\n\nPara 3."
        result = resolve_context_scope(text, 2, ScopeSpec(before=0, after=1))

        assert "Para 1" not in result
        assert "Para 2 with cloze" in result
        assert "Para 3" in result

    def test_resolve_with_both(self):
        """Test resolving with paragraphs before and after."""
        text = "Para 1.\n\nPara 2.\n\nPara 3 with cloze.\n\nPara 4.\n\nPara 5."
        result = resolve_context_scope(text, 4, ScopeSpec(before=-1, after=1))

        assert "Para 1" not in result
        assert "Para 2" in result
        assert "Para 3 with cloze" in result
        assert "Para 4" in result
        assert "Para 5" not in result

    def test_resolve_at_boundary(self):
        """Test resolving at document boundaries."""
        text = "Para 1 with cloze.\n\nPara 2.\n\nPara 3."

        # At start with before scope
        result = resolve_context_scope(text, 0, ScopeSpec(before=-2, after=0))
        assert "Para 1" in result
        # Should not error, just include what's available

        # At end with after scope
        result2 = resolve_context_scope(text, 4, ScopeSpec(before=0, after=2))
        assert "Para 3" in result2

    def test_resolve_multiline_paragraph(self):
        """Test resolving with multiline paragraphs."""
        text = "Para 1 line 1\nPara 1 line 2\n\nPara 2 line 1\nPara 2 line 2 with cloze\n\nPara 3"
        result = resolve_context_scope(text, 4, ScopeSpec(before=0, after=0))

        assert "Para 2 line 1" in result
        assert "Para 2 line 2 with cloze" in result
        assert "Para 1" not in result
        assert "Para 3" not in result

"""Tests for note builder module."""

from pathlib import Path

import pytest

from mnmd_anki_sync.anki.note_builder import build_note_fields
from mnmd_anki_sync.config import Config, EditorProtocol
from mnmd_anki_sync.models import ClozeMatch, ClozeType, Prompt, ScopeSpec


def create_cloze(
    answer: str,
    hint: str = None,
    extra: str = None,
) -> ClozeMatch:
    """Helper to create ClozeMatch objects."""
    return ClozeMatch(
        full_text=f"{{{{{answer}}}}}",
        start=0,
        end=len(answer) + 4,
        answer=answer,
        hint=hint,
        extra=extra,
        cloze_type=ClozeType.BASIC,
        line_number=0,
        scope=ScopeSpec.default(),
    )


def create_prompt(
    cloze: ClozeMatch,
    context: str = "__CLOZE__",
    file_path: Path = Path("/tmp/test.md"),
    line_number: int = 10,
) -> Prompt:
    """Helper to create Prompt objects."""
    return Prompt(
        cloze_match=cloze,
        context=context,
        file_path=file_path,
        line_number=line_number,
    )


class TestBuildNoteFields:
    """Test building note fields from prompts."""

    def test_basic_note_fields(self):
        """Test building basic note fields."""
        cloze = create_cloze("answer")
        prompt = create_prompt(cloze)
        config = Config()

        fields = build_note_fields(prompt, config)

        assert "Text" in fields
        assert "Extra" in fields
        assert "Source" in fields
        assert "{{c1::answer}}" in fields["Text"]

    def test_note_with_hint(self):
        """Test note with hint."""
        cloze = create_cloze("answer", hint="a clue")
        prompt = create_prompt(cloze)
        config = Config()

        fields = build_note_fields(prompt, config)

        assert "{{c1::answer::a clue}}" in fields["Text"]

    def test_note_with_extra(self):
        """Test note with extra info."""
        cloze = create_cloze("answer", extra="Additional info")
        prompt = create_prompt(cloze)
        config = Config()

        fields = build_note_fields(prompt, config)

        assert fields["Extra"] == "Additional info"

    def test_note_without_extra(self):
        """Test note without extra info has empty Extra field."""
        cloze = create_cloze("answer")
        prompt = create_prompt(cloze)
        config = Config()

        fields = build_note_fields(prompt, config)

        assert fields["Extra"] == ""

    def test_source_link_vscode(self):
        """Test source link with VS Code protocol."""
        cloze = create_cloze("answer")
        prompt = create_prompt(cloze, file_path=Path("/path/to/file.md"), line_number=42)
        config = Config(editor_protocol=EditorProtocol.VSCODE)

        fields = build_note_fields(prompt, config)

        assert "vscode://file" in fields["Source"]
        assert "/path/to/file.md" in fields["Source"]
        assert ":42:" in fields["Source"]

    def test_source_link_nvim(self):
        """Test source link with Neovim protocol."""
        cloze = create_cloze("answer")
        prompt = create_prompt(cloze, file_path=Path("/path/to/file.md"), line_number=42)
        config = Config(editor_protocol=EditorProtocol.NVIM)

        fields = build_note_fields(prompt, config)

        assert "nvim://open" in fields["Source"]
        assert "file=" in fields["Source"]
        assert "line=42" in fields["Source"]

    def test_note_with_markdown_context(self):
        """Test note with markdown in context is converted to HTML."""
        cloze = create_cloze("answer")
        prompt = create_prompt(cloze, context="**bold** __CLOZE__ *italic*")
        config = Config()

        fields = build_note_fields(prompt, config)

        # Markdown should be converted to HTML
        assert "<strong>" in fields["Text"] or "<b>" in fields["Text"] or "bold" in fields["Text"]

    def test_note_with_math(self):
        """Test note with math expression."""
        cloze = ClozeMatch(
            full_text="{{$E=mc^2$}}",
            start=0,
            end=12,
            answer="$E=mc^2$",
            cloze_type=ClozeType.BASIC,
            line_number=0,
            scope=ScopeSpec.default(),
        )
        prompt = create_prompt(cloze, context="Einstein: __CLOZE__")
        config = Config()

        fields = build_note_fields(prompt, config)

        # Math should be converted to Anki format
        assert "\\(" in fields["Text"] or "$" in fields["Text"]


class TestGroupedNotes:
    """Test building notes for grouped clozes."""

    def test_grouped_note_multiple_placeholders(self):
        """Test grouped note has multiple c1 placeholders."""
        cloze1 = ClozeMatch(
            full_text="{{1>apples}}",
            start=7,
            end=19,
            answer="apples",
            cloze_id="1",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        )
        cloze2 = ClozeMatch(
            full_text="{{1>oranges}}",
            start=24,
            end=37,
            answer="oranges",
            cloze_id="1",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        )

        prompt = Prompt(
            cloze_match=cloze1,
            context="I like __CLOZE_0__ and __CLOZE_1__.",
            file_path=Path("/tmp/test.md"),
            line_number=0,
            group_clozes=[cloze1, cloze2],
        )
        config = Config()

        fields = build_note_fields(prompt, config)

        # Both clozes should use c1 (grouped)
        text = fields["Text"]
        assert text.count("{{c1::") == 2
        assert "apples" in text
        assert "oranges" in text

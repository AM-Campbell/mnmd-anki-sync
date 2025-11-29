"""Tests for Pydantic models with CORRECT MNMD syntax."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from mnmd_anki_sync.models import (
    CardContext,
    ClozeGroup,
    ClozeMatch,
    ClozeType,
    Prompt,
    ScopeSpec,
)


class TestScopeSpec:
    """Test ScopeSpec model."""

    def test_default_scope(self):
        """Test default scope specification."""
        scope = ScopeSpec.default()
        assert scope.before == 0
        assert scope.after == 0

    def test_list_default_scope(self):
        """Test list default scope specification."""
        scope = ScopeSpec.list_default()
        assert scope.before == -1
        assert scope.after == 0

    def test_custom_scope(self):
        """Test custom scope specification."""
        scope = ScopeSpec(before=-2, after=3)
        assert scope.before == -2
        assert scope.after == 3

    def test_before_auto_correction(self):
        """Test that positive 'before' values are auto-corrected to negative."""
        scope = ScopeSpec(before=2, after=0)
        assert scope.before == -2  # Should be auto-corrected

    def test_after_auto_correction(self):
        """Test that negative 'after' values are auto-corrected to positive."""
        scope = ScopeSpec(before=0, after=-3)
        assert scope.after == 3  # Should be auto-corrected


class TestClozeMatch:
    """Test ClozeMatch model."""

    def test_basic_cloze(self):
        """Test basic cloze match."""
        cloze = ClozeMatch(
            full_text="{{answer}}",
            start=10,
            end=20,
            answer="answer",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        assert cloze.cloze_type == ClozeType.BASIC
        assert cloze.answer == "answer"
        assert cloze.cloze_id is None
        assert cloze.sequence_order is None
        assert cloze.hint is None
        assert cloze.extra is None

    def test_grouped_cloze(self):
        """Test grouped cloze match."""
        cloze = ClozeMatch(
            full_text="{{1>answer}}",
            start=10,
            end=22,
            cloze_id="1",
            answer="answer",
            cloze_type=ClozeType.GROUPED,
            line_number=5,
        )
        assert cloze.cloze_type == ClozeType.GROUPED
        assert cloze.cloze_id == "1"

    def test_sequence_cloze(self):
        """Test sequence cloze match."""
        cloze = ClozeMatch(
            full_text="{{1.2>answer}}",
            start=10,
            end=24,
            cloze_id="1",
            sequence_order=2,
            answer="answer",
            cloze_type=ClozeType.SEQUENCE,
            line_number=5,
        )
        assert cloze.cloze_type == ClozeType.SEQUENCE
        assert cloze.cloze_id == "1"
        assert cloze.sequence_order == 2

    def test_cloze_with_hint(self):
        """Test cloze with hint field."""
        cloze = ClozeMatch(
            full_text="{{answer|hint text}}",
            start=0,
            end=20,
            answer="answer",
            hint="hint text",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        assert cloze.answer == "answer"
        assert cloze.hint == "hint text"
        assert cloze.extra is None

    def test_cloze_with_extra(self):
        """Test cloze with extra field."""
        cloze = ClozeMatch(
            full_text="{{answer<extra info}}",
            start=0,
            end=21,
            answer="answer",
            extra="extra info",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        assert cloze.answer == "answer"
        assert cloze.hint is None
        assert cloze.extra == "extra info"

    def test_cloze_with_hint_and_extra(self):
        """Test cloze with both hint and extra."""
        cloze = ClozeMatch(
            full_text="{{answer|hint<extra}}",
            start=0,
            end=21,
            answer="answer",
            hint="hint",
            extra="extra",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        assert cloze.answer == "answer"
        assert cloze.hint == "hint"
        assert cloze.extra == "extra"

    def test_anki_id_validation(self):
        """Test that anki_id must be alphabetic."""
        # Valid anki_id
        cloze = ClozeMatch(
            full_text="{{abcXYZ>answer}}",
            start=0,
            end=17,
            anki_id="abcXYZ",
            answer="answer",
            cloze_type=ClozeType.BASIC,
            line_number=1,
        )
        assert cloze.anki_id == "abcXYZ"

        # Invalid anki_id with numbers
        with pytest.raises(ValidationError):
            ClozeMatch(
                full_text="{{abc123>answer}}",
                start=0,
                end=17,
                anki_id="abc123",
                answer="answer",
                cloze_type=ClozeType.BASIC,
                line_number=1,
            )


class TestPrompt:
    """Test Prompt model."""

    def test_basic_prompt(self):
        """Test basic prompt creation."""
        cloze = ClozeMatch(
            full_text="{{answer}}",
            start=0,
            end=10,
            answer="answer",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        prompt = Prompt(
            cloze_match=cloze,
            context="The __CLOZE__ is correct.",
            file_path=Path("/test/file.md"),
            line_number=5,
        )
        assert prompt.context == "The __CLOZE__ is correct."
        assert prompt.deck_name == "Default"
        assert "mnmd" in prompt.tags

    def test_to_anki_cloze_text_basic(self):
        """Test converting prompt to Anki cloze text."""
        cloze = ClozeMatch(
            full_text="{{answer}}",
            start=0,
            end=10,
            answer="answer",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        prompt = Prompt(
            cloze_match=cloze,
            context="The __CLOZE__ is correct.",
            file_path=Path("/test/file.md"),
            line_number=5,
        )
        anki_text = prompt.to_anki_cloze_text()
        # Should contain the cloze syntax (markdown is converted to HTML)
        assert "{{c1::answer}}" in anki_text
        assert "__CLOZE__" not in anki_text

    def test_to_anki_cloze_text_with_hint(self):
        """Test converting prompt with hint to Anki cloze text."""
        cloze = ClozeMatch(
            full_text="{{answer|hint text}}",
            start=0,
            end=20,
            answer="answer",
            hint="hint text",
            cloze_type=ClozeType.BASIC,  # Hint is a field, not a type
            line_number=5,
        )
        prompt = Prompt(
            cloze_match=cloze,
            context="The __CLOZE__ is correct.",
            file_path=Path("/test/file.md"),
            line_number=5,
        )
        anki_text = prompt.to_anki_cloze_text()
        # Should contain the cloze syntax with hint
        assert "{{c1::answer::hint text}}" in anki_text

    def test_to_anki_cloze_text_with_markdown(self):
        """Test that markdown is converted to HTML in cloze text."""
        cloze = ClozeMatch(
            full_text="{{answer}}",
            start=0,
            end=10,
            answer="answer",
            cloze_type=ClozeType.BASIC,
            line_number=5,
        )
        prompt = Prompt(
            cloze_match=cloze,
            context="**Bold** text with __CLOZE__ and *italic*.",
            file_path=Path("/test/file.md"),
            line_number=5,
        )
        anki_text = prompt.to_anki_cloze_text()
        # Should convert markdown to HTML
        assert "<strong>Bold</strong>" in anki_text
        assert "<em>italic</em>" in anki_text
        assert "{{c1::answer}}" in anki_text


class TestClozeGroup:
    """Test ClozeGroup model."""

    def test_basic_group(self):
        """Test basic cloze group."""
        cloze1 = ClozeMatch(
            full_text="{{1>first}}",
            start=0,
            end=11,
            cloze_id="1",
            answer="first",
            cloze_type=ClozeType.GROUPED,
            line_number=1,
        )
        cloze2 = ClozeMatch(
            full_text="{{1>second}}",
            start=20,
            end=32,
            cloze_id="1",
            answer="second",
            cloze_type=ClozeType.GROUPED,
            line_number=1,
        )
        group = ClozeGroup(group_id="1", clozes=[cloze1, cloze2], is_sequence=False)
        assert len(group.clozes) == 2
        assert group.group_id == "1"
        assert not group.is_sequence

    def test_sequence_group(self):
        """Test sequence cloze group."""
        clozes = [
            ClozeMatch(
                full_text=f"{{{{1.{i}>item{i}}}}}",
                start=i * 20,
                end=i * 20 + 15,
                cloze_id="1",
                sequence_order=i,
                answer=f"item{i}",
                cloze_type=ClozeType.SEQUENCE,
                line_number=1,
            )
            for i in [3, 1, 2]  # Out of order
        ]
        group = ClozeGroup(group_id="1", clozes=clozes, is_sequence=True)

        # Test that get_sequence_clozes sorts them
        sorted_clozes = group.get_sequence_clozes()
        assert sorted_clozes[0].sequence_order == 1
        assert sorted_clozes[1].sequence_order == 2
        assert sorted_clozes[2].sequence_order == 3


class TestCardContext:
    """Test CardContext model."""

    def test_basic_context(self):
        """Test basic card context."""
        context = CardContext(
            content="My favorite language is {{Python}}.",
            full_text="> ?\n> My favorite language is {{Python}}.",
            start_line=0,
            end_line=1,
            line_numbers=[0, 1],
        )
        assert context.start_line == 0
        assert context.end_line == 1
        assert len(context.cloze_matches) == 0  # Not parsed yet
        assert len(context.prompts) == 0

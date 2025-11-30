"""Tests for prompt generator module."""

from pathlib import Path

from mnmd_anki_sync.models import CardContext, ClozeMatch, ClozeType, ScopeSpec
from mnmd_anki_sync.parser.prompt_generator import (
    _generate_group_prompt,
    _generate_sequence_prompts,
    _group_clozes,
    generate_prompts,
)


def create_cloze(
    full_text: str,
    start: int,
    end: int,
    answer: str,
    cloze_id: str = None,
    sequence_order: int = None,
    anki_id: str = None,
    hint: str = None,
    cloze_type: ClozeType = ClozeType.BASIC,
    line_number: int = 0,
) -> ClozeMatch:
    """Helper to create ClozeMatch objects."""
    return ClozeMatch(
        full_text=full_text,
        start=start,
        end=end,
        answer=answer,
        cloze_id=cloze_id,
        sequence_order=sequence_order,
        anki_id=anki_id,
        hint=hint,
        cloze_type=cloze_type,
        line_number=line_number,
        scope=ScopeSpec.default(),
    )


def create_context(content: str, clozes: list, start_line: int = 0) -> CardContext:
    """Helper to create CardContext objects."""
    return CardContext(
        content=content,
        full_text=content,
        start_line=start_line,
        end_line=start_line + content.count("\n"),
        line_numbers=list(range(start_line, start_line + content.count("\n") + 1)),
        cloze_matches=clozes,
    )


class TestGroupClozes:
    """Test cloze grouping logic."""

    def test_group_basic_clozes(self):
        """Test that basic clozes are placed in individual groups."""
        cloze1 = create_cloze("{{first}}", 0, 9, "first")
        cloze2 = create_cloze("{{second}}", 10, 20, "second")

        groups = _group_clozes([cloze1, cloze2])

        assert len(groups) == 2
        # Each basic cloze gets its own individual group
        assert any(len(g.clozes) == 1 and g.clozes[0] == cloze1 for g in groups.values())
        assert any(len(g.clozes) == 1 and g.clozes[0] == cloze2 for g in groups.values())

    def test_group_grouped_clozes(self):
        """Test that clozes with same ID are grouped together."""
        cloze1 = create_cloze(
            "{{1>apples}}", 0, 12, "apples", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        cloze2 = create_cloze(
            "{{1>oranges}}", 20, 33, "oranges", cloze_id="1", cloze_type=ClozeType.GROUPED
        )

        groups = _group_clozes([cloze1, cloze2])

        assert len(groups) == 1
        assert "1" in groups
        assert len(groups["1"].clozes) == 2
        assert groups["1"].is_sequence is False

    def test_group_sequence_clozes(self):
        """Test that sequence clozes are marked as such."""
        cloze1 = create_cloze(
            "{{1.1>first}}",
            0,
            13,
            "first",
            cloze_id="1",
            sequence_order=1,
            cloze_type=ClozeType.SEQUENCE,
        )
        cloze2 = create_cloze(
            "{{1.2>second}}",
            20,
            34,
            "second",
            cloze_id="1",
            sequence_order=2,
            cloze_type=ClozeType.SEQUENCE,
        )

        groups = _group_clozes([cloze1, cloze2])

        assert len(groups) == 1
        assert "1" in groups
        assert groups["1"].is_sequence is True

    def test_group_mixed_clozes(self):
        """Test grouping with mixed cloze types."""
        basic = create_cloze("{{basic}}", 0, 9, "basic")
        grouped1 = create_cloze(
            "{{1>one}}", 10, 19, "one", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        grouped2 = create_cloze(
            "{{1>two}}", 20, 29, "two", cloze_id="1", cloze_type=ClozeType.GROUPED
        )

        groups = _group_clozes([basic, grouped1, grouped2])

        assert len(groups) == 2  # One individual, one grouped


class TestGenerateGroupPrompt:
    """Test single group prompt generation."""

    def test_generate_basic_prompt(self):
        """Test generating prompt for a single basic cloze."""
        cloze = create_cloze("{{answer}}", 4, 14, "answer", line_number=0)
        content = "The {{answer}} is here."
        context = create_context(content, [cloze])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="_individual_0", clozes=[cloze], is_sequence=False)

        prompt = _generate_group_prompt(group, context, Path("/tmp/test.md"))

        assert prompt is not None
        assert "__CLOZE__" in prompt.context
        assert prompt.cloze_match == cloze
        assert prompt.group_clozes is None  # Single cloze, no group

    def test_generate_grouped_prompt(self):
        """Test generating prompt for grouped clozes."""
        content = "I like {{1>apples}} and {{1>oranges}}."
        cloze1 = create_cloze(
            "{{1>apples}}", 7, 19, "apples", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        cloze2 = create_cloze(
            "{{1>oranges}}", 24, 37, "oranges", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        context = create_context(content, [cloze1, cloze2])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="1", clozes=[cloze1, cloze2], is_sequence=False)

        prompt = _generate_group_prompt(group, context, Path("/tmp/test.md"))

        assert prompt is not None
        assert "__CLOZE_0__" in prompt.context
        assert "__CLOZE_1__" in prompt.context
        assert prompt.group_clozes is not None
        assert len(prompt.group_clozes) == 2

    def test_generate_empty_group_returns_none(self):
        """Test that empty group returns None."""
        content = "Some text."
        context = create_context(content, [])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="empty", clozes=[], is_sequence=False)

        prompt = _generate_group_prompt(group, context, Path("/tmp/test.md"))

        assert prompt is None

    def test_other_clozes_shown_as_answers(self):
        """Test that clozes not in group are shown as answers."""
        content = "The {{1>cat}} chased the {{mouse}}."
        cloze1 = create_cloze("{{1>cat}}", 4, 13, "cat", cloze_id="1", cloze_type=ClozeType.GROUPED)
        cloze2 = create_cloze("{{mouse}}", 25, 34, "mouse")
        context = create_context(content, [cloze1, cloze2])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="1", clozes=[cloze1], is_sequence=False)

        prompt = _generate_group_prompt(group, context, Path("/tmp/test.md"))

        assert "__CLOZE__" in prompt.context
        assert "mouse" in prompt.context  # Other cloze shown as answer


class TestGenerateSequencePrompts:
    """Test sequence prompt generation."""

    def test_generate_sequence_prompts(self):
        """Test generating prompts for sequence clozes."""
        content = "Steps: {{1.1>first}}, {{1.2>second}}, {{1.3>third}}."
        cloze1 = create_cloze(
            "{{1.1>first}}",
            7,
            20,
            "first",
            cloze_id="1",
            sequence_order=1,
            cloze_type=ClozeType.SEQUENCE,
        )
        cloze2 = create_cloze(
            "{{1.2>second}}",
            22,
            36,
            "second",
            cloze_id="1",
            sequence_order=2,
            cloze_type=ClozeType.SEQUENCE,
        )
        cloze3 = create_cloze(
            "{{1.3>third}}",
            38,
            51,
            "third",
            cloze_id="1",
            sequence_order=3,
            cloze_type=ClozeType.SEQUENCE,
        )
        context = create_context(content, [cloze1, cloze2, cloze3])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="1", clozes=[cloze1, cloze2, cloze3], is_sequence=True)

        prompts = _generate_sequence_prompts(group, context, Path("/tmp/test.md"))

        assert len(prompts) == 3

        # First prompt: first is hidden, rest are ellipsis
        assert "__CLOZE__" in prompts[0].context
        assert "..." in prompts[0].context

        # Second prompt: first is shown, second is hidden, third is ellipsis
        assert "first" in prompts[1].context
        assert "__CLOZE__" in prompts[1].context
        assert "..." in prompts[1].context

        # Third prompt: first and second are shown, third is hidden
        assert "first" in prompts[2].context
        assert "second" in prompts[2].context
        assert "__CLOZE__" in prompts[2].context

    def test_sequence_sorted_by_order(self):
        """Test that sequence prompts are in correct order even if clozes aren't."""
        content = "{{1.3>third}} {{1.1>first}} {{1.2>second}}"
        # Deliberately out of order
        cloze3 = create_cloze(
            "{{1.3>third}}",
            0,
            13,
            "third",
            cloze_id="1",
            sequence_order=3,
            cloze_type=ClozeType.SEQUENCE,
        )
        cloze1 = create_cloze(
            "{{1.1>first}}",
            14,
            27,
            "first",
            cloze_id="1",
            sequence_order=1,
            cloze_type=ClozeType.SEQUENCE,
        )
        cloze2 = create_cloze(
            "{{1.2>second}}",
            28,
            42,
            "second",
            cloze_id="1",
            sequence_order=2,
            cloze_type=ClozeType.SEQUENCE,
        )
        context = create_context(content, [cloze3, cloze1, cloze2])

        from mnmd_anki_sync.models import ClozeGroup

        group = ClozeGroup(group_id="1", clozes=[cloze3, cloze1, cloze2], is_sequence=True)

        prompts = _generate_sequence_prompts(group, context, Path("/tmp/test.md"))

        # Prompts should be for first, second, third (by sequence order)
        assert prompts[0].cloze_match.answer == "first"
        assert prompts[1].cloze_match.answer == "second"
        assert prompts[2].cloze_match.answer == "third"


class TestGeneratePrompts:
    """Test main prompt generation function."""

    def test_generate_prompts_basic(self):
        """Test generating prompts for basic clozes."""
        content = "{{first}} and {{second}}."
        cloze1 = create_cloze("{{first}}", 0, 9, "first")
        cloze2 = create_cloze("{{second}}", 14, 24, "second")
        context = create_context(content, [cloze1, cloze2])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        assert len(prompts) == 2

    def test_generate_prompts_grouped(self):
        """Test generating prompts for grouped clozes (one prompt per group)."""
        content = "{{1>a}} and {{1>b}}."
        cloze1 = create_cloze("{{1>a}}", 0, 7, "a", cloze_id="1", cloze_type=ClozeType.GROUPED)
        cloze2 = create_cloze("{{1>b}}", 12, 19, "b", cloze_id="1", cloze_type=ClozeType.GROUPED)
        context = create_context(content, [cloze1, cloze2])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        # Grouped clozes produce ONE prompt
        assert len(prompts) == 1
        assert prompts[0].group_clozes is not None
        assert len(prompts[0].group_clozes) == 2

    def test_generate_prompts_sequence(self):
        """Test generating prompts for sequence clozes (one per step)."""
        content = "{{1.1>a}} {{1.2>b}} {{1.3>c}}."
        cloze1 = create_cloze(
            "{{1.1>a}}", 0, 9, "a", cloze_id="1", sequence_order=1, cloze_type=ClozeType.SEQUENCE
        )
        cloze2 = create_cloze(
            "{{1.2>b}}", 10, 19, "b", cloze_id="1", sequence_order=2, cloze_type=ClozeType.SEQUENCE
        )
        cloze3 = create_cloze(
            "{{1.3>c}}", 20, 29, "c", cloze_id="1", sequence_order=3, cloze_type=ClozeType.SEQUENCE
        )
        context = create_context(content, [cloze1, cloze2, cloze3])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        # Sequence clozes produce N prompts (one per item)
        assert len(prompts) == 3

    def test_generate_prompts_empty_context(self):
        """Test generating prompts from empty context."""
        context = create_context("No clozes here.", [])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        assert len(prompts) == 0

    def test_generate_prompts_mixed(self):
        """Test generating prompts with mixed cloze types."""
        content = "{{basic}} {{1>grouped1}} {{1>grouped2}} {{2.1>seq1}} {{2.2>seq2}}."
        basic = create_cloze("{{basic}}", 0, 9, "basic")
        grouped1 = create_cloze(
            "{{1>grouped1}}", 10, 24, "grouped1", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        grouped2 = create_cloze(
            "{{1>grouped2}}", 25, 39, "grouped2", cloze_id="1", cloze_type=ClozeType.GROUPED
        )
        seq1 = create_cloze(
            "{{2.1>seq1}}",
            40,
            52,
            "seq1",
            cloze_id="2",
            sequence_order=1,
            cloze_type=ClozeType.SEQUENCE,
        )
        seq2 = create_cloze(
            "{{2.2>seq2}}",
            53,
            65,
            "seq2",
            cloze_id="2",
            sequence_order=2,
            cloze_type=ClozeType.SEQUENCE,
        )
        context = create_context(content, [basic, grouped1, grouped2, seq1, seq2])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        # 1 basic + 1 grouped + 2 sequence = 4 prompts
        assert len(prompts) == 4


class TestPromptAttributes:
    """Test prompt attributes are set correctly."""

    def test_prompt_has_file_path(self):
        """Test that prompts have the file path."""
        cloze = create_cloze("{{test}}", 0, 8, "test")
        context = create_context("{{test}}", [cloze])

        prompts = generate_prompts(context, Path("/my/file.md"))

        assert prompts[0].file_path == Path("/my/file.md")

    def test_prompt_has_line_number(self):
        """Test that prompts have the line number."""
        cloze = create_cloze("{{test}}", 0, 8, "test", line_number=5)
        context = create_context("{{test}}", [cloze], start_line=5)

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        assert prompts[0].line_number == 5

    def test_prompt_has_anki_id(self):
        """Test that prompts inherit Anki ID from cloze."""
        cloze = create_cloze("{{abc>test}}", 0, 12, "test", anki_id="abc")
        context = create_context("{{abc>test}}", [cloze])

        prompts = generate_prompts(context, Path("/tmp/test.md"))

        assert prompts[0].anki_id == "abc"

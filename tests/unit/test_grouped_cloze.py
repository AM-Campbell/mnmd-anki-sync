"""Tests for grouped cloze functionality with CORRECT MNMD syntax."""

from pathlib import Path

from mnmd_anki_sync.models import CardContext, ClozeMatch, ClozeType, ScopeSpec
from mnmd_anki_sync.parser.prompt_generator import generate_prompts


def test_grouped_cloze_individual_answers():
    """Test that grouped clozes show individual answers, not combined."""
    # Create grouped clozes
    clozes = [
        ClozeMatch(
            full_text="{{1>red}}",
            start=30,
            end=39,
            cloze_id="1",
            answer="red",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
        ClozeMatch(
            full_text="{{1>blue}}",
            start=41,
            end=51,
            cloze_id="1",
            answer="blue",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
        ClozeMatch(
            full_text="{{1>yellow}}",
            start=57,
            end=69,
            cloze_id="1",
            answer="yellow",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
    ]

    context = CardContext(
        content="The three primary colors are {{1>red}}, {{1>blue}}, and {{1>yellow}}.",
        full_text="> ?\n> The three primary colors are {{1>red}}, {{1>blue}}, and {{1>yellow}}.",
        start_line=0,
        end_line=1,
        line_numbers=[0, 1],
        cloze_matches=clozes,
    )

    prompts = generate_prompts(context, Path("/test.md"))

    # Should generate ONE prompt for the group
    assert len(prompts) == 1

    prompt = prompts[0]

    # Should have group_clozes set
    assert prompt.group_clozes is not None
    assert len(prompt.group_clozes) == 3

    # Convert to Anki format
    anki_text = prompt.to_anki_cloze_text()

    # Should have each answer individually, all with c1
    assert "{{c1::red}}" in anki_text
    assert "{{c1::blue}}" in anki_text
    assert "{{c1::yellow}}" in anki_text

    # Should NOT have combined answers
    assert "red / blue / yellow" not in anki_text

    # Should have the structure
    assert "primary colors are" in anki_text


def test_single_cloze_no_grouping():
    """Test that single clozes work without grouping."""
    clozes = [
        ClozeMatch(
            full_text="{{Paris}}",
            start=22,
            end=31,
            answer="Paris",
            cloze_type=ClozeType.BASIC,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
    ]

    context = CardContext(
        content="The capital of France is {{Paris}}.",
        full_text="> ?\n> The capital of France is {{Paris}}.",
        start_line=0,
        end_line=1,
        line_numbers=[0, 1],
        cloze_matches=clozes,
    )

    prompts = generate_prompts(context, Path("/test.md"))

    assert len(prompts) == 1
    prompt = prompts[0]

    # Should NOT have group_clozes
    assert prompt.group_clozes is None

    anki_text = prompt.to_anki_cloze_text()
    assert "{{c1::Paris}}" in anki_text


def test_grouped_cloze_with_hints():
    """Test that grouped clozes with hints work correctly."""
    clozes = [
        ClozeMatch(
            full_text="{{2>apple|fruit}}",
            start=0,
            end=17,
            cloze_id="2",
            answer="apple",
            hint="fruit",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
        ClozeMatch(
            full_text="{{2>banana|fruit}}",
            start=22,
            end=40,
            cloze_id="2",
            answer="banana",
            hint="fruit",
            cloze_type=ClozeType.GROUPED,
            line_number=0,
            scope=ScopeSpec.default(),
        ),
    ]

    context = CardContext(
        content="{{2>apple|fruit}} and {{2>banana|fruit}}.",
        full_text="> ?\n> {{2>apple|fruit}} and {{2>banana|fruit}}.",
        start_line=0,
        end_line=1,
        line_numbers=[0, 1],
        cloze_matches=clozes,
    )

    prompts = generate_prompts(context, Path("/test.md"))

    assert len(prompts) == 1
    prompt = prompts[0]

    # Convert to Anki format
    anki_text = prompt.to_anki_cloze_text()

    # Each cloze should have its own hint
    assert "{{c1::apple::fruit}}" in anki_text
    assert "{{c1::banana::fruit}}" in anki_text

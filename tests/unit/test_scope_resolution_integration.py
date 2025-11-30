"""Integration tests for scope resolution with paragraph contexts."""

from pathlib import Path

from mnmd_anki_sync.parser.cloze_parser import parse_clozes
from mnmd_anki_sync.parser.context_extractor import extract_card_contexts
from mnmd_anki_sync.parser.prompt_generator import generate_prompts


class TestScopeModifierWithParagraphs:
    """Test scope modifiers work with paragraph-based (non > ?) contexts."""

    def test_scope_before_includes_previous_paragraph(self):
        """Test [-1] includes the paragraph before the cloze."""
        text = """Context paragraph here.

The answer is {{here}}[-1]."""

        contexts = extract_card_contexts(text)
        assert len(contexts) == 1

        # Parse clozes
        contexts[0].cloze_matches = parse_clozes(
            contexts[0].content, start_line=contexts[0].start_line
        )

        # Generate prompts with full document
        prompts = generate_prompts(contexts[0], Path("/test.md"), full_document=text)
        assert len(prompts) == 1

        # The prompt should include both paragraphs
        assert "Context paragraph here." in prompts[0].context
        assert "__CLOZE__" in prompts[0].context

    def test_scope_after_includes_next_paragraph(self):
        """Test [1] includes the paragraph after the cloze."""
        text = """The answer is {{here}}[1].

Context paragraph after."""

        contexts = extract_card_contexts(text)
        assert len(contexts) == 1

        contexts[0].cloze_matches = parse_clozes(
            contexts[0].content, start_line=contexts[0].start_line
        )

        prompts = generate_prompts(contexts[0], Path("/test.md"), full_document=text)
        assert len(prompts) == 1

        # The prompt should include both paragraphs
        assert "__CLOZE__" in prompts[0].context
        assert "Context paragraph after." in prompts[0].context

    def test_scope_both_directions(self):
        """Test [-1,1] includes paragraphs before and after."""
        text = """Before paragraph.

The answer is {{here}}[-1,1].

After paragraph."""

        contexts = extract_card_contexts(text)
        assert len(contexts) == 1

        contexts[0].cloze_matches = parse_clozes(
            contexts[0].content, start_line=contexts[0].start_line
        )

        prompts = generate_prompts(contexts[0], Path("/test.md"), full_document=text)
        assert len(prompts) == 1

        # The prompt should include all three paragraphs
        assert "Before paragraph." in prompts[0].context
        assert "__CLOZE__" in prompts[0].context
        assert "After paragraph." in prompts[0].context

    def test_no_scope_only_includes_current_paragraph(self):
        """Test that no scope modifier only includes the current paragraph."""
        text = """Before paragraph.

The answer is {{here}}.

After paragraph."""

        contexts = extract_card_contexts(text)
        assert len(contexts) == 1

        contexts[0].cloze_matches = parse_clozes(
            contexts[0].content, start_line=contexts[0].start_line
        )

        prompts = generate_prompts(contexts[0], Path("/test.md"), full_document=text)
        assert len(prompts) == 1

        # The prompt should only include the cloze paragraph
        assert "Before paragraph." not in prompts[0].context
        assert "__CLOZE__" in prompts[0].context
        assert "After paragraph." not in prompts[0].context

    def test_scope_with_explicit_block_uses_block_content(self):
        """Test that > ? blocks don't need scope modifiers (they define context)."""
        text = """> ?
> Context is defined here.
>
> The answer is {{here}}."""

        contexts = extract_card_contexts(text)
        assert len(contexts) == 1

        contexts[0].cloze_matches = parse_clozes(
            contexts[0].content, start_line=contexts[0].start_line
        )

        prompts = generate_prompts(contexts[0], Path("/test.md"), full_document=text)
        assert len(prompts) == 1

        # The prompt should include the full block content
        assert "Context is defined here." in prompts[0].context
        assert "__CLOZE__" in prompts[0].context

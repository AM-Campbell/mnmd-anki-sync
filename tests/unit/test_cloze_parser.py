"""Tests for cloze parser with CORRECT MNMD syntax."""

import pytest

from mnmd_anki_sync.models import ClozeType, ScopeSpec
from mnmd_anki_sync.parser.cloze_parser import parse_cloze_ids, parse_clozes, parse_scope


class TestParseClozeIds:
    """Test parsing of cloze ID strings."""

    def test_parse_simple_id(self):
        """Test parsing simple numeric ID."""
        cloze_id, seq, anki_id = parse_cloze_ids("1")
        assert cloze_id == "1"
        assert seq is None
        assert anki_id is None

    def test_parse_sequence_id(self):
        """Test parsing sequence ID (id.order)."""
        cloze_id, seq, anki_id = parse_cloze_ids("1.2")
        assert cloze_id == "1"
        assert seq == 2
        assert anki_id is None

    def test_parse_alpha_id(self):
        """Test parsing alphabetic Anki ID (base52)."""
        cloze_id, seq, anki_id = parse_cloze_ids("abc")
        assert cloze_id is None
        assert seq is None
        assert anki_id == "abc"

    def test_parse_id_with_anki_id(self):
        """Test parsing ID with Anki ID (cloze_id,anki_id)."""
        cloze_id, seq, anki_id = parse_cloze_ids("1,abcXYZ")
        assert cloze_id == "1"
        assert seq is None
        assert anki_id == "abcXYZ"

    def test_parse_anki_id_first(self):
        """Test parsing with Anki ID first (anki_id,cloze_id)."""
        cloze_id, seq, anki_id = parse_cloze_ids("abcXYZ,1")
        assert cloze_id == "1"
        assert seq is None
        assert anki_id == "abcXYZ"

    def test_parse_sequence_with_anki_id(self):
        """Test parsing sequence ID with Anki ID."""
        cloze_id, seq, anki_id = parse_cloze_ids("1.2,abcXYZ")
        assert cloze_id == "1"
        assert seq == 2
        assert anki_id == "abcXYZ"

    def test_parse_sequence_anki_id_first(self):
        """Test parsing sequence with Anki ID first."""
        cloze_id, seq, anki_id = parse_cloze_ids("abcXYZ,1.2")
        assert cloze_id == "1"
        assert seq == 2
        assert anki_id == "abcXYZ"


class TestParseScope:
    """Test parsing of scope specifications."""

    def test_parse_none_default(self):
        """Test parsing None with default."""
        scope = parse_scope(None, in_list=False)
        assert scope.before == 0
        assert scope.after == 0

    def test_parse_none_list(self):
        """Test parsing None in list context."""
        scope = parse_scope(None, in_list=True)
        assert scope.before == -1
        assert scope.after == 0

    def test_parse_single_negative(self):
        """Test parsing single negative value."""
        scope = parse_scope("-1")
        assert scope.before == -1
        assert scope.after == 0

    def test_parse_single_positive(self):
        """Test parsing single positive value."""
        scope = parse_scope("2")
        assert scope.before == 0
        assert scope.after == 2

    def test_parse_before_and_after(self):
        """Test parsing before,after specification."""
        scope = parse_scope("-1,2")
        assert scope.before == -1
        assert scope.after == 2


class TestParseClozes:
    """Test parsing clozes from text."""

    def test_parse_basic_cloze(self):
        """Test parsing basic cloze."""
        text = "The answer is {{42}}."
        clozes = parse_clozes(text)

        assert len(clozes) == 1
        assert clozes[0].answer == "42"
        assert clozes[0].cloze_type == ClozeType.BASIC
        assert clozes[0].cloze_id is None
        assert clozes[0].anki_id is None
        assert clozes[0].hint is None
        assert clozes[0].extra is None

    def test_parse_grouped_cloze(self):
        """Test parsing grouped cloze."""
        text = "I like {{1>apples}} and {{1>oranges}}."
        clozes = parse_clozes(text)

        assert len(clozes) == 2
        assert clozes[0].cloze_id == "1"
        assert clozes[1].cloze_id == "1"
        assert clozes[0].cloze_type == ClozeType.GROUPED
        assert clozes[1].cloze_type == ClozeType.GROUPED
        assert clozes[0].answer == "apples"
        assert clozes[1].answer == "oranges"

    def test_parse_sequence_cloze(self):
        """Test parsing sequence cloze."""
        text = "{{1.1>First}} {{1.2>Second}} {{1.3>Third}}"
        clozes = parse_clozes(text)

        assert len(clozes) == 3
        assert clozes[0].sequence_order == 1
        assert clozes[1].sequence_order == 2
        assert clozes[2].sequence_order == 3
        assert all(c.cloze_type == ClozeType.SEQUENCE for c in clozes)
        assert all(c.cloze_id == "1" for c in clozes)

    def test_parse_with_anki_id(self):
        """Test parsing cloze with Anki ID."""
        text = "Answer: {{1,abcXYZ>hello}}"
        clozes = parse_clozes(text)

        assert clozes[0].cloze_id == "1"
        assert clozes[0].anki_id == "abcXYZ"
        assert clozes[0].answer == "hello"

    def test_parse_with_anki_id_first(self):
        """Test parsing with Anki ID in first position."""
        text = "Answer: {{abcXYZ,1>hello}}"
        clozes = parse_clozes(text)

        assert clozes[0].cloze_id == "1"
        assert clozes[0].anki_id == "abcXYZ"
        assert clozes[0].answer == "hello"

    def test_parse_with_scope(self):
        """Test parsing cloze with scope specification."""
        text = "Text {{answer}}[-1,2]"
        clozes = parse_clozes(text)

        assert clozes[0].scope.before == -1
        assert clozes[0].scope.after == 2

    def test_parse_with_hint(self):
        """Test parsing cloze with hint."""
        text = "{{Python|programming language created by Guido}} is great."
        clozes = parse_clozes(text)

        assert len(clozes) == 1
        assert clozes[0].answer == "Python"
        assert clozes[0].hint == "programming language created by Guido"
        assert clozes[0].cloze_type == ClozeType.BASIC
        assert clozes[0].extra is None

    def test_parse_grouped_with_hint(self):
        """Test parsing grouped cloze with hint."""
        text = "The {{1.2>404 Not Found|In the 4xx range}} error."
        clozes = parse_clozes(text)

        assert clozes[0].cloze_id == "1"
        assert clozes[0].sequence_order == 2
        assert clozes[0].answer == "404 Not Found"
        assert clozes[0].hint == "In the 4xx range"
        assert clozes[0].cloze_type == ClozeType.SEQUENCE

    def test_parse_with_extra(self):
        """Test parsing cloze with extra info."""
        text = "Package manager is {{pip<PyPI hosts over 400,000 packages}}."
        clozes = parse_clozes(text)

        assert len(clozes) == 1
        assert clozes[0].answer == "pip"
        assert clozes[0].extra == "PyPI hosts over 400,000 packages"
        assert clozes[0].hint is None
        assert clozes[0].cloze_type == ClozeType.BASIC

    def test_parse_with_hint_and_extra(self):
        """Test parsing cloze with both hint and extra."""
        text = "The {{staging area|second area<Also called the index}} in git."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "staging area"
        assert clozes[0].hint == "second area"
        assert clozes[0].extra == "Also called the index"

    def test_parse_multiple_basic_clozes(self):
        """Test parsing multiple basic clozes."""
        text = "My favorite {{sport}} is {{running}}."
        clozes = parse_clozes(text)

        assert len(clozes) == 2
        assert clozes[0].answer == "sport"
        assert clozes[1].answer == "running"
        assert all(c.cloze_type == ClozeType.BASIC for c in clozes)

    def test_parse_complex_combination(self):
        """Test parsing complex combination of clozes."""
        text = "{{1.1>First}} basic {{test|a hint}} and {{1.2>second<extra>}} with {{2>shared}}."
        clozes = parse_clozes(text)

        assert len(clozes) == 4
        # Check sequence clozes
        assert clozes[0].cloze_type == ClozeType.SEQUENCE
        assert clozes[0].sequence_order == 1
        assert clozes[0].answer == "First"
        # Check basic cloze with hint
        assert clozes[1].cloze_type == ClozeType.BASIC
        assert clozes[1].answer == "test"
        assert clozes[1].hint == "a hint"
        # Check sequence with extra
        assert clozes[2].cloze_type == ClozeType.SEQUENCE
        assert clozes[2].sequence_order == 2
        assert clozes[2].answer == "second"
        assert clozes[2].extra == "extra>"
        # Check grouped cloze
        assert clozes[3].cloze_type == ClozeType.GROUPED
        assert clozes[3].cloze_id == "2"

    def test_parse_preserves_positions(self):
        """Test that parsing preserves correct positions."""
        text = "Start {{first}} middle {{second}} end."
        clozes = parse_clozes(text)

        assert clozes[0].start == 6  # Position of {{first}}
        assert clozes[1].start == 23  # Position of {{second}}

    def test_parse_math_inline(self):
        """Test parsing math with $ delimiters."""
        text = "Einstein's {{$E = mc^2$|famous equation}}."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "$E = mc^2$"
        assert clozes[0].hint == "famous equation"

    def test_parse_math_complex(self):
        """Test parsing complex math expression."""
        text = "Solution: {{(-b ± √(b² - 4ac)) / 2a}}"
        clozes = parse_clozes(text)

        assert clozes[0].answer == "(-b ± √(b² - 4ac)) / 2a"

    def test_parse_with_markdown(self):
        """Test parsing clozes containing markdown."""
        text = "Supports **{{bold}}** and *{{italic}}* text."
        clozes = parse_clozes(text)

        assert len(clozes) == 2
        assert clozes[0].answer == "bold"
        assert clozes[1].answer == "italic"

    def test_parse_with_code(self):
        """Test parsing clozes with inline code."""
        text = "List comprehension: {{`[x for x in iterable]`}}"
        clozes = parse_clozes(text)

        assert clozes[0].answer == "`[x for x in iterable]`"

    def test_parse_comma_in_answer(self):
        """Test parsing answer containing commas."""
        text = "Data: {{ordered, mutable}}"
        clozes = parse_clozes(text)

        assert clozes[0].answer == "ordered, mutable"

    def test_parse_reflow_single_newline_in_answer(self):
        """Test that single newlines in answer are normalized to spaces (reflow)."""
        text = "The capital is {{a very\nlong answer}}."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "a very long answer"

    def test_parse_reflow_single_newline_in_hint(self):
        """Test that single newlines in hint are normalized to spaces."""
        text = "Answer: {{Paris|the capital\nof France}}."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "Paris"
        assert clozes[0].hint == "the capital of France"

    def test_parse_reflow_single_newline_in_extra(self):
        """Test that single newlines in extra are normalized to spaces."""
        text = "Answer: {{pip<PyPI hosts over\n400,000 packages}}."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "pip"
        assert clozes[0].extra == "PyPI hosts over 400,000 packages"

    def test_parse_reflow_multiple_newlines_preserved(self):
        """Test that double newlines (paragraph breaks) are preserved."""
        text = "Answer: {{first paragraph\n\nsecond paragraph}}."
        clozes = parse_clozes(text)

        assert clozes[0].answer == "first paragraph\n\nsecond paragraph"

    def test_parse_reflow_complex_with_all_parts(self):
        """Test reflow normalization in answer, hint, and extra together."""
        text = "Test: {{long\nanswer|long\nhint<long\nextra}}"
        clozes = parse_clozes(text)

        assert clozes[0].answer == "long answer"
        assert clozes[0].hint == "long hint"
        assert clozes[0].extra == "long extra"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_cloze_body_skipped(self):
        """Test that empty cloze bodies are skipped."""
        text = "Empty: {{}} and valid {{answer}}."
        clozes = parse_clozes(text)

        # Empty cloze should be skipped
        assert len(clozes) == 1
        assert clozes[0].answer == "answer"

    def test_whitespace_only_cloze_skipped(self):
        """Test that whitespace-only cloze bodies are skipped."""
        text = "Whitespace: {{   }} and valid {{answer}}."
        clozes = parse_clozes(text)

        # Whitespace-only cloze should be skipped
        assert len(clozes) == 1
        assert clozes[0].answer == "answer"

    def test_only_hint_cloze_skipped(self):
        """Test that cloze with only hint (empty answer) is skipped."""
        text = "Only hint: {{|just a hint}} and valid {{answer}}."
        clozes = parse_clozes(text)

        # Cloze with only hint (empty answer) should be skipped
        assert len(clozes) == 1
        assert clozes[0].answer == "answer"

    def test_only_extra_cloze_skipped(self):
        """Test that cloze with only extra (empty answer) is skipped."""
        text = "Only extra: {{<just extra}} and valid {{answer}}."
        clozes = parse_clozes(text)

        # Cloze with only extra (empty answer) should be skipped
        assert len(clozes) == 1
        assert clozes[0].answer == "answer"

    def test_invalid_sequence_order_ignored(self):
        """Test that invalid sequence order (non-numeric) is handled gracefully."""
        cloze_id, seq, anki_id = parse_cloze_ids("1.abc")

        assert cloze_id == "1"
        assert seq is None  # Invalid order should be None
        assert anki_id is None

    def test_invalid_scope_returns_default(self):
        """Test that invalid scope specification returns default."""
        scope = parse_scope("abc")
        assert scope.before == 0
        assert scope.after == 0

    def test_invalid_scope_two_parts_returns_default(self):
        """Test that invalid two-part scope returns default."""
        scope = parse_scope("abc,def")
        assert scope.before == 0
        assert scope.after == 0

    def test_unclosed_cloze_ignored(self):
        """Test that unclosed cloze braces are ignored."""
        text = "Unclosed {{without closing and valid {{answer}}."
        clozes = parse_clozes(text)

        # Only the properly closed cloze should be parsed
        assert len(clozes) == 1
        assert clozes[0].answer == "answer"

    def test_nested_braces_in_latex(self):
        """Test that nested braces in LaTeX are handled correctly."""
        text = "Math: {{$\\frac{a}{b}$}}"
        clozes = parse_clozes(text)

        assert len(clozes) == 1
        assert clozes[0].answer == "$\\frac{a}{b}$"

    def test_deeply_nested_braces(self):
        """Test parsing with deeply nested braces."""
        text = "Nested: {{${a{b{c}}}$}}"
        clozes = parse_clozes(text)

        assert len(clozes) == 1
        assert clozes[0].answer == "${a{b{c}}}$"

    def test_mixed_valid_invalid_ids(self):
        """Test parsing with mixed valid and invalid ID parts."""
        # Should ignore the invalid "123abc" part (not purely numeric or alphabetic)
        cloze_id, seq, anki_id = parse_cloze_ids("1,123abc,xyz")

        assert cloze_id == "1"
        assert anki_id == "xyz"

    def test_empty_id_string(self):
        """Test parsing empty ID string."""
        cloze_id, seq, anki_id = parse_cloze_ids("")

        assert cloze_id is None
        assert seq is None
        assert anki_id is None

    def test_none_id_string(self):
        """Test parsing None ID string."""
        cloze_id, seq, anki_id = parse_cloze_ids(None)

        assert cloze_id is None
        assert seq is None
        assert anki_id is None

    def test_scope_with_spaces(self):
        """Test scope parsing handles spaces correctly."""
        scope = parse_scope("-1, 2")
        assert scope.before == -1
        assert scope.after == 2

    def test_large_scope_values(self):
        """Test scope with large values."""
        scope = parse_scope("-100,100")
        assert scope.before == -100
        assert scope.after == 100

    def test_consecutive_clozes(self):
        """Test parsing consecutive clozes without space."""
        text = "{{first}}{{second}}{{third}}"
        clozes = parse_clozes(text)

        assert len(clozes) == 3
        assert clozes[0].answer == "first"
        assert clozes[1].answer == "second"
        assert clozes[2].answer == "third"

    def test_cloze_at_line_boundaries(self):
        """Test clozes at start and end of lines."""
        text = "{{start}}\nmiddle\n{{end}}"
        clozes = parse_clozes(text)

        assert len(clozes) == 2
        assert clozes[0].answer == "start"
        assert clozes[0].line_number == 0
        assert clozes[1].answer == "end"
        assert clozes[1].line_number == 2

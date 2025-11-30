"""Tests for ID writer module."""

import tempfile
from pathlib import Path

from mnmd_anki_sync.models import ClozeMatch, ClozeType, Prompt, ScopeSpec
from mnmd_anki_sync.sync.id_writer import write_ids_to_file


def create_cloze_match(
    full_text: str,
    start: int,
    end: int,
    answer: str,
    cloze_id: str = None,
    sequence_order: int = None,
    anki_id: str = None,
    hint: str = None,
    extra: str = None,
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
        extra=extra,
        cloze_type=cloze_type,
        line_number=line_number,
        scope=ScopeSpec.default(),
    )


def create_prompt(cloze_match: ClozeMatch, context: str = "test") -> Prompt:
    """Helper to create Prompt objects."""
    return Prompt(
        cloze_match=cloze_match,
        context=context,
        anki_id=cloze_match.anki_id,
        file_path=Path("/tmp/test.md"),
        line_number=cloze_match.line_number,
    )


class TestWriteIdsToFile:
    """Test writing Anki IDs back to files."""

    def test_write_basic_cloze_id(self):
        """Test writing ID to a basic cloze."""
        content = "The answer is {{42}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{42}}",
            start=14,
            end=20,
            answer="42",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "The answer is {{abcXYZ>42}}."

    def test_write_grouped_cloze_id(self):
        """Test writing ID to a grouped cloze."""
        content = "I like {{1>apples}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{1>apples}}",
            start=7,
            end=19,
            answer="apples",
            cloze_id="1",
            anki_id="abcXYZ",
            cloze_type=ClozeType.GROUPED,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "I like {{1,abcXYZ>apples}}."

    def test_write_sequence_cloze_id(self):
        """Test writing ID to a sequence cloze."""
        content = "Step {{1.1>first}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{1.1>first}}",
            start=5,
            end=18,
            answer="first",
            cloze_id="1",
            sequence_order=1,
            anki_id="abcXYZ",
            cloze_type=ClozeType.SEQUENCE,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "Step {{1.1,abcXYZ>first}}."

    def test_skip_cloze_without_anki_id(self):
        """Test that clozes without Anki IDs are skipped."""
        content = "The answer is {{42}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{42}}",
            start=14,
            end=20,
            answer="42",
            anki_id=None,  # No Anki ID
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == content  # Unchanged

    def test_skip_already_written_id(self):
        """Test that already-written IDs are not duplicated."""
        content = "The answer is {{abcXYZ>42}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{abcXYZ>42}}",
            start=14,
            end=27,
            answer="42",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == content  # Unchanged

    def test_write_multiple_clozes(self):
        """Test writing IDs to multiple clozes."""
        content = "{{first}} and {{second}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze1 = create_cloze_match(
            full_text="{{first}}",
            start=0,
            end=9,
            answer="first",
            anki_id="aaaaaa",
            cloze_type=ClozeType.BASIC,
        )
        cloze2 = create_cloze_match(
            full_text="{{second}}",
            start=14,
            end=24,
            answer="second",
            anki_id="bbbbbb",
            cloze_type=ClozeType.BASIC,
        )
        prompts = [create_prompt(cloze1), create_prompt(cloze2)]

        write_ids_to_file(file_path, prompts)

        result = file_path.read_text()
        assert result == "{{aaaaaa>first}} and {{bbbbbb>second}}."

    def test_write_preserves_scope(self):
        """Test that scope specifications are preserved."""
        content = "The answer is {{42}}[-1,2]."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{42}}[-1,2]",
            start=14,
            end=26,
            answer="42",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "The answer is {{abcXYZ>42}}[-1,2]."

    def test_write_preserves_hint(self):
        """Test that hints are preserved."""
        content = "The answer is {{Python|programming language}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{Python|programming language}}",
            start=14,
            end=45,
            answer="Python",
            hint="programming language",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "The answer is {{abcXYZ>Python|programming language}}."

    def test_write_preserves_extra(self):
        """Test that extra info is preserved."""
        content = "The answer is {{pip<PyPI has packages}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{pip<PyPI has packages}}",
            start=14,
            end=39,
            answer="pip",
            extra="PyPI has packages",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert result == "The answer is {{abcXYZ>pip<PyPI has packages}}."

    def test_write_grouped_clozes_same_id(self):
        """Test writing the same ID to all clozes in a group."""
        content = "I like {{1>apples}} and {{1>oranges}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze1 = create_cloze_match(
            full_text="{{1>apples}}",
            start=7,
            end=19,
            answer="apples",
            cloze_id="1",
            anki_id="abcXYZ",
            cloze_type=ClozeType.GROUPED,
        )
        cloze2 = create_cloze_match(
            full_text="{{1>oranges}}",
            start=24,
            end=37,
            answer="oranges",
            cloze_id="1",
            anki_id="abcXYZ",
            cloze_type=ClozeType.GROUPED,
        )

        # Prompt with group_clozes
        prompt = Prompt(
            cloze_match=cloze1,
            context="test",
            anki_id="abcXYZ",
            file_path=Path("/tmp/test.md"),
            line_number=0,
            group_clozes=[cloze1, cloze2],
        )

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        assert "{{1,abcXYZ>apples}}" in result
        assert "{{1,abcXYZ>oranges}}" in result

    def test_write_empty_prompts_list(self):
        """Test that empty prompts list doesn't modify file."""
        content = "The answer is {{42}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        write_ids_to_file(file_path, [])

        result = file_path.read_text()
        assert result == content  # Unchanged

    def test_write_multiline_cloze(self):
        """Test writing ID to a cloze spanning multiple lines."""
        content = "The answer is {{a very\nlong answer}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze = create_cloze_match(
            full_text="{{a very\nlong answer}}",
            start=14,
            end=36,
            answer="a very long answer",  # Normalized
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        result = file_path.read_text()
        # The content should be extracted and ID added
        assert "abcXYZ>" in result

    def test_reverse_order_replacement(self):
        """Test that replacements are done in reverse order to preserve positions."""
        # Two clozes where the second one's position would be affected if first is replaced first
        content = "{{short}} {{longertext}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        cloze1 = create_cloze_match(
            full_text="{{short}}",
            start=0,
            end=9,
            answer="short",
            anki_id="aaaaaa",
            cloze_type=ClozeType.BASIC,
        )
        cloze2 = create_cloze_match(
            full_text="{{longertext}}",
            start=10,
            end=24,
            answer="longertext",
            anki_id="bbbbbb",
            cloze_type=ClozeType.BASIC,
        )
        prompts = [create_prompt(cloze1), create_prompt(cloze2)]

        write_ids_to_file(file_path, prompts)

        result = file_path.read_text()
        # Both should be correctly replaced
        assert "{{aaaaaa>short}}" in result
        assert "{{bbbbbb>longertext}}" in result


class TestAtomicWrite:
    """Test atomic file writing behavior."""

    def test_temp_file_cleaned_on_success(self):
        """Test that temp file is removed after successful write."""
        content = "The answer is {{42}}."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            file_path = Path(f.name)

        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

        cloze = create_cloze_match(
            full_text="{{42}}",
            start=14,
            end=20,
            answer="42",
            anki_id="abcXYZ",
            cloze_type=ClozeType.BASIC,
        )
        prompt = create_prompt(cloze)

        write_ids_to_file(file_path, [prompt])

        assert not temp_path.exists()
        assert file_path.exists()

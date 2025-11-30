"""Tests for file ID utilities."""

import tempfile
from pathlib import Path

from mnmd_anki_sync.utils.file_id import (
    ensure_file_id,
    extract_file_id,
    generate_file_id,
    get_file_tag,
)


class TestGenerateFileID:
    """Tests for generate_file_id()."""

    def test_generates_8_char_id(self):
        """Test that generated ID is 8 characters."""
        file_id = generate_file_id()
        assert len(file_id) == 8

    def test_generates_unique_ids(self):
        """Test that each call generates a unique ID."""
        id1 = generate_file_id()
        id2 = generate_file_id()
        assert id1 != id2

    def test_generates_alphanumeric(self):
        """Test that ID contains only alphanumeric and safe chars."""
        file_id = generate_file_id()
        assert file_id.replace("-", "").replace("_", "").isalnum()


class TestExtractFileID:
    """Tests for extract_file_id()."""

    def test_extracts_from_frontmatter(self):
        """Test extracting ID from YAML frontmatter."""
        content = """---
mnmd_file_id: abc123xy
---

# Content here
"""
        assert extract_file_id(content) == "abc123xy"

    def test_extracts_with_other_frontmatter(self):
        """Test extracting ID from frontmatter with other fields."""
        content = """---
title: My Notes
author: Test User
mnmd_file_id: xyz789ab
tags: [test, notes]
---

# Content here
"""
        assert extract_file_id(content) == "xyz789ab"

    def test_returns_none_without_frontmatter(self):
        """Test returns None when no frontmatter."""
        content = "# Just a heading\n\nWith some content."
        assert extract_file_id(content) is None

    def test_returns_none_without_id_field(self):
        """Test returns None when frontmatter has no ID."""
        content = """---
title: My Notes
author: Test User
---

# Content here
"""
        assert extract_file_id(content) is None

    def test_handles_malformed_frontmatter(self):
        """Test handles malformed frontmatter gracefully."""
        content = """---
title: My Notes
mnmd_file_id
---

# Content here
"""
        assert extract_file_id(content) is None


class TestEnsureFileID:
    """Tests for ensure_file_id()."""

    def test_adds_id_to_file_without_frontmatter(self):
        """Test adds ID to file without frontmatter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Content\n\nSome text here.")
            temp_path = Path(f.name)

        try:
            file_id, modified = ensure_file_id(temp_path)

            # Should be modified
            assert modified is True
            assert len(file_id) == 8

            # Read back content
            content = temp_path.read_text()

            # Should have frontmatter now
            assert content.startswith("---\n")
            assert f"mnmd_file_id: {file_id}" in content
            assert "# Test Content" in content
        finally:
            temp_path.unlink()

    def test_adds_id_to_existing_frontmatter(self):
        """Test adds ID to existing frontmatter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """---
title: My Notes
author: Test User
---

# Test Content
"""
            )
            temp_path = Path(f.name)

        try:
            file_id, modified = ensure_file_id(temp_path)

            # Should be modified
            assert modified is True
            assert len(file_id) == 8

            # Read back content
            content = temp_path.read_text()

            # Should have ID in frontmatter
            assert f"mnmd_file_id: {file_id}" in content
            assert "title: My Notes" in content
            assert "author: Test User" in content
        finally:
            temp_path.unlink()

    def test_does_not_modify_file_with_existing_id(self):
        """Test doesn't modify file that already has ID."""
        existing_id = "test1234"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                f"""---
mnmd_file_id: {existing_id}
---

# Test Content
"""
            )
            temp_path = Path(f.name)

        try:
            file_id, modified = ensure_file_id(temp_path)

            # Should NOT be modified
            assert modified is False
            assert file_id == existing_id

            # Read back content - should be unchanged
            content = temp_path.read_text()
            assert f"mnmd_file_id: {existing_id}" in content
        finally:
            temp_path.unlink()

    def test_stable_id_across_calls(self):
        """Test that same file gets same ID across multiple calls."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Content")
            temp_path = Path(f.name)

        try:
            file_id1, modified1 = ensure_file_id(temp_path)
            file_id2, modified2 = ensure_file_id(temp_path)

            # First call should modify
            assert modified1 is True
            # Second call should not
            assert modified2 is False
            # IDs should match
            assert file_id1 == file_id2
        finally:
            temp_path.unlink()


class TestGetFileTag:
    """Tests for get_file_tag()."""

    def test_returns_correct_format(self):
        """Test tag format is correct."""
        file_id = "abc123xy"
        tag = get_file_tag(file_id)
        assert tag == "mnmd-file-abc123xy"

    def test_works_with_different_ids(self):
        """Test works with various file IDs."""
        assert get_file_tag("test1234") == "mnmd-file-test1234"
        assert get_file_tag("xyz789ab") == "mnmd-file-xyz789ab"

"""Tests for base52 encoding/decoding."""

import pytest

from mnmd_anki_sync.utils.base52 import decode_base52, encode_base52


class TestBase52Encoding:
    """Test base52 encoding functionality."""

    def test_encode_zero(self):
        """Test encoding zero."""
        assert encode_base52(0) == "a"

    def test_encode_small_numbers(self):
        """Test encoding small numbers."""
        assert encode_base52(1) == "b"
        assert encode_base52(25) == "z"
        assert encode_base52(26) == "A"
        assert encode_base52(51) == "Z"

    def test_encode_larger_numbers(self):
        """Test encoding larger numbers."""
        assert encode_base52(52) == "ba"
        assert encode_base52(1234567890) == "dmSkYk"

    def test_encode_anki_ids(self):
        """Test encoding realistic Anki note IDs."""
        # Anki note IDs are typically large integers
        assert isinstance(encode_base52(1609459200000), str)
        assert encode_base52(1609459200000).isalpha()


class TestBase52Decoding:
    """Test base52 decoding functionality."""

    def test_decode_single_char(self):
        """Test decoding single character strings."""
        assert decode_base52("a") == 0
        assert decode_base52("b") == 1
        assert decode_base52("z") == 25
        assert decode_base52("A") == 26
        assert decode_base52("Z") == 51

    def test_decode_multi_char(self):
        """Test decoding multi-character strings."""
        assert decode_base52("ba") == 52
        assert decode_base52("dmSkYk") == 1234567890

    def test_decode_invalid_string(self):
        """Test decoding with invalid characters."""
        with pytest.raises(ValueError, match="Invalid base52 string"):
            decode_base52("abc123")

        with pytest.raises(ValueError, match="Invalid base52 string"):
            decode_base52("abc-def")

    def test_decode_empty_string(self):
        """Test decoding empty string."""
        with pytest.raises(ValueError):
            decode_base52("")


class TestBase52Roundtrip:
    """Test base52 encoding/decoding roundtrip."""

    @pytest.mark.parametrize(
        "number",
        [
            0,
            1,
            52,
            100,
            1000,
            10000,
            1234567890,
            1609459200000,  # Typical Anki ID
            9999999999999,  # Large Anki ID
        ],
    )
    def test_roundtrip(self, number):
        """Test that encode -> decode returns original number."""
        encoded = encode_base52(number)
        decoded = decode_base52(encoded)
        assert decoded == number

    def test_encoded_is_alphabetic(self):
        """Test that all encoded strings are purely alphabetic."""
        for num in [0, 1, 52, 1000, 1234567890]:
            encoded = encode_base52(num)
            assert encoded.isalpha(), f"Encoded {num} as {encoded!r} contains non-alpha characters"

"""Base52 encoding for Anki note IDs.

Uses case-sensitive alphabetic characters only (no digits) to avoid confusion with cloze IDs.
"""

BASE52_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base52(num: int) -> str:
    """Convert a number to base52 string (letters only).

    Args:
        num: The number to encode (Anki note ID)

    Returns:
        Base52 encoded string

    Examples:
        >>> encode_base52(0)
        'a'
        >>> encode_base52(52)
        'ba'
        >>> encode_base52(1234567890)
        'bkcQMk'
    """
    if num == 0:
        return BASE52_CHARS[0]

    result = []
    while num:
        result.append(BASE52_CHARS[num % 52])
        num //= 52
    return "".join(reversed(result))


def decode_base52(s: str) -> int:
    """Convert a base52 string back to a number.

    Args:
        s: Base52 encoded string

    Returns:
        Decoded number (Anki note ID)

    Raises:
        ValueError: If string contains non-alphabetic characters

    Examples:
        >>> decode_base52('a')
        0
        >>> decode_base52('ba')
        52
        >>> decode_base52('bkcQMk')
        1234567890
    """
    if not s.isalpha():
        raise ValueError(f"Invalid base52 string: {s!r}. Must contain only letters.")

    result = 0
    for char in s:
        if char not in BASE52_CHARS:
            raise ValueError(f"Invalid character {char!r} in base52 string")
        result = result * 52 + BASE52_CHARS.index(char)
    return result

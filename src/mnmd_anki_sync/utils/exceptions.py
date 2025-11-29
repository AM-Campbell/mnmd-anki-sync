"""Custom exceptions for mnmd-anki-sync."""


class MNMDError(Exception):
    """Base exception for all mnmd-anki-sync errors."""

    pass


class AnkiConnectionError(MNMDError):
    """Raised when cannot connect to AnkiConnect."""

    pass


class AnkiAPIError(MNMDError):
    """Raised when AnkiConnect API returns an error."""

    pass


class ParseError(MNMDError):
    """Raised when markdown parsing fails."""

    pass


class ValidationError(MNMDError):
    """Raised when data validation fails."""

    pass


class ConfigError(MNMDError):
    """Raised when configuration is invalid."""

    pass

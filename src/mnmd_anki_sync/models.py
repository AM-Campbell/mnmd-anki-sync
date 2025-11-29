"""Pydantic models for mnmd-anki-sync."""

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClozeType(str, Enum):
    """Type of cloze deletion."""

    BASIC = "basic"  # {{text}}  or {{text|hint}}  or {{text<extra}}
    GROUPED = "grouped"  # {{id>text}}  or {{id>text|hint<extra}}
    SEQUENCE = "sequence"  # {{id.order>text}}  or {{id.order>text|hint<extra}}


class ScopeSpec(BaseModel):
    """Paragraph scope specification for context."""

    before: int = Field(default=0, description="Paragraphs before (0 or negative)")
    after: int = Field(default=0, description="Paragraphs after (0 or positive)")

    @field_validator("before")
    @classmethod
    def validate_before(cls, v: int) -> int:
        """Ensure before is non-positive."""
        if v > 0:
            return -v  # Auto-correct to negative
        return v

    @field_validator("after")
    @classmethod
    def validate_after(cls, v: int) -> int:
        """Ensure after is non-negative."""
        if v < 0:
            return -v  # Auto-correct to positive
        return v

    @classmethod
    def default(cls) -> "ScopeSpec":
        """Default scope: current paragraph only."""
        return cls(before=0, after=0)

    @classmethod
    def list_default(cls) -> "ScopeSpec":
        """Default for list items: include paragraph before."""
        return cls(before=-1, after=0)


class ClozeMatch(BaseModel):
    """Raw cloze match from regex parsing."""

    full_text: str = Field(description="Complete {{...}} text")
    start: int = Field(description="Start position in context")
    end: int = Field(description="End position in context")
    cloze_id: Optional[str] = Field(default=None, description="Group ID (e.g., '1' or 'poetry')")
    sequence_order: Optional[int] = Field(default=None, description="Sequence order (e.g., 1, 2, 3)")
    anki_id: Optional[str] = Field(default=None, description="Base52 Anki note ID")
    answer: str = Field(description="The occluded text")
    hint: Optional[str] = Field(default=None, description="Hint text")
    extra: Optional[str] = Field(default=None, description="Extra text")
    scope: ScopeSpec = Field(default_factory=ScopeSpec.default, description="Scope specification")
    cloze_type: ClozeType = Field(description="Type of cloze")
    line_number: int = Field(description="Line in source file")

    @field_validator("anki_id")
    @classmethod
    def validate_anki_id(cls, v: Optional[str]) -> Optional[str]:
        """Ensure anki_id is alphabetic if provided."""
        if v is not None and not v.isalpha():
            raise ValueError(f"Anki ID must be alphabetic (base52), got: {v!r}")
        return v


class Prompt(BaseModel):
    """A single Anki prompt (one cloze revealed, others hidden/shown)."""

    cloze_match: ClozeMatch = Field(description="The cloze this prompt tests")
    context: str = Field(description="Full context with __CLOZE__ placeholder(s)")
    anki_id: Optional[str] = Field(default=None, description="Anki note ID (base52)")
    file_path: Path = Field(description="Source file")
    line_number: int = Field(description="Line number for source link")
    deck_name: str = Field(default="Default", description="Target Anki deck")
    tags: List[str] = Field(default_factory=lambda: ["mnmd"], description="Anki tags")
    group_clozes: Optional[List[ClozeMatch]] = Field(
        default=None, description="For grouped clozes, list of all clozes in group"
    )

    def to_anki_cloze_text(self) -> str:
        """Convert to Anki cloze format {{c1::answer}} or {{c1::answer::hint}}.

        Converts markdown to HTML and replaces __CLOZE__ placeholder(s).
        Also converts math in answers and hints.

        Returns:
            Anki-formatted cloze text (HTML)
        """
        from .utils.markdown_utils import markdown_to_html, convert_math_to_anki

        context_text = self.context

        # Handle grouped clozes differently
        if self.group_clozes and len(self.group_clozes) > 1:
            # For grouped clozes, replace each indexed placeholder with its answer
            for i, cloze in enumerate(self.group_clozes):
                placeholder = f"__CLOZE_{i}__"
                safe_placeholder = f"<span id='mnmd-cloze-{i}'></span>"
                context_text = context_text.replace(placeholder, safe_placeholder)

            # Convert markdown to HTML
            html_context = markdown_to_html(context_text)

            # Replace each safe placeholder with its answer (all using c1)
            for i, cloze in enumerate(self.group_clozes):
                safe_placeholder = f"<span id='mnmd-cloze-{i}'></span>"
                # All grouped clozes use c1, with hint if present
                # Convert math in answer and hint
                answer = convert_math_to_anki(cloze.answer)
                hint_text = f"::{convert_math_to_anki(cloze.hint)}" if cloze.hint else ""
                html_context = html_context.replace(
                    safe_placeholder, f"{{{{c1::{answer}{hint_text}}}}}"
                )

            return html_context
        else:
            # Single cloze - use simple placeholder
            SAFE_PLACEHOLDER = "<span id='mnmd-cloze'></span>"

            # Replace __CLOZE__ with safe placeholder
            safe_context = context_text.replace("__CLOZE__", SAFE_PLACEHOLDER)

            # Convert markdown to HTML
            html_context = markdown_to_html(safe_context)

            # Replace safe placeholder with Anki cloze syntax
            # Convert math in answer and hint
            answer = convert_math_to_anki(self.cloze_match.answer)
            hint_text = f"::{convert_math_to_anki(self.cloze_match.hint)}" if self.cloze_match.hint else ""
            return html_context.replace(
                SAFE_PLACEHOLDER, f"{{{{c1::{answer}{hint_text}}}}}"
            )


    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow Path type


class CardContext(BaseModel):
    """A card context (> ? block) containing multiple clozes."""

    content: str = Field(description="Clean content (without > prefixes)")
    full_text: str = Field(description="Original text with > prefixes")
    start_line: int = Field(description="Starting line number")
    end_line: int = Field(description="Ending line number")
    line_numbers: List[int] = Field(description="All line numbers in context")
    cloze_matches: List[ClozeMatch] = Field(
        default_factory=list, description="Parsed clozes in this context"
    )
    prompts: List[Prompt] = Field(default_factory=list, description="Generated prompts")


class ClozeGroup(BaseModel):
    """A group of related clozes (for grouped and sequence clozes)."""

    group_id: str = Field(description="Group identifier")
    clozes: List[ClozeMatch] = Field(description="All clozes in this group")
    is_sequence: bool = Field(default=False, description="True for sequence clozes")

    def get_sequence_clozes(self) -> List[ClozeMatch]:
        """Get clozes sorted by sequence order.

        Returns:
            Sorted list of clozes (by sequence_order if is_sequence)
        """
        if not self.is_sequence:
            return self.clozes
        return sorted(self.clozes, key=lambda c: c.sequence_order or 0)

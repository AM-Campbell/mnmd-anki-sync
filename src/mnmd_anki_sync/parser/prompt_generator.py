"""Generate Anki prompts from parsed clozes."""

from pathlib import Path
from typing import Dict, List, Optional

from ..models import CardContext, ClozeGroup, ClozeMatch, ClozeType, Prompt
from .scope_resolver import resolve_context_scope


def generate_prompts(card_context: CardContext, file_path: Path) -> List[Prompt]:
    """Generate all prompts from a card context.

    Handles:
    - Basic clozes: One prompt per cloze
    - Grouped clozes: One prompt for all clozes with same ID
    - Sequence clozes: Progressive reveal prompts

    Args:
        card_context: The card context containing clozes
        file_path: Path to source file

    Returns:
        List of Prompt objects
    """
    clozes = card_context.cloze_matches

    if not clozes:
        return []

    # Group clozes by ID
    groups = _group_clozes(clozes)
    prompts = []

    for group in groups.values():
        if group.is_sequence:
            # Generate sequence prompts (progressive reveal)
            prompts.extend(_generate_sequence_prompts(group, card_context, file_path))
        else:
            # Generate single prompt for group (or individual if no group)
            prompt = _generate_group_prompt(group, card_context, file_path)
            if prompt:
                prompts.append(prompt)

    return prompts


def _group_clozes(clozes: List[ClozeMatch]) -> Dict[str, ClozeGroup]:
    """Group clozes by ID.

    Args:
        clozes: List of ClozeMatch objects

    Returns:
        Dictionary mapping group_id to ClozeGroup
    """
    groups = {}
    individual_counter = 0

    for cloze in clozes:
        if cloze.cloze_id:
            group_id = cloze.cloze_id
            if group_id not in groups:
                groups[group_id] = ClozeGroup(
                    group_id=group_id,
                    clozes=[],
                    is_sequence=(cloze.cloze_type == ClozeType.SEQUENCE),
                )
            groups[group_id].clozes.append(cloze)
        else:
            # Individual cloze without group
            group_id = f"_individual_{individual_counter}"
            individual_counter += 1
            groups[group_id] = ClozeGroup(
                group_id=group_id, clozes=[cloze], is_sequence=False
            )

    return groups


def _generate_group_prompt(
    group: ClozeGroup, context: CardContext, file_path: Path
) -> Optional[Prompt]:
    """Generate a single prompt for a cloze group.

    Args:
        group: The cloze group
        context: The card context
        file_path: Source file path

    Returns:
        Prompt object or None if group is empty
    """
    if not group.clozes:
        return None

    # For grouped clozes, use the first cloze's metadata
    primary_cloze = group.clozes[0]

    # Build context text with clozes replaced
    context_text = context.content

    # Replace clozes in reverse order to preserve positions
    for cloze in sorted(context.cloze_matches, key=lambda c: c.start, reverse=True):
        # Check if this cloze is in our group by comparing start positions
        is_in_group = any(gc.start == cloze.start for gc in group.clozes)

        if is_in_group:
            # This is a target cloze - replace with indexed placeholder
            if len(group.clozes) > 1:
                # Grouped: use indexed placeholder - find index by start position
                idx = next(
                    (i for i, gc in enumerate(group.clozes) if gc.start == cloze.start),
                    0  # Default to 0 if not found (shouldn't happen, but safe)
                )
                replacement = f"__CLOZE_{idx}__"
            else:
                # Single cloze: use simple placeholder
                replacement = "__CLOZE__"
        else:
            # Other cloze - show the answer
            replacement = cloze.answer

        context_text = context_text[: cloze.start] + replacement + context_text[cloze.end :]

    # Apply scope resolution
    scoped_context = resolve_context_scope(
        context_text, primary_cloze.line_number - context.start_line, primary_cloze.scope
    )

    return Prompt(
        cloze_match=primary_cloze,
        context=scoped_context,
        anki_id=primary_cloze.anki_id,
        file_path=file_path,
        line_number=primary_cloze.line_number,
        group_clozes=group.clozes if len(group.clozes) > 1 else None,
    )


def _generate_sequence_prompts(
    group: ClozeGroup, context: CardContext, file_path: Path
) -> List[Prompt]:
    """Generate progressive reveal prompts for sequence clozes.

    Args:
        group: The sequence cloze group
        context: The card context
        file_path: Source file path

    Returns:
        List of Prompt objects (one per sequence item)
    """
    sorted_clozes = group.get_sequence_clozes()
    prompts = []

    for i, target_cloze in enumerate(sorted_clozes):
        # Build context: show clozes before this one, hide this one, hide rest
        context_text = context.content

        for cloze in sorted(context.cloze_matches, key=lambda c: c.start, reverse=True):
            if cloze == target_cloze:
                # Current target - hide it
                replacement = "__CLOZE__"
            elif cloze in sorted_clozes[:i]:
                # Already revealed in sequence - show it
                replacement = cloze.answer
            elif cloze in sorted_clozes[i + 1 :]:
                # Not yet revealed - show ellipsis
                replacement = "..."
            else:
                # Different group - show answer
                replacement = cloze.answer

            context_text = context_text[: cloze.start] + replacement + context_text[cloze.end :]

        scoped_context = resolve_context_scope(
            context_text, target_cloze.line_number - context.start_line, target_cloze.scope
        )

        prompts.append(
            Prompt(
                cloze_match=target_cloze,
                context=scoped_context,
                anki_id=target_cloze.anki_id,
                file_path=file_path,
                line_number=target_cloze.line_number,
            )
        )

    return prompts

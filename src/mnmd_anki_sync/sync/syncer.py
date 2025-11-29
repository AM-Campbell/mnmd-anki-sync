"""Main sync orchestration."""

from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console
from rich.progress import track

from ..anki.client import AnkiConnectClient
from ..anki.note_builder import build_note_fields
from ..anki.note_type import NOTE_TYPE_NAME, ensure_note_type_exists
from ..config import Config
from ..models import CardContext, Prompt
from ..parser.cloze_parser import parse_clozes
from ..parser.context_extractor import extract_card_contexts
from ..parser.prompt_generator import generate_prompts
from ..utils.base52 import decode_base52, encode_base52
from ..utils.file_id import ensure_file_id, get_file_tag
from .id_writer import write_ids_to_file


class Syncer:
    """Sync markdown files to Anki."""

    def __init__(self, config: Config, console: Optional[Console] = None) -> None:
        """Initialize syncer.

        Args:
            config: Configuration
            console: Rich console for output (optional)
        """
        self.config = config
        self.console = console or Console()
        self.client = AnkiConnectClient(config.anki_url)

    def sync_file(self, file_path: Path, deck_name: Optional[str] = None) -> Dict[str, int]:
        """Sync a markdown file to Anki.

        Args:
            file_path: Path to markdown file
            deck_name: Target deck (uses config default if None)

        Returns:
            Statistics dictionary with counts

        Raises:
            AnkiConnectionError: Cannot connect to Anki
            AnkiAPIError: Anki operation failed
        """
        deck = deck_name or self.config.default_deck

        # Ensure note type exists
        ensure_note_type_exists(self.client)

        # Ensure file has stable ID
        file_id, id_added = ensure_file_id(file_path)
        file_tag = get_file_tag(file_id)

        if id_added:
            self.console.print(f"[dim]Added file ID to {file_path.name}: {file_id}[/dim]")

        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract card contexts
        contexts = extract_card_contexts(content)

        if not contexts:
            self.console.print(f"[yellow]No card contexts found in {file_path}[/yellow]")
            return {"created": 0, "updated": 0, "skipped": 0, "deleted": 0}

        # Parse clozes in each context and generate prompts
        all_prompts: List[Prompt] = []
        for context in contexts:
            # Parse clozes
            context.cloze_matches = parse_clozes(context.content, start_line=context.start_line)

            # Generate prompts
            prompts = generate_prompts(context, file_path)
            all_prompts.extend(prompts)

        if not all_prompts:
            self.console.print(f"[yellow]No clozes found in {file_path}[/yellow]")
            return {"created": 0, "updated": 0, "skipped": 0, "deleted": 0}

        # Sync prompts
        stats = {"created": 0, "updated": 0, "skipped": 0, "deleted": 0}

        # Track Anki IDs present in this file
        current_file_note_ids: Set[int] = set()

        for prompt in track(
            all_prompts,
            description=f"Syncing {file_path.name}",
            console=self.console,
        ):
            # Set deck and tags (include file tag)
            prompt.deck_name = deck
            prompt.tags = self.config.default_tags + [file_tag]

            # Build note fields
            fields = build_note_fields(prompt, self.config)

            # Check if note exists
            if prompt.anki_id:
                # Try to update existing note
                try:
                    anki_note_id = decode_base52(prompt.anki_id)  # Decode from base52
                except ValueError:
                    # Invalid base52 ID - will create new note
                    anki_note_id = None

                if anki_note_id is not None:
                    # Verify note exists in Anki
                    notes_info = self.client.notes_info([anki_note_id])
                    if notes_info and len(notes_info) > 0 and notes_info[0]:
                        # Update existing note
                        self.client.update_note_fields(anki_note_id, fields)
                        # Ensure file tag is present
                        self.client.add_tags([anki_note_id], file_tag)
                        # Track this note ID
                        current_file_note_ids.add(anki_note_id)
                        stats["updated"] += 1
                        continue

            # Create new note
            try:
                note_id = self.client.add_note(
                    deck_name=deck,
                    model_name=NOTE_TYPE_NAME,
                    fields=fields,
                    tags=prompt.tags,
                )

                # Track this note ID
                current_file_note_ids.add(note_id)

                # Update prompt with new Anki ID (in base52)
                anki_id_base52 = encode_base52(note_id)
                prompt.cloze_match.anki_id = anki_id_base52

                # For grouped clozes, set ID on ALL clozes in the group
                if prompt.group_clozes:
                    for cloze in prompt.group_clozes:
                        cloze.anki_id = anki_id_base52

                stats["created"] += 1
            except Exception as e:
                self.console.print(f"[red]Failed to create note: {e}[/red]")
                stats["skipped"] += 1

        # Detect and delete orphaned cards
        # Find all cards in Anki with this file's tag
        try:
            anki_file_note_ids = self.client.find_notes(f"tag:{file_tag}")

            # Find notes that are in Anki but not in the current file
            orphaned_note_ids = [
                nid for nid in anki_file_note_ids if nid not in current_file_note_ids
            ]

            if orphaned_note_ids:
                self.console.print(
                    f"[yellow]Deleting {len(orphaned_note_ids)} orphaned cards...[/yellow]"
                )
                self.client.delete_notes(orphaned_note_ids)
                stats["deleted"] = len(orphaned_note_ids)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not detect orphaned cards: {e}[/yellow]")

        # Write Anki IDs back to file
        write_ids_to_file(file_path, all_prompts)

        self.console.print(
            f"[green]Synced {file_path.name}:[/green] "
            f"{stats['created']} created, "
            f"{stats['updated']} updated, "
            f"{stats['deleted']} deleted, "
            f"{stats['skipped']} skipped"
        )

        return stats

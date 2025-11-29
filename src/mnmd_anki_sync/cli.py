"""CLI for mnmd-anki-sync."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from . import __version__
from .config import Config, EditorProtocol
from .sync.syncer import Syncer

app = typer.Typer(
    name="mnmd",
    help="Sync mnemonic markdown files to Anki",
    add_completion=False,
)

console = Console()


def _preview_sync(files: List[Path], deck: Optional[str], config: Config) -> None:
    """Preview what would be synced without making changes."""
    from rich.table import Table

    from .parser.cloze_parser import parse_clozes
    from .parser.context_extractor import extract_card_contexts
    from .parser.prompt_generator import generate_prompts
    from .utils.file_id import extract_file_id

    total_new = 0
    total_existing = 0

    for file_path in files:
        console.print(f"\n[bold]File: {file_path}[/bold]")

        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for file ID
        file_id = extract_file_id(content)
        if not file_id:
            console.print("  [dim]Would add new file ID to frontmatter[/dim]")

        # Extract contexts and parse
        contexts = extract_card_contexts(content)

        if not contexts:
            console.print("  [yellow]No card contexts found[/yellow]")
            continue

        all_prompts = []
        for context in contexts:
            context.cloze_matches = parse_clozes(context.content, start_line=context.start_line)
            prompts = generate_prompts(context, file_path)
            all_prompts.extend(prompts)

        if not all_prompts:
            console.print("  [yellow]No clozes found[/yellow]")
            continue

        # Build summary table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Line", style="dim", width=6)
        table.add_column("Type", width=10)
        table.add_column("Answer", max_width=40)
        table.add_column("Status", width=12)

        new_count = 0
        existing_count = 0

        for prompt in all_prompts:
            cloze = prompt.cloze_match
            cloze_type = cloze.cloze_type.value.capitalize()

            # Truncate answer if too long
            answer = cloze.answer
            if len(answer) > 37:
                answer = answer[:37] + "..."

            if cloze.anki_id:
                status = "[green]Update[/green]"
                existing_count += 1
            else:
                status = "[cyan]Create[/cyan]"
                new_count += 1

            table.add_row(
                str(cloze.line_number + 1),
                cloze_type,
                answer,
                status,
            )

        console.print(table)

        target_deck = deck or config.default_deck
        console.print(f"  Target deck: [cyan]{target_deck}[/cyan]")
        console.print(f"  Tags: [cyan]{', '.join(config.default_tags)}[/cyan]")
        console.print(
            f"  Summary: [cyan]{new_count}[/cyan] new, " f"[green]{existing_count}[/green] updates"
        )

        total_new += new_count
        total_existing += existing_count

    console.print(
        f"\n[bold]Total: {total_new} would be created, {total_existing} would be updated[/bold]"
    )


@app.command()
def sync(
    files: List[Path] = typer.Argument(
        ...,
        help="Markdown files to sync",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    deck: Optional[str] = typer.Option(
        None,
        "--deck",
        "-d",
        help="Target Anki deck (default: from config or 'Default')",
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help="Comma-separated tags to add (default: 'mnmd')",
    ),
    editor: Optional[EditorProtocol] = typer.Option(
        None,
        "--editor",
        "-e",
        help="Editor protocol for source links",
    ),
    anki_url: Optional[str] = typer.Option(
        None,
        "--anki-url",
        help="AnkiConnect URL (default: http://localhost:8765)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without syncing",
    ),
) -> None:
    """Sync markdown files to Anki.

    Creates cloze deletion cards from mnemonic markdown syntax.
    """
    # Load config
    config = Config.load_default()

    # Apply CLI overrides
    if editor:
        config.editor_protocol = editor
    if anki_url:
        config.anki_url = anki_url
    if tags:
        config.default_tags = [t.strip() for t in tags.split(",")]

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")
        _preview_sync(files, deck, config)
        return

    # Create syncer
    syncer = Syncer(config, console)

    # Sync each file
    total_stats = {"created": 0, "updated": 0, "skipped": 0}

    for file_path in files:
        try:
            stats = syncer.sync_file(file_path, deck_name=deck)
            for key in total_stats:
                total_stats[key] += stats[key]
        except Exception as e:
            console.print(f"[red]Error syncing {file_path}: {e}[/red]")
            raise typer.Exit(1)

    # Print summary
    console.print("\n[bold green]Sync complete![/bold green]")
    console.print(
        f"Total: {total_stats['created']} created, "
        f"{total_stats['updated']} updated, "
        f"{total_stats['skipped']} skipped"
    )


@app.command()
def validate(
    files: List[Path] = typer.Argument(
        ...,
        help="Markdown files to validate",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Validate markdown syntax without syncing.

    Checks for parsing errors and displays statistics.
    """
    from rich.table import Table

    from .parser.cloze_parser import parse_clozes
    from .parser.context_extractor import extract_card_contexts

    for file_path in files:
        console.print(f"\n[bold]Validating {file_path}[/bold]")

        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract contexts
        contexts = extract_card_contexts(content)

        if not contexts:
            console.print("[yellow]No card contexts found (> ? blocks)[/yellow]")
            continue

        # Parse clozes
        total_clozes = 0
        for context in contexts:
            clozes = parse_clozes(context.content, start_line=context.start_line)
            total_clozes += len(clozes)

        # Create summary table
        table = Table(title="Validation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Card Contexts", str(len(contexts)))
        table.add_row("Total Clozes", str(total_clozes))

        console.print(table)
        console.print("[green]✓ File is valid[/green]")


@app.command()
def syntax(
    pager: bool = typer.Option(
        True,
        "--pager/--no-pager",
        help="Use pager (less) to display syntax guide",
    )
) -> None:
    """Show syntax guide for mnemonic markdown.

    Displays the complete syntax documentation including cloze types,
    hints, extras, math support, and more.
    """
    # Find syntax-notes.md in the package
    syntax_file = Path(__file__).parent / "syntax-notes.md"

    if not syntax_file.exists():
        console.print("[red]Error: syntax-notes.md not found[/red]")
        console.print("\nYou can find the documentation at:")
        console.print("https://github.com/yourusername/mnmd-anki-sync/blob/main/syntax-notes.md")
        raise typer.Exit(1)

    content = syntax_file.read_text(encoding="utf-8")

    if pager and sys.stdout.isatty():
        # Use less for better navigation
        try:
            # Try to use less with color support
            proc = subprocess.Popen(["less", "-R"], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=content)
        except FileNotFoundError:
            # less not available, fall back to rich markdown
            console.print(Markdown(content))
    else:
        # No pager or not a TTY, use rich markdown rendering
        console.print(Markdown(content))


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"mnmd-anki-sync version {__version__}")


if __name__ == "__main__":
    app()

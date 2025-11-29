#!/usr/bin/env python3
"""
Mnemonic Markdown to Anki Sync Script

Syncs cards from mnemonic markdown (mnmd) files to Anki using AnkiConnect.
Supports:
- Simple cloze syntax: {{answer}}
- Card contexts with: > ?
- Anki ID storage in base52 format: {{AnkiID>answer}}
- Cloze IDs (numeric): {{1>answer}} or {{1,AnkiID>answer}}

Each mnemonic markdown cloze creates one Anki Cloze note (always using {{c1::...}}).
"""

import re
import json
import urllib.request
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# Base52 encoding (case-sensitive alphanumeric, no digits to avoid confusion with cloze IDs)
BASE52_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base52(num: int) -> str:
    """Convert a number to base52 string (letters only)."""
    if num == 0:
        return BASE52_CHARS[0]
    
    result = []
    while num:
        result.append(BASE52_CHARS[num % 52])
        num //= 52
    return ''.join(reversed(result))


def decode_base52(s: str) -> int:
    """Convert a base52 string back to a number."""
    result = 0
    for char in s:
        result = result * 52 + BASE52_CHARS.index(char)
    return result


def invoke_anki(action: str, **params) -> dict:
    """Call AnkiConnect API."""
    request_json = json.dumps({
        'action': action,
        'version': 6,
        'params': params
    }).encode('utf-8')
    
    response = urllib.request.urlopen(
        urllib.request.Request('http://localhost:8765', request_json)
    )
    response_data = json.loads(response.read().decode('utf-8'))
    
    if len(response_data) != 2:
        raise Exception('Response has unexpected number of fields')
    if 'error' not in response_data:
        raise Exception('Response is missing required error field')
    if 'result' not in response_data:
        raise Exception('Response is missing required result field')
    if response_data['error'] is not None:
        raise Exception(response_data['error'])
    
    return response_data['result']


def ensure_mnmd_note_type():
    """Create the MNMD Cloze note type if it doesn't exist."""
    # Check if it exists
    model_names = invoke_anki('modelNames')
    
    if 'MNMD Cloze' in model_names:
        return
    
    print("Creating MNMD Cloze note type...")
    
    # Create the note type based on Cloze
    invoke_anki('createModel',
        modelName='MNMD Cloze',
        inOrderFields=['Text', 'Extra', 'Source'],
        css='.card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n\n.cloze {\n font-weight: bold;\n color: blue;\n}\n.nightMode .cloze {\n color: lightblue;\n}',
        isCloze=True,
        cardTemplates=[
            {
                'Name': 'Cloze',
                'Front': '{{cloze:Text}}',
                'Back': '{{cloze:Text}}<br>{{Extra}}<br><br>{{Source}}'
            }
        ]
    )
    
    print("✓ Created MNMD Cloze note type")


class ClozePrompt:
    """Represents a single cloze prompt within a card context."""
    
    def __init__(self, cloze_id: Optional[str], anki_id: Optional[str], 
                 answer: str, context: str, position: int, 
                 line_number: int, file_path: Path):
        self.cloze_id = cloze_id  # Numeric string or None
        self.anki_id = anki_id    # Base52 string or None
        self.answer = answer
        self.context = context    # Full card context with other clozes visible
        self.position = position  # Position in context text
        self.line_number = line_number  # Line number in original file
        self.file_path = file_path  # Path to source file
    
    def to_anki_cloze_text(self) -> str:
        """
        Convert context to Anki cloze format.
        Replace the placeholder with {{c1::answer}}.
        """
        return self.context.replace('__CLOZE__', f'{{{{c1::{self.answer}}}}}')
    
    def to_anki_note(self, deck_name: str = "Default", tags: List[str] = None) -> dict:
        """Convert to Anki note format using MNMD Cloze type."""
        source_link = f'<a href="vscodium://file{str(self.file_path.resolve())}:{self.line_number}:1">Open in VSCodium</a>'
        
        if tags == None:
            tags = ['mnmd']
        
        return {
            'deckName': deck_name,
            'modelName': 'MNMD Cloze',
            'fields': {
                'Text': self.to_anki_cloze_text(),
                'Extra': '',
                'Source': source_link
            },
            'tags': tags 
        }


def parse_cloze_pattern(match) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse a cloze pattern like {{answer}}, {{1>answer}}, {{AnkiID>answer}}, 
    or {{1,AnkiID>answer}}.
    
    Returns: (cloze_id, anki_id, answer)
    """
    content = match.group(1)
    
    # Check for ID prefix
    if '>' in content:
        ids, answer = content.split('>', 1)
        
        # Parse IDs (could be cloze_id, anki_id, or both)
        parts = ids.split(',')
        cloze_id = None
        anki_id = None
        
        for part in parts:
            part = part.strip()
            if part.isdigit():
                cloze_id = part
            elif part.isalpha():
                anki_id = part
        
        return cloze_id, anki_id, answer.strip()
    else:
        # No IDs, just answer
        return None, None, content.strip()


def extract_card_contexts(markdown_text: str) -> List[Dict]:
    """
    Extract all card contexts (> ? blocks) from markdown.
    
    Returns list of dicts with 'start_line', 'end_line', 'content', 'full_text'
    """
    lines = markdown_text.split('\n')
    card_contexts = []
    in_card = False
    card_start = None
    card_lines = []
    card_line_numbers = []
    
    for i, line in enumerate(lines):
        if line.strip() == '> ?':
            # Start of card context
            in_card = True
            card_start = i
            card_lines = [line]
            card_line_numbers = [i]
        elif in_card:
            if line.startswith('>'):
                # Continue card context
                card_lines.append(line)
                card_line_numbers.append(i)
            else:
                # End of card context
                if card_lines:
                    content = '\n'.join(card_lines)
                    # Strip leading '>' from each line
                    clean_content = '\n'.join(
                        line[1:].strip() if line.startswith('>') else line 
                        for line in card_lines
                    )
                    card_contexts.append({
                        'start_line': card_start,
                        'end_line': i - 1,
                        'content': clean_content,
                        'full_text': content,
                        'line_numbers': card_line_numbers
                    })
                in_card = False
                card_start = None
                card_lines = []
                card_line_numbers = []
    
    # Handle card context at end of file
    if in_card and card_lines:
        content = '\n'.join(card_lines)
        clean_content = '\n'.join(
            line[1:].strip() if line.startswith('>') else line 
            for line in card_lines
        )
        card_contexts.append({
            'start_line': card_start,
            'end_line': len(lines) - 1,
            'content': clean_content,
            'full_text': content,
            'line_numbers': card_line_numbers
        })
    
    return card_contexts


def extract_clozes_from_context(context_text: str, context_start_line: int, 
                                 file_path: Path) -> List[ClozePrompt]:
    """
    Extract all cloze prompts from a card context.
    Each {{}} becomes a separate Anki Cloze note.
    """
    # Find all clozes
    cloze_pattern = re.compile(r'\{\{(.+?)\}\}')
    matches = list(cloze_pattern.finditer(context_text))
    
    if not matches:
        return []
    
    prompts = []
    
    # Parse all clozes first
    parsed_clozes = []
    for match in matches:
        cloze_id, anki_id, answer = parse_cloze_pattern(match)
        parsed_clozes.append((match, cloze_id, anki_id, answer))
    
    # Create a prompt for each cloze
    for i, (match, cloze_id, anki_id, answer) in enumerate(parsed_clozes):
        # Calculate which line this cloze is on
        lines_before_match = context_text[:match.start()].count('\n')
        line_number = context_start_line + lines_before_match + 1  # +1 for 1-indexed
        
        # Create question text: hide this cloze, show others as plain text
        # Work backwards through matches to avoid offset issues
        question = context_text
        for j in range(len(parsed_clozes) - 1, -1, -1):
            other_match, _, _, other_answer = parsed_clozes[j]
            if j == i:
                # This is the one to hide - replace with placeholder
                question = question[:other_match.start()] + '__CLOZE__' + question[other_match.end():]
            else:
                # Show this one - replace with just the answer
                question = question[:other_match.start()] + other_answer + question[other_match.end():]
        
        # Strip the '?' line if present (it's the first line from "> ?")
        question_lines = question.split('\n')
        if question_lines and question_lines[0].strip() == '?':
            question_lines = question_lines[1:]
        question = '\n'.join(question_lines).strip()
        
        prompts.append(ClozePrompt(
            cloze_id=cloze_id,
            anki_id=anki_id,
            answer=answer,
            context=question,
            position=match.start(),
            line_number=line_number,
            file_path=file_path
        ))
    
    return prompts


def sync_to_anki(prompts: List[ClozePrompt], deck_name: str = "Default", tags: List[str] = None) -> List[ClozePrompt]:
    """
    Sync prompts to Anki and return updated prompts with Anki IDs.
    Each prompt becomes one Anki Cloze note with {{c1::...}}.
    """
    updated_prompts = []
    
    if tags == None:
        tags = ['mnmd']
    
    for prompt in prompts:
        if prompt.anki_id:
            # Card already has Anki ID, update it
            note_id = decode_base52(prompt.anki_id)
            try:
                note_info = invoke_anki('notesInfo', notes=[note_id])
                if note_info and note_info[0]:
                    # Update existing note
                    source_link = f'<a href="vscodium://file{str(prompt.file_path.resolve())}:{prompt.line_number}:1">Open in VSCodium</a>'
                    invoke_anki('updateNoteFields', note={
                        'id': note_id,
                        'fields': {
                            'Text': prompt.to_anki_cloze_text(),
                            'Extra': '',
                            'Source': source_link
                        }
                    })
                    invoke_anki('updateNoteTags', note=note_id, tags=' '.join(tags))
                    updated_prompts.append(prompt)
                else:
                    # Note doesn't exist, create new
                    raise Exception("Note not found")
            except:
                # Create new note
                note_id = invoke_anki('addNote', note=prompt.to_anki_note(deck_name, tags))
                prompt.anki_id = encode_base52(note_id)
                updated_prompts.append(prompt)
        else:
            # Create new note
            note_id = invoke_anki('addNote', note=prompt.to_anki_note(deck_name, tags))
            prompt.anki_id = encode_base52(note_id)
            updated_prompts.append(prompt)
    
    return updated_prompts


def write_ids_back(file_path: Path, markdown_text: str, 
                   card_contexts: List[Dict], all_prompts: List[List[ClozePrompt]]) -> str:
    """
    Write Anki IDs back to the markdown file.
    """
    lines = markdown_text.split('\n')
    
    # Process each card context
    for context_idx, context in enumerate(card_contexts):
        prompts = all_prompts[context_idx]
        if not prompts:
            continue
            
        context_start = context['start_line']
        
        # Get the lines for this context
        context_lines = lines[context_start:context['end_line'] + 1]
        context_text = '\n'.join(context_lines)
        
        # Find and replace clozes with IDs
        cloze_pattern = re.compile(r'\{\{(.+?)\}\}')
        matches = list(cloze_pattern.finditer(context_text))
        
        # Work backwards to preserve positions
        for match, prompt in zip(reversed(matches), reversed(prompts)):
            old_content = match.group(1)
            cloze_id, old_anki_id, answer = parse_cloze_pattern(match)
            
            # Build new content with IDs
            if cloze_id and prompt.anki_id:
                new_content = f"{cloze_id},{prompt.anki_id}>{answer}"
            elif cloze_id:
                new_content = f"{cloze_id}>{answer}"
            elif prompt.anki_id:
                new_content = f"{prompt.anki_id}>{answer}"
            else:
                new_content = answer
            
            # Replace in context_text
            context_text = context_text[:match.start()] + '{{' + new_content + '}}' + \
                          context_text[match.end():]
        
        # Write back to lines
        new_context_lines = context_text.split('\n')
        lines[context_start:context['end_line'] + 1] = new_context_lines
    
    return '\n'.join(lines)


def sync_file(file_path: Path, deck_name: str = "Default", tags: List[str] = None):
    """Sync a single markdown file to Anki."""
    print(f"Processing {file_path}...")
    
    # Read file
    markdown_text = file_path.read_text(encoding='utf-8')
    
    # Extract card contexts
    card_contexts = extract_card_contexts(markdown_text)
    print(f"Found {len(card_contexts)} card contexts")
    
    if not card_contexts:
        print("No card contexts found (looking for '> ?' blocks)")
        return
    
    # Extract and sync prompts from each context
    all_prompts = []
    for context in card_contexts:
        prompts = extract_clozes_from_context(
            context['content'], 
            context['start_line'],
            file_path
        )
        print(f"  Found {len(prompts)} clozes in context at line {context['start_line'] + 1}")
        
        if prompts:
            updated_prompts = sync_to_anki(prompts, deck_name, tags)
            all_prompts.append(updated_prompts)
        else:
            all_prompts.append([])
    
    # Write IDs back to file
    updated_text = write_ids_back(file_path, markdown_text, card_contexts, all_prompts)
    file_path.write_text(updated_text, encoding='utf-8')
    
    total_synced = sum(len(prompts) for prompts in all_prompts)
    print(f"✓ Synced {total_synced} cards to Anki")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync mnemonic markdown files to Anki'
    )
    parser.add_argument('files', nargs='+', help='Markdown files to sync')
    parser.add_argument('--deck', default='Default', help='Anki deck name')
    parser.add_argument('--tags', default='', help='Comma-separated tags (e.g., "chemistry,chapter1")')

    
    args = parser.parse_args()
    
    # Parse tags
    tags = ['mnmd']  # Always include mnmd tag
    if args.tags:
        tags.extend(tag.strip() for tag in args.tags.split(','))
    
    # Test AnkiConnect connection
    try:
        invoke_anki('version')
        print("✓ Connected to AnkiConnect")
    except Exception as e:
        print(f"✗ Could not connect to AnkiConnect: {e}")
        print("Make sure Anki is running with AnkiConnect installed")
        return
    
    # Ensure MNMD Cloze note type exists
    try:
        ensure_mnmd_note_type()
    except Exception as e:
        print(f"✗ Error creating MNMD Cloze note type: {e}")
        return
    
    # Process each file
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"✗ File not found: {file_path}")
            continue
        
        try:
            sync_file(path, args.deck, tags)
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()

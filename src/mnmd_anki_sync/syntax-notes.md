MNMD-ANKI-SYNC(1)                User Commands               MNMD-ANKI-SYNC(1)

NAME
       mnmd - sync mnemonic markdown files to Anki

DESCRIPTION
       Mnemonic Markdown (MNMD) is a syntax for embedding cloze deletions in
       markdown files. This tool syncs them to Anki as flashcards.

BASIC CLOZE SYNTAX
       {{answer}}
              Creates a cloze deletion. The answer is hidden on the front,
              shown on the back. Any paragraph containing a cloze becomes a
              flashcard automatically.

              Example:
                  Water boils at {{100}} degrees Celsius.

              Front: Water boils at [...] degrees Celsius.
              Back:  Water boils at 100 degrees Celsius.

HINTS
       {{answer|hint}}
              Add a hint shown on the card front inside the brackets.

              Example:
                  The speed of light is {{299,792,458|in m/s}} m/s.

              Front: The speed of light is [...in m/s] m/s.

EXTRA INFORMATION
       {{answer<extra}}
              Add extra info shown only on the card back. Note: no closing >.

              Example:
                  Python's package manager is {{pip<PyPI has 400k+ packages}}.

              Back shows: pip
                          PyPI has 400k+ packages

COMBINED SYNTAX
       {{answer|hint<extra}}
              Combine hints and extras.

              Example:
                  Git's staging area is {{the index|preparation area<also called cache}}.

GROUPED CLOZES
       {{id>answer}}
              Hide multiple items together using the same numeric ID.

              Example:
                  Primary colors are {{1>red}}, {{1>blue}}, and {{1>yellow}}.

              Front: Primary colors are [...], [...], and [...].
              (All three hidden together, revealed together)

SEQUENCE CLOZES
       {{id.order>answer}}
              Create progressive reveals. Each card shows previous items.

              Example:
                  The order of planets:
                  {{1.1>Mercury}}
                  {{1.2>Venus}}
                  {{1.3>Earth}}

              Creates 3 cards:
              Card 1: [...], Card 2: Mercury, [...], Card 3: Mercury, Venus, [...]

SCOPE MODIFIERS
       {{answer}}[-before,after]
              Include surrounding paragraphs in the card context.

              [-1]        Include 1 paragraph before
              [1]         Include 1 paragraph after
              [-1,1]      Include 1 before and 1 after
              [-2,0]      Include 2 before, none after

              Default: current paragraph only (no modifier needed)

              Example:
                  Context paragraph here.

                  The answer is {{here}}[-1].

              Card includes both the context paragraph and the cloze paragraph.

EXPLICIT CONTEXT BLOCKS
       > ?
              Use block quotes starting with "> ?" to define multi-paragraph
              card contexts explicitly. Useful when you want full control over
              what content appears on the card.

              Example:
                  > ?
                  > First paragraph of context.
                  >
                  > Second paragraph with {{cloze}}.

              Everything inside the block becomes the card content.

MATH SUPPORT
       LaTeX math is converted to Anki's format automatically.

       Inline:  $E = mc^2$         becomes \(E = mc^2\)
       Block:   $$\int x dx$$      becomes \[\int x dx\]

       Example:
           Einstein's equation: {{$E = mc^2$}}.

       Math works in answers, hints, and surrounding text.

MARKDOWN SUPPORT
       Standard markdown is converted to HTML for Anki:

       **bold**                    Bold text
       *italic*                    Italic text
       `code`                      Inline code
       ```lang ... ```             Code blocks
       - item                      Unordered lists
       1. item                     Ordered lists
       ![alt](path)                Images
       Two spaces + newline        Line break

ANKI IDS
       After syncing, IDs are written back to your file automatically:

           {{abc>answer}}           (abc is the base52 Anki note ID)
           {{1,abc>answer}}         (grouped cloze with Anki ID)
           {{abc,1.2>answer}}       (sequence cloze with Anki ID)

       These prevent duplicates on re-sync. Don't edit them manually.

SOURCE LINKS
       Each card includes a link to open the source file in your editor.
       Configure with --editor flag or ~/.mnmdrc config file.

       Supported: vscode, vscodium, nvim, obsidian, file

CONFIGURATION
       Create ~/.mnmdrc (YAML):

           editor_protocol: vscode
           default_deck: My Deck
           default_tags:
             - mnmd
             - study
           anki_url: http://localhost:8765

EXAMPLES
       Simple card:
           The mitochondria is {{the powerhouse of the cell}}.

       Card with hint and extra:
           HTTP status 404 means {{Not Found|4xx = client error<RFC 7231}}.

       Grouped cloze:
           DNA bases: {{1>Adenine}}, {{1>Thymine}}, {{1>Guanine}}, {{1>Cytosine}}.

       Math card:
           Area of a circle: {{$A = \pi r^2$|geometry}}.

       Scope modifier (include context paragraph):
           Background info here.

           The answer is {{here}}[-1].

SEE ALSO
       mnmd sync --help
       mnmd validate --help
       https://github.com/am-campbell/mnmd-anki-sync

AUTHOR
       Aidan McHold Campbell

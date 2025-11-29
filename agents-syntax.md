# Mnemonic Markdown Syntax Reference for LLMs

This document specifies the syntax for generating mnemonic markdown (MNMD) for Anki flashcards.

## Core Principles

1. **Clozes can appear ANYWHERE**: Place `{{...}}` clozes directly in your regular markdown
2. **Context is automatic**: By default, the surrounding paragraph (separated by `\n\n`) becomes the card context
3. **`> ?` blocks are optional**: Use them ONLY when you need custom context boundaries
4. **Syntax is strict**: Extra characters, wrong delimiters, or incorrect ordering will break parsing
5. **IDs are alphanumeric**: Group IDs are numeric, Anki IDs are alphabetic (base52)

## Key Structural Rules

### DEFAULT: Clozes in Regular Markdown (MOST COMMON)

**You can put clozes ANYWHERE in your document:**

```markdown
# My Notes

The capital of France is {{Paris}}.

The capital of Spain is {{Madrid}}.

Python was created by {{Guido van Rossum}} in {{1991}}.
```

This creates **3 separate cards**:
1. Card 1: "The capital of France is [...]" (context = first paragraph)
2. Card 2: "The capital of Spain is [...]" (context = second paragraph)
3. Card 3: Two cards from the third paragraph (both clozes share that paragraph as context)

**Rules:**
- Paragraphs are separated by blank lines (`\n\n`)
- Each cloze uses its paragraph as default context
- Multiple clozes in same paragraph = multiple cards with shared context

### SPECIAL CASE: `> ?` Blocks for Custom Context

Use `> ?` blocks ONLY when you need to:
- Define custom context boundaries
- Include content that shouldn't be part of the context
- Group content differently than paragraph boundaries

```markdown
> ?
> The capital of France is {{Paris}}.

> ?
> The capital of Spain is {{Madrid}}.
```

**`> ?` block rules:**
- First line must be `> ?`
- All subsequent lines need `> ` prefix
- Blank line (no `>`) ends the block
- Use ONLY when paragraph-based context isn't suitable

## Card Context Syntax

**Required structure for all flashcards:**

```markdown
> ?
> [Your content with clozes]
```

**Rules:**
- First line must be `> ?` (blockquote with question mark)
- All subsequent lines in that block must start with `> ` (blockquote prefix)
- Each cloze within generates one or more cards
- Empty lines within context are preserved (keep the `> ` prefix)
- One blank line WITHOUT `>` separates contexts (ends the block)
- One `> ?` block = one shared context for all clozes in it

### Single Cloze per Block (Most Common)
```markdown
> ?
> The capital of France is {{Paris}}.

> ?
> Python is a {{dynamically typed|type checking at runtime}} language.
```
These create two separate cards with different contexts.

### Multiple Clozes in Same Block (Shared Context)
```markdown
> ?
> Python was created by {{Guido van Rossum}} in {{1991}}.
```
This creates TWO cards, both showing the full sentence as context:
- Card 1: "Python was created by [...] in 1991."
- Card 2: "Python was created by Guido van Rossum in [...]."

### When to Use Multiple Clozes in One Block
Use one `> ?` block with multiple clozes when:
- Facts are closely related and benefit from shared context
- You want the learner to see other answers as hints
- The sentence naturally contains multiple testable facts

Use separate `> ?` blocks when:
- Concepts are independent
- Each deserves its own focused context
- Facts are unrelated

**Most common pattern:** One `> ?` block per concept/fact.

### Block Structure Examples

**CORRECT - Separate independent cards:**
```markdown
> ?
> The capital of France is {{Paris}}.

> ?
> The capital of Spain is {{Madrid}}.
```
Note: Blank line between blocks (no `>` prefix on blank line).

**CORRECT - Multiple clozes sharing context:**
```markdown
> ?
> React was created by {{Facebook}} and released in {{2013}}.
```
Both clozes see the full sentence.

**CORRECT - Multi-line block:**
```markdown
> ?
> The HTTP status codes are grouped:
> - {{2xx}} for success
> - {{4xx}} for client errors
> - {{5xx}} for server errors
```
All lines have `> ` prefix until you want to end the block.

**CORRECT - Empty lines within block:**
```markdown
> ?
> First paragraph with {{cloze}}.
>
> Second paragraph in same context.
```
Note: Empty line still has `> ` prefix.

**WRONG - Missing `> ?` marker:**
```markdown
The capital of France is {{Paris}}.
```

**WRONG - Missing `>` prefix on lines:**
```markdown
> ?
The capital of France is {{Paris}}.
```

**WRONG - Using `> ?` on multiple lines:**
```markdown
> ?
> ?
> The capital of France is {{Paris}}.
```
Only the first line should be `> ?`.

## Cloze Syntax Patterns

### Pattern 1: Basic Cloze
```
{{answer}}
```
- Simplest form
- Hides the answer text
- Shows surrounding paragraph as context

### Pattern 2: Cloze with Hint
```
{{answer|hint}}
```
- `|` separates answer from hint
- Hint appears on card back only
- Hint provides additional context

**IMPORTANT:** The hint syntax is NOT `{{.|hint}}`. That is WRONG.

### Pattern 3: Cloze with Extra
```
{{answer<extra}}
```
- `<` starts extra information
- NO closing `>` character
- Extra runs until `}}`
- Extra appears on card back

**IMPORTANT:** The extra syntax is NOT `{{.<extra>}}` or `{{answer<extra>}}`. The correct form has NO closing `>`.

### Pattern 4: Combined Hint and Extra
```
{{answer|hint<extra}}
```
- Order matters: answer, then hint (after `|`), then extra (after `<`)
- All three components are optional except answer

### Pattern 5: Grouped Cloze
```
{{id>answer}}
```
- `id` is a numeric identifier (e.g., `1`, `2`, `poetry`)
- All clozes with same ID are hidden together
- Use for related items that should appear as one card

**Example:**
```markdown
> ?
> My favorite colors are {{1>red}} and {{1>blue}}.
```
Creates one card with both items hidden: "My favorite colors are [...] and [...]"

### Pattern 6: Sequence Cloze
```
{{id.order>answer}}
```
- `id.order` where `id` is group, `order` is sequence number
- Creates progressive reveal cards
- Order should be integers: `1.1`, `1.2`, `1.3`

**Example:**
```markdown
> ?
> Roses are {{1.1>red}},
> Violets are {{1.2>blue}},
> Sugar is {{1.3>sweet}}.
```

### Pattern 7: With Scope Control
```
{{answer}}[-before,after]
{{answer}}[-1,2]
{{answer}}[-1]
{{answer}}[2]
```
- Scope controls paragraph context
- `[-n]` or negative = paragraphs before
- `[n]` or positive = paragraphs after
- `[-n,m]` = n before, m after
- Default: current paragraph only (`[0,0]`)
- Lists default to `[-1]` (include paragraph before)

### Pattern 8: With Anki ID
```
{{ankiID,groupID>answer}}
{{groupID,ankiID>answer}}
```
- Anki IDs are alphabetic base52 (e.g., `abc`, `XYZ`, `aBcD`)
- Order doesn't matter: ID can come before or after group ID
- **DO NOT manually write Anki IDs** - they are auto-generated on sync
- Only include if updating existing cards

## Math Syntax

### Inline Math
```
$E = mc^2$
```
- Single dollar signs for inline equations
- Works in answers, hints, and context

### Block Math
```
$$\int_0^\infty e^{-x^2} dx$$
```
- Double dollar signs for display equations
- Can span multiple lines

### Math in Clozes
```markdown
> ?
> Einstein's equation is {{$E = mc^2$}}.
> The quadratic formula is {{$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$|solves ax² + bx + c = 0}}.
```

**Important:** Math with nested braces (like `\frac{a}{b}`) is supported.

## Image Syntax

Standard markdown image syntax:
```
![Alt text](path/to/image.png)
```

Works in card context:
```markdown
> ?
> The Python logo: ![Python logo](./python.png)
> Python is a {{programming language}}.
```

## Complete Syntax Combinations

### All Features Combined
```
{{ankiID,groupID.order>answer|hint<extra}}[scope]
```

**Breakdown:**
1. `ankiID,groupID` - Optional IDs (comma-separated, either order)
2. `.order` - Optional sequence number (requires groupID)
3. `>` - Separator (required if IDs present)
4. `answer` - Required answer text
5. `|hint` - Optional hint (after pipe)
6. `<extra` - Optional extra (after `<`, NO closing `>`)
7. `[scope]` - Optional scope like `[-1,2]`

## Critical Rules to Avoid Errors

### ✅ CORRECT Syntax
```markdown
{{answer}}
{{answer|hint}}
{{answer<extra info}}
{{answer|hint<extra}}
{{1>answer}}
{{1.2>answer}}
{{abc,1>answer}}
{{answer}}[-1]
```

### ❌ WRONG Syntax (DO NOT USE)
```markdown
{{.|hint}}                    # WRONG: No standalone hint
{{.<extra>}}                  # WRONG: No standalone extra
{{answer<extra>}}             # WRONG: Extra has NO closing >
{{id.>answer}}                # WRONG: Order required with dot
{{>answer}}                   # WRONG: Empty ID
{{answer}|hint}               # WRONG: Hint must be inside braces
{{answer[scope]}}             # WRONG: Scope must be outside braces
```

## Common Patterns for Generation

### Simple Q&A
```markdown
> ?
> The capital of France is {{Paris}}.
```

### Definition with Context
```markdown
> ?
> {{API|Application Programming Interface}} is a set of protocols for building software.
```

### List Items (Grouped)
```markdown
> ?
> The three primary colors are {{1>red}}, {{1>blue}}, and {{1>yellow}}.
```

### Step-by-Step Process (Sequence)
```markdown
> ?
> Git workflow:
> {{1.1>git add .}}
> {{1.2>git commit -m "message"}}
> {{1.3>git push}}
```

### Technical Term with Extra Info
```markdown
> ?
> {{Closure<A function that captures variables from its surrounding scope}} is a powerful JavaScript feature.
```

### Math Concept
```markdown
> ?
> The Pythagorean theorem states: {{$a^2 + b^2 = c^2$|where c is the hypotenuse}}
```

## Generation Guidelines

### DO:
1. **Always wrap clozes in `> ?` blocks**
2. **Use descriptive hints for technical terms**
3. **Group related items with same ID**
4. **Use sequences for ordered steps**
5. **Include extra info for complex concepts**
6. **Use math delimiters for equations**
7. **Keep answers concise** (1-5 words ideal)
8. **Test syntax mentally**: can you parse it unambiguously?

### DON'T:
1. **Don't create empty clozes**: `{{}}` is invalid
2. **Don't nest clozes**: `{{outer {{inner}} }}` is invalid
3. **Don't use unsupported characters in IDs**: only alphanumeric
4. **Don't mix sequence and non-sequence in same group**: Pick one style
5. **Don't forget blockquote markers**: Every line needs `> `
6. **Don't add closing `>` to extras**: `<extra>` → `<extra`
7. **Don't create hint-only or extra-only clozes**: Answer is always required
8. **Don't put scope inside braces**: `[scope]` goes outside `}}`

## Validation Checklist

Before generating mnemonic markdown, verify:

- [ ] Every cloze is wrapped in a `> ?` block
- [ ] Every line in block starts with `> `
- [ ] Cloze syntax matches patterns exactly
- [ ] No closing `>` after extra text
- [ ] Hints use `|` separator inside braces
- [ ] Math uses `$` or `$$` delimiters
- [ ] Group IDs are numeric (or alphanumeric for names)
- [ ] Sequence IDs use `id.order` format
- [ ] Scope is outside braces: `}}[scope]`
- [ ] No nested clozes
- [ ] No empty answers

## Block Structure Decision Tree

**When generating flashcards, decide on block structure:**

### Generate SEPARATE `> ?` blocks when:
```markdown
> ?
> The capital of France is {{Paris}}.

> ?
> The capital of Germany is {{Berlin}}.

> ?
> The capital of Italy is {{Rome}}.
```
- Facts are independent
- Each fact stands alone
- Different topics/concepts
- **This is the DEFAULT approach**

### Generate ONE `> ?` block with multiple clozes when:
```markdown
> ?
> {{React}} was created by {{Facebook}} in {{2013}} and uses a {{virtual DOM}}.
```
- Multiple facts in same sentence
- Facts are tightly coupled
- Seeing other answers helps learning
- All facts relate to same concept

### Generate ONE `> ?` block with grouped clozes when:
```markdown
> ?
> The primary colors are {{1>red}}, {{1>blue}}, and {{1>yellow}}.
```
- Items in a list
- All items should be hidden together
- Testing knowledge of the complete set

## Example Output Template

**Template for independent facts (most common):**
```markdown
> ?
> [Context sentence with {{cloze}}]

> ?
> [Different fact with {{another|hint}} cloze]

> ?
> [Separate concept with {{answer<explanation}}]
```

**Template for related facts in one context:**
```markdown
> ?
> [Sentence with {{first fact}} and {{second fact}}]
```

**Template for grouped items:**
```markdown
> ?
> [List intro]: {{1>item1}}, {{1>item2}}, {{1>item3}}
```

**Template for sequences:**
```markdown
> ?
> [Process description]:
> {{1.1>Step one}}
> {{1.2>Step two}}
> {{1.3>Step three}}
```

## Markdown Formatting Within Context

You can use standard markdown within card contexts:

- **Bold**: `**text**`
- *Italic*: `*text*`
- `Code`: `` `code` ``
- Lists: `- item` or `1. item`
- Links: `[text](url)`
- Images: `![alt](url)`

All formatting is preserved in Anki cards.

## Quick Reference

| Pattern | Syntax | Example |
|---------|--------|---------|
| Basic | `{{answer}}` | `{{Paris}}` |
| Hint | `{{answer\|hint}}` | `{{API\|Application Programming Interface}}` |
| Extra | `{{answer<extra}}` | `{{pip<Python package manager}}` |
| Combined | `{{answer\|hint<extra}}` | `{{RAM\|temporary storage<Random Access Memory}}` |
| Grouped | `{{id>answer}}` | `{{1>red}}` |
| Sequence | `{{id.order>answer}}` | `{{1.2>second step}}` |
| Scope | `{{answer}}[scope]` | `{{answer}}[-1,1]` |
| Math | `{{$formula$}}` | `{{$E=mc^2$}}` |

## Error Recovery

If generation fails, check these common issues:

1. **Missing `> ?` marker**: Add at start of block
2. **Extra closing bracket**: Count braces, ensure they match
3. **Wrong delimiter**: Check `|` for hints, `<` for extra (no closing `>`)
4. **Scope inside braces**: Move `[scope]` outside `}}`
5. **Nested clozes**: Flatten to separate clozes
6. **Empty answer**: Add content between `{{` and `}}`

## Version Notes

This specification is for mnmd-anki-sync v0.1.0+

**Breaking changes from earlier versions:**
- Hint syntax changed from `{{.|hint}}` to `{{answer|hint}}`
- Extra syntax changed from `{{.<extra>}}` to `{{answer<extra}}`
- HINT and EXTRA are no longer separate cloze types
- Anki IDs can now appear in any order with group IDs

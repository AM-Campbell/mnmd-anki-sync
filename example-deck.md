---
mnmd_file_id: INYbaJQa
---

# Example Mnemonic Markdown Deck

This file demonstrates all features of mnemonic markdown syntax for Anki flashcards.

## Basic Clozes (Default: Paragraph Context)

The capital of France is {{bLmBsEJM>Paris}}.

The capital of Spain is {{bLmBsELj>Madrid}}.

Python is a {{bLmBsEMG>dynamically typed}} programming language.

## Multiple Clozes in Same Paragraph

Python was created by {{bLmBsEOc>Guido van Rossum}} in {{bLmBsEPA>1991}}.

The three primary colors are {{bLmBsEQW>red}}, {{bLmBsESu>blue}}, and {{bLmBsETQ>yellow}}.

## Clozes with Hints

HTTP stands for {{bLmBsEVn>Hypertext Transfer Protocol|HTTP}}.

REST stands for {{bLmBsEWK>Representational State Transfer|REST}}.

The `len()` function in Python returns the {{bLmBsEYi>length|number of items}} of a sequence.

## Clozes with Extra Information

The package manager for Python is {{bLmBsEZF>pip<PyPI hosts over 400,000 packages}}.

Git is a {{bLmBsFbc>distributed version control system<created by Linus Torvalds in 2005}}.

JavaScript uses {{bLmBsFcz>prototypal inheritance<unlike class-based inheritance in Java}}.

## Combined Hints and Extras

API stands for {{bLmBsFdV>Application Programming Interface|API<interfaces between software components}}.

RAM is {{bLmBsFft>Random Access Memory|temporary storage<data is lost when power is off}}.

## Grouped Clozes (Same ID = Hidden Together)

The three states of matter are {{1,bLmBsFgQ>solid}}, {{1,bLmBsFgQ>liquid}}, and {{1,bLmBsFgQ>gas}}.

In Python, the primary data structures are {{bLmBsFim>lists}}, {{bLmBsFjJ>dictionaries}}, {{bLmBsFlg>sets}}, and {{bLmBsFmE>tuples}}.

A valid HTTP request requires a {{bLmBsFob>method}}, a {{bLmBsFpy>URL}}, and {{bLmBsFqU>headers}}.

## Sequence Clozes (Progressive Reveal)

The Git workflow typically follows these steps:
- {{git.1,bLmBsFsr>git add .}}
- {{git.2,bLmBsFtO>git commit -m "message"}}
- {{git.3,bLmBsFvl>git push}}

To create a Python virtual environment:
1. {{venv.1,bLmBsFwJ>python -m venv venv}}
2. {{venv.2,bLmBsFyf>source venv/bin/activate}}
3. {{venv.3,bLmBsFzD>pip install -r requirements.txt}}

## Math Support (LaTeX)

Einstein's famous equation is {{bLmBsFBa>$E = mc^2$}}.

The quadratic formula is {{bLmAHHpn>$x = \frac{-b \pm \sqrt{b^2 - 4ac}}.

The Pythagorean theorem states that {{bLmBsFCw>$a^2 + b^2 = c^2$|where c is the hypotenuse}}.

The derivative of $x^2$ is {{bLmBsFDU>$2x$}}.

## Block Math

The Taylor series expansion:

$$f(x) = f(a) + f'(a)(x-a) + \frac{f''(a)}{2!}(x-a)^2 + \cdots$$

The integral formula for area is {{bLmBsFFr>$$\int_a^b f(x) dx$$}}.

## Scope Control (Context Boundaries)

This paragraph provides important context.

This sentence contains {{bLmBsFGO>a cloze}}[-1] that includes the paragraph above.

{{bLmBsFIl>This cloze}}[1] includes the paragraph below for context.

This paragraph provides additional context that helps understand the cloze above.

## Markdown Formatting Works

Python lists are **{{bLmBsFJH>ordered}}** and *{{bLmBsFLe>mutable}}* collections.

The `git status` command shows {{bLmBsFMB>untracked files}}.

Common HTTP status codes:
- {{bLmBsFNZ>200}} - OK
- {{bLmBsFPw>404}} - Not Found
- {{bLmBsFQT>500}} - Internal Server Error

## Code in Context

In Python, you can create a list with:
```python
my_list = [1, 2, 3]
```

The variable `my_list` is of type {{bLmBsFSq>list}}.

## Images in Cards (if you have image files)

<!-- Uncomment and adjust path if you have images:
![Python Logo](./images/python-logo.png)

The Python logo features two snakes representing {{bLmBsFTN>the dual nature of Python 2 and 3}}.
-->

## With Headings and Structure

### Programming Languages

#### Python
- Created in: {{bLmBsFVj>1991}}
- Creator: {{bLmBsFWG>Guido van Rossum}}
- Type system: {{bLmBsFYe>dynamic}}

#### JavaScript
- Created in: {{bLmBsFZB>1995}}
- Creator: {{bLmBsGaX>Brendan Eich}}
- Runs in: {{bLmBsGcv>browsers}}

### Data Structures

#### Lists
Lists in Python are {{bLmBsGdS>ordered, mutable}} collections.

#### Sets
Sets contain {{bLmBsGfp>unique}} elements.

#### Dictionaries
Dictionaries store {{bLmBsGgM>key-value}} pairs.

## Special Case: Custom Context with > ? Blocks

Sometimes you need to override paragraph boundaries or create custom contexts.

> ?
> This is a custom context block.
> It can span multiple lines with precise control.
> The capital of Italy is {{bLmBsGij>Rome}}.

Normal paragraph-based context resumes here with {{bLmBsGjG>another cloze}}.

> ?
> Custom contexts are useful for:
> - {{bLmBsGlc>Overriding paragraph boundaries}}
> - {{bLmBsGmz>Creating multi-line contexts}}
> - {{bLmBsGnW>Excluding surrounding content}}

> ?
> You can also use them for lists where each item is separate:
> - Item one has {{bLmBsGpt>cloze A}}
> - Item two has {{bLmBsGqR>cloze B}}
> - Item three has {{bLmBsGso>cloze C}}

## Mixed Syntax (Advanced)

In a RESTful API, {{bLmBsGtK>GET}} retrieves data, {{bLmBsGvh>POST}} creates resources, {{bLmBsGwE>PUT}} updates resources, and {{bLmBsGyc>DELETE}} removes them.

The HTTP status code {{bLmBsGzy>201|Created}} indicates successful resource creation, while {{bLmBsGAW>204|No Content}} means success with no response body.

Database transactions must be {{bLmBsGCt>ACID<Atomic, Consistent, Isolated, Durable}} compliant.

## Complex Example: All Features Combined

> ?
> React is a JavaScript {{bLmBsGDP>library|UI framework<technically a library, not a framework>}} created by {{bLmBsGFm>Facebook}} in {{bLmBsGGK>2013}}.
>
> Its key innovation is the {{bLmBsGIh>virtual DOM|VDOM<improves performance by minimizing actual DOM updates>}}.

In modern React, functional components use {{bLmBsGJD>hooks}} to manage state.

The most common hooks are {{bLmBsGLa>useState}}, {{bLmBsGMy>useEffect}}, and {{bLmBsGNU>useContext}}.

A basic React component follows this pattern:
```jsx
function MyComponent() {
  return <div>Hello</div>;
}
```

The JSX syntax is {{bLmBsGPr>transpiled to JavaScript|converted at build time}}.

## Tips for Creating Good Cards

**DO:**
- Keep answers concise (1-5 words ideal)
- Use hints for technical terms
- Add extras for complex concepts
- Use grouped clozes for related items
- Use sequences for ordered steps

**DON'T:**
- Make answers too long or complex
- Create overlapping clozes that confuse
- Forget to test your cards after syncing

## End of Example Deck

This deck demonstrates:
- ✅ Clozes in regular paragraphs (default, most common)
- ✅ `> ?` blocks for custom contexts (special cases)
- ✅ Hints with `|`
- ✅ Extras with `<` (no closing `>`)
- ✅ Grouped clozes with same ID
- ✅ Sequence clozes with `id.order`
- ✅ Math with `$` and `$$`
- ✅ Scope control with `[before,after]`
- ✅ Full markdown support

**Total cards in this deck:** ~80+ flashcards from natural markdown!

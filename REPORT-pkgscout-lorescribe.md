# REPORT-pkgscout-lorescribe

## SUMMARY BLOCK

`brief-base v6 read`

- **State:** done.
- **Deviations:** (1) The brief assigned a git worktree; repo `CLAUDE.md` carries a standing
  "NO WORKTREES UNTIL WORKTREES WORK" directive. Brief > CLAUDE.md per brief-base §precedence,
  so I worked in the worktree and note the conflict here. (2) I ran read-only probes that
  *imported* `lorescribe` and *ephemerally installed* candidate packages via
  `uv run --no-sync --with …` (brief-authorized). No file in the tree was modified except this
  report; the lockfile was not touched.
- **Coverage:** all **12** production files / **4,357 LOC** under `lorescribe/lorescribe/` read in
  full (`astroid_parse` 1021, `python_ast` 590, `javascript` 571, `xml_generic` 524, `sql` 494,
  `markdown` 383, `text` 202, `registry` 182, `models` 168, `stylesheet` 166, `base` 55,
  `__init__` 1 — sums to 4,357, matching the brief). Measured at `6654be0` on 2026-07-25.
- **Not re-reported:** #201 (`scripts/` statistical core) and #202 (`_txn.retry_on_conflict`) are
  out of my file set and untouched here.
- **Scope-law raises (not package findings, not buried):** items **S1–S4** below.

### Ranked verdicts — ranked by what a WRONG choice costs

| # | Symbol | Hand-rolls | Library | Verdict |
|---|---|---|---|---|
| 1 | `javascript.py::_scan_braces` | JS block scanning by counting `{`/`}` | `tree-sitter` + `tree-sitter-javascript` | **REPLACE-WITH-ADAPTER** |
| 2 | `markdown.py::_parse_sections`, `::_line_range` | ATX-only heading + fence parser; substring line anchor | `markdown-it-py` (already locked) | **REPLACE-WITH-ADAPTER** |
| 3 | `_fit_to_cap` · `_enforce_token_cap` · `_split_to_cap`+`_char_slice` · `_fit_window_end` · `stylesheet.chunk` (**5 copies of one policy**) | "shrink until it fits the token cap" | `RecursiveCharacterTextSplitter(length_function=…)` (already a dep) | **REPLACE-WITH-ADAPTER** |
| 4 | `xml_generic.py::_line_range` (+ triple parse) | fabricated line spans; ElementTree drops source offsets | `lxml` (already locked) | **REPLACE-WITH-ADAPTER** |
| 5 | `sql.py::_strip_psql_meta_commands` | line-wise `\`-prefix strip, string-blind | `sqlglot.tokenize` — **already imported in this file** | **REPLACE** |
| 6 | `stylesheet.py` (whole chunker) | line windows, zero CSS parsing | `tinycss2` — **measurably fails on `.scss`** | **KEEP + RE-OPEN TRIGGER** |
| 7 | `registry.py` routing | suffix map + per-chunker `handles()` | `identify` | **KEEP + RE-OPEN TRIGGER** |
| 8 | `text.py::_locate_lines` | linear offset→line scan per window | stdlib `bisect` | **REPLACE** (low value) |
| 9 | `astroid_parse.py::evict_resolved_file` | pokes astroid's private `_mod_file_cache` | none exists | **GENUINELY BESPOKE** (+ needs a pin) |
| 10 | `_assign_sub_ordinals` ×2 · `_compose_embedding_text` ×2 · minified-detect ×2 · `window#N` mint ×4 | in-house duplication, **no package involved** | — | **ONE-IMPLEMENTATION defects** |

### Decisions needed from the operator

- **D1.** #1–#4 add three direct dependencies (`tree-sitter`+`tree-sitter-javascript`,
  `markdown-it-py`, `lxml`). Two of the three are **already in `uv.lock`**. Approve the set, or
  a subset, or sequence them?
- **D2.** #4 (lxml) trades a **loud** refusal for a **silent** one unless a ~15-line adapter is
  written — see §4. Confirm the adapter is wanted (my recommendation: yes, it is required).
- **D3.** #1/#2 change chunk boundaries → **point-IDs change → a full reindex**. Confirm that
  cost is acceptable before either lands.

### Tool honesty

lore's index watches the MAIN checkout, not this worktree (#125), so **every structural question
here was answered by `Read`/`grep` in the worktree, not by `lore_search`/`lore_impact`** — stated
per brief-base §4. The one cross-package question (is `line_start` actually served to agents?) was
also grep, for the same reason. No lore friction filed: this is the known #125 bound, not a new gap.

---

## Method note — how claims are marked

- **[source-verified]** — I read the code in this worktree at `6654be0` and/or executed it.
- **[library-verified]** — I executed the library, version named.
- **[my judgement]** — an opinion, sizing, or recommendation.

Every probe below that reports a defect is **paired with a positive control**, per repo law
(*"a probe needs a control"*). Every probe asserted `lorescribe.__file__` resolves inside
`/home/ejprice/PycharmProjects/lore-pkt11i` before running (per *PROVE WHICH TREE YOU ARE
TESTING*); the receipt printed:

```
PROVENANCE lorescribe.__file__ = /home/ejprice/PycharmProjects/lore-pkt11i/lorescribe/lorescribe/__init__.py
OK: testing the pkt11i worktree
```

---

## 1. `javascript.py::_scan_braces` — the brace counter truncates function bodies into the index

**REPLACE-WITH-ADAPTER · highest rank**

### What it does

`JavascriptChunker._detect_units` matches top-level units with four regexes (`_RE_FUNCTION`,
`_RE_CLASS`, `_RE_EXPORT_NAMED`, `_RE_EXPORT_DEFAULT_ANON`) and then finds each unit's end by
`_scan_braces`, which counts `{` and `}` characters. Its own docstring concedes the gap:
*"String literals containing braces are not parsed (good enough for the generic structural
split)."* **[source-verified]**

### It is not good enough — measured

A `}` inside a string literal closes the function early. The truncated tail is then re-filed as an
anonymous `window#N` chunk under a different identity:

```
BRACE-IN-STRING probe: identities = ['alpha', 'window#0', 'beta']
  identity='alpha'    lines=1-2   type=js_function      <-- body TRUNCATED
  identity='window#0' lines=3-5   type=window           <-- the rest of alpha(), misfiled
  identity='beta'     lines=6-8   type=js_function
  _scan_braces(alpha at line 0) -> 1   (0-indexed; CORRECT answer is 3)

CONTROL (no brace in string): identities = ['alpha', 'beta']
  _scan_braces(alpha) -> 3 (expect 3)
```

**[source-verified]** The control proves the probe discriminates: the identical file with the
string literal removed scans correctly. So the failure is caused by the string, not by the fixture.

Consequence: a retrieval hit on `alpha` returns a function body **missing its return statement**,
and the missing half is indexed under a meaningless `window#0` identity. The index is silently
wrong, and nothing in the suite can see it — `tests/test_javascript.py` has no brace-in-string
fixture. This is the repo's own *"what WRONG build would this fixture still pass?"* class.

The same scanner is blind to `//` and `/* */` comments, regex literals (`/}{/g`), and template
literals (`` `${x} }` ``). Separately, `_RE_EXPORT_NAMED` only matches `export const|let|var`, so a
plain top-level `const f = () => {…}` — the dominant modern idiom — is never detected as a unit at
all and falls into anonymous windows. **[source-verified]**

### The library does the job

`tree-sitter` 0.26.0 + `tree-sitter-javascript` 0.25.0, on a file containing *every* hazard above:

```
TOP-LEVEL NODES (type, name, 1-based line span):
  function_declaration   name=alpha  lines 1-7     <-- correct despite "}" , /}{/g , `${x} }` , // }
  class_declaration      name=Beta   lines 9-9
  export_statement       name=None   lines 11-11
  lexical_declaration    name=None   lines 13-13   <-- the bare `const arrow = () => {…}` the regex misses
has ERROR nodes? False
```

**[library-verified: tree-sitter 0.26.0, tree-sitter-javascript 0.25.0]**

`start_point` / `end_point` give exact 0-based `(row, col)` — so line spans come from the parser
instead of being derived. tree-sitter is also **error-tolerant**: a partial parse yields a tree with
`ERROR` nodes rather than an exception, which subsumes today's implicit "regex never fails" property
without needing a syntax-error fallback path.

### The adapter (the real gap)

tree-sitter gives a CST; it does **not** give lore's `JsBlock` seam, the `JsProfile` hook, the
`window#N` gap-filling between units, or token-cap fitting. Keep all of that. **Size: replace
`_detect_units` + `_match_unit` + `_scan_braces` + `_scan_statement_or_braces` (~70 LOC) with a
~30-LOC walk over `tree.root_node.children` that emits `_DetectedUnit`s.** Everything downstream of
`_scan_blocks` is untouched. **[my judgement]**

### Proving control

The brace-in-string probe above, **as a committed test**: assert `chunk()` on that fixture yields
exactly `['alpha', 'beta']`. It is RED on today's code (proven above) and GREEN after the swap —
a mutation-proven pin, not a decoration. Add the sibling fixtures (regex literal, template literal,
comment, bare arrow `const`) in the same file. **[my judgement]**

---

## 2. `markdown.py::_parse_sections` / `::_line_range` — three CommonMark defects, one false citation

**REPLACE-WITH-ADAPTER**

### What it does

`_parse_sections` walks lines with two regexes: `_HEADING_LINE` (ATX `#`-prefixed only) and
`_FENCE_LINE`. The module docstring justifies hand-rolling by an *empirical* objection to LangChain's
`MarkdownHeaderTextSplitter` — that it **merges** same-named sections and **rewrites** content
(stripping indentation inside fences). That objection is correct and I am not disputing it.
**It does not apply to `markdown-it-py`**, which is a *tokenizer*, not a splitter: it returns
`token.map = [start_line, end_line)` and you slice the **raw source** yourself, byte-for-byte.
**[source-verified for the objection; library-verified for the non-applicability]**

### Three defects, measured against today's code

```
=== A. SETEXT HEADINGS (valid CommonMark) ===
  identities: ['(preamble)']
  CONTROL (same doc written with ATX): ['Introduction', 'Introduction > Details']

=== B. CommonMark closing-fence-length rule ===
  identities: ['Doc']
  (expected ['Doc','After'] — a 4-backtick fence is NOT closed by 3 backticks,
   so the trailing '# After' heading is swallowed into the code block)

=== D. _line_range substring mis-anchor ===
  identity='Alpha' reported lines 3-3  text='value'
  identity='Beta'  reported lines 3-3  text='value'
  (true source lines: '# Alpha'=1, its body=3 ; '# Beta'=5, its body=7)
```

**[source-verified]**

- **A — setext headings are invisible.** `Title\n=====` is standard CommonMark. A document written
  in setext style collapses to **one chunk with identity `(preamble)`** — section-level retrieval
  for that file is destroyed. The ATX control proves the parser works when the syntax is the one
  shape it knows.
- **B — the fence-length rule is wrong.** `_parse_sections` compares `marker[:3] == fence_marker`,
  truncating both to 3 characters, so a 4-backtick fence is closed by a 3-backtick one. Everything
  after is swallowed. (Related, same cause: `_FENCE_LINE` allows *any* leading whitespace, but
  CommonMark caps fence indent at 3 spaces — a fence inside an indented code block toggles state.)
- **D — served citations point at the wrong line.** `_line_range` anchors by
  `if anchor in source_line` — the **first** line containing the anchor as a substring. Both
  sections' bodies report line 3; `Beta`'s body is at line 7.

I checked case **C** (a 4-space-indented `# …` inside an indented code block) and it is **handled
correctly** — the `^` anchor on `_HEADING_LINE` rejects it. I am not reporting it as a defect.
**[source-verified]** — noting this because reporting a non-defect would be the same failure as
missing one.

### Why D is worse than "advisory metadata"

`Chunk.line_start` is not internal. `loremaster/loremaster/search.py` renders it into the citation
lore serves to agents:

```
search.py::_render… ->  _sanitise_line(f"[SOURCE:{file_path}:{line_start}]")
                        f"{_SHORT_CITATION_PREFIX}{tier}:{file_path}:{line_start}-{line_end}@{hash6}]"
```

**[source-verified]** An agent following `[SOURCE:doc.md:3]` for the `Beta` section lands on the
wrong line. Under the repo's **TRUST DOCTRINE** ("a served count describes the whole set its label
claims… no render over-claims"), a wrong citation is a served-surface falsehood, not a cosmetic nit.

### The library does the job

`markdown-it-py` 4.2.0 — **already in `uv.lock`** (transitively, via `rich` 15.0.0)
**[library-verified]**:

```
=== A. SETEXT ===        [('h1','Introduction',[0,2],'='), ('h2','Details',[5,7],'-')]
=== B. FENCE LENGTH ===  [('h1','Doc',[0,1],'#'),          ('h1','After',[8,9],'#')]
=== C. INDENTED CODE === [('h1','Doc',[0,1],'#')]           (correctly NOT a heading)
=== D. LINE MAPS ===     heading_open map=[0,1] raw=['# Alpha']
                         paragraph_open map=[2,3] raw=['value']
                         heading_open map=[4,5] raw=['# Beta']
                         paragraph_open map=[6,7] raw=['value']
```

All three defects fixed, and `map` supplies true line spans — so `_line_range` is **deleted**, not
reimplemented.

### The adapter (the real gap)

`markdown-it-py` gives a token stream, not lore's section model. Keep: the heading-path breadcrumb,
`PREAMBLE_IDENTITY`, the occurrence-ordinal disambiguator (`_build_identity`), and the size/token
splitting. **Replace `_parse_sections`, `_segment_by_fence` and `_line_range` (~90 LOC) with a
~35-LOC walk that builds `_Section`s from `heading_open` tokens and slices raw source by `map`.**
`_size_split_protecting_fences`'s fence detection also becomes free — `fence` tokens carry their own
`map`. **[my judgement]**

### Proving control

The A/B/D probes as committed tests (RED today, proven above). Critically, **keep a byte-exactness
pin**: chunk a document with an indented fenced code block and assert `source_text` is byte-identical
to the raw source slice — that is the property the original hand-roll existed to protect, and it must
survive the swap. This is the repo's *removed-behavior inventory* rule applied. **[my judgement]**

---

## 3. Token-cap fitting — **five** hand-rolled copies of one policy

**REPLACE-WITH-ADAPTER · this is the ONE-IMPLEMENTATION finding**

### Derived, not estimated

`grep -n "count_tokens(" lorescribe/lorescribe/*.py` → **13 call sites across 7 files**. Of those,
**five files implement an independent "shrink until it fits" algorithm**, each different:

| Module | Symbol | Algorithm |
|---|---|---|
| `text.py` | `TextChunker._fit_to_cap` | recursive **character bisection** |
| `markdown.py` | `MarkdownChunker._enforce_token_cap` | re-split at a **halved character budget**, recursive |
| `python_ast.py` | `PythonAstChunker._split_to_cap` + `._char_slice` | greedy **line accumulation**, then char slicing with a chars-per-token estimate |
| `javascript.py` | `JavascriptChunker._fit_window_end` | **line-at-a-time shrink** |
| `stylesheet.py` | `StylesheetChunker.chunk` (inline) | **line-at-a-time shrink** (a sixth variant, not even extracted to a method) |

The remaining two (`sql.py::_build_chunks`, `xml_generic.py::_emit`) only *test* the cap and route to
a structural split. **[source-verified]**

This is the repo's `#102` shape exactly: one POLICY — *"no emitted chunk's composed
`embedding_text` may exceed `ctx.max_input_tokens`"* — cloned five ways. The tests match the shape:
the invariant is pinned **separately** in `test_text_chunker.py`, `test_markdown.py`,
`test_javascript.py`, `test_stylesheet.py`, `test_python_ast.py`. There is **no single
cross-chunker cap invariant**, so a sixth chunker added tomorrow inherits nothing and is pinned only
if its author remembers. **[source-verified]**

### The library does most of the job — verified, with the gap named

`langchain-text-splitters` 1.1.2 is **already a direct dependency** and `RecursiveCharacterTextSplitter`
accepts `length_function`. Passing `ctx.count_tokens` makes it natively token-aware, and every
`from_language` separator list terminates in `""` (a character-level base case), so the recursion
always bottoms out:

```
MARKDOWN seps: ['\n#{1,6} ', '```\n', '\n\\*\\*\\*+\n', '\n---+\n', '\n___+\n', '\n\n', '\n', ' ', '']
PYTHON   seps: ['\nclass ', '\ndef ', '\n\tdef ', '\n\n', '\n', ' ', '']
JS       seps: ['\nfunction ', '\nconst ', … , '\n', ' ', '']
```

Measured against the **real** voyage-4 tokenizer (`loresigil.tokens.VoyageTokenCounter`, a local Rust
BPE — *not* a network call), splitting a real 383-line source file at a 60-token cap:

```
  MARKDOWN  cap=60 pieces=  88 max_tokens=  56 OVER-CAP=0
  PYTHON    cap=60 pieces=  88 max_tokens=  56 OVER-CAP=0
  JS        cap=60 pieces=  88 max_tokens=  56 OVER-CAP=0
  indivisible-atom cap=5: pieces=1000 max_tokens=2 OVER-CAP=0   <-- base-case control
```

**[library-verified: langchain-text-splitters 1.1.2]**

### But the library does **not** promise the hard cap — and I can show why

Two independent reasons, both verified:

1. **Its own source concedes it.** In `TextSplitter._merge_splits`, an over-budget chunk is emitted
   with only `logger.warning("Created a chunk of size %d, which is longer than the specified %d")`.
   In `RecursiveCharacterTextSplitter._split_text`, when a split exceeds `chunk_size` and
   `new_separators` is empty, it does `final_chunks.append(s)` verbatim. **[library-verified,
   read from the installed source]**
2. **`_merge_splits` sums per-piece lengths** and compares the sum to `chunk_size`. That is exact
   only if the counter is subadditive. **The real voyage-4 tokenizer is not:**

```
  VIOLATION: ' import Chunker\nfrom lore' | 'scribe.models import Chun'  40 + 40 < 81
  VIOLATION: '[str] = frozen'             | 'set({".md", ".markdown"})'   4 + 67 < 72
  VIOLATION: '          ``True`` for ``'  | '.md`` / ``.markdown`` (an'   9 + 52 < 62
  subadditivity: 4/4000 violations (count(a+b) > count(a)+count(b))
```

**[library-verified: `tokenizers`-backed `VoyageTokenCounter`, 4/4000 = 0.1% of random splice
points]** BPE merges across a join can *increase* the count. Rare, but the cap is a hard
correctness constraint (the embedder returns HTTP 422, never truncates), so 0.1% is not zero.

**This is the two-sided rule resolving to side 2, on a small surface:** the package does the hard
part (separator-aware, language-aware splitting); it does **not** do the hard-cap guarantee. So
hand-roll exactly that — once.

### The adapter

**One shared function**, e.g. `lorescribe.sizing.fit_to_cap(text, header, ctx, *, language)`:

1. Compute `budget = ctx.max_input_tokens - ctx.count_tokens(header + "\n")` — this **subtracts the
   header**, which today only `python_ast` does correctly (`markdown._enforce_token_cap` measures
   the composed text but hands the splitter a budget in **characters** with no header subtraction).
2. Delegate to `RecursiveCharacterTextSplitter.from_language(language, chunk_size=budget,
   chunk_overlap=0, length_function=ctx.count_tokens)`.
3. **Verify and recurse**: any piece whose *composed* text still exceeds the cap is re-split at a
   halved budget; the terminal case emits as-is. This is the ~10-line bespoke part.

Delete all five copies; each chunker calls the seam. **~180 LOC of duplicated fitting collapses to
~35.** **[my judgement]**

### Proving control — the one that matters

**PROVE SHARING BY MUTATION** (standing law): change the shared budget arithmetic in
`fit_to_cap` and **all five chunkers' cap pins must go RED**. A chunker that stays green is a
private copy wearing the shared name — which is exactly what exists today. Plus one new
**cross-chunker invariant test**: parametrize over every registered chunker and assert
`ctx.count_tokens(chunk.embedding_text) <= ctx.max_input_tokens` for all emitted chunks. That is
the invariant a sixth chunker inherits for free. **[my judgement]**

---

## 4. `xml_generic.py::_line_range` — every XML chunk cites line 1

**REPLACE-WITH-ADAPTER**

### What it does

The docstring is honest about the limitation: *"ElementTree does not preserve original source
offsets through `fromstring`, so the span is reported relative to the serialized element text: it
always starts at line 1."* **[source-verified]** Measured:

```
TRUE source lines: <odoo>=1  view_a=2  view_b=5
  identity='name' SERVED line_start=1 line_end=2  metadata['line_range']=(1, 2)
  identity='name' SERVED line_start=1 line_end=2  metadata['line_range']=(1, 2)
```

**[source-verified]** Same served-citation consequence as §2/D — `[SOURCE:views.xml:1]` for every
XML chunk in the corpus, forever.

Secondly, `chunk()` **parses the source three times**: `_reject_if_too_deep` (defused `iterparse`),
`safe_fromstring`, and `_collect_namespaces` (defused `iterparse` again). **[source-verified]**

### The library does the job

`lxml` 6.1.1 (libxml2 2.14.6) — **already in `uv.lock`**, and `lorescribe/pyproject.toml` already
declares an optional extra `lxml = ["lxml>=5"]`:

```
  <root>   id=None sourceline=1
  <record> id=a    sourceline=2
  <field>  id=None sourceline=3
  <record> id=b    sourceline=5
  <field>  id=None sourceline=6

  nsmap on root: {}   (namespaces available WITHOUT a second parse of the source)
```

**[library-verified: lxml 6.1.1]** True source lines, plus `nsmap` collapses the third parse.

### The security question — investigated, not assumed

Replacing `defusedxml` means taking on the XXE / entity-bomb surface it currently owns. Probed with
`etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False, load_dtd=False)`:

```
  billion-laughs   parsed OK  len(text)=       0  CANARY-LEAKED=False
  XXE-file-read    parsed OK  len(text)=       0  CANARY-LEAKED=False
  CONTROL resolve_entities=True on a benign entity -> 'hi'
```

**[library-verified: lxml 6.1.1]** The control proves the refusal is real, not a no-op: with
`resolve_entities=True` the same parser *does* expand a benign entity. So lxml is safe against both
attacks.

**⚠ But the failure mode differs, and this is the gap.** `defusedxml` **raises**
(`EntitiesForbidden` / `ExternalReferenceForbidden`). `xml_generic.chunk` deliberately lets those
propagate — its docstring promises a hostile document is *"refused at parse time, never expanded"*,
and `_collect_namespaces` / `_reject_if_too_deep` each carry a comment saying security exceptions
must NOT be caught. **[source-verified]** lxml instead **silently drops** the entity (text length 0
above). Under the repo's trust doctrine — *"failures are LOUD, never silent"* — a silent swap is a
behaviour regression, and it is precisely the *removed-behavior inventory* item the repo's
delete/replace law says must be adjudicated rather than lost.

### The adapter (the real gap — this is D2)

Alongside the lxml parse, inspect `root.getroottree().docinfo.internalDTD` (and `.system_url`) and
**raise** when a DTD or entity declaration is present — restoring loud refusal on top of lxml's safe
parse. **~15 LOC.** Depth handling can then use lxml's own bounded parse instead of the third
`iterparse` sweep, with `MAX_DEPTH` retained as the explicit policy. **[my judgement]**

### Proving control

Port the existing hostile-document tests in `tests/test_xml_generic.py` unchanged — they assert a
**raise**, so they are the exact pin that catches a silent-drop regression. Add a
`sourceline`-correctness test asserting a nested `<record>`'s `line_start` equals its true source
line (RED today, proven above). **[my judgement]**

---

## 5. `sql.py::_strip_psql_meta_commands` — destroys source inside dollar-quoted bodies

**REPLACE · the library is already imported in this very file**

### The defect, measured

`_strip_psql_meta_commands` blanks any line whose first non-whitespace character is `\`. It is
string-blind, so a `\`-leading line **inside a `DO $$ … $$` body** is destroyed — and `DO $$ … $$`
is named in the module docstring as the motivating corpus feature:

```
=== HAZARD: a backslash line INSIDE a dollar-quoted body gets blanked ===
  before: '\\d not_a_meta_command_here'
  after : ''            <-- body line DESTROYED inside $$...$$

=== CONTROL: a genuine psql meta-command outside a block is correctly blanked ===
   '\nSELECT 1;'
```

**[source-verified]** The control proves the function's intended behaviour still works, so the
failure is the string-blindness, not the fixture. The corrupted text is what gets indexed as
`source_text`.

### The fix needs no new package

`sqlglot` 30.8.0 is already imported here, and `_iter_statement_spans` already relies on its
tokenizer to skip `;` inside dollar-quoted blocks. The tokenizer models the whole body as **one
`STRING` token with exact offsets**:

```
  TokenType.COMMAND     start=  0 end=  1 text='DO'
  TokenType.STRING      start=  3 end= 51 text="$$\nBEGIN\n  RAISE NOTICE 'x';\n\\d not_a_meta\nE"
  TokenType.SEMICOLON   start= 52 end= 52 text=';'
  TokenType.SELECT      start= 54 end= 59 text='SELECT'
```

**[library-verified: sqlglot 30.8.0]** Fix: tokenize **first**, then blank a `\`-leading line only
when its offset lies **outside** every token span. Requires reordering the pipeline (tokenize before
strip) — ~10 LOC, no new dependency. Do **not** hand-roll a dollar-quote tracker; the library you
already import knows where the strings are.

### On replacing sqlglot wholesale with `pglast` — investigated, **not** recommended

`pglast` 8.4 wraps libpg_query (the real PostgreSQL 18.4 grammar) and gives exact statement
boundaries with zero hand-rolled span logic:

```
  stmt_location=10 stmt_len=26 node=IndexStmt  -> 'CREATE INDEX idx_a ON t(c)'
  stmt_location=39 stmt_len=36 node=SelectStmt -> 'WITH x AS (SELECT 1) SELECT * FROM x'
  pglast on a psql meta-command: ParseError    -> psql stripping is STILL needed
```

**[library-verified: pglast 8.4]** It is a genuinely better *parser* for a Postgres-only corpus,
but: it does **not** remove the psql-stripping need (proven above), sqlglot is already load-bearing
and verified at 116/116 on the real corpus, and swapping parsers rewrites all of
`_created_object` / `_referenced_tables` / `_cte_names` / `_leading_comment`. **Verdict: KEEP
sqlglot; fix the stripper.** Re-open trigger: if the corpus ever needs constructs sqlglot degrades
to a `Command` node (procedural bodies, PG-specific DDL) to be *structurally* understood rather than
merely preserved. **[my judgement]**

### Proving control

The dollar-quote probe as a committed test: assert `chunk()` on that fixture yields a `source_text`
byte-identical to the original `DO $$ … $$` block. RED today (proven above).

---

## 6. `stylesheet.py` — `tinycss2` does `.css` and **measurably fails** on `.scss`

**KEEP + RE-OPEN TRIGGER**

The chunker does no CSS parsing at all: 200-line windows with 40-line overlap, plus a
minified-file skip. Rule boundaries, selectors and at-rules are invisible; overlapping windows also
mean the same rule is embedded twice. **[source-verified]**

`tinycss2` 1.5.1 handles real CSS correctly — braces inside strings and comments do **not** break
rule boundaries, and every rule carries `source_line`:

```
  qualified-rule   line=  1 prelude='.header'
  at-rule          line=  5 prelude='(max-width: 600px)'
  qualified-rule   line= 10 prelude='.footer::after'      (this rule contains content:"}")
```

**But it does not do the SCSS job**, which this chunker also claims (`.scss` is in
`_CLAIMED_EXTENSIONS`):

```
  qualified-rule   line=1  prelude='$primary: #333;\n@mixin flex'   <-- WRONG: two statements fused
  qualified-rule   line=3  prelude='.card'
```

**[library-verified: tinycss2 1.5.1]** Variables, `@mixin`, nesting and `&:hover` are not CSS, and
tinycss2 mis-parses them into a single bogus prelude. Swapping in tinycss2 today would make `.scss`
chunking *worse* than line windows.

**Verdict: KEEP.** Stylesheets are the lowest-semantic-value corpus in the set, the current code is
simple and correct-by-construction (it makes no structural claims it cannot honour), and the only
library that does the whole job is `tree-sitter-scss` — i.e. finding #1's dependency, not a new one.

**Re-open trigger (the #202 shape):** the day (a) stylesheet retrieval quality is an actual
complaint, **or** (b) finding #1 lands and `tree-sitter` is already a dependency — at which point
`tree-sitter-css`/`tree-sitter-scss` costs one more grammar package rather than a new toolchain, and
the trade flips. **[my judgement]**

---

## 7. `registry.py` — `identify` could own the classification; it should not own it yet

**KEEP + RE-OPEN TRIGGER**

`ChunkerRegistry` is a 182-LOC routing policy: override > predicate (`handles`) > suffix map >
`[]`. The routing *policy* is lore's own and no package supplies it. The *classification* half —
filename → language — is exactly what `identify` 2.6.19 (pre-commit's own classifier) does,
including the basename cases the registry's tier-2 docstring names as its motivation:

```
  pyproject.toml -> ['pyproject','text','toml']     Dockerfile -> ['dockerfile','text']
  Makefile       -> ['makefile','text']             b.min.js   -> ['javascript','text']
  CMakeLists.txt -> ['cmake','plain-text','text']   go.mod     -> ['go-mod','text']
```

**[library-verified: identify 2.6.19]**

**Verdict: KEEP.** Today every registered chunker's `handles()` is a pure suffix test with no
overlaps, so `identify` would replace working code with equivalent working code — churn against
proven, guarded routing, which is the #202 trade. (Note: tier 2 never fires for the *base* chunker
set, but it is genuinely reachable — `loremaster/loremaster/server.py` documents extensions
registering basename/pattern chunkers. Not dead code. **[source-verified]**)

**Re-open trigger:** the first basename-keyed chunker (a `Dockerfile` / `Makefile` / `pyproject.toml`
chunker), or the third new language added — at that point per-chunker `handles()` stops scaling and
`identify` becomes the cheaper answer. **[my judgement]**

---

## 8. `text.py::_locate_lines` — stdlib `bisect` does this

**REPLACE (low value)**

`_locate_lines` converts a character offset to a 1-based line by walking `source_lines` from the
top on **every call**, i.e. O(lines) per window → O(lines × windows) per file. The standard idiom is
a prefix-sum of line lengths plus `bisect.bisect_right` — O(log lines) after one O(lines) setup.
**[source-verified]** No behaviour change, ~8 LOC, stdlib only. Low rank because it is a performance
and idiom issue, not a correctness one — the current code is correct.

Related, same file: `_CHARS_PER_TOKEN_ESTIMATE = 4` sizes the splitter's character budget by
heuristic **even though the real token counter is injected on `ctx`**. Finding #3's adapter
(`length_function=ctx.count_tokens`) deletes this constant. **[source-verified]**

---

## 9. `astroid_parse.py::evict_resolved_file` — genuinely bespoke, but unpinned

**GENUINELY BESPOKE**

It reaches into astroid's **private** `AstroidManager._mod_file_cache` and depends on its key being a
2-tuple — the module even defines `_MOD_FILE_CACHE_KEY_LENGTH = 2` and checks the shape defensively.
**[source-verified]** I looked for a public alternative: `AstroidManager.clear_cache()` is public but
nukes the entire cache, which defeats the whole point (the warm dependency cache is the documented
speed win). **There is no public per-module eviction API.** So this is the two-sided rule landing on
side 2 correctly: minimal surface, private access confined to one function.

What is missing is the *verifiability* half. **Recommendation: add a pin that asserts the private
attribute exists and its key shape is still a 2-tuple**, so an astroid upgrade fails a test rather
than silently degrading eviction to a no-op (which would resurrect stale-AST resolution — the #24
class). One test, ~6 lines. Note `astroid>=4.1.2` is an open lower bound in
`lorescribe/pyproject.toml`, so an upgrade can arrive without any code change. **[my judgement]**

The rest of `astroid_parse.py` is correct package usage and should not be touched: `_function_signature`
delegates rendering to `node.args.as_string()` rather than hand-rolling it, `_absolute_import_modname`
delegates relative-import resolution to `module_node.relative_to_absolute_name`, and the
`apply_transforms=False` comment shows the astroid cache semantics were investigated, not assumed.
`_discover_package_parent_dirs` uses `os.walk` on a genuine layout question no package answers.
**[source-verified]**

---

## 10. In-house duplication — no package involved, same defect class

These are **ONE IMPLEMENTATION** violations, derived by grep, reported because scope law forbids
burying them.

- **`_assign_sub_ordinals` — 2 definitions, byte-identical code bodies.**
  `javascript.py::JavascriptChunker._assign_sub_ordinals` and
  `xml_generic.py::XmlChunker._assign_sub_ordinals`. `diff` of the two 5-line bodies exits 0.
  **[source-verified]** The JS docstring says *"This mirrors the XML chunker's pass exactly."*
  That sentence is the literal antipattern brief-base §6 names: **a pattern to clone is a defect to
  clone.** This is `(identity, sub_ordinal)` — the natural key that becomes the deterministic
  point-ID. A divergence between the two copies is a silent downstream point-ID collision.
  → one shared `assign_sub_ordinals(chunks)` both call.
- **`_compose_embedding_text` — 2 private copies restating a third, authoritative rule.**
  `markdown.py::MarkdownChunker._compose_embedding_text` and
  `python_ast.py::PythonAstChunker._compose_embedding_text` both re-implement
  `models.py::Chunk.embedding_text`. Both docstrings say they are *"kept in lockstep with the
  model's composition rule"* — by hand. **[source-verified]** Under the repo's *"prose that describes
  behaviour must be DERIVED from the behaviour, not re-stated beside it"* law, the fix is to expose
  the model's composition once (a module-level `compose_embedding_text(header, text)` that
  `Chunk.embedding_text` itself calls) so changing it is a type error at every site, not a prose bug.
- **Minified detection — 2 implementations, different constants, same policy.**
  `javascript.py::JavascriptChunker._is_minified` (`MINIFIED_AVG_LINE_LENGTH = 800`, `.min.js`) vs
  `stylesheet.py::_is_minified_by_content` + `_is_minified_by_filename`
  (`MINIFIED_AVG_LINE_LEN = 200`, `.min.css`). **[source-verified]** The 4× threshold gap may well be
  deliberate per-language tuning — but it is undocumented and unreachable from one place, so nothing
  says whether it is a decision or a drift. → one `is_minified(source, path, *, avg_line_threshold,
  minified_suffix)` with the two constants as named per-language arguments.
- **`window#N` identity mint — 4 independent constructions** of the same string format:
  `text.py` (`f"window#{ordinal}"`), `stylesheet.py` (`f"window#{window_index}"`),
  `javascript.py` (`f"window#{window_index}"`), `python_ast.py`
  (`f"window{IDENTITY_DISAMBIGUATOR}{window_index}"` — which *happens* to render identically).
  **[source-verified]** This is an identity format, i.e. part of the point-ID contract. → one helper.

---

## Scope-law raises (not this mission's findings — surfaced, not buried)

- **S1 — `lorescribe[lxml]` is a declared dependency nothing uses.** `lorescribe/pyproject.toml`
  declares `[project.optional-dependencies] lxml = ["lxml>=5"]`, and `lxml` is resolved in
  `uv.lock`, but **zero** production or test modules import it (grep over `*.py`, `*.toml`,
  `Containerfile`; the only `lxml` hits in the tree are unrelated test fixture *strings* in
  `loremaster/tests/test_source.py` and `test_read_file.py`). **[source-verified]** Either finding
  #4 makes it real, or it should be deleted. Someone already reached this conclusion once and the
  work was never done — worth knowing before D1 is decided.
- **S2 — `sql.py`'s module docstring describes a pipeline the code does not run.** The docstring
  says step 2 is *"Parse the cleaned source with `error_level=IGNORE`"* (multi-statement) and step 3
  is a *"last-ditch fallback"* of splitting on `;` and `parse_one`-ing each fragment. The code never
  performs step 2: `chunk` calls `_iter_statement_spans` (tokenizer-derived spans) and then
  `_parse_statement` (`parse_one`) per span — i.e. the documented "last-ditch" is the **primary**
  path. **[source-verified]** This is the repo's *served-English-has-no-gate* class (§"A DIAGNOSIS IS
  NOT AN INSTRUMENT"): prose that no gate checks against behaviour.
- **S3 — the `astroid>=4.1.2` lower bound is open and the code depends on astroid internals.**
  See finding #9. An `astroid` 4.2 could silently reshape `_mod_file_cache` with no test failing.
- **S4 — the token-cap invariant has no cross-chunker pin.** Five per-chunker assertions, no shared
  one; a sixth chunker inherits no guard. See finding #3. Raised separately because it is true
  **today**, whether or not finding #3 is actioned.

---

## What I did NOT verify

Stated explicitly so nothing here reads as broader than it is:

- I did **not** run the `lorescribe` test suite. My brief was a read-only scout and brief-base §3
  forbids unrequested suite runs. Every RED/GREEN claim above is about a probe I ran and pasted, not
  about the suite.
- I did **not** measure reindex cost for D3, or embedding-quality impact of changed chunk
  boundaries. Both are real and neither is estimable from source.
- The subadditivity measurement (finding #3) is **4/4000 on one file with one seed (11)** against the
  voyage-4 tokenizer. It proves violations *exist*; it does not establish a rate for the whole corpus.
- I did **not** benchmark tree-sitter or markdown-it-py throughput against the current regex scanners.
  For a full-corpus indexing sweep that could matter; I have no number for it.

---

*Measured 2026-07-25 against worktree `/home/ejprice/PycharmProjects/lore-pkt11i`, branch
`pkt11i-floor-calibration-dark`, at commit `6654be0`. Library versions are named at each
`[library-verified]` claim. All probes asserted `lorescribe.__file__` resolved inside that worktree
before running.*

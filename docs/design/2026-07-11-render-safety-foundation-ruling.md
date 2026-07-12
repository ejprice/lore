# PKT-28 Phase 0 — Render-Safety Foundation ruling

CHANGELOG: **v2 amended 2026-07-11** — cold audit (REPORT-phase0-audit-1.md) REFUTED the
LiteralString-enforcement leg: mypy 2.1.0 erases `typing.LiteralString` to a bare `str`
alias (PEP 675 checking is pyright-only), so §ENFORCEMENT row 3 fired at NO gate
(working exploit: scratchpad/audit1/row3_exploit.py). v2 re-bases the template-slot
guarantee on an AST template-literal pin + runtime no-newline asserts (both adopted),
hardens the mint-pin, and adds a subprocess-mypy meta-test so the mypy layer is never
unverified again. Section names unchanged — C1 briefs reference them.
CHANGELOG: **v3 micro-amendment 2026-07-11** — re-verify GO residuals (audit §RESIDUALS):
R2 runtime guards widened from bare `\n` to the full CONTROL_CHAR_PATTERN class
(U+2028/U+2029/CR/NEL fracture lines too, per sanitise.py's own threat model); R1
template pin gains the ImportFrom-asname check for the verb names (reassigned-name
shape stays documented-uncaught at the pin, killed at runtime by R2).

Author: design-consultant-pkt28 (Fable) · 2026-07-11 · status: FINAL (v2, post-audit)
Inputs: finding #90 (get) · loremaster/loremaster/sanitise.py · tests/test_mcp_server.py
TestRenderInjectionRegistry (loremaster/tests/test_mcp_server.py:7629-7763) ·
docs/plans/v2/PKT-28-agent-comms.md · ~/.claude/plans/one-of-claude-codes-nifty-garden.md
§Tool surface · DESIGN-LAW §1 · server.py:2865/3058/3458 (the three raw helpers, read live)
Environment facts (CORRECTED v2): requires-python ">=3.14", mypy>=1.17 `strict = true` +
pydantic plugin, per-member typecheck.sh. `typing.LiteralString` is AVAILABLE but **NOT
ENFORCED**: mypy 2.1.0 parses the annotation and then erases it to plain `str`
(`Revealed type is "str"` — audit §PROBE-A, ls_matrix.py); PEP 675 enforcement has never
shipped in mypy, only pyright. The annotation MAY stay as documentation/future-proofing,
but what actually enforces the template slot is the AST template-literal pin + the
runtime no-newline assert (§ENFORCEMENT row 3, v2). v1's "strict-mode enforced" claim
was wrong — my verification checked availability (python/mypy versions), never
enforcement; the audit's subprocess probe is the instrument that was missing.

---

## §RULING

**Hybrid: option (b) as the chassis, option (c)'s *scoped* variants as its bypass pins —
built so option (a)'s end-state is an incremental PKT-03 adoption of the same seam, not a
Phase-0 rewrite.**

Phase 0 builds a typed render-assembly seam (`SafeLine` + `Rendered` + a three-verb
assembly vocabulary in a new `loremaster/render.py`) that ALL new comms renders (C1–C5)
are authored on, plus two zero-semantics AST pins that close the bypass routes the type
system cannot see. Existing task/finding renders are NOT retyped now — but the three
helpers finding #90 names as live-forgeable TODAY get the C0-idiom manual
`sanitise_line` wraps + RenderCases pulled forward into Phase 0 (small, mechanical,
live defect). The crux — `class SafeString(str)` enforces nothing against f-string
coercion — is resolved not by the value type alone but by the **return type**: comms
render paths are typed `-> Rendered`, and the only mint of `Rendered` is the assembly
vocabulary, whose inputs are typed `SafeLine | int`. A raw f-string is a plain `str`;
mypy `strict` rejects it at the return and value boundaries. The TEMPLATE slot is the
one leg mypy cannot guard (v2 — LiteralString is unenforced, audit §PROBE-A): it is
guarded by an AST template-literal pin plus render_line/render_join runtime no-newline
asserts, which together are *stronger* than PEP 675 would have been (syntactic — no
aliasing/inference gaps, and the runtime leg caps blast even past the pin). Option
(c) as the *sole* instrument is **not viable** as a guard (see per-option analysis:
aliasing false-negatives make it a heuristic detector — silent-pass on the miss is
DESIGN-LAW §1.4's cardinal failure class); option (a) *now* is rejected on scope (the
legacy retype drags in the eval-pinned search render surface and blocks C1).

---

## Per-option analysis (the brief's 5 required axes each)

### Option (a) — FULL SafeString typed-render seam, existing renders retyped now

1. **Enforcement vs f-string coercion:** identical mechanism to the hybrid below —
   the value type alone is unenforceable (f-strings coerce anything via
   format()/str(); `f"{raw}"` is never a mypy error), so (a) only works *with* the
   return-type seam + the template-literal/mint AST pins + runtime asserts. Gate:
   mypy primary for values/returns; pytest for the template slot (v2).
2. **Now vs PKT-03:** everything now — seam + comms + retype of rollup/batch/
   task_rows/finding_rows/claim/finding_detail/diff.py *and* transitively the
   search.py render pipeline (it shares the sanitiser idiom). Nothing left for PKT-03
   but D1.4.
3. **C1–C5 ergonomics:** same as hybrid (good) — but C1 waits behind the retype.
4. **Registry fate:** could shrink to a smoke battery once everything is typed.
5. **Gate integration:** typecheck.sh unchanged; BUT the search.py/rollup retype is
   render-shape-risk on an eval-pinned surface — DESIGN-LAW §6 pins smoke_p8b as
   render-shape-coupled and the 35-pair standing bar was graded on current renders;
   any byte drift needs re-verification.
   **Verdict: REJECTED as Phase 0.** Multi-session scope for a phase sized one
   contract/builder pair; inverts the operator's resequence (comms ahead of PKT-01);
   the same seam reaches (a)'s end-state incrementally through PKT-03 with zero rework.

### Option (b) — SafeString + typed helpers for NEW comms renders only

1. **Enforcement vs f-string coercion:** as stated in §ENFORCEMENT — return-type seam
   (mypy), `**values: SafeLine | int` (mypy), template-literal AST pin + runtime
   no-newline assert on the template slot (pytest — v2: mypy does not enforce
   LiteralString), runtime type-assert in the mint (pytest), AST mint-pin (pytest).
   Naked (b) — "SafeString +
   helpers" without the return-type seam and pins — would NOT be mechanical (a builder
   could return a raw f-string beside the helpers); the return-type seam is what makes
   it viable. This ruling's (b) includes it.
2. **Now vs PKT-03:** seam + pins + registry generalization + 3 live-forgeable wraps
   now; legacy retype, diff.py import migration, tree-wide sweep, D1.4 stay PKT-03.
3. **C1–C5 ergonomics:** good — see §C1-C5-AUTHORING. Template-call style reads well
   for row-shaped renders; fenced/compose/join cover the fleet/drain/story composites.
4. **Registry fate:** survives as the observable-behavior battery; scaffolding shared;
   comms side gains an auto-enumerated completeness pin (see §REGISTRY-MIGRATION).
5. **Gate integration:** new module rides the existing per-member mypy strict run;
   no config change; ruff untouched; pins are ordinary pytest.
   **Verdict: CHOSEN (with (c)'s scoped pins).**

### Option (c) — AST render-hygiene scan as the enforcement instrument, no retyping

1. **Enforcement vs f-string coercion:** a pytest-time scanner walking designated
   render code, flagging any JoinedStr FormattedValue / .format / %-format whose
   operand is an agent-controlled field not wrapped in `sanitise_line(...)`. "Agent-
   controlled" is a *semantic* property — the scanner needs a hand-maintained
   deny-list of (model, field) names (subject, body, owner, actor, created_by, note,
   …) and matches `X.field` attribute nodes. It mechanically catches the direct
   idiom (`f"{task.owner}"`) — gate: pytest — but is **structurally blind to
   aliasing** (`owner = task.owner` … `f"{owner}"`), helper indirection, `str()` /
   `.join()` wrappers, and dict access. Those are silent passes, and a hygiene
   instrument that silently passes the miss is worse than none (confident-wrong,
   DESIGN-LAW §1.3/§1.4). Hardening it to type-aware data-flow is a real
   static-analysis project (and mypy's plugin API exposes no JoinedStr hook, so a
   mypy plugin is not an available shortcut — verified against mypy plugin hook
   surface: function/method/attribute hooks only).
2. **Now vs PKT-03:** scan now, nothing else; the tree-wide sweep IS the scan.
3. **C1–C5 ergonomics:** zero help — builders still hand-wrap every field and get
   feedback only at test time, per-site, with false-positive noise to manage.
4. **Registry fate:** unchanged and still load-bearing (the scan proves nothing
   about output behavior).
5. **Gate integration:** pytest only; mypy contributes nothing.
   **Verdict: NOT VIABLE as the sole guard** — it cannot mechanically catch the
   aliased interpolation, and the brief's bar is explicit that such an option is out.
   Its two *scoped, zero-semantics* variants ARE adopted as pins (mint-pin now;
   tree-wide heuristic sweep as a PKT-03 *detector* for the legacy surface — where
   it audits existing code rather than guarding new construction, false-negatives
   degrade to "sweep coverage" not "guarantee", which is honest).

### Candidate mechanisms evaluated and where they landed
- **NewType("SafeLine", str)** — mypy-equivalent to the subclass but erases the
  runtime distinction → loses the Any-leak backstop and makes the mint-pin weaker
  (a NewType call is a bare identity function). REJECTED in favor of `class
  SafeLine(str)`.
- **Runtime type-assert at the single final render-emit boundary** — impossible
  *post*-interpolation: once any value is interpolated, the composite is a plain
  `str` and carries no provenance. The assert MUST sit at the pre-interpolation
  mint (inside `render_line`, per-value). ADOPTED there; the "final boundary" is
  instead enforced by the `Rendered` return **type**, which needs no runtime check.
- **Module-wide f-string ban in render modules (AST)** — enforceable and simple,
  but conflicts with house style (f-strings always — exceptions/log messages inside
  those modules would be collateral). v1 called it redundant "because an internal
  f-string cannot become `Rendered`" — the audit's row3_exploit refuted that (an
  f-string in the TEMPLATE slot mints a genuine Rendered). v2's adopted
  template-literal pin IS precisely a targeted f-string ban on that one slot, which
  keeps the module-wide ban unnecessary. Module-wide ban stays REJECTED.
- **mypy plugin hooking f-string operand types** — no JoinedStr hook in the plugin
  API. NOT AVAILABLE.

---

## §ENFORCEMENT — how a raw interpolation fails, mechanically

The chain of custody: **a value can only reach a served comms render through the
assembly vocabulary, and the vocabulary only accepts proven-safe types.**

New seam (Phase 0):
- `loremaster/sanitise.py`: `class SafeLine(str)` — the ONLY sanctioned mints are
  `sanitise_line(text: str) -> SafeLine` (retyped return; covariant, so all existing
  callers type-check unchanged) and `render_join` below.
- `loremaster/render.py` (new):
  - `class Rendered(str)` — the served-render type; minted ONLY here.
  - `render_line(template: LiteralString, /, **values: SafeLine | int) -> Rendered`
    — named-placeholder `.format(**values)`; runtime-asserts every value is
    `isinstance(v, (SafeLine, int))` and that value keys exactly cover the template
    (typo guard); raises `RenderSafetyError` naming the offending key. **v2/v3:** ALSO
    raises `RenderSafetyError` if any CONTROL_CHAR_PATTERN-class character (`\n`, CR,
    NEL, U+2028/U+2029 — the full sanitise.py hostile class, v3/R2) appears in the
    template OR in any value — render_line is structurally single-line;
    `render_compose` is the only sanctioned newline-joiner. (The `LiteralString` annotation is retained as documentation
    only — mypy does not enforce it; docstrings must name the AST pin + runtime
    assert as the real instruments.)
  - `render_fenced(body: str) -> Rendered` — RAW str by design: bodies stay verbatim
    inside a backtick fence sized `max(MIN_FENCE_WIDTH, max_backtick_run(body)+1)`
    (the _render_finding_detail idiom, server.py:2911).
  - `render_compose(*parts: Rendered) -> Rendered` — newline-joins parts.
  - `render_join(separator: LiteralString, parts: Iterable[SafeLine]) -> SafeLine` —
    kills the `", ".join(...)` demotion pothole (join returns plain str). **v2
    RULING on semantics:** a newline separator is NEVER legal — render_join
    runtime-rejects (`RenderSafetyError`) a separator or any part containing any
    CONTROL_CHAR_PATTERN-class character (v3/R2 — not just `"\n"`),
    so `SafeLine`'s one-line invariant is held BY CONSTRUCTION at every mint
    (sanitise_line collapses newlines; render_join now rejects them). A literal
    `"\n"` would pass the AST template-literal pin (it IS a Constant str), which is
    exactly why the runtime rejection is the instrument here. Multi-line structure
    belongs to `render_compose(Rendered)` alone.
- Comms render paths — `AppContext.comms()` and every `_render_comms_*` helper — are
  typed `-> Rendered`.

Failure matrix (every smuggling path → which gate fires):

| # | Smuggling attempt | Caught by | Gate |
|---|---|---|---|
| 1 | `render_line(..., owner=task.owner)` (raw str value) | arg type `SafeLine \| int` | **mypy** (typecheck.sh) |
| 2 | `return f"- {task.owner}"` from a comms render path | return type `Rendered` — an f-string is `str` | **mypy** |
| 3 | `render_line(f"row {raw}", ...)` — agent text in the TEMPLATE slot (v2: the audit's row3_exploit; mypy is SILENT here, LiteralString unenforced) | (i) AST template-literal pin: `args[0]` of every `render_line`/`render_join` call in the prod package must be an `ast.Constant` str — JoinedStr/Name/BinOp/Call/Attribute in that slot all offend; zero false-positive cost (no legitimate non-literal template exists) and no aliasing gap (it inspects the argument NODE, not a type; v3/R1: plus the same ImportFrom-asname check as the mint-pin for the verb names — `render_line as rl` can't dodge it; the reassigned-name shape `rl = render_line` stays documented-uncaught at the pin and is killed at runtime by (ii)); (ii) render_line's runtime guard over template AND values rejects the full CONTROL_CHAR_PATTERN class (v3/R2 — not just `\n`: U+2028/U+2029/CR/NEL are line-fracturing per sanitise.py's own threat model), capping the blast even if the pin were ever bypassed — a forged row requires a line break, and every line-breaking codepoint in the threat model is rejected | **pytest** (both) |
| 4 | `", ".join(safe_parts)` passed as a value | join returns `str`, not SafeLine (fail-closed demotion) → use `render_join` | **mypy** |
| 5 | value arrives as `Any` (decoder leak — mypy is silent on Any) | per-value `isinstance` assert inside `render_line` → `RenderSafetyError` | **pytest** (every render is test-exercised; in prod it fails LOUD, never silent-forges — §14 posture) |
| 6 | `SafeLine(raw)` / `Rendered(raw)` / `cast(SafeLine, raw)` minted outside sanitise.py/render.py | AST mint-pin over the loremaster prod package (tests exempt). **v2 hardening (all three adopted from audit §PROBE-C):** also flag (i) string-form `cast("SafeLine", x)` — any `cast` whose first arg is a Constant str naming a seam type (the likeliest bypass: normal idiom under `from __future__ import annotations`); (ii) import-as-alias of SafeLine/Rendered outside the seam (`ImportFrom` with asname on seam names — no legitimate use); (iii) subclassing SafeLine/Rendered outside the seam (`ClassDef` bases scan — closes subclass-mint). All three are zero-false-positive syntactic checks in the same pin module | **pytest** |
| 7 | hostile value that IS laundered but row-shaped on one line | cannot add a line (no newline survives sanitise_line); renders inline inside its own row — the existing threat model is line-integrity, not content censorship | **pytest** (registry battery asserts: no added lines, no surviving Cc/Cf/Zl/Zp, no forged row line) |
| 8 | `render_join("\n", parts)` or a line-fracturing part → multi-line SafeLine that would sail through render_line's isinstance check (v2, audit finding) | render_join's runtime rejection of the full CONTROL_CHAR_PATTERN class in separator AND parts (v3/R2 — `\n`, CR, NEL, U+2028/U+2029 all fracture lines) + render_line's same char-class guard over values — the one-line invariant is enforced at both mints and at the consumption boundary | **pytest** |

Honesty note (REWRITTEN v2 — v1's version was refuted): mypy guards ONLY the value
and return legs (rows 1/2/4, verified by subprocess probe with exact error codes);
the TEMPLATE leg is pytest-guarded (rows 3/8) because mypy does not enforce
LiteralString — v1 claimed otherwise as a verified fact and the cold audit disproved
it with a working exploit that was green at mypy, the runtime assert, the mint-pin,
and ruff simultaneously. `# type: ignore`, an `Any`-typed seam, or an exotic mint
evasion (getattr/importlib) can still defeat individual layers; absolute proof is
not claimed. The v2/v3 property actually delivered: **render_line and render_join are
structurally incapable of emitting any line-breaking or control character (the full
CONTROL_CHAR_PATTERN class) at runtime**, so every newline in a
served comms render is either render_compose structure or fenced body — a row
forgery (which requires a line break) must defeat the runtime asserts themselves, not
merely one static layer. And the subprocess-mypy meta-test (§BUILD-NOW item 9) pins
what mypy actually does and doesn't enforce, so no future enforcement claim on this
seam can ship unverified again.

---

## §BUILD-NOW — Phase-0 work list (sized for ONE tdd-contract/builder pair)

1. **sanitise.py**: add `class SafeLine(str)`; retype `sanitise_line -> SafeLine`;
   optional 2-line convenience `safe_str(value: object) -> SafeLine`
   (= `sanitise_line(str(value))` — the existing `str(ref)`/`str(owner)` idiom,
   server.py:2766/3259).
2. **loremaster/render.py** (new, ~120 lines): `Rendered`, `RenderSafetyError`,
   `render_line`, `render_fenced`, `render_compose`, `render_join` as specced above.
   **v2/v3:** render_line runtime-rejects any CONTROL_CHAR_PATTERN-class character
   in the template or any value; render_join likewise in the separator or any part
   (R2 — the full sanitise.py hostile class, not just `"\n"`). Docstrings carry
   the enforcement story and must name the AST pins + runtime asserts as the
   template-slot instruments, NEVER mypy/LiteralString (the audit's probe-F table
   lists five shipped docstrings teaching the false claim — correct all five, plus
   the three-vs-four verb-count self-contradiction at render.py:14/59).
3. **loremaster/tests/test_render.py** (contract-first): hostile fixtures per
   brief-base §3 (newline + row-forge payload + backtick runs) through
   sanitise_line→render_line → single-line assertions; fence-sizing vs embedded
   fence-shaped lines; runtime assert fires on raw-str-as-Any and names the key;
   missing/extra template keys loud; compose/join behavior; `Rendered`/`SafeLine`
   are str (wire compatibility).
4. **loremaster/tests/render_injection_scaffold.py** (shared helper module, not
   test_-prefixed): extract `_INJECTION_THREAT_CHARS`, `_ROW_FORGE_PAYLOAD`,
   `RenderCase`, and the three meta-assertions (as
   `assert_render_injection_safe(...)`) from test_mcp_server.py; test_mcp_server.py
   imports them back (its RenderCases stay where they are).
5. **loremaster/tests/test_render_seam_pins.py**: the AST mint-pin (row 6 above,
   WITH the v2 hardening: string-form cast / import-as-alias / subclass-mint) +
   **the AST template-literal pin (row 3, v2 — the row-3 instrument):** every
   `render_line`/`render_join` call in the prod package has an `ast.Constant` str
   as `args[0]`; pin self-tests use synthetic offender trees (f-string template,
   Name template, concatenation) so the scanner can never vacuously pass + a
   reusable `assert_actions_covered(actions, cases, exemptions)` completeness
   helper for C1's dispatch-table pin (see §REGISTRY-MIGRATION).
6. **Pull-forward wraps (the live-forgeable trio, finding #90's list)**:
   `_render_finding_rows` (subject/kind/area/category/created_by — server.py:2874-77),
   `_render_task_rows` (subject/owner/blocked_by — :3472-75),
   `_render_claim_result` (owner, both branches — :3073/3078) — C0-idiom manual
   `sanitise_line`/`safe_str` wraps, NOT retyped to render.py; plus one RenderCase
   per wrapped field via the shared scaffold and the family names added to
   `_EXPECTED_INJECTION_REGISTERED_RENDERS`. Rationale: forgeable on master today;
   these rows co-render with comms output in rollup, so comms forgery-safety is
   defeated end-to-end while they stay raw; and they dogfood deliverable 4.
7. **Completeness-pin docstring correction** (finding #90's explicit ask): the pin
   catches a REMOVED RenderCase, it cannot auto-detect a NEW unregistered render —
   fix the "Fails loudly" overstatement (test_mcp_server.py:7757-7761).
8. Gates: typecheck.sh (new modules ride the loremaster member, strict), ruff clean,
   scoped pytest with passed-COUNT tails. No config changes anywhere.
9. **Subprocess-mypy meta-test (v2, audit remediation 4 — the process fix):** a test
   that shells out to `uv run mypy` against COMMITTED fixture files and asserts the
   failure matrix's mypy rows fire with their exact error codes — row 1 `[arg-type]`,
   row 2 `[return-value]`, row 4 `[arg-type]` — AND asserts row 3 is mypy-SILENT
   (pinning reality: if a future mypy ships PEP 675 the row-3 fixture flips loudly
   and tells us the documentation can upgrade). The audit's probe files
   (scratchpad/audit1/row0–row4) are ready-made fixtures — commit them under the
   loremaster test tree. Also correct test_render.py:16's false claim that "this
   module cannot drive a real mypy failure from inside pytest" — it can, via
   subprocess, and that claim is exactly why the broken layer shipped unverified.

Optional (contract pair's call, drop without regret): xfail-strict rows in
`_INJECTION_THREAT_CHARS` for the known D1.4 survivors (U+061C ALM, U+00AD soft
hyphen, one tag char) — they document the gap and flip green when D1.4 lands.

## §DEFERRED — stays PKT-03

- Tree-wide RETYPE of legacy renderers (rollup, batch, task/finding rows, claim,
  finding_detail, diff.py, and — pending its own operator ruling given eval coupling —
  the search.py render pipeline) onto the render.py vocabulary.
- diff.py import migration (`loremaster.search._sanitise_line` → `loremaster.sanitise`)
  and eventual retirement of search.py's back-compat re-exports.
- The tree-wide heuristic AST render-hygiene SWEEP (deny-list attribute scanner) as a
  *detection instrument* over the legacy surface — closes #90's 2b gap heuristically
  where the typed seam hasn't reached; the comms surface needs no heuristic (closed by
  construction + dispatch-table pin).
- D1.4 (below).

**Draft update text for finding #90** (lead files it; supersede or note per house
preference):

> PHASE-0 PULL-FORWARD (PKT-28 render-safety foundation, ruled 2026-07-11, amended v2
> post-audit): Phase 0 ships the guard-by-construction seam — SafeLine (sanitise.py;
> sanitise_line now returns it), loremaster/render.py (Rendered + render_line/
> render_fenced/render_compose/render_join; SafeLine|int values [mypy]; runtime
> type-assert + no-newline asserts on template/values/separator/parts), the AST
> template-literal pin + hardened mint-pin (string-form cast, import-alias,
> subclass-mint), the subprocess-mypy meta-test (mypy enforces values/returns ONLY —
> LiteralString is unenforced by mypy, per the Phase-0 cold audit), the shared
> injection-scaffold module, the corrected
> completeness-pin docstring (2b), AND the three live-forgeable wraps
> (_render_finding_rows/_render_task_rows/_render_claim_result) with RenderCases.
> REMAINING FOR PKT-03: diff.py import migration + search.py re-export retirement;
> retype of legacy renderers onto render.py (search.py pipeline requires an eval-
> coupling ruling first, DESIGN-LAW §6); the tree-wide heuristic render-hygiene AST
> sweep as a legacy-surface detector (2b on the comms surface is closed by
> construction + the C1 dispatch-table completeness pin); D1.4 unicodedata category
> engine under a superset-equivalence oracle (the injection meta-test's category-
> based assertions are already the acceptance instrument).

## §C1-C5-AUTHORING — the pattern comms builders follow

Rules (go in the C1 builder brief, ~6 lines):
1. Every comms render path is typed `-> Rendered`; assemble ONLY via render.py verbs.
   Templates and join-separators are INLINE STRING LITERALS — never a variable,
   f-string, or concatenation (the template-literal pin fires; mypy does NOT check
   this slot — v2). One logical line per render_line; newlines only via
   render_compose (render_line/render_join reject `"\n"` at runtime).
2. Agent free text crosses in as `sanitise_line(x)` / `safe_str(x)` at the callsite —
   uniformly, including charset-ASSERTed names (the type demands it; a no-op wrap on
   clean ASCII is cheaper than an exemption story).
3. Multi-line bodies (brief bodies at register/brief_get, message bodies in story
   detail) go through `render_fenced` ONLY — verbatim inside the fence, never
   sanitise_line'd (bodies must round-trip verbatim; sanitisation is render-time
   line policy, never storage mutation — domain models keep RAW str fields).
4. Counts/seqs/elision numbers are `int`s straight into `render_line` (DESIGN-LAW
   §1.2 counted elision: `render_line("+{more} more unread — re-drain or raise
   limit", more=elided)`).
5. Each new action registers one RenderCase per agent-free-text param in the comms
   battery; the dispatch-table pin fails until it's registered or exempted-with-reason.
6. Never construct SafeLine/Rendered directly (mint-pin fires).

Worked shape (drain, the render-heaviest C2 composite):

```python
lines: list[Rendered] = [render_line("unread for {agent}:", agent=safe_str(agent))]
for edge in shown:
    lines.append(render_line(
        "#{seq} [{grade}] {sender}→you ({task}): {body}",
        seq=edge.seq, grade=sanitise_line(edge.grade),
        sender=sanitise_line(edge.sender), task=safe_str(edge.task_id),
        body=sanitise_line(edge.body),
    ))
if elided:
    lines.append(render_line("+{n} more unread — re-drain or raise limit", n=elided))
if ack_required:
    lines.append(render_line("ACK REQUIRED: {seqs}",
                             seqs=render_join(" ", [safe_str(s) for s in ack_required])))
return render_compose(*lines)
```

A considered-and-rejected ergonomic variant: sanitise at the pydantic view-model
boundary (fields typed SafeLine with validators). Rejected for Phase 0 — it couples
storage models to render policy and corrupts verbatim body round-trips; render-time
wrapping keeps one policy. Builders MAY hoist per-row unpack helpers returning
SafeLine-typed tuples when a render touches many fields (pure ergonomics; the seam
is unchanged).

## §REGISTRY-MIGRATION — fate of TestRenderInjectionRegistry

**It survives, generalized — the seam does not replace it.** The typed seam proves
construction; the registry proves *observable output behavior* end-to-end (its three
assertions are the acceptance oracle, and they are what a regression in sanitise.py
itself would trip). Migration:
- Scaffolding (threat chars, forge payload, RenderCase, assertions) moves to the
  shared `render_injection_scaffold.py`; test_mcp_server.py imports it; its existing
  RenderCases + the hand-maintained `_EXPECTED_INJECTION_REGISTERED_RENDERS` pin stay
  for the LEGACY surface (docstring corrected, Phase 0 item 7).
- The comms test module (C1) instantiates its OWN battery from the scaffold with an
  **auto-enumerated completeness pin**: C1 must expose the action dispatch as an
  introspectable table (`_COMMS_ACTIONS: dict[str, handler]` — a design prescription
  this ruling adds to C1); the pin iterates the table and fails for any action
  lacking a RenderCase or an explicit exemption-with-reason. Default = fail. That
  inverts the 2b gap on the comms surface: new action → red until covered; only
  exemptions are hand-maintained, and each is visible and reviewable.

## §D1.4 — recommendation (one paragraph)

**Stays PKT-03.** It is a tree-wide behavior change on the SHARED seam — every legacy
render's bytes shift — which breaks the byte-exact oracle and requires its own
superset-equivalence contract, and smoke_p8b is render-shape-coupled (DESIGN-LAW §6)
so it must move in step; the residual survivors (ALM U+061C, soft hyphen U+00AD, tag
chars) are real but exotic, with no live exploit path on the served surface today;
and Phase 0 is sized one contract/builder pair whose mission is the seam. Two facts
make the deferral cheap and honest: the injection meta-test's assertions are ALREADY
unicodedata-category-based (test_mcp_server.py:7747-7750), so the D1.4 acceptance
instrument exists; and the optional xfail survivor rows (§BUILD-NOW) turn the known
gap into a visible pin that flips green when D1.4 lands. Nothing in comms C1–C5
depends on D1.4 — SafeLine's contract is "whatever sanitise_line guarantees", so the
engine can strengthen underneath without touching the seam or the comms renders.

## §OPERATOR-BRIEFING (plain language)

We're about to build agent-to-agent messaging into lore. Everything one agent types
(message bodies, briefing docs, notes) gets rendered into ANOTHER agent's context —
so a malicious or buggy value must never be able to forge fake output lines (e.g. a
fake "task done" row). Today's defense: every render site must remember to wrap each
field in a cleaning function, and a hand-kept test list checks the sites we know
about. Forgetting a wrap on a new render is silent — that's the hole.

Three options were on the table:
- (a) Full retrofit: introduce a "proven-clean string" type everywhere, including all
  existing renders, now.
- (b) Middle path: the clean-string type + typed assembly helpers for NEW comms
  renders only; existing renders keep manual wraps until the later cleanup packet
  (PKT-03).
- (c) A test-time code scanner that tries to spot renders using unwrapped fields; no
  type changes.

My pick: **(b), plus (c)'s simple pins** — because of a subtlety: a "clean string"
type alone enforces nothing (Python f-strings happily absorb any value). The teeth
come from making comms renders return a special `Rendered` type that ONLY our
assembly helpers can produce, and those helpers only accept proven-clean values —
so a forgotten wrap on a value becomes a type-checker ERROR at commit time, not a
silent hole. One slot the type-checker cannot guard (the message template itself — a
real Python type-checker limitation our cold audit proved with a working exploit) is
guarded instead by small test-time pins plus runtime checks that make the helpers
physically unable to emit a forged extra line; a meta-test now verifies exactly what
the type-checker does and doesn't enforce, so we never over-trust it again. The full
scanner-only option (c) can be fooled by simple variable aliasing, so it's demoted
to a later audit tool for old code, not the guard for new code.

Cost now: one test-writer/builder pair builds two small modules + pins, and we also
fix three existing renders that are forgeable today (part of the PKT-03 cleanup
pulled forward). Saved across C1–C5: every new comms render (fleet views, message
drains, story timelines) is safe by construction — no per-render security fixture
authoring, no forgotten-wrap class of bug, and the reviewer burden drops to "does it
type-check".

---
*Consultant remains available via SendMessage for follow-ups.*

# Packet 63c — ruling amendment 6 (sidecar-63c-2, 2026-09-24): adversary-r3 MP-1…MP-5, fork R-3, and the STOP-rule

Rules `REPORT-adversary-63c-i-a-r3.md` (verdict INSUFFICIENT; graded `39935f6`; committed `c22419d`) — the
five new survivors' classification, fork R-3, and the lead's STOP-rule question. Directive: lore_comms
#16005 on thread `63c`, **which I could not drain**: the lore server answers (`POST /mcp` → HTTP 200,
probed) but this session's MCP client is stuck at `ECONNREFUSED` since outage #2 and will not reconnect
without a session restart. The lead-log entry at `c22419d` states the full ask and is the durable copy I
worked from; this committed doc is the receipt. Pass run on `Read`/`sed`/`awk`, said so. HEAD at ruling:
`c22419d`. Vocabulary as amendment-4 (GATING / NON-GATING / PROSE / KNOWN BOUND).

## The STOP-rule question first, because it decides the shape of everything below
- **The numbers converge** (survivors 11 → 7 → 5, every prior survivor killed on its declared pin, SAT
  reproduced independently at 11405/0, zero HEAD-greens turned red). That is a contract improving, not a
  spiral. **But the lead read the tell correctly:** MP-1 is N1c's class — a private literal deciding
  identity legality — relocated one call site up, from the decision HOME to the SKIP gate that calls it.
  The instruments so far are a hand-list of consumer ENTRY POINTS (mutation) and an allowlist keyed on the
  pattern ATTRIBUTE (static); both are blind to a regex literal that never names the pattern, wherever it
  sits. Adding the traffic line to the hand-list is the fourth relocation of the same hidden constant.
- **Ruling: the class gets a DESIGN closure in r4, with its threat model written into the instrument, and
  r4 is the LAST pre-build contract round for 63c-i-a.**
  1. **Threat model (stated in the pin, per "A GATE NEEDS A THREAT MODEL"):** the gate catches the HONEST
     ENGINEER who pastes the charset regex into a new call site (N1c and X1 are exactly that — the same
     text with one extra `.`). It is NOT a boundary against an author who rewords the class (`[0-9a-z]`)
     to evade it; anyone who can commit here can already ship anything. Verdicts follow mechanically: a
     pasted twin caught is the gate working; a reworded evasion surviving is not a defect of the gate.
  2. **The static ∀ (allowlist the safe, keyed on the TEXT, not on names or sites):** over every
     production member (`parse_production_trees` + `assert_scan_reached_every_member` — the reach
     instrument r3 already uses), the charset text `[a-z0-9][a-z0-9_` occurs in exactly ONE string
     constant in the workspace: `lorerunes`' `AGENT_NAME_PATTERN`. Every other `re.compile` / `re.fullmatch`
     / `re.match` / `re.search` / raw literal carrying it is a private decision → RED naming `file:line`.
     Positive controls: a synthetic module with the pasted twin (N1c/X1 text) reds; the drifted-dot twin
     reds; a `.pattern` read stays green (it is the prose shape the attribute allowlist already blesses).
  3. **The effect leg for the SKIP gate (MP-1 proper, KP-X1's shape):** BASELINE — a legal attribution is
     looked up once (a spy registry counting `get_agent`); under the shared-decision mutation it is looked
     up ZERO times. Plus the corpus leg: ∀ `_HOSTILE_IDENTIFIERS`, `_comms_traffic_line` performs zero
     lookups (R8's read budget, pinned as an effect over the shared corpus rather than over one value).
  4. **The entry-point hand-list stays, its reach stated:** `_IDENTIFIER_DECISION_CONSUMERS` is the
     effect twin of the static pin; its docstring says it is a list and that the text pin is the ∀.
  5. **After r4:** any further private-decision door the r4 adversary constructs is a **pinned KNOWN
     BOUND** carrying the threat model above as its rationale — never an r5. A survivor in a NEW class is
     ruled by the sidecar before any round is briefed, default pin-the-miss unless it is a live production
     defect. 63c sits on the critical path (63c → 64 → 65); maximal rigor on a fourth relocation of one
     literal is the same error as under-verifying, in the other direction.
- **Swept up while measuring (awk over the four members):** `surreal_schema._IDENTIFIER_CHARSET_PATTERN`
  is a raw-string TWIN of the pattern text at HEAD (it feeds the `brief.name` ASSERT that ii drops and the
  `agent` ASSERTs that i-a drops). Under the text pin it is RED at HEAD, correctly: A4's "ONE spelling" is
  not met while production carries the text twice. **Builder item (i-a, one line):**
  `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` imported from `lorerunes` (stdlib-only, no
  cycle) — `brief`'s ASSERT stays byte-identical until ii. Goes in the builder brief beside the two prose
  lines the r2 adversary named.

## MP-1 — GATING
As ruled above: text-twin static pin + SKIP-gate effect leg (mutation + corpus). The production shape is
unchanged from A4-bis (the gate reads the home; the home calls `is_legal_identifier`); what changes is that
"NOT rewired" now has a pin on both sides — static for the text, effect for the gate.

## MP-2 — GATING; fork R-3: the VALUE is NOT normative, no ceiling pin
- **Pin:** R-Q5-1 gains the mutation leg exactly as KP-X2 — `monkeypatch.setattr(principals,
  "_REFUSAL_ID_SAMPLE_SIZE", 3)`, seed 3 + 15 traps, the reason names the full count (18) and EXACTLY 3
  ids. This is "prove sharing by MUTATION" applied to a constant: a restated `[:10]` that agrees at birth
  is invisible to a read and visible to a perturbation. The builder writes exactly one line reading the
  constant.
- **R-3:** reading (a) — `10` in amendment-4 was the reference build's choice written as an example, not a
  ruling; the ruling was "a NAMED constant, no literal". Pins: the constant is a positive `int`, it is
  READ (MP-2), the reason names the FULL count on a separate line so the reader loses nothing at any
  bound. **No upper "sanity ceiling" pin:** a `≤ 20` in a test is a second magic number restating a design
  choice in the wrong home; if a ceiling is wanted it is a constant beside the sample size in
  `principals.py` with a docstring, and nothing in this packet needs it (the refusal is a one-shot
  operator-facing migrate message, not a hot served surface). The constant's docstring states WHY its
  value (a screenful; the count is served beside it).

## MP-3 — GATING; the spelling pin is REPLACED by the effect pin
- **Ruling:** the FORK-C rider-2 pin becomes KP-X3's shape — once `lorerunes.is_legal_identifier` exists,
  `monkeypatch.delattr(lorerunes, "is_legal_identifier")` and a hostile fake register (`"fixer-b\n"`) must
  NOT succeed (any exception; `fake.db.agents` stays empty). It subsumes X3b (the ruled spelling kept),
  X3 (`except Exception:`), a bare `except:`, `builtins.ImportError`, and the `getattr(…, None)` read —
  every silent-skip shape at once, because it observes the property ("the guard must not outlive its
  premise") rather than one spelling of one guard. The source-text pin is DELETED, not kept beside it (two
  pins for one property, one of them a proxy, is decoration that reads as coverage); the effect pin's
  failure text teaches the fix: *"delete the HEAD-RED guard; import the predicate at module top"*.
- Classification GATING because it re-shapes the builder's one granted test-tree edit (amendment-5
  FORK-C rider 3 stands: the builder deletes the guard in REFACTOR; this pin is what reds until it does).

## MP-4 — NON-GATING
Beside the FORK-A exact-set pin: `relation_endpoints(emit_schema_ddl(g)) == {}` for each pinned unswept
generator, same KNOWN-BOUND message and re-open trigger (KP-R5's shape). Better still, as the adversary's
parenthetical says: define "unswept" as *emits a statement the ∀-ENFORCED sweep cannot see* and pin THAT
set to ∅ — then a relation appearing inside `lease` or `floor_calibration` reds the bound on the exact
day it stops being "not a live hole". The bound's premise becomes an observation instead of a docstring
sentence, which is the whole of my amendment-5 FORK-A ruling made honest.

## MP-5 — NON-GATING
The parity matrix gains the RE-register door: (α register → credentialed consistent re-register) and
(consistent register → each mixed pair), comparing outcome class + the three stamps, real vs fake
(KP-FX1's shape). THE QUANTIFIER LAW on MP-E: "the fake mirrors the writer ∀ inputs" was measured on the
CREATE door only; N10's door has a fake-side twin and now gets the same row.

## Prose / archival (r4 carries them; none gates anything)
- MP-P1: `test_ddl_write_target_coverage_124.py::_emit` docstring → *"whenever the generator has a `dim`
  parameter"*.
- R-1: the parity matrix is 34 rows, not 36 — fix the report/commit prose when archiving.
- R-2: paste `r3b_files.txt` into the archived r3 report (a claim that cannot be re-run verbatim is a
  lost instrument).
- R-5: one sentence in D7 naming where the retired resolver's virtue (c) survives.

## §W — r4 worklist (one revision, one adversary delta, then the builder)
| # | item | class |
|---|---|---|
| 1 | MP-1: text-twin static pin (threat model in the instrument) + SKIP-gate effect leg (mutation + corpus) + `_IDENTIFIER_DECISION_CONSUMERS` docstring states its reach | **GATING** |
| 2 | MP-2: perturb `_REFUSAL_ID_SAMPLE_SIZE`; positive-int pin; no ceiling | **GATING** |
| 3 | MP-3: effect pin replaces the spelling pin; teaching failure text | **GATING** |
| 4 | MP-4: unswept emitters emit no relation (or: the "unseen statements" set is ∅) | NON-GATING |
| 5 | MP-5: parity matrix re-register rows | NON-GATING |
| 6 | MP-P1 · R-1 · R-2 · R-5 | PROSE |
| — | builder brief: `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` (one line) + delete the FORK-C guard in REFACTOR + the r2 adversary's two prose lines | lead |

Items 4–5 are small enough that splitting r4 buys nothing; take all five in one revision. **This is the
last pre-build contract round** (STOP-rule §5 above); the r4 adversary delta grades it and the builder is
spawned on SUFFICIENT, or on INSUFFICIENT-with-only-pinned-bounds.

## §E — operator-visible
- The STOP-rule invocation: after r4, private-decision doors in the identity class become pinned KNOWN
  BOUNDS with a stated honest-engineer threat model, not further contract rounds. Flagged because it caps
  rigor on a security-adjacent seam by design; my reading is that the seam's real boundary is the tool
  layer's refusal (which the text pin and the effect legs both cover), and that the residual — an author
  deliberately rewording a regex to evade a gate — is outside any gate this repo can honestly build.
- Session note for the lead: this sidecar's lore client did not recover from outage #2 although the
  server answers; ledger traffic to me should keep its durable copy in the lead report until this session
  is restarted or the client reconnects on its own.

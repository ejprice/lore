brief-base v14 read
brief project v7 read

# REPORT — fix4-partition (packet 63a fix wave, FIX 4 / finding #452)

## Summary block
- state: **done**
- deviation (benign): my idle-gate contract landed as `/tmp/claude-idle-gate-lore/unknown-fix4-partition.contract` because `$CLAUDE_SESSION_ID` was unset in my shell env; the hook falls back to the v1 default `REPORT-fix4-partition.md` — which is exactly the artifact I owe, so no false nudge is possible.
- **Packages considered:** none — no mechanism specified (this fix classifies an existing production param; it introduces no library-shaped mechanism).
- **Reuse ledger:** none — no new reusable symbol. The change adds one data entry (`"capability"`) + an evidence comment to the EXISTING `_NOT_SERVED_OUT` frozenset, following the existing `labels` entry's idiom verbatim.
- **Graded:** n/a — this is a BUILD report measuring my OWN change (RED→GREEN), not a verdict on another artifact. For provenance: worked at HEAD `278f524` (SAME as `git rev-parse HEAD` at report time).
- decisions-needed: none
- receipt pointers:
  - RED-before / GREEN-after tails → §"RED→GREEN receipts" below.
  - the exact entry added → §"The edit".
  - the trace evidence → §"Classification decision + trace".
  - sibling-pin confirmation → §"Sibling pins stay green".

## Mission
FIX 4 (finding #452): one RED pin —
`loremaster/tests/test_link5_render_containment.py::TestTheDerivedPartitionHasNoDoor::test_every_registered_free_text_param_is_gated_or_contained`.
63a added a new `capability=` free-text param (the `<name>:<secret>` verified-credential arg on
`lore_recall` / `lore_remember`) that is in NO partition half, so the derived door pin reddened.

## Tooling
lore (MCP) was first choice throughout: `lore_get_symbol` for `AppContext.recall` / `.remember` /
`._resolve_subject`, `governed.resolve_subject`, `GovernedDenied`, `owner_stamp.stamp_owner` /
`OwnerStampError`, `credentials.parse_credential`; `lore_read` for `agents.py::verify_capability`;
`lore_search` for orientation. **One grep fallback, disclosed:** I used `grep -n "capability"
loremaster/loremaster/server.py` to enumerate EVERY occurrence of the `capability` param across the
server (a rename/exhaustiveness question — "is `capability` an input param on any tool other than
recall/remember?"), which is exactly the CLAUDE.md case (a) where grep stays honest and the graph's
astroid bounds do not guarantee exhaustiveness. Result: `capability` is an input param on exactly
the two tools (`lore_remember` wrapper ~server.py:11346, `lore_recall` wrapper ~11421), both routing
it identically to the handler. No `lore_findings` friction filed — lore answered every structural
question directly; the grep was a deliberate exhaustiveness cross-check, not a routing-around.

## RED→GREEN receipts
RED-before (at HEAD `278f524`, before the edit), scoped to the class:
```
FAILED loremaster/tests/test_link5_render_containment.py::TestTheDerivedPartitionHasNoDoor::test_every_registered_free_text_param_is_gated_or_contained
E   AssertionError: these registered free-text params are in NO partition half ...
E       ['capability']
1 failed, 3 passed in 6.84s
```
GREEN-after (whole file):
```
160 passed in 7.87s
```
GREEN-after (the four partition pins, named):
```
TestTheDerivedPartitionHasNoDoor::test_every_registered_free_text_param_is_gated_or_contained PASSED
TestTheDerivedPartitionHasNoDoor::test_no_classification_names_a_param_outside_the_universe PASSED
TestTheDerivedPartitionHasNoDoor::test_every_assigned_class_has_a_neutralisation_driver PASSED
TestTheDerivedPartitionHasNoDoor::test_the_charset_gated_half_is_the_link1b_validated_set PASSED
4 passed in 1.15s
```

## Classification decision + trace
**Class chosen: `_NOT_SERVED_OUT`** (the "value never reaches a served answer" bound), NOT
`_CHARSET_GATED` and NOT a `_PARAM_CLASS` containment class.

**The crux question** (per brief): does the VALUE of `capability` (`<name>:<secret>`) ever get
RENDERED into a served answer/error an agent reads? **Answer: no, by construction — deliberately.**
`capability` is a credential; echoing its value would ITSELF be the §F3a defect. This is the expected
finding for a secret — NOT the unexpected-leak / STOP-and-flag case.

Trace (symbols, all `lore` tier — the value flows only DOWN, never OUT):
- Tool wrappers `server.py` `recall` (~11421) / `remember` (~11346) pass `capability` SOLELY to the
  handler and return the handler's string. (The `Field(description=_capability_param_description(...))`
  is the static param HELP TEXT served in the schema — authored by us, not the caller's value; every
  param has one. That is the distinction the brief flagged: description-served ≠ value-rendered.)
- `AppContext.recall` (server.py:4185-4213) / `AppContext.remember` (server.py:4069-4155) pass
  `capability` SOLELY to `AppContext._resolve_subject`.
- `AppContext._resolve_subject` (server.py:4157-4183) → `governed.resolve_subject`.
- `governed.resolve_subject` (governed.py:121-184) → `owner_stamp.stamp_owner` →
  `AgentRegistry._verify_capability_owner` (`credentials.parse_credential` + `verify_capability`).

Every consumer NEUTRALISES the value, never renders it:
- **parse** — `credentials.parse_credential` (credentials.py:23-47) returns a uniform `None` on any
  malformed input: no raise, no echo.
- **verify** — `agents.py::verify_capability` (agents.py:942+) docstring, verbatim: the denial reason
  is "laundered into a DEBUG log (never the raw credential, §F3a) and never reaches the caller"; a
  uniform `None` deny reaches the caller. `_deny_capability` logs "a fixed vocabulary token — NEVER
  the raw credential". A DEBUG log is not a served answer.
- **DENY render** — `owner_stamp.OwnerStampError`'s two messages are FIXED strings (no
  `agent_capability` echo); `resolve_subject` catches it and re-raises `GovernedDenied` with a FIXED
  teaching string. The ONLY `!r` on that whole path is `{email!r}` in `resolve_subject` — that is the
  transport-token PRINCIPAL EMAIL (`access_token.subject`), a DIFFERENT value, not the `capability`
  param.
- **SUCCESS render** — a verified `capability` resolves to a `pdp.Subject` (principal_id/agent_id/
  role/visible_keep_ids) that SCOPES the backend read; recall then serves
  `_render_recalled_memories(recalled)` (memory text/kind/importance/score/refs) and remember serves
  the deterministic `uuid5` memory id (+ optional length-warning line). Neither embeds the credential.

**Why not `_CHARSET_GATED`:** the Link-1b seam `AppContext._validate_comms_identities` gates exactly
`{agent, session, name, to}`; the sibling pin `test_the_charset_gated_half_is_the_link1b_validated_set`
requires `_CHARSET_GATED` to EQUAL that seam's signature. `capability` is parsed by
`parse_credential` and verified by hash — it is NOT charset-gated by that seam. Adding it there would
be false AND would redden that sibling pin. **Why not `_PARAM_CLASS`:** a containment class asserts
the value IS rendered and neutralised at a render site; `capability`'s value is rendered at NO site,
so a containment class would be a false classification.

## The edit
`loremaster/tests/test_link5_render_containment.py` ONLY (+25 / -1). The assertion BODIES are
untouched — no gate was weakened. The change adds one correctly-evidenced data entry to the set the
door pin checks against (exactly what the pin's own failure message instructs), plus its evidence
comment. Final line:
```python
_NOT_SERVED_OUT: frozenset[str] = frozenset({"labels", "capability"})
```
with a preceding comment block giving the full DOWN-not-OUT trace above and this re-open trigger:
> RE-OPEN TRIGGER: any served render OR error begins embedding a caller `capability` value (an echo
> of the raw credential) — that is a §F3a credential leak: STOP-and-flag it FIRST, then (only if the
> echo is somehow legitimate) move it into a driven `_PARAM_CLASS` containment class.

## Sibling pins stay green (not weakened)
- `test_no_classification_names_a_param_outside_the_universe` (stale-entry / reverse leg, ~883):
  GREEN. It still fires if `capability` is ever retired from the schema — I added `capability` ONLY
  because it IS in the derived universe (that is why the door pin fired). No phantom classification
  introduced.
- `test_every_assigned_class_has_a_neutralisation_driver` (~889): GREEN, unchanged — I did not touch
  `_PARAM_CLASS`, so its assigned classes are the same driven set.
- `test_the_charset_gated_half_is_the_link1b_validated_set` (~898): GREEN, unchanged — I did not touch
  `_CHARSET_GATED`.

The door pin still proves EVERY registered free-text param is in a partition half; its scope is not
narrowed. This is a real reconciliation of a NEW production param (`capability`, 63a) with the STANDING
derived invariant, not a hack-to-green.

## Not-hack-to-green self-check
- Did I edit an assertion body to pass? No — bodies untouched (verified by diff: the change is in the
  `_NOT_SERVED_OUT` comment + frozenset literal only).
- Did the "fix" make the pin green by weakening what it checks? No — the reverse-leg stale-entry pin
  still guards the same union; a retired `capability` would redden it.
- Is the class evidence-backed (trust-doctrine / partition law)? Yes — full symbol-cited trace above;
  the one grep fallback disclosed and justified.

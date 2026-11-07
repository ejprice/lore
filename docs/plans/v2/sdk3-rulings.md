# SDK3 — operator rulings

Packet: SDK3 (Python SDK `surrealdb` 2.0.0 → 3.0.0 on SurrealDB 3.3.5).
Packet doc: `docs/plans/v2/sdk3-python-sdk-3-migration.md` (contract author's).
Rulings here are binding on every SDK3 agent (contract author, adversary, builder, cold audit).

## R1 — the inventory is a WORKAROUND RE-EVALUATION, not a preservation list (operator, 2026-11-07)

Operator, verbatim: *"inventory of SDK 2.0 behaviours we rely on — much of which is likely
workarounds for driver or DB bugs that need to be re-evaluated."*

Much of what lore "relies on" exists BECAUSE of a defect in SDK 2.0 or in the engine (3.1.5–3.2.4).
Carrying such code forward with a fresh pin preserves the workaround after its reason is gone.
Ask of every inventory row: *"is this code here because something was broken, and is it still
broken on SDK 3.0 + 3.3.5?"*

Every removed-behaviour inventory row therefore carries:

| column | content |
|---|---|
| origin | `sdk-bug` / `engine-bug` / `design` (lore's own choice, no defect behind it) |
| defect | the finding #, store-ref section, or receipt that documents the bug; `undocumented` if none |
| re-probed | the defect's status on **SDK 3.0.0 + engine 3.3.5**, MEASURED by a probe you run (instrument + output in the packet doc), never inferred from release notes: `still-present` / `gone` / `changed` (describe) |
| fate | `retire` (bug gone → delete the workaround; pin the CORRECT behaviour that now holds natively) · `keep` (bug still present; keep the pinned known bound) · `simplify` (bug changed) · `design` rows use the original preserved / dropped / spec-silent fates |

Scope: not only SDK-2.0-shaped branches. Include the ENGINE workarounds in the store-seam code
that store reference §6.5 / §6.6 / §2 / §3 document, wherever the SDK swap or the 3.3.5 engine
could have changed the underlying behaviour. Examples to evaluate, not an exhaustive list:
- KeyError-as-transport and `websockets.ConnectionClosed*` classification;
- NotAllowed-after-silent-reconnect;
- statement[0]-only validation and later-statement error swallowing (§6.5, §6.6 #10);
- `_is_domain_cascade_notice` root-cause selection;
- the bare `"TransactionConflict"` literal (#111);
- the per-owner `_ensure_connection` self-heal (#576);
- `SELECT *` omitting NONE columns (§6.6 #12);
- `CONTENT` not composing with `SET` (§6.6 #11).

Existing KNOWN-BOUND pins ("this pin goes RED the day someone closes the hole") are the
instrument: run them against an SDK 3.0 scratch build. A known-bound pin going red is a `gone`
signal for that row, to confirm with a probe.

Rider (same sentence, per CLAUDE.md "THE RIDER IS PART OF THE RULING"): **every `retire` row
ships with a pin that FAILS if the workaround is still needed**, i.e. a test that drives the
formerly-broken case through the plain SDK 3.0 path and asserts the correct behaviour, AND a
mutation proof that re-introducing the old defect's symptom reddens it.

Decision rights: a `retire` whose re-probe is unambiguous is decided by the evidence. A row
whose re-probe is ambiguous, or whose retirement changes a served surface, is an operator fork:
list it in the packet doc's forks section.

## R2 — F1: `run_query` returns its ONE statement's result, and refuses anything else (operator, 2026-11-07)

Ruled option A. `_txn.run_query` is lore's single-statement seam (every production caller sends one
statement; multi-statement work rides `execute_transaction`). Under SDK 3.0 `query()` returns one entry
per statement, so `run_query` selects that one statement's result itself, and RAISES when the SDK
returns anything other than exactly one result — never a silent `[0]`. This is the seam's contract,
not a mimicry of SDK 2.0 (which validated only statement[0]).

Rider: `scout._scout_query_once` and `inbox_awaiter._live_query` are converted to the same seam, so
the selection rule lives in exactly one place. Pin it like this: a lost compare-and-swap must read
as lost (the measured SDK 3.0 failure was `[[]]` read truthy, 8/8 racers winning), a counter must
read its scalar, a `LIVE SELECT` must yield its bare id, and a two-statement call must raise; prove
the sharing by mutation (break the selection in the seam — scout and the inbox awaiter must redden
with it).

Rejected: B (per-caller `[0]`, 27 copies of the rule); C (`query_raw` for every statement; unmeasured
outside transactions). Not covered by this ruling: the test harness `run()` fixture.

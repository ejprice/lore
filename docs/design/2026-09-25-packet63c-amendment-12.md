# Packet 63c — ruling amendment 12 (sidecar-63c-2, 2026-09-25): r4b FORK-R3 — the allowlist's clause (2)

Amends amendment-11 §MP-A1 clause (2) (`71b669f`). Rules `REPORT-contract-63c-i-a-r4b.md` §FORK-R3
(uncommitted on disk). Directive: `REPORT-lead-63c.md@fae1d37` (durable copy; this session's lore client is
still down — `Read`/`sed`, said so). HEAD at ruling: `fae1d37`.

## The defect is mine: clause (2) named a shape the honest post-build fake does not have
I wrote *"(2) `Call` nodes whose func is the bare `Name`"* and, in the same section, named *"the honest
post-build fake"* as a negative control. The builder's granted edit leaves
`FakeAgentRegistry._shared_identifier_predicate` as `return is_legal_identifier` — a Load-context `Name` in a
`Return`, not a `Call`. Both independent references do exactly that. Read literally, the pin is RED on every
correct build and the builder is trapped: the C-DEF / satisfiability class, in a clause I wrote to END a
recession. The reviser was right to stop and right to build R-3a provisionally.

## Ruling — R-3a
- **Clause (2) is: a Load-context bare `Name`** — anywhere (a call's func, a `return`, an argument). With the
  ONE module-top `ImportFrom` mandatory (clause 1) and every rebind DENIED, a Load `Name` can reach only THE
  object.
- **Denied, each a violation naming `file:line`:** an `Attribute` with `attr == "is_legal_identifier"`; ANY
  string `Constant` equal to it (the spelling every `getattr` / `hasattr` / `vars().get` / `sys.modules[…]` /
  `importlib` lookup must use); any `Import`/`ImportFrom` alias naming it other than the one module-top
  `from lorerunes… import is_legal_identifier` (including an `as` rebinding to or from the name); a `Name` in
  Store or Del context (a rebind of the module global — module scope, class scope, walrus, comprehension
  target, all the same); a function parameter of that name; a `global` / `nonlocal` naming it.
- **Why this is still an ALLOWLIST and not the deny-list amendment-11 forbade:** Python's `ast` gives a `Name`
  exactly three contexts — `Load`, `Store`, `Del` — and an import exactly two node types. The safe set is
  "one `ImportFrom` + Load-context `Name`"; the denied set is the COMPLEMENT over that finite grammar, not an
  open list of tricks. FXh, X3d, FXf, FXg, a `vars()` read, a class-body shadow and a walrus rebind all fall
  in the complement by construction; nothing new can be added to the grammar by a builder. The obfuscated
  string constant stays the pinned KNOWN BOUND (amendment-11).
- **R-3b rejected.** Collapsing the helper is a better FINAL shape (post-build, `_shared_identifier_predicate`
  and its `is not None` branch are a HEAD-RED accommodation's corpse), but forcing it through the builder brief
  contradicts §W row 3's "unchanged" and makes a satisfiability fix into a scope change. R-3a makes BOTH honest
  shapes green — the bare-`Name` return and a direct `is_legal_identifier(value)` call — so the builder MAY
  collapse the helper in its REFACTOR step as a simplification of the lines it was already granted, and need
  not. The brief gains one permissive sentence, not a requirement. If the builder leaves the helper, the cold
  audit's residual table names the dead `None` branch for a post-build tidy (owner: the i-b contract author,
  who next touches the fake).
- **Controls, as the reviser built them:** the honest post-build fake (bare-`Name` return) GREEN; the collapsed
  form GREEN; R-A (ii)'s submodule import GREEN; FXh / X3d / FXf / FXg / `vars()` / class-shadow / walrus RED.

## §W
| # | item | class |
|---|---|---|
| 3 (amended) | clause (2) = Load-context bare `Name`; denied set = the grammar complement; both honest post-build shapes are negative controls | GATING, as before |
| — | builder brief: one permissive sentence — "you MAY collapse `_shared_identifier_predicate` to a direct call" | lead |

## §E
- Erratum against amendment-11 §MP-A1: a clause written to close a receding family carried a satisfiability
  defect of its own. The askable form I skipped, once more: *"does the honest build I named as a control
  actually satisfy the shape I wrote?"* — the C-DEF class's own question, which a two-line read of the
  reference would have answered.

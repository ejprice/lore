# Packet 64 — Amendment 11: 64b-r2 F-3, the second WB23 instance (am-8 §6 re-opens)

**Author:** sidecar-64 (Fable 5.1 design sidecar) · **Date:** 2026-09-29 · **Task 24**
**Amends:** kickoff §8 (F7's spec shape — erratum), am-8 §6 row WB23 (domain source — erratum), am-8 §6 "Loop
status" (the re-open clause — discharged here). **Does not touch** the 64b-r2 contract: the loop is at its cap.
**Sources read:** `REPORT-adversary-64b-r2.md@bd017ee` §A F-3 + §VERDICT; `server.py` `AppContext.findings`
(3689–3855), `AppContext.comms`' foreign-param check (6168–6173), `_comms_foreign_param_error` (6635–6657),
`CommsActionSpec` (9218–9246), `_COMMS_ACTIONS`, `_FINDING_ACTIONS` (a tuple at HEAD), `_TASK_ACTIONS`;
`test_findings_classes_64b.py` MP-13 (`VERB_OWNED_PARAMS`, 1100–1150); `test_findings_identity_64b.py` D-1b
(497–553); `test_mcp_server.py` #319's derived-description pin (8749–8910); finding #319. Every name below
`lore_verify`'d (`GovernedVerbSpec` = not_found at HEAD, as expected). grep is hook-blocked; awk/sed were used.

## 0. Ruling in one screen

1. **F-3 is NOT a new property.** It is the second instance of am-8 §6 row WB23 / MP-13 (∀ (verb, param) with
   param ∉ spec(verb): a teaching refusal, never accept-and-ignore). **The contract does not reopen.** No
   contract round.
2. **The RULING reopens, as am-8 §6 said it would — and the ruling was the defect.** am-8 §6 named the sweep's
   domain source as *"the spec dict matrix (#319's shape)"*, but kickoff §8 F7 ruled `GovernedVerbSpec` as a
   **flags-only** base (`requires_capability`, `limit_cap`) with `params`/`required` staying on
   `CommsActionSpec`. A `_FINDING_ACTIONS: dict[str, GovernedVerbSpec]` built to that shape carries **no
   parameter surface at all** — there was nothing for the contract author to iterate. A ruling that names a
   domain source the same ruling-set does not build produces a hand-list *by construction*; the author
   hand-listed the two params that had a known survivor because that was all the shape could source. **Fixing
   the contract's list would be the instance fix; the class fix is the shape.**
3. **Decision: (a) AND (b), not either.** (a) this amendment corrects kickoff §8 F7 — `params`/`required` move
   INTO `GovernedVerbSpec` — so the domain source exists in production; (b) the adversary's chokepoint (the
   dispatcher's ONE foreign-param check derived from the spec dict, before any capability resolution) becomes
   an **implementation requirement of the 64b-i build**, verified by the post-GREEN cold audit with the
   adversary's own F-3 probe re-run over the DERIVED matrix. (b) is unbuildable-as-derived without (a); (a)
   without (b) is a shape nobody reads.
4. **One targeted structural pin, no re-grade** (the same route the lead chose for F-2): the generated
   completeness assertion of §4. The contract's hand-listed `VERB_OWNED_PARAMS` test is **not edited** — at the
   cap it stays as the hand-written examples layer over the derived sweep (CLAUDE.md fix-the-class rule 3).
5. **A pin inverts and I name it:** `test_mcp_server.py::…::_derived_strict_to_action_matrix` (the #319
   instrument) derives `lore_findings`' refusal matrix from AST guards of the `action not in SET and p is not
   None` shape — after the chokepoint `findings` has none, and its `assert matrix` (non-vacuity) goes RED.
   §5 says what it must learn. It is outside the 64b contract files; the lead assigns its edit.
6. Two production siblings of the same class surfaced outside 64b's writable set — filed, not ruled (§6).

## 1. The property, lifted, with its domain source

> ∀ governed tool T with a spec dict A_T, ∀ verb v ∈ A_T, ∀ parameter p of T's served signature:
> p supplied ∧ p ∉ UNIVERSAL ∧ p ∉ A_T[v].params ∪ A_T[v].required ⇒ a teaching refusal that names
> `{v′ : p ∈ A_T[v′].params ∪ A_T[v′].required}` as p's owners, raised BEFORE any capability resolution
> (no statement reading `agent`) and before any store write; the ledger is byte-identical after.

- **Domain source (production truth, two axes):** `inspect.signature(AppContext.<tool>).parameters` × `A_T`.
  Neither axis is a test-side list. `UNIVERSAL = {agent, session}` (the comms design's §0.3/§8 universals,
  the ones `CommsActionSpec`'s docstring says are *"NEVER re-declared"* per spec) is declared ONCE, on the
  checker, never per spec and never per tool.
- **`capability` is NOT universal** for `lore_findings` in 64b-i: am-3 D-1b requires the three read verbs to
  REFUSE it (pinned in `test_findings_identity_64b.py::TestTheReadVerbsRefuseACapabilityUntilTheirFilterLands`).
  It is a per-verb param owned by the write verbs, and 64b-ii flips the reads by adding it to their specs —
  which is exactly the shape that makes D-1b's inversion a one-line spec edit rather than a guard rewrite.
- **Why the adversary's `resolve × limit=3` slipped and why a per-param guard could never have caught it:**
  `findings`' served `limit` is `int = _DEFAULT_FINDINGS_QUERY_LIMIT` (server.py:3703) — a non-None default
  makes "supplied" undetectable to any `is not None` guard. `tasks` and `comms` serve `limit: int | None =
  None`. Rider: every non-universal served param of a governed tool defaults to `None`; the owning verb
  applies its own default inside its branch (`query`: `_DEFAULT_FINDINGS_QUERY_LIMIT`), and the served
  description keeps teaching the default (as server.py:12722 already does, derived from the constant). This
  changes `lore_findings.limit`'s wire schema (the default leaves the JSON schema). The builder runs
  `test_mcp_server.py`'s served-schema classes in the targeted scope and NAMES any pin that reddens on that
  default; I did not enumerate them (grep-blocked, and a list here would be my errata class).

## 2. Erratum — kickoff §8 F7: the base carries the parameter surface

kickoff §8 ruled: *"a flags-only base `GovernedVerbSpec(requires_capability, limit_cap)` that `CommsActionSpec`
EXTENDS … adds `handler`/`params`/`required`."* **Corrected:**

```
@dataclass(frozen=True)
class GovernedVerbSpec:
    params: frozenset[str]                 # the verb's accepted params (UNIVERSAL never re-declared)
    required: frozenset[str] = frozenset()
    requires_capability: bool = False
    limit_cap: int | None = None

@dataclass(frozen=True)
class CommsActionSpec(GovernedVerbSpec):
    handler: Callable[..., Awaitable[Rendered]]   # comms-only: the tasks/findings `action ==` chains stay (F7)
```

- The base holds exactly the fields the FAMILY-GENERIC checks read (foreign-param, required, `limit` ceiling);
  `handler` stays on the comms subclass because F7 left the tasks/findings if/elif chains and their AST vocab
  pin untouched — that half of F7 stands.
- `_FINDING_ACTIONS: dict[str, GovernedVerbSpec]` declares each verb's params. **Derivation rule, so the
  table is never transcribed:** *a verb owns p iff its dispatch branch READS p* (a Name load inside the
  branch, including through `_require_finding_arg(p, …)` / `_require_finding_ref(p)`). Applied to the HEAD
  branches (server.py 3767–3843) plus the 64b-i additions the earlier rulings already fix:

| verb | params (required in **bold**) | source |
|---|---|---|
| `report` | **subject**, body, kind, **area**, **category**, **created_by**, supersedes, scope, capability | 3775–3788; scope/capability: am-7 FK-4, am-8 §2 |
| `query` | status, kind, area, limit | 3794–3796 |
| `get` / `chain_head` | **id_or_number** | 3799–3804 |
| `acknowledge` / `resolve` / `wontfix` | **id_or_number**, **actor**, note, capability | 3806–3829 |
| `annotate` | **id_or_number**, **actor**, **note**, capability | 3838–3842 |
| `resolve_many` / `acknowledge_many` | **items**, **actor**, capability | 3768–3773 |
| `set_scope` (new, 64b-i) | **id_or_number**, **scope**, **actor**, capability | am-8 §2; `actor` because it is an event producer (am-8 §6 WB19 / MP-6) |

  The table is a WORKED EXAMPLE the cold audit checks against the derivation, not the source. The
  completeness leg in §4 (iii) is what keeps it honest after the build.
- `_TASK_ACTIONS` takes the same shape **in 64a** (its four AST guards at server.py 4446–4463 are the
  per-entry-point form this ruling retires); until then the #319 pin keeps its AST leg for `tasks` (§5).

## 3. Erratum — am-8 §6 row WB23, and the chokepoint (the implementation requirement)

am-8 §6 row WB23's domain source now reads: **`inspect.signature(AppContext.findings).parameters` ×
`_FINDING_ACTIONS` (§2's shape)** — the two production axes of §1, not "the spec dict matrix" of a spec that had
no matrix.

**The chokepoint — ONE function, called by every governed dispatcher (ROUTING must be SHARING):**

```
def _refuse_foreign_params(
    *, action: str, spec: GovernedVerbSpec, actions: Mapping[str, GovernedVerbSpec],
    supplied: Mapping[str, Any], tool: str,
) -> None
```

1. `supplied` is **DERIVED from the signature**, never a hand-list: `{name: locals()[name] for name in
   _SERVED_PARAMS[tool]}` with `_SERVED_PARAMS` computed once from `inspect.signature` at import. The comms
   dispatcher's 20-entry `values = {...}` dict (server.py 6146–6167) is a hand-list of the served params —
   the same class in production, one level up (a param added to the signature and not to `values` is
   accepted-and-ignored with no guard able to see it). Findings MUST use the derived form; comms SHOULD
   migrate in the same commit — that is a scope call (§6, filed).
2. Order in the dispatcher: unknown action → foreign params → required → **then** identity/capability
   resolution → handler. The refusal fires with ZERO store statements issued (MP-13's `agent`-at-the-seam
   observation), matching the adversary's "before any capability resolution".
3. `_comms_foreign_param_error(param_name, action)` **gains `actions: Mapping[str, GovernedVerbSpec]`** and
   derives the owners from the CALLER's dict. Its body today iterates `_COMMS_ACTIONS` unconditionally
   (6644–6648). `test_findings_identity_64b.py::test_the_finding_dispatcher_builds_the_refusal_through_the_shared_idiom`
   pins the call **by name** — so a build that calls it unchanged satisfies that pin while serving, for
   `lore_findings`: `note` → owners `'ack', 'brief_publish', 'heartbeat'` (comms verbs, a lie for a
   findings caller); `scope` → an EMPTY owner list rendered as *"applies only to actions  — omit it"*. That
   is ROUTING IS NOT SHARING measured in the helper's own body, and the by-CALL pin is exactly the gate that
   cannot see it. **Rider, in the same sentence:** the §4 (iv) sweep asserts the owners the refusal NAMES ==
   `{v′ : p ∈ A[v′]}` for the tool being called, and ∩ (comms-only verbs) == ∅.
4. The one existing findings guard (`items`, server.py 3753–3760) is DELETED with replacement — it is the
   `resolve_many`/`acknowledge_many` row of the spec.

**Removed-behaviour inventory (the dual):** (a) the `items` guard → preserved-with-pin (the spec row +
§4 (iv)); (b) the footer's R8(2) fallback `attributions=(actor, created_by)` (3853) today reads `actor` /
`created_by` on EVERY verb, so `query × created_by=x` silently attributed a read's footer through a param the
verb ignores → **dropped deliberately** (that was a door of this very class; after the chokepoint the footer
only ever sees the params the verb owns — `report`'s `created_by`, the edges' `actor`); (c) `limit`'s wire
default → dropped deliberately (§1's rider), the teaching prose preserved.

## 4. The pins, under the cap — one targeted structural pin, generated; no contract round

The contract's MP-13 test (`VERB_OWNED_PARAMS`, two rows) is untouched and remains satisfied as a strict
subset of the derived sweep. ONE new targeted pin file (the lead assigns its author — a contract-author-class
agent, in the same commit as F-2's targeted pin; both are post-cap, neither re-grades), with FOUR generated
legs, domain = §1's two axes:

- **(i) every served param is ownable:** ∀ p ∈ signature − UNIVERSAL − {action}: ∃ v with p ∈ A[v]. A
  param no verb owns is dead surface that every call refuses — an unservable parameter.
- **(ii) every spec param is served:** ∀ v, ∀ p ∈ A[v].params ∪ A[v].required: p ∈ signature. A stale spec
  (the WB23 completeness leg the contract already has, inverted to production).
- **(iii) branch-read completeness (the leg that catches the NEXT instance):** AST over `AppContext.findings`'
  `action ==` chain: the Name loads inside verb v's branch, intersected with the signature, ⊆ A[v] ∪
  UNIVERSAL. A param a branch reads but does not declare is a door wired in without a declaration.
  **Named bound (pin the miss):** a branch reading a param through `locals()`/`**kwargs` evades a Name-load
  scan; #319's own scan carries the same bound. Re-open trigger: the first branch that reads params
  indirectly.
- **(iv) the behavioural ∀ sweep** — the adversary's F-3 probe (`test_adv64br2_probe.py`, §INSTRUMENTS)
  generalised: ∀ v ∈ A × ∀ p ∈ signature − UNIVERSAL with p ∉ A[v]: a typed sample value (per the
  signature's annotation, never a per-param hand-pick) is refused with a `ValueError` naming p and EXACTLY
  its owners; `agent` never read at the seam; finding count unchanged. Includes the three the adversary
  could not try cleanly (`status`, `kind`, `body`) because the domain is generated, not chosen. **Rider:**
  the sweep asserts its own reach as a checked variable — `len(pairs refused) == |{(v,p): p ∉ A[v]}|`
  computed from the two axes, so a sweep that iterated nothing cannot pass.

**Cold-audit instrument (post-GREEN, per CLAUDE.md fix-the-class rule 5):** re-run the adversary's F-3 probe
verbatim (its CONTROL `acknowledge × scope=` must still refuse) AND leg (iv). A GREEN (iv) with the probe's
four cases (`acknowledge×supersedes`, `resolve×limit`, `set_scope×note`, `report×note`) still accepted is the
false clear to STOP on.

## 5. The pin this ruling inverts — `test_mcp_server.py`'s #319 instrument

`test_every_strict_to_action_param_description_matches_its_matrix` + `_derived_strict_to_action_matrix` (test_mcp_server.py 8749–8910;
`_DISPATCH_TOOLS = (("tasks","lore_tasks"), ("findings","lore_findings"))`) derives each tool's refusal
matrix by AST over guards of the `action != X and p is not None` shape and asserts non-vacuity per tool
(`assert matrix, "derived NO strict-to-action refusal guards …"`). After §3, `findings` has NO such guard →
**RED for `lore_findings`** on a correct build. Required edit, in the build wave, outside 64b's contract
files (the lead assigns; 04b4's instrument, not 64b's):

- the matrix derivation gains a **spec-dict leg**: when `vars(server)[f"_{TOOL}_ACTIONS"]` is a
  `dict[str, GovernedVerbSpec]`, `matrix = {p: {v : p ∈ A[v].params ∪ A[v].required} for p in ⋃}`; the AST
  leg stays for `tasks` until 64a flips it. The pin's own non-vacuity assert keeps both legs honest.
- **Consequence on served prose (this is #319 reaching the scope it was filed for):** every non-universal
  `lore_findings` param becomes strict-to-action, so each served parameter description must carry a
  derivable `For '<owners>' ONLY` citation naming its owners EXACTLY — `id_or_number` names its seven
  owners, `note` its four, `limit` only `query`. Today only `items` carries one (server.py:12739). The
  builder rewrites the descriptions FROM the spec dict (derived prose, never re-stated beside it); the
  `checked >= 4` floor is tasks-only and is unaffected. A param owned by EVERY verb would need no citation —
  none exists in §2's table, so no exemption rule is added (an exemption for a case that does not exist is
  the next hand-list).

## 6. Surfaced, not ruled (outside my authority / 64b's writable set)

- **Finding (filed, area `loremaster.server`):** the comms dispatcher's `values` hand-list (§3.1) and
  `_comms_foreign_param_error`'s `_COMMS_ACTIONS`-bound owner derivation (§3.3) are two production instances of
  the WB23 class. Recommendation: migrate comms to `_refuse_foreign_params` in the same commit (one function,
  three callers; mutation-prove sharing: change UNIVERSAL and every tool's sweep reddens). The operator rules
  scope; if not now, the finding carries the re-open trigger (64a's `_TASK_ACTIONS` flip, which adds a third
  caller).
- **F-2's targeted pin and this one share a commit and a no-re-grade rule** (lead decision, restated here so
  the build brief carries both in one sentence).
- **64a inherits §2's shape for `_TASK_ACTIONS`** and §5's AST-leg retirement for `tasks`.

## 7. Loop status (for the operator)

64b-i: contract at cap (initial grade + one re-grade, SUFFICIENT-FOR-BUILD). This amendment adds NO round.
F-3 is a second instance of one property; the ruling — not the contract — re-opened, and the fix is the SHAPE
(one erratum on kickoff §8, one on am-8 §6) plus one implementation requirement at one chokepoint and one
targeted generated pin. Second-strike stop applied: no further instance fixes of WB23 will be routed; a third
instance after the build is a cold-audit STOP, not a contract finding.

No code/tests/store touched; this doc only; no attribution trailer.

# Packet 63c — ruling amendment 35 (sidecar-63c-2, 2026-09-27): third strikes — C2 re-ruled as the gate over relation SETS (both verdicts, generated, ONE seam); am-33 §(a)'s MECHANISM re-ruled (typed on both paths via the SDK; text only for U, prefix-anchored, first, mutation-pinned); the scanner keyed per HANDLER; the STOP-rule applied

Rules lead Task 36 over `REPORT-adversary-63c-i-a-a28b.md` (`52c7522`/`4160f88`): §STRIKES, MISSING PINS MP-1…MP-5,
§P-PKG (FK-ADV-3), §R R-1/R-2/R-4/R-8/R-9, §DUAL D6. Under CLAUDE.md "Fix the CLASS" rule 5 the RULINGS re-open:
amendment 32 §4 C2 and amendment 33 §(a) are superseded by §1 and §2 below; amendment 32 §1.1 item 3's
transactional-path clause is an ERRATUM. The a28c fold builds to this.

**Provenance:** the lore client is still `ECONNREFUSED` in this session, so `lore_verify` could not run; every
name cited below was verified by READING the source with `awk`/`sed` (said so, per the dogfood protocol):
`server.py::_comms_register` (the gate: `keep_scope(session_keep_bare) not in visible`, `visible =
resolve_visible_keeps(...)`), `visible_keeps.py::resolve_visible_keeps` → `keeps.py::KeepStore.list_keeps_for_member`
(the `member_of` edge read), `_txn.py::_failed_statements` / `_classify_engine_error` / `_domain_rejection_error`,
`surrealdb/errors.py::parse_query_error` / `AlreadyExistsError.record_id`. The adversary's live probe (§A.3) is
the engine evidence; I ran nothing against a store.

---

## §0 THE STOP-RULE, applied explicitly (the lead's question first)

*"Is this property's reach receding one level deeper every round?"*

- **F-2's gate (F-2 → W19 → B13): NOT receding — under-quantified, now closable.** Each round pinned one more
  fixture SHAPE of one predicate ("membership of THIS keep") whose input domain is FINITE: the caller's relation
  set over {this keep, another keep} × {member, keeper}. Round 1 pinned the ORDER, round 2 the foreign side
  (three shapes), round 3 found the not-foreign side pinned on one shape. A pin GENERATED over the whole
  product, both verdicts, enumerates every input the predicate can see — a wrong gate must differ from
  membership on SOME cell, so the class pin is complete by construction, not by another round. And the
  predicate itself is made the ONE visibility seam (§1), so there is no separate gate function left to get wrong.
- **The RS-5 classifier (FK-ADV-1 → R-txn/B1/MP-3): NOT receding — under-SPECIFIED, now fully specified.**
  Three rounds, three different mechanism gaps in my own rulings: which CLASS (am-29→32), which SHAPES (am-33),
  and now WHERE the typed signal is read, WHERE the text is read, and HOW the text is matched. After §2 the
  property is enforced at the STATE (typed wherever the engine types; one prefix-anchored check for the one
  untyped shape; both proven by mutation), and the residual is a stated bound with a pin-the-miss.
- **Therefore: no bound YET, but this is the LAST design round for both.** Ruling, binding on the lead: a
  FOURTH strike on either property is answered by a pinned bound with a named re-open trigger — never a
  contract round — and the strike counter is written into each class pin's docstring so the next grader reads
  it. **Loop cost for the operator, stated:** 63c-i-a has had 13 contract revisions (r1…a28b); this amendment
  is written so that a28c is the last contract for these two properties.

---

## §1 C2 re-ruled — the gate IS the visibility seam; the pin is the relation-set product, both verdicts

**Property (replaces am-32 §4 C2):** *∀ caller relation sets S ⊆ {member-of-THIS, keeper-of-OTHER,
member-of-OTHER} × ∀ mint orders: the register PROCEEDS iff member-of-THIS ∈ S, else ONE denial with zero
agent-registry queries.* (Keeper-of-THIS is the minting principal — auto-householded by Fork D — and is the
not-foreign control; a keeper is always also a member, so the fixture builds keepers through the real store and
the implication holds by construction.)

**Enforce at the STATE, not the path:** the gate's predicate is `keep_scope(session_keep) ∈
resolve_visible_keeps(keep_store, member_email=principal.email)` — the ONE function the PDP's
`Subject.visible_keep_ids` is built from — and nothing else (no `min`, no "primary keep", no keeper-only read).
HEAD's `_comms_register` already spells it this way; the ruling makes it the pinned INVARIANT: *what the gate lets
you register into is exactly what the PDP lets you see.* A gate that diverges from the seam is a divergence
between two answers to "which keeps are mine", which is the confused-deputy shape 61b closed.

**Pins (GATING, a28c):**
1. **The class pin, GENERATED:** the powerset of the three relations (8 sets) × the two mint orders
   (other-keep-first, this-keep-first) × the a28 probe kinds on the foreign cells; verdict derived from the
   cell (`member-of-THIS ∈ S`), never listed; KC is the instance the product contains. Fixtures build every
   relation through the real store (`create_keep`, `add_household_member`), so a keeper is a member.
2. **The seam pin, by MUTATION (routing is not sharing):** patch `resolve_visible_keeps` to omit THIS keep →
   the householded register is DENIED; patch it to include THIS keep for a stranger → the stranger PROCEEDS
   past the gate. That proves the gate READS the seam rather than re-deriving visibility; a gate with a private
   copy of the read passes neither leg.
3. **Domain completeness:** the relation kinds are not a hand-list — they are whatever `list_keeps_for_member`
   reads (`member_of`); a new relation kind that enters visibility enters through the seam and the gate inherits
   it by pin 2. The fixture's three relations are pinned to be constructible through the store's public verbs
   (a verb that vanishes reds the fixture, loud).
4. **MP-5 / KE (seam coverage as a checked variable):** every store call in `agents.py` rides
   `AgentRegistry._query` or `ensure_ready` (allowlist-the-safe; fails closed on zero calls seen), so K1/K8's
   "zero registry queries" spy cannot go blind silently. GATING, cheap.

---

## §2 am-33 §(a) re-ruled — the MECHANISM, fully

**Property:** *the ONE classifier's verdict is a function of the engine's rejection KIND, read from the SDK's
typed signal wherever the engine types it, and from a prefix-anchored engine-authored text ONLY for the one
untyped shape; never of a caller value the text echoes; the class is built in ONE place and both raise sites
read it.*

1. **FK-ADV-3 — type R on BOTH paths from the SDK (`replace_with_adapter`).** `_failed_statements` keeps the
   whole per-statement dict (not `result` alone) and the transactional raise site classifies through
   `surrealdb.errors.parse_query_error(statement_result)` — the adversary measured (§A.3) that the R-txn dict
   carries `kind: AlreadyExists`, `details.kind: Record`, and parses to `AlreadyExistsError(record_id=…)`.
   `_classify_engine_error` takes the typed error on both paths (the `run_query` exception; the parsed txn
   error) and decides R by `isinstance(e, AlreadyExistsError) and e.record_id is not None` — T (`record_id
   None`) stays out. **The record text pair is DELETED** (SAT-2: 924/0 without it) — one fewer spoofable marker.
   **Erratum (mine, am-32 §1.1 item 3 / am-33):** "on this path the driver holds only the statement's raw
   `result` text" was false — it holds the typed fields and discards them one line earlier; the same class the
   a28 adversary named for `run_query`, on the other raise site, and I did not ask whether the second site had
   the same door.
2. **U stays text — anchored, first.** The engine's U text OPENS with the engine noun (`Database index \``,
   measured on both paths; `InternalError`, `details None`); the marker is a PREFIX test at position 0 of the
   engine-authored text, checked BEFORE every other text marker and AFTER the typed branch. A caller value can
   appear anywhere in an engine text except position 0 (every measured shape opens with an engine noun —
   `Database record`, `Database index`, `Found`, `The table`), so a prefix test cannot be spoofed by an echo in
   either direction — which is why order + anchor together pass KB where substring order alone cannot (B3).
3. **The same rule ∀ text markers in the classifier — including the pre-existing ones (R-9).** The governed
   marker (`governed_conflict:`) becomes a prefix test at the engine-authored start of the THROW text (the
   builder measures the live THROW wrapping and anchors to it); ASSERT / coercion / recursion-depth keep their
   phrases but are checked LAST, after every anchored marker, so an echoed value can only ever move a text
   INTO one of those three — which is where an echoed-value text belongs anyway (an ASSERT text carrying a
   hostile value IS an ASSERT). Property, pinned GENERATED (KB widened): ∀ marker phrases × ∀ live host shapes ×
   both paths, the phrase injected as the echoed value never moves the class.
4. **Confinement proven by MUTATION, not by prose (MP-1 KA + R-8):** patch `_classify_engine_error` to
   "unspecified" → the U collision loses the class on BOTH raise sites, and an ASSERT the patched classifier
   labels unique GAINS it on both; patch `_domain_rejection_error` to return the base class → both identity
   legs lose it. Two shared things, each mutated once; a raise site with a private copy of either fails a leg.
5. **Pin-the-miss (the residual bound):** each live shape's text starts with its engine noun on the pinned
   engine version; and U-sdk/U-txn carry no typed fields. Trigger: either changes → re-anchor / add the typed
   branch and delete the pin. Docstring names the strike count (§0).

---

## §3 MP-4 / S8 — the scanner's domain is keyed per HANDLER; D6 restored (a DUAL loss)

- **Key:** `file::function::<handler position>` (lineno or ordinal), never `file::function`. Both exact sets name
  HANDLERS; two domain handlers in one function are two entries. KD (count handlers with the scanner's own
  parts; one entry each) lands.
- **F-4's scope restored (DUAL D6):** every `except` clause whose caught closure contains exhaustion, anywhere in
  a listed door's FUNCTION (any `try`), must be a bare `raise` — the OLD pin's quantifier. a28b's "PRESERVED,
  WIDENED" (U-9) narrowed it to the door's own try and let S8 (`findings.annotate`'s second try re-reading after
  exhaustion and RETURNING a row — a #102 false clear) through: that is a DUAL loss, recorded as the a28b
  author's erratum, repaired here.
- **R-2 (S4):** the re-read definition gains *a `SELECT` literal in the handler's OWN body* (`_issues_a_read
  (handler)`) beside the same-class-method form — one line; 63c-i-a's. The remaining bound (a `SELECT` built
  without a literal) is am-7's named one; the runtime leg covers it.
- **S1–S3 CONFIRMED as 58's fate classifier** (58 am-10 Reading (i): closure ∋ exhaustion whatever the
  spelling; bare `except:` counts). Rider: the CAS scanner's docstring states the bound ("subclass-only; a
  superclass / tuple-valued / bare catch is the fate classifier's"), and the lead confirms 58-r4 lands am-10 —
  until it does, NO instrument sees those shapes and the lead report carries that as an open row.

---

## §4 Fold items confirmed (a28c)
- **R-4:** the gating pin's field→read partition is DERIVED — each `MigratePreconditionCounts` field carries its
  read tag (`json_schema_extra={"read": "agent" | "message" | "operator"}`), the pin iterates the tags, and a
  field without a tag fails the completeness leg (the name-suffix rule and its vacuous `_read_of` go).
- **am-34** stands (the adversary's §AM34 rows change no verdict); its F-5 fix and the `"empty"` member fold into
  a28c as ruled.
- **R-7 / #514** (a teammate's staged index sweeps into a bare commit and poisons `scratch_copy.sh` copies):
  an instrument/process finding for the lead; I note only that `scratch_copy.sh` should `git reset --hard HEAD`
  the copy's index as part of its provenance assertion — the law's instrument should do what the law says.

## §W
| # | item | gate |
|---|---|---|
| 1 | C2: generated relation-set product × mint orders, both verdicts; seam mutation pin; KE | GATING |
| 2 | R typed on both paths (`_failed_statements` keeps the dict; `parse_query_error`); record text pair deleted | GATING |
| 3 | U prefix-anchored, first; every marker anchored/ordered; KB generated over phrases × shapes × paths; KA + the `_domain_rejection_error` mutation; pin-the-miss | GATING |
| 4 | scanner keyed per handler; F-4 scope restored; R-2's one-line re-read widening; S1–S3 bound stated | GATING |
| 5 | R-4 derived read tags | GATING (fold) |

## §E — operator-visible
- **Loop cost:** 13 contract revisions on 63c-i-a. §0 makes a28c the last contract round for the two struck
  properties by RULE: a fourth strike → pinned bound, no round. If you would rather bound them NOW, the bounds
  would be: C2 — "the gate is pinned on the foreign side and one not-foreign shape; trigger: a multi-keep
  principal denied in production"; RS-5 — "substring markers; trigger: a misclassified rejection in the
  server log". I recommend against: both closures above are one generated pin each, and the a28c author is
  already folding.
- §2 item 1 changes `_failed_statements`' record shape (a driver internal every transactional caller rides —
  the shape is consumed only inside `_txn`, by my reading). Pre-authorized under the pre-production law; here for
  you to pull.

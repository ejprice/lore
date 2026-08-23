# REPORT-adversary-61a-w2

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK (RE-GRADE 2 — spelling-agnostic guard + pinned bound)
- state: **done** — re-graded the round-3 delta empirically (two-layer reference build, probe-module reach scan, pinned-bound discrimination probe).
- **VERDICT: CONTRACT SUFFICIENT.** The round-3 revision closes my round-2 separate-clause gap: the detector now keys on the passthrough-first POLICY spelling-agnostically (`_bare_reraise_passthrough_classes` unions the transport classes over all bare-reraise handlers before the translate). The ONLY residual is the conditional-reraise-inside-one-handler evasion, and it is an **HONESTLY-PINNED ACCEPTED BOUND** (#137/#138 class) — not a gap — with a threat model, a re-open trigger, and proven discrimination. This satisfies the lead's SUFFICIENT criterion.
- round-3 delta results (all VERIFIED): (1) two-clause full clone now REDS the reach SCAN (probe module), single-tuple still reds, partial-passthrough (only Conn) EXCLUDED in BOTH spellings, scan still finds EXACTLY the 9 at HEAD, `transitive_blockers` still excluded · (2) the conditional-reraise bound is honestly pinned (GREEN today; REDS when I extended the detector to catch it — proven discrimination; positive control: the both-spellings test proves the detector flags real clones) · (3) satisfiability **76 passed** on my two-layer reference (75 + the new bound pin); RED@HEAD (reach: 9 sites; lorerunes: 20 failed, `reclassify` absent).
- Packages considered: none — confirmed (stdlib `contextlib`; no library for app-specific error-translation policy).
- Reuse ledger: none (adversary writes no reusable symbol).
- Graded: `fb68427` · HEAD-at-report: `fb68427` · SAME (contract revised in the working tree, uncommitted; graded at `fb68427`).
- decisions-needed: none. The conditional-reraise bound is accepted (reach STOP-rule); its re-open trigger is in `test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`.
- receipt POINTERS: round-3 §RG2-1/2/3 · round-2 detail §"RE-GRADE (revised contract…)" · round-1 §"ROUND 1".

---

# RE-GRADE 2 (round-3: spelling-agnostic guard + pinned bound, 2026-08-23)

The author closed my round-2 separate-clause gap and pinned the next-spelling-down as an accepted bound. Scope: verify ONLY the delta (the lead's (1)–(3)). Reference: my round-2 two-layer build in `/tmp/adv-61aw2b` (production seam unchanged between round-2 and round-3 — only the contract's detector changed), with the round-3 contract test files copied in; **`loremaster.__file__` = `/tmp/adv-61aw2b/loremaster/loremaster/__init__.py`**.

## RG2-1 — the spelling-agnostic detector: VERIFIED
- **`_try_has_full_idiom` now keys on the POLICY, not the spelling.** `_bare_reraise_passthrough_classes` returns the `{Conn, Contention}` subset a bare-reraise handler covers; `_try_has_full_idiom` unions it over all handlers BEFORE the pure-translate and requires `{Conn, Contention} ⊆ covered`. Tuple and two-clause both satisfy it; a partial (one class) does not.
- **Empirical reach SCAN** (probe module `_adv_probe2.py` dropped in the package, three functions): the scan flagged `two_clause_full_clone` (my round-2 evasion — now caught ✓) and did **NOT** flag `partial_two_clause` (only Conn) nor `partial_tuple` (only Conn in a tuple) — partials correctly excluded in BOTH spellings. The single-tuple clone still reds (round-2 + the detector control).
- **Still exactly the 9 at HEAD** (ran the reach scan on the real tree): the same 6 keep + `principal_keys.mint` + 2 principal — no two-clause clone was lurking, `transitive_blockers` still excluded, allowlist still empty.
- The detector's own control `test_the_detector_keys_on_the_policy_in_BOTH_house_spellings` (full_tuple/full_two_clause True; translate_only/wrong_order/cas/partial_tuple/partial_two_clause False) PASSES at HEAD.

## RG2-2 — the conditional-reraise bound: HONESTLY PINNED (accepted, not a miss)
The one shape that still evades — a conditional re-raise INSIDE a single `except SurrealStoreError` handler (`if isinstance(e, (Conn, Contention)): raise` then `raise Domain(...) from e`) — is pinned by `test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`. I verified it is a real, discriminating pin, not decoration:
- **GREEN today** — the detector returns False for the conditional shape (part of the 76 passed), and the pin asserts exactly that, carrying the threat model (honest house-spelling copy-paster, not a deliberate obfuscator) + a re-open trigger + a "delete this pin if you close it" instruction.
- **Proven discrimination** — I temporarily extended the scratch detector to catch the conditional shape (a two-line `if isinstance(_s, ast.If)` branch); `test_the_conditional_reraise_shape_is_a_KNOWN_BOUND` then **REDS** (its `is False` assertion fails). So the pin fails the instant the bound is closed, forcing the next engineer to delete it and say so — exactly the PIN-THE-MISS contract.
- **Positive control** — the sibling `test_the_detector_keys_on_the_policy_in_BOTH_house_spellings` proves the detector is not vacuously False (it flags both house spellings), so the bound pin's GREEN is meaningful.
- This is the reach STOP-rule applied correctly: the conditional shape is a non-house structure an honest copy-paster would not write; chasing it is the reach spiral CLAUDE.md forbids. Accepting it as a named, discriminating bound is the right call — I do NOT flag it as a miss.

## RG2-3 — satisfiability + RED@HEAD
- Correct two-layer reference → **`76 passed`** (20 lorerunes + 56 seam; the +1 over round-2's 75 is the new bound pin), `-n auto`, `loremaster.__file__` inside the scratch.
- RED@HEAD: reach scan lists the 9 clones; lorerunes revised contract → `20 failed` (`reclassify` absent, clean `_load_reclassify` fail).

## VERDICT: CONTRACT SUFFICIENT
The reach guard is now spelling-agnostic (the round-2 evasion reds), still property-derived and finding exactly the 9, mutation-provable at both seam layers, and satisfiable (76 passed) / RED@HEAD. The sole residual — the conditional-reraise shape — is an honestly-pinned, threat-modeled, discrimination-proven accepted bound, which by the lead's own criterion is SUFFICIENT. I tried to break it (two-clause reach scan, partial exclusions, bound-discrimination probe) and could not. Builder release is not blocked by anything I found.

---

# RE-GRADE (round-2: revised contract, 2026-08-23)

The author landed the fix for my round-1 reach finding via two sidecar rulings (D2 two-layer seam; addendum-2/-4 shape-keyed guard + route `principal_keys` + preserve `transitive_blockers`). Scope: verify the delta (the lead's (a)–(d)). Scratch: `/tmp/adv-61aw2b` via `scratch_copy.sh`; **`loremaster.__file__` = `/tmp/adv-61aw2b/loremaster/loremaster/__init__.py`**, **`lorerunes.__file__` = `/tmp/adv-61aw2b/lorerunes/lorerunes/__init__.py`** (runs its own code). My two-layer reference: `lorerunes/lorerunes/reclassify.py` (Layer 1, keyword-only `reclassify(*, passthrough, catch, make_error)`), `__init__` re-export, `_txn.wrap_store_rejection(domain_error, context)` (Layer 2, plain function → call-time `reclassify` lookup), and all 9 methods routed via `with wrap_store_rejection(...)`.

## RG-A — REACH (the fixed instrument): verified, with ONE gap
- **Property-derived, not a hand-list.** `_full_idiom_sites()` `rglob`s EVERY `loremaster` module and AST-matches `_try_has_full_idiom`. My round-1 finding (the 2-store `_CASES` hand-list) is genuinely gone.
- **Finds EXACTLY the 9 at HEAD** (ran the reach detector on the real tree): `keeps.py` `{create_keep, add_household_member, remove_household_member, set_rank, set_keeper, delete_keep}` + `principal_keys.py::mint` (L412) + `principals.py::{create, set_subject}` — no more, no fewer.
- **A NEW verbatim (tuple-form) clone reds** — dropped a probe module into the package with a tuple-form full-idiom function → the reach pin flagged `('_adv_probe_store.py', 'tuple_clone_new_store', …)`. ✓
- **Correct exclusions verified against the REAL sites** (ground-truthed each): `tasks._transition` / `tasks.supersede` / `findings.append` = CAS (multi-statement translate body → not a pure-translate handler); `tasks.transitive_blockers` = wrap-everything (NO passthrough-first, sole translate → excluded BY SHAPE, ledgered #408); `floor_calibration` = fence-verdict (multi-statement translate body). The detector's own synthetic controls (`test_the_detector_keys_on_the_full_idiom_not_the_translate_line`, `test_the_allowlist_is_empty`) PASS. Allowlist is empty.
- **⚠ THE GAP (empirically proven, RG-A reproduction).** The SAME probe module carried a second function, `separate_clause_clone_new_store`, that is the identical #400 policy spelled with **two separate passthrough clauses** (`except SurrealConnectionError: raise` / `except TxnContentionExhaustedError: raise` / `except SurrealStoreError as e: raise Domain(...) from e`). The reach pin flagged the tuple clone but **NOT** the separate-clause clone — `_is_passthrough_first_handler` requires `{SurrealConnectionError, TxnContentionExhaustedError} <= names` for a SINGLE handler, and two separate handlers each carry a singleton. This spelling is **already in the tree** (`tasks.py:1668/1996`, `findings.py:1023/1079` use separate passthrough clauses for their CAS wraps), so it is an honest variant, not a contrived evasion. **The pin that should exist:** widen `_is_passthrough_first_handler` to accept the union-of-separate-clauses spelling (a probe: a future separate-clause pure-translate clone must red the reach pin). This is a 7th instance of the documented instrument-lesson shape ("keyed on the tuple form → defeated by the separate-clause spelling").

## RG-B — ROUTING-IS-NOT-SHARING over all 9 (the two-layer mutation): holds
Reverted `principal_keys.mint` to a **behaviour-correct private copy** (local `try/except`, not routed). Seam contract result: **5 pins RED** —
- `TestNoFullIdiomCloneOutsideTheSeam::test_no_full_idiom_wrap_appears_outside_the_seam` (reach — mint's local idiom reappears)
- `TestTheRoutedSetIsDerivedAndComplete::{test_the_routed_set_equals_the_invocation_map, test_the_routed_set_equals_the_known_wrapping_verbs}[principal_key]` (coverage)
- `TestSharingProvenByMutation::test_dropping_LAYER1_reclassify_moves_every_routed_path[principal_key-mint]` (Layer 1)
- `TestSharingProvenByMutation::test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path[principal_key-mint]` (Layer 2)

**GREEN throughout (positive controls):** every behaviour-preservation pin for `principal_key-mint` (the private copy IS behaviour-correct — proving the pins catch pure not-sharing), and the ENTIRE keep + principal sides. The **two-layer** proof is real: BOTH the Layer-1 (`reclassify`) and Layer-2 (`wrap_store_rejection`) mutations move the routed path. The rejected option (b) — a store calling `reclassify` DIRECTLY with a cloned taxonomy — is caught by the Layer-2 mutation + the coverage pin (it would not reference `wrap_store_rejection`, so it drops out of the routed set): construction-verified.

## RG-C — `principal_keys` routed correctly
In the reference build `mint` routes through `wrap_store_rejection`; behaviour preserved (its raw-store→domain and transport-passthrough pins are among the 75 passed). The private-copy revert (RG-B) reds precisely, confirming the pin sees it.

## RG-D — Satisfiability + RED@HEAD
- Correct two-layer reference → **`75 passed`** (20 lorerunes + 55 seam), `-n auto`, on my own build (`loremaster.__file__` inside the scratch).
- RED@HEAD: reach detector on the real tree lists the 9 clones (RED); lorerunes revised contract at HEAD → **`20 failed`** (`reclassify` absent, clean `_load_reclassify` fail — right reason).
- (Round-1 already proved the lorerunes wrong-build discrimination; the semantics are unchanged, only the signature — `make_error` factory + keyword-only — which the new lorerunes pins cover.)

## VERDICT: CONTRACT INSUFFICIENT
The reach fix is verified and genuinely strong — my round-1 finding is closed, the guard is property-derived, finds exactly 9, catches a verbatim new clone, and is mutation-provable at both layers. The SOLE remaining gap is the separate-clause passthrough spelling (RG-A): a full-#400-policy clone in a spelling already used in the tree evades the detector. Resolution is **cover it** (widen `_is_passthrough_first_handler`, cheap) **or name it** (an explicit pinned bound + a threat-model docstring line, per the reach STOP-rule) — operator/lead's call. Nothing else blocks the builder; if the lead judges this a pinned-bound rather than a fix, that closes the gate too.

---

# ROUND 1 (original grade of the pre-revision contract — retained for provenance; SUPERSEDED by the RE-GRADE above)

The round-1 finding (the reach guard's cross-store reach was a 2-store `_CASES` hand-list, with ≥4 identical clones outside it) is what the revision fixed. The round-1 empirical receipts (lorerunes 5 wrong builds; the routing-not-sharing private-copy proof; catch-all 16 transport pins; corpse sweep; purity control) established the contract's within-scope discrimination and remain valid for the pre-revision structure. The revision generalised the reach from a store hand-list to a module-wide shape scan and expanded the routed set from 8 to 9 (adding `principal_keys.mint`, the true clone my round-1 §E identified). The store-granularity gap is closed; the finer spelling-granularity gap (RG-A) is what remains.

Key round-1 receipts (pre-revision, at `fb68427`):
- P1 lorerunes wrong builds: catch-all→3 ordering pins, from-error→chain pin, context→context pin, bare-except→2 over-catch pins, swallow→5 pins; correct→15 passed.
- P1c routing-not-sharing: private-copy `principals.create`→4 pins red, behaviour + keep side green.
- Behaviour: catch-all→16 transport pins red; correct→41 passed.
- Cross-store finding (now FIXED): `principal_keys.py`, `tasks.py`, `findings.py`, `floor_calibration/store.py` cloned the policy outside the then-2-store reach. The revision routes `principal_keys` and excludes the CAS/wrap-everything/fence sites BY SHAPE.

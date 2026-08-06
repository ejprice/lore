# REPORT-closer-04b5-selfecho-1 — route the bare-ValueError SELF-ECHO doors (operator all-or-nothing)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore loaded first try (`ToolSearch "+lore"`, no #334
flake); registered `closer-04b5-selfecho-1` (session pkt04b5, builder, opus-4-8) + drained (empty
inbox). Full tool access — Bash/pytest/mypy/ruff present; ran the widened AST scan + byte-check +
mutation proof as my OWN instruments (see §RECEIPTS; the scan is committed as the widened contract
leg). grep is the honest tool for the anchor-free `!r` sweep (CLAUDE.md dogfood case (a)/(c) —
non-symbol textual seam + cross-cutting map); used it, said so, individual per-site verdicts (no
"all remaining are X"). No lore weakness forced a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done-with-deviations** — all self-echo doors routed; enforcement fork surfaced (I
  proceeded with my recommendation); one out-of-scope render self-echo surfaced (map.py:487).
- deviations: (1) **enforcement fork** `q:selfecho-enforce` — signalled to lead, proceeded with the
  recommended two-class enforcement (§FORK). (2) **map.py:487** — a RENDER self-echo of
  `changed_since` via `.format()`, closed-vocab-safe + outside my error-half scope; SURFACED, not
  routed (§DEVIATIONS).
- Packages considered: none — no mechanism specified (reused the in-tree `render_attributed` seam,
  the ONE-IMPLEMENTATION move; imported it into read_file.py/map.py — no circular risk, render
  imports only sanitise).
- Graded: this is my own build (no verdict rendered on another's artifact); base-derived at
  HEAD `4fc9f7a`.
- decisions-needed (lead): ratify or redirect the enforcement fork (§FORK); rule on the map.py:487
  render self-echo (§DEVIATIONS) — it may be a `.format()` blind spot in the render-half instrument.
- receipt pointers: routing map §ROUTING · enforcement §ENFORCEMENT · RED→GREEN + forward mutation
  §RECEIPTS · byte-check §RECEIPTS · gates §GATES · non-doors NOT routed §NON-DOORS.

---

## THE ENFORCEMENT FORK (q:selfecho-enforce) — surfaced per brief + brief-base §2/§5

**Empirical finding (widened AST scan): the self-echo residual splits into TWO classes with
DIFFERENT tractability, and the brief's "cover `ValueError`" is inconsistent with its own target
set** (which names `tier`=lore_read=`ReadFileError` and `changed_since`=diff=`MapChangedSinceError`
— NEITHER is a `ValueError`).

**Class 1 — custom caller-boundary error classes (CLEANLY reddening-scannable):**
`ReindexTierError(ValueError)`, `MapChangedSinceError(Exception)`, `MapFocusNotFoundError(Exception)`,
`ReadFileError(Exception)`. Every one of their raise sites interpolates ONLY caller params
(tier/path/changed_since/focus) or ints — **zero system-value sites** (verified over all sites). So
they were added to the scan's base set exactly like the existing seven → true reddening
completeness, **no exemptions, no infra over-reach** (`SurrealStoreError`/`MapRebuildingError`/
`ProbeGateError`/`SchemaRebuildingError` subclass none of the eleven → not pulled in).

**Class 2 — bare `ValueError` (OVERLOADED → name-blind-UNSOUND for a full reddening scan):**
comms action/kind/set_status, memory kind, findings action, rollup `since`. Bare `ValueError` is
used BOTH for caller-input rejects AND internal invariants (chunker `owner`, ext-tool
`param.kind.description`, config `self.tier`, symbols `self.status`, `tasks._validate_done_summary`
`target`). An is-a-parameter refinement cleanly drops 8 of 9 false positives, but **`tasks.py`
`target` is irreducible**: a bare-Name *parameter* in door_vocab yet SEMANTICALLY closed-vocab (a
transition status validated by `_validate_transition` one call earlier — a spurious collision with
lore_impact's free-text `target`). No name-blind syntactic property separates it from a real
`{action!r}`; distinguishing needs validation-gate dataflow = the P-F/P-S-scale machinery the brief
says NOT to build for a self-echo class. Same for `store/surreal.py:1263` (`tier`, infra
`SurrealStoreError` on a corrupt row, closed-vocab + #133 over-reach if scanned).

**MY DECISION (proceeded, non-blocking — brief authorises "recommend the fallback if the clean
widening is not tractable"):** Class 1 → **base-extend** the scan 7→11 (REDDENING; brief-preferred,
clean). Class 2 → the brief's **sanctioned BOUNDED PIN-THE-MISS**: route every site + behavioural
containment pins (forgery→neutralised, mutation-proven) + a named re-open trigger. **Recommendation
to the lead: keep the bounded pin for bare `ValueError`** (Class-1 base-extension already delivers
reddening for the higher-structure classes; operator ruled these self-echoes "lower-stakes but IN").
Redirect if you want Class 2 also given a reddening scan (is-a-parameter + one pinned `target`
exemption) despite the "no elaborate machinery" caution.

## §ROUTING — every routed site (29 raise sites; `f"...{p!r}"` → `f"...{render_attributed(p)}"`)
Re-derived at HEAD `4fc9f7a` by anchor-free grep + the widened AST scan (audit list was a starting
point). `render_attributed`'s inline delimiter self-closes (fence_width sizes it longer than any
inner run) — byte-safe per §ROUTING-RULES #1.

**Class 1 — CUSTOM caller-boundary errors (11 sites; enforced by the reddening scan):**
- `read_file.py` `ReadFileError`: `_unknown_tier_error` (tier), `_missing_file_error` (path+tier),
  `_containment_error` (path+tier), `_resolve_span` ×3 (tier+path each; ints left).
- `map.py`: `MapChangedSinceError` (changed_since) · `MapFocusNotFoundError` (focus ×2).
- `server.py`: `ReindexTierError` ×2 (tier) · `MapChangedSinceError` (changed_since).
- Added imports: `from loremaster.render import render_attributed` in read_file.py + map.py.

**Class 2 — bare `ValueError` (18 sites; bounded PIN-THE-MISS):**
- `server.py` comms: unknown action, required-arg action, limit-range action, set_status+action,
  `_comms_foreign_param_error` ×2 (action).
- `server.py` findings: unknown action, batch `_resolve_or_acknowledge_many` ×3 (action), items-omit.
- `server.py` tasks: since-omit / limit-omit / max_depth-omit / items-omit / unknown-action (action),
  rollup `since` teaching error.
- `server.py` memory: unknown kind.

## §ENFORCEMENT (in `test_link5_render_containment.py`)
- `_served_error_bases()` 7→11 (+ReindexTierError, MapChangedSinceError, MapFocusNotFoundError,
  ReadFileError); `_domain_error_names()` scans server/map/read_file too (issubclass filter keeps
  their non-boundary siblings out). Population-guard renamed
  `test_the_served_error_bases_name_the_expected_population`, expects the 4 new names.
- Class docstring bound (3) rewritten (why bare `ValueError` is UNSOUND for a reddening scan).
- New `TestBareValueErrorSelfEchoesAreContained` — drives FORGERY + HOSTILE_MULTILINE through the
  store-free comms unknown-action reject + the pure `_comms_foreign_param_error` staticmethod;
  asserts `not _leaks` + marker round-trips. Carries the named re-open trigger.

## §RECEIPTS
- **RED→GREEN (the widened scan is non-vacuous):** before routing, the 11-base scan named exactly
  **17 door-entries** (read_file tier/path, map changed_since/focus, server tier/changed_since) +
  the 2 behavioural pins RED (forgery leaked via `!r`). After routing: **all GREEN**.
- **Forward mutation proof:** un-routed read_file `_unknown_tier_error` → scan RED naming
  `read_file.py:207 — ... 'tier' OUTSIDE the containment seam`; restored byte-exact → GREEN.
- **Byte-check (brief VERIFY-2), 2 custom-class sites, hostile `custom`+newline+row-forge+backtick-runs:**
  `read_file unknown-tier` leaks=**False** (`unknown tier `````custom`…`, delimiter sized above the
  run); `map changed_since` leaks=**False**. Plus the behavioural pin covers 2 comms sites (leaks=False).

## §GATES
- **04b5 contract** (`test_link5_render_containment.py` + `test_task_read_surface.py`, `-n auto`):
  **253 passed, 1 skipped** (≥251; +2 my behavioural pins).
- **Suites the routed sites live in** (comms/mcp_server + map/read_file/diff + task_ledger, combined,
  `-n auto`): **2049 passed, 1 skipped, 0 failed**. Fixed **9 exact-text pins** (P8d — they
  certified the OLD `'value'` repr; updated to the render_attributed form).
- **mypy** (`scripts/typecheck.sh`): **ZERO in my touched files** (grep-confirmed 0); 102 remaining
  all in 8 auth-WIP files (#333, pre-existing/operator-accepted). My initial 2 SimpleNamespace
  arg-type errors fixed (typed `Any`, as the comms `_harness`).
- **ruff** (`uv run ruff check` on all 6 touched code files): **All checks passed**.

## §NON-DOORS — verified NOT routed (per audit ruling + brief; each individually)
- `tasks.py:1838` `{target!r}` — closed-vocab (`_validate_transition` rejects non-status first);
  spurious collision with impact's `target`. NOT a live door.
- `store/surreal.py:1263` `{tier!r}` — infra `SurrealStoreError` on a corrupt row; tier is a
  resolved configured tier (closed-vocab) + #133 over-reach. NOT scanned, NOT routed.
- `server.py:641/658` `{owner!r}` (chunker suffix-owner, a local), `server.py:10471`
  `{param.kind.description!r}` (introspection), `config.py:309/318` `{self.tier!r}` (config value),
  `symbols.py:900/906/912` `{self.status!r}` (internal enum), `scout.py:918` `{kind!r}` (internal
  command kind), `findings.py:592` `{value!r}` (blank-only, not a registered param), all `*limit*`
  (int). Excluded by construction (attribute/local, or param not in door_vocab).

## §DEVIATIONS
1. **Enforcement fork** (§FORK) — surfaced to lead as `q:selfecho-enforce` signal; proceeded with
   the recommended two-class enforcement.
2. **map.py:487 — RENDER self-echo of `changed_since` via `.format()`** (`_CHANGED_SINCE_SUMMARY_
   TEMPLATE.format(since=changed_since, …)` with `{since!r}`). This is OUTSIDE my error-half scope
   (it is a RENDER, not an error). It is currently **closed-vocab-safe** — line 487 is reached only
   after `changed_since` resolves to a real server-minted snapshot id; a forgery is rejected upstream
   by the (now routed) `MapChangedSinceError`. But two things worth the lead/render-half owner's eye:
   (a) it is a caller-param self-echo the error-half scan does not cover; (b) it is a `.format()`
   template, so if the render-half P-U instrument scans only f-string interpolations it may be a
   BLIND SPOT. SURFACED, not routed (out of scope + closed-vocab-safe + would need a template change
   not a simple wrap). Recommend the lead route the render-half owner to confirm P-U covers `.format()`.

## §STORE
No store/schema/DDL change (string/render edits over caller params only). `docs/reference/
surrealdb-31-capabilities.md` not consulted — no store change to adjudicate.

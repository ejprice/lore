# REPORT — lead (regression-fix wave, session regfix-20260817)

lead-base v6 read

## SUMMARY BLOCK

- **Verdicts acted on:** `5c8230c` (cold audit graded the working tree atop this) -> HEAD-when-acted `5c8230c` -> **SAME** (no STALE acted on; committed as `edb1a03` = `5c8230c` + the exact audited edits).
- **Directives:** 0 ledger / 0 wake / 0 prose-duplicated (all agent instruction front-loaded in spawn briefs; no steering messages sent).
- **Rulings:** 5 in a committed artifact (commit `edb1a03` body + this report) / 0 body-only.
- **Agents:** 4 spawned / 4 ledger-retired / 0 left-running.
- **Uncommitted at stop:** 0 files.

## MISSION

Operator task: examine ALL failing tests; separate incomplete-packet failures from regressions;
identify the regressions and orchestrate a fix. Lead writes no code; a sonnet agent runs the full
harness; coordination via lore comms.

## WHAT WAS FOUND

Full suite at HEAD `5c8230c`: **451 failed + 135 errors** (9878 passed, skill suite 117/0 clean).

- **446 failed = the incomplete packet** — auth/posture/roster WIP (packets 39/45/48/49):
  ImportError on not-yet-built symbols + `LoreConfig extra_forbidden` on new `auth`/`google_oauth`
  keys. RED_ADJUDICATED in `scripts/pending_contracts.yaml` (finding #333). **Not regressions.**
- **140 non-reconciling = 5 regressions** from recent on-branch packets. **0 store-artifacts**
  (no #336/3.2.4 involvement), **0 hidden auth-WIP**. All are TEST-code / docstring — **no
  production serving code is defective** (production `agents.py` and `surreal.py:1254` proven correct).

| Cluster | Tests | Root cause | Packet | Fix |
|---|---|---|---|---|
| A | 135 err (`test_message_ledger` 130 + `test_comms_footer` 5) | `_seed_agents` routes multi-statement DDL through single-statement `_query`; pkt-07's NEW `multi_statement_violations` guard (147be46) correctly flags it (store §3) | 07 | test helper → `execute_transaction` (mirror prod); guard kept armed |
| B1 | `test_secret_typing` (1) | 3 spike probes mint `SecretStr` outside pkt-42 allowlist | 07/07a | allowlist (API requires SecretStr) + re-open trigger |
| B2 | `test_secret_typing` (1) | `fastmcp_migration_spike` builds MCP Bearer auth the x-api-key seam can't express | 59 | exact-path exempt + re-open trigger |
| C | `test_surreal_harness` (1) | stale harness docstring counts (54→56 importers, 37→40 callers) | 47a | re-derive both counts |
| D | `test_ast_reach_helpers` (1) | new whole-tree parser clone `_find_indexer_construction_sites`; shared parser can't express its member-scripts reach | 47a | allowlist + re-open trigger |
| E | `test_comms_footer` (1) | `surreal.py:1254` interpolates `entity_table` (controlled table name; can't param-bind) | 47a | KNOWN_SAFE_DOORS adjudication (mutation-checked) + re-open trigger |

Four of five are the repo's own AST/checked-variable invariants firing exactly as designed on a new
site a recent packet landed without migrating/allowlisting/adjudicating.

## ORCHESTRATION

1. `harness-runner` (sonnet) — full-suite census + skill suite. Confirmed 451f/135e; skill 117/0.
2. `regr-diagnostician` (opus-4.8, read-only) — root-caused each of the 140 to its introducing
   commit; classified 5 regressions / 0 artifacts / 0 auth-WIP; verified the 446-reconcile.
3. Lead ruled each cluster (fix, never weaken the invariant; allowlist only where the preferred
   fix is genuinely inexpressible, evidence-backed + re-open trigger).
4. `regr-fixer` (opus-4.8) — implemented all 5; 665/0 on the affected set; mutation-checked E.
   Caught a SECOND stale count (C's 37→40) the "re-derive both" rider surfaced.
5. `regr-coldaudit` (opus-4.8, fresh context, REFUTE) — **GO**: full suite 451f/135e → **446f/0e**
   (residual = identical auth-WIP bucket, zero new reds); independently refuted D/E/B2's
   justifications (all hold); confirmed A mirrors prod, guard untouched, B1/C.
6. Lead random-receipt spot-check (D file): 9 passed. Committed `edb1a03`.

## RESULT

- **Suite non-auth-green.** Full suite now **446 failed / 0 errors** — the 446 are exactly the
  incomplete-packet auth WIP; **every regression closed, zero new red.**
- **No deploy** — test-only; production artifact unaffected (precedent: pkts 07/02a/03a).
- #384 resolved with SHA `edb1a03`; #385 unaffected (still latent-by-design).

## RESIDUALS (surfaced, not buried)

- **B2 file-level exempt** (`_FASTMCP_SPIKE_EXEMPT`): exempts all future auth construction in
  `scripts/fastmcp_migration_spike.py`; re-open trigger keyed on credential-NATURE, not site-count.
  Cold-audit judged acceptable for a throwaway spike. A future fake-token site there would be
  silently exempt. Tighter alternative if ever revisited: site-level exempt, or delete the spike
  (pkt 59 is shipped).
- The 446 auth-WIP failures remain RED_ADJUDICATED — they discharge when packets 39/45/48/49 build.
  This wave did not touch them (correct: incomplete packet, operator-owned).

# REPORT-lead-packet61 — Authorization PDP + audit (the load-bearing core of the 60–65 track)

lead-base v6 read

## SUMMARY BLOCK

| field | value | pass |
|---|---|---|
| `Verdicts acted on:` | every adversary/cold-audit/security verdict acted on at its graded HEAD → SAME (each re-verified by a lead re-run or receipt before acting; the 61b-w2 GO acted on at `5b50063`) | ✅ no STALE acted on |
| `Directives:` | spawn-briefs front-loaded / sidecar follow-ups: native wake + `lore_comms` durable / 0 prose-duplicated | ✅ duplicated = 0 |
| `Rulings:` | committed ruling doc (`docs/design/2026-08-22-packet61-pdp-audit-rulings.md`: Forks A–L + FR-4 + Fork-I/G/F-H addenda + R1) / 0 body-only | ✅ body-only = 0 |
| `Agents:` | 25 pkt61 worker agents non-retired at close-out → all 25 ledger-retired (`heartbeat status=retired`) / 0 left running (fleet shows the pkt61 session as `lead-61` only) | ✅ retired = live-set, left-running = 0 |
| `Uncommitted at stop:` | 0 files (tree clean at `5b50063`, before this report) | ✅ 0 |

_Spawn total across the packet's 7 waves is larger than 25 (earlier waves' agents aged into `retired` before close-out, across a context-compaction boundary); the verifiable invariant is that the pkt61 session now shows only `lead-61`._

## Outcome

Packet 61 (Authorization PDP + audit) is **CODE COMPLETE — COMMIT-ONLY** on `feat/surreal-unification`
(deploys with 39+60+62–65 at packet 65's single joint cutover; NO 61-alone deploy). Split into
**61a (Foundations + Audit)** and **61b (PDP engine + resolver + coverage)**; commits `84d20a3..5b50063`.
Full pipeline (probe → contract → contract-adversary → build → cold-audit → **dedicated security-auditor**
on the PDP core → commit) Opus 4.8 end-to-end + a long-running Fable design sidecar; all coordination
on `lore_comms`; operator offline for the build (design forks ruled by the sidecar within delegated
authority, operator-ratified where flagged).

Delivered: **one in-process authorization brain** in `lorerunes.pdp` — a closed predicate IR
(ScopeEq/OwnerPrincipalEq/OwnerAgentEq/ScopeInKeeps/And/Or/AllRows/NoRows) with two TOTAL interpreters
(`to_surql` + `matches`), so the single-brain invariant `authorize(s,a,r).allowed ≡
authorize_filter(s,a).matches(r)` holds **by construction** (`authorize = authorize_filter().matches()`),
pinned by a **LIVE-STORE 3.2.4 differential oracle** (never a mock); admin short-circuit a node OF the
filter; audit-obligation a flag on `Decision`; frozen stdlib `Subject`/`Resource`/`Decision`. Plus the
append-only ADMIN-EXEMPT `audit` store (`loremaster.audit`) with §9 identity-at-write, the visible-Keeps
resolver (`KeepStore.list_keeps_for_member` + `resolve_visible_keeps`), and the default-GOVERNED
tool-population classification registry.

Gates at completion (HEAD `5b50063`, solo): **currency PASS** (typecheck/ruff/pytest green-or-owned);
cold audit full suite **8798 passed / 0 failed**; all mutation proofs RED-and-restored on independent
instruments.

## Commit arc

- `84d20a3` design ruled + split 61a/61b · `b2f7790` FR-4 keeper-delete ruling
- **61a-w1** `66b795c` #402 keeper-on-principal-delete refuse-while-keeping (+ admin verbs; member_of auto-cascade probe; RED_ORPHANED→GREEN) · `fb68427` archive
- `42cdac0` Fork-I addenda · **61a-w2** `6ad460b` #400 shared engine-rejection wrap seam (`lorerunes.reclassify` + `_txn.wrap_store_rejection`) · `f87e774` archive
- **61a-w3** `708c74e` #398/#399 structural fold-coverage invariant · `e92bd0f` archive
- `f904423` Fork-G addendum · **61a-w4** `4f36782` append-only ADMIN-EXEMPT audit store + §9 identity-at-write · `99a912f` archive · `7aab121` INDEX 61a CODE COMPLETE
- **probe** `c6c6bc2` #413 read-filter index behaviour (IN-inside-OR TableScan trap) · `599354a` archive
- `136fdab` Fork A/C/D + B/D addenda · **61b-w1** `3b0894e` the PDP core (IR + oracle + security fixes #416/SEC-F2/F3/F4/R4) · `1048138` archive (incl. security-auditor)
- `af04b4a` sidecar rulings Fork F/H + R1 · **61b-w2** `650b37f` visible-Keeps resolver · `252c221` tool-population registry · `5b50063` INDEX 61 CODE COMPLETE + archive

## The adversary / cold-audit / security loop earned its keep

1. **#402 packet-60 escapee (RED_ORPHANED at kickoff):** Fork A's `keep.keeper` field link left
   `test_principal_key_is_the_ONLY_record_principal_link` red. Closed as 61a-w1 (refuse-while-keeping +
   exact-set pin re-classification + member_of auto-cascade live probe).
2. **#416 (MEDIUM, the dedicated security-auditor's marquee catch):** `ScopeInKeeps.to_surql` emitted
   UNPARENTHESIZED disjuncts — safe as a top-level `Or` child but a cross-principal leak under
   `And`-composition, latent in the PUBLIC IR where the entry-point oracle could not see it. Fixed: every
   node emits a self-contained parenthesized fragment + a live composition-safety pin (mutation M7:
   unparenthesize → composition pin reds while the oracle stays green) + re-probed index-neutral.
3. **#413 (probe):** `IN` inside an `OR` is a TableScan trap (#107 class); the read-filter emitter must
   expand `IN` to per-value equalities. Folded into the store reference §2.
4. **61b-w2 adversary (2 low-sev):** Fork F bare-return unpinned; the born-wrap covered the SELECT but
   not the resolution read — both closed before the builder shipped.
5. **The reach law (#344/#345) working:** the coverage growth-pin caught the sidecar's *illustrative*
   named-7 corpus list (the live registry had 9), forcing `lore_verify`+`lore_index` to be classified →
   sidecar ruled **R1: shared_read**. The pin is the set's keeper; the count is not re-frozen.

## Ground-truth caught 4 sidecar premise slips (the discipline working, not a defect in the sidecar)

CAS-vs-wrap lumping in #400; a false "zero-regression" claim on `transitive_blockers` (it wraps
transport deliberately — a different idiom); an imprecise `agent`-fold rationale (fold still sound); and
a "pydantic" slip in Fork D (lorerunes is stdlib-only → stdlib dataclasses). Each surfaced by a lead or
contract-author ground-truth pass and corrected before it reached code.

## OPEN FOLLOW-UPS (ledgered, none blocking)

- **#406** — the #406-class read-gap: the mirror `KeepStore` reads (`list_keeps_for_keeper`/`get_keep`/
  `list_household`/`_read_membership`) + `PrincipalStore.get_by_email` are UNWRAPPED; `list_keeps_for_member`
  deliberately does NOT clone the gap. Fold set + derive-by-property instruction annotated on #406. Trigger:
  a consumer-law hardening wave / the 63/64 store rework.
- **#420** — Fork H-c: routing governed VERBS through `authorize`/`authorize_filter` is pkt 63's job; at
  61 HEAD the classification registry is present but INERT (no boundary enforced yet). Trigger: pkt 63 kickoff.
- **#421** — test-env fragility: the currency gate false-REDs under `/tmp` INODE exhaustion (not space) —
  pytest `tmp_path` OSErrors + the idle-gate hook's hardcoded `/tmp` marker. Fix: teach the hook to honor
  `$TMPDIR`; periodic session-hygiene reap of `/tmp` scratch trees. (Diagnosed + cleared this session by
  the operator freeing `/tmp` inodes; the gate then went PASS with no code change.)
- **#404–#419** — bounds/deferrals ledgered across the packet (incl. #417 reach-law STOP-rule, #405
  full-suite `-n auto` flake).

Reports (all pipeline artifacts across 7 waves): `docs/plans/v2/receipts/2026-08-23-packet61*/`.

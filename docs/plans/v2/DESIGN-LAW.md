# Standing design law — lore v2 (binding rulings, one place)

Process law lives in repo CLAUDE.md. THIS file is **design** law: operator rulings and
measured invariants that bind future build work. Packets cite sections by name; a
packet session reads only the sections its packet lists. Receipts point at the source
documents — cite, don't re-derive. Changing anything here requires a fresh operator
ruling (and for §2/§3, a fresh model consult).

## 1. Client design law (three-model consult, 2026-07-06 — binds ALL surface work)
Source: docs/design/2026-07-06-client-needs-consult.md:449-473,490-495.
1. Context/attention is the dominant client cost; **call count is not the bottleneck**.
   Client metrics: signal-per-token, tokens-per-correct-answer, taxed (mechanical) calls.
2. Counted-elision grammar is the gold standard; the top-elided SCORE is load-bearing;
   re-ask values must be honest and clamped to the enforceable cap.
3. Caveats ship WITH verdicts. Under-claiming is nearly free; ONE confident-wrong costs
   authority for the session (authority→witness, ~doubles calls).
4. Misses teach a decision tree. Silent anything — truncation, zeros, noise-as-hit,
   crowd-out — is the cardinal failure class.
5. Strategy + invariants → read-once instructions; recovery moves, capability hints,
   confidence caveats → embedded per-response.
6. Structured/secondary fields keep the primary render's discipline (the S1 reversal:
   over MCP the model IS the consumer — no unbudgeted JSON dumps beside a capped render).
7. **THE TRUST RULING (operator, 2026-07-24 — elevates this section to the fixed star):**
   the clients are agent models (Sonnet 5 / Opus / Fable), never humans, and TRUST is the
   acceptance criterion for every served surface — an agent that catches the MCP wrong or
   dishonest once routes around it, taxing every future session. Clause 3's mechanism
   (one confident-wrong → authority→witness) is the measured form of the same law.
   Acceptance = consumer-agent batteries with keyed honesty probes + the
   CALL_AGAIN/ROUTE_AROUND routing test (packet 03b rulings §C5 is the reusable template;
   repo CLAUDE.md carries the standing statement).

## 2. Map/impact semantics (2026-07-04 consult — semantic LAW; format-only changes still need a fresh operator decision + consult)
Source: docs/design/2026-07-04-map-test-segregation.md.
- Default map EXCLUDES test nodes from render but keeps their edges feeding rank mass;
  test hubs surface via an always-rendered elision line.
- `focus=` on a test-shaped node auto-inverts to full test prominence (non-negotiable).
- Caps are never dead ends: every `+K more` teaches its expansion verb; `focus=` lifts
  the focused module's cap; caps scale with `budget=`.
- impact's covering-tests join rides the `answers_to` bare-name bridge (no silent
  `tests:0`); depth>1 rollups labeled TRANSITIVE.
- Do-not-relitigate: down-rank-only unified list; silent test omission; tag-only fixes.

## 3. Search confidence / weak-match law (2026-07-06 consult + external validation)
Source: docs/design/2026-07-06-weak-match-discrimination.md:490-549,
2026-07-06-weak-match-external-validation.md:47-54.
- **No fused-RRF-score floor can ever discriminate** — fused score is a rank-reciprocal
  code; C3/C4/C5 permanently rejected. **Magnitude-or-nothing**: only pre-fusion cosine
  has a physical basis.
- Two-tier asymmetry: per-hit flags are near-free; the AGGREGATE absence verdict is the
  guarded surface — precision-first, ≤5% false-fire on real-query union, advisory
  wording MANDATORY (hardening the wording voids the ruling).
- D3 carve-out: verdict fires iff max shown-hit cosine < floor AND no shown hit carries
  a verbatim-identifier anchor (BM25 magnitude is never the gate).
- **The cosine floor is valid ONLY for the exact embedder + prompt config it was
  measured on** — any embedding/prompt change invalidates it → survey re-run. (This is
  the invariant packets 10/11 (formerly PKT-01/02) operationalize per-corpus.)
- Constants are MEASURED via committed deterministic surveys, never guessed; sufficiency
  notices are justified by failure-without-signal, not proven benefit (keep wording honest).
- Ledgered follow-ups (packet 28, formerly PKT-17): relative-score fusion;
  source-concentration and pool-size signals adoptable only under pre-registered rules.
- **Ranking-influence disclosure (operator-ruled 2026-07-11):** any non-similarity
  influence on served result ORDER (graph centrality, boosts, reranker) must be
  disclosed to the consuming LLM — per-hit annotation or a labeled separate lane —
  with per-hit cosine still rendered as the physical signal. Served order silently
  disagreeing with visible similarity is a trust/false-confidence defect, same class
  as the fused-score lie.

## 4. Graph correctness invariants
Source: lore-v2-RESUME.md:222-224, P8a:92-93 (extraction receipt in receipts/).
- Graphs are built WITH `project_roots` (resolution on) + astroid cache reset at sweep
  boundaries; any NEW composition path must supply both or liveness verdicts drift
  false-dead. Bare-name queries ride `answers_to`; keep fake-vs-real double parity pinned.
- Test refs are never production refs: dead ⇔ production_references==0;
  only_referenced_by_tests is its own smell.

## 5. Store idioms beyond repo CLAUDE.md
Sources: P8c:139-143, P8d:217-221 (extraction receipt).
- **Two-step table recreate is mandatory** (REMOVE+DEFINE in one tx conflicts with async
  HNSW build) and the window must be lock-excluded from concurrent writers — a raced
  write auto-creates SCHEMALESS and the DDL rolls back (memory eea2c3a1;
  memory/local.py::_rebuild_lock is the reference).
- Hot-row minting: under the OLD deterministic linear backoff, N-way contention on one
  row exhausted the shared 5-attempt retry 43% @ N=8 (every racer slept the identical
  duration and re-collided in lockstep — finding #102). Cloning that mechanism by hand
  is exactly how finding #108 happened (briefs' own private mint, a DIFFERENT jitter bug
  at 8-way contention) — so ANY new hot-row mint calls `_txn.retry_on_conflict`; it is
  the ONE driver every caller shares, never a mechanism to reproduce. It owns: per-attempt
  FULL jitter freshly drawn from the process PRNG on EVERY attempt (never cached, never
  derived from the contended row's id or any call parameter), a guaranteed attempt FLOOR
  (`_MAX_TXN_CONFLICT_ATTEMPTS`), a wall-clock deadline that may only cut retries once
  that floor is met, and the typed `TxnContentionExhaustedError` on exhaustion. A
  per-call or id-derived jitter source, or a private retry loop of any shape, **is** the
  defect #102/#108 exist to remove — measured post-fix: zero exhaustions across 2900
  mints at N up to 32.
- FLEXIBLE-array migrations: a non-option field added to FLEXIBLE array items rejects
  new writes lacking it while legacy rows survive (IF-NOT-EXISTS never retro-validates).
- Counting-client errors: `TerminalCountError` (4xx≠429 — stop) vs `RuntimeError`
  (retry exhaustion — retry); catch subclass to stop, base to retry.
- Never substitute the in-memory engine for the `[real]` test tier (29 tests
  legitimately fail on engine semantics; a down spike = ~861 loud errors by design).

## 6. Eval + measurement pins
Sources: docs/eval/2026-07-04-p8a-baseline.md:44-49; client-needs ruling.
- The A/B instrument is `docs/eval/evaluation_harness_p8a.py` + `connections_p8a.py`,
  REUSED VERBATIM, pinned model `claude-sonnet-4-5-20250929` — measurement pins are
  never "upgraded". Harness venv needs anthropic+mcp; key at /home/ejprice/docker/mcp/.env.
- Standing bar: 35-pair set graded by client metrics (§1.1). 11-pair calls-leg RETIRED.
- `CLAUDE_PER_VOYAGE_CEILING = 1.78` is a measured constant (token-weighted p95 max
  across 3 corpora) — re-measure via scripts/token_survey.py on corpus change, never assume.
- `smoke_p8b.py` is render-shape-coupled to server.py renderers — render changes update
  it in step.

## 7. Migration law (v0.3 → v2 fleet)
Source: docs/design/2026-07-04-migration-concurrency.md:37-47,117-161.
- Invariants I1–I4: no acknowledged memory lost; non-destructive until operator-confirmed
  retire; no duplicates (uuid5 idempotence); receipts before trust (count parity + spot
  recalls before any retirement).
- The MCP endpoint swap is the LAST data step and the definition of "takes over" — it
  follows the final replay + parity receipt, never precedes it.
- Never delete the shared Qdrant pod (127.0.0.1:16333) until post-P8f-soak cleanup;
  `QDRANT__SERVICE__API_KEY` stays in lore.env until then (DI's live container consumes it).

## 8. Orchestration substrate law
Source: docs/orchestration/2026-07-06-orchestration-context-retro.md:24-28,81-86.
- **Push is the enemy; pull is fine.** A push message-bus inside lore is REJECTED — do
  not re-propose (it recreates the advisory-inbox failure). Ledger verbs are durable
  pull with compact renders: summarized value objects, never dumps.
- Content flows agent-to-agent through disk/ledger, never transiting the lead.
- lore_tasks state machine: claimed → in_progress → done (claimed→done illegal).
- **Store-and-forward PULL sanctioned (operator-worded, 2026-07-11):** *"A durable
  message store drained by recipients at their own turn boundaries, with LIVE SELECT as
  contentless wake-only, is store-and-forward PULL and is sanctioned; L5 (advisory
  in-memory push) remains rejected."* This admits the agent-comms subsystem (packets
02–06, `comms-subsystem.md`, formerly PKT-28)
  (durable rows/edges recipient-drained at own turn boundaries; LIVE SELECT wake-only) —
  it is comms-research mitigation #1, NOT the rejected L5 push bus.
- **Append-only is NOT a requirement (operator, 2026-07-11, explicit).** Where the
  comms design retains immutability (e.g. message bodies immutable after send) it is a
  stated, individually strikeable DESIGN CHOICE with a reason — never law. Delivery/ack
  state lives on RELATE edges as write-once CAS stamps (a lost-update guard, not
  append-only ideology; only the recipient stamps its own edges → zero hot-row
  contention).

## 9. Memory contract
Source: lore-v2-RESUME.md:73-78 (extraction receipt).
- The recall→cite→remember loop's chunk-key ref shape must not change; only
  `valid_until=null` rows boost/inject; drifted refs render `(drifted — re-verify)`;
  uuid5 content-derived memory ids are the idempotency invariant.

## 10. Enrichment honesty (binds packets 29/30, formerly PKT-14/15)
Source: MASTER-PLAN §2.
- Generated text is ALWAYS rendered marked `(ai summary)` and never inside source
  fences. BM25-only first; vector-side re-embedding with summaries is v1.2+ (schema-
  fingerprint implications). Enrichment is opt-in per project, rate-limited, resumable.

## 11. Config dynamism hazard guards (operator-accepted wholesale 2026-07-05)
Source: docs/design/2026-07-05-p13-config-dynamism-disposition.md:107-113.
- `project.slug`: derive at ONBOARD only, then FREEZE — never re-derive on a live index.
- `surreal.database`/`namespace`: derive strictly from the frozen slug via
  `effective_surreal_database`; no other derivation source.
- `exclude_dirs` auto-derivation: ADDITIVE to operator config (union, never replace),
  logged, and requires a real dir-shape signal (e.g. pyvenv.cfg), not name heuristics.
- `chunkers` wiring: explicit operator opt-in; announce the re-chunk in index status
  BEFORE executing.

## 12. Deployment checkpoint criterion
Source: docs/design/2026-07-04-p8-decomposition-rationale.md:80-93.
- Every packet ends suite-green + cold-audited + committed, and (where its surface is
  observable) redeployed + smoke-verified. Instructions-block changes stay fused to the
  surface changes they describe.

## 13. Toolchain gotchas that bit once (build-environment law)
- **`uv sync --all-packages` always** (fresh worktrees included) — a bare `uv sync`/
  `uv run` PRUNES workspace-member deps and breaks imports mid-build.
- Uniform store error posture: every `_query` domain branch classifies + logs
  server-side + launders the client-facing error (b262ab4/7793eff) — new store code
  matches or the audit flags it.

## 14. Singular durable store (operator-ruled 2026-07-11)
- **SurrealDB is the SINGULAR durable store for lore data — all modes, all roles.**
  The SQLite write-through memory ledger is retired (packet 18, formerly PKT-24); no side-channel
  durability stores may be introduced. This OVERRIDES MASTER-PLAN §1's "write-through
  ledger stays" clause.
- Durability posture is store-level backup (single-node: state-dir snapshots /
  `surreal export`; split: PVC snapshots / managed backups) — REQUIRED and documented,
  never assumed.
- Write paths fail LOUD on store failure; a silent durability fallback is a defect.
- The only sanctioned ledger touch-point is READING v0.3 `<slug>.memory.db` files as
  a migration import source (packet 20 N3, formerly PKT-12), frozen and deleted post-soak.

## 15. Test-instrument packets get an adversary too (operator-ruled 2026-07-19, packet 02a)
A packet whose DELIVERABLE is an instrument (a scanner, a pin battery, a completeness
guard) has no separate contract for the contract-adversary to grade — the instrument IS
the tests. Today that means it ships with a builder and a cold audit but **skips the one
role whose killer question is exactly right for it**: *"if a builder satisfied this
perfectly but fixed NOTHING, would it still pass?"*
- **Instrument packets route through the `contract-adversary`, grading the INSTRUMENT'S
  DISCRIMINATION** (does each pin go RED on a plausible wrong build?) before the lead
  accepts the wave. The adversary builds wrong implementations; here it builds wrong
  RENDERS and wrong SHAPES and reports what the instrument waves through.
- **Receipts (packet 02a, why this exists).** The cold audit caught a pin whose marker was
  a shared PREFIX of a sibling variant, so an always-wrong-variant build passed the entire
  instrument file 40/40 — **a vacuous proof inside the anti-vacuity instrument**, caught
  only by a sibling packet's test. It also caught a promise shape invisible to both
  scanners. Both are the adversary's native question, found one stage late and at the cost
  of a full NO-GO cycle.
- **A scanner's unknown-shape branch DENIES, it never silently placeholders.** Measured in
  02a: an `else: [_PLACEHOLDER]` fallthrough made `%`-format, `.format()` and `str.join`
  promises **invisible while the guard reported green** — allow-by-default wearing
  deny-by-default's clothes. Enumerate the SAFE set (evidence-backed per entry); everything
  else fails loud naming `file:line` + the AST shape. Patching shapes one at a time is the
  repo's six-defeats lesson recurring inside the packet built to prevent it.
- **Every marker/pin proves it discriminates AGAINST ITS SIBLINGS, mechanically** — a
  cross-satisfaction meta-test, not a human's reading. A marker satisfiable by a sibling
  branch's output cannot prove its own predicate gates emission.
- **EXECUTE YOUR OWN CLAIMS — a comment stating a reason is a SOURCE, not an oracle.** This
  is `READ THE DEPENDENCY'S DOCS — THEN VERIFY THEM` (repo CLAUDE.md) turned inward: we
  already knew a vendor's doc can lie, and 02a proved OUR OWN evidence comments lie the same
  way. **5 of 02a's 8 defects were claims stated as reasons and never run.** The exemption
  `# EVIDENCE: these evaluate to bools/numbers, never to prose` covered `Compare | BoolOp |
  UnaryOp` — TRUE for two, FALSE for the third (`"" or "prose"` → `'prose'`), hiding the
  commonest Python default idiom (`x or "…"`) in plain sight. A bounded sweep then EXECUTED
  all 18 claims in that exemption set and found **3 more false**. Therefore: any exemption
  asserting *"this cannot happen"* ships with the EXECUTED probe that establishes it, and the
  condemning measurement stays an executable PIN (`test_the_retired_<X>_claim_is_false_by_execution`)
  so a retired claim can never be re-asserted from memory. Corollary for reviewers: in any
  deny-by-default gate, **attack the SAFE set first** — the allowlist is where the claims are,
  and claims are where the defects live.

# The #210 / #207 / #211 security fix wave — close-out and merge preconditions

> ⚠ **SUPERSEDED SYMBOLS (dated record):** this file mentions `_BRIEF_PUBLISH_`, a retired
> prefix — the four private mint-retry constants briefs.py once hand-rolled, DELETED by
> finding #108; the shared `_txn.retry_on_conflict` driver owns that policy now. The prose
> below is preserved as the record of its date; do not update it — this banner is the warning.

> ✅ **MERGED 2026-07-26 at `c192cb4`** (fast-forwarded to `feat/surreal-unification`; worktree
> removed). This file was written as a merge instruction sheet — it is kept because the preconditions
> below were followed and the reasoning is the record of why. **Outcome, measured:**
> - pre-merge baseline from main @ `2f32a3b`: **1 failed / 6936 passed**
> - post-merge @ `c192cb4`: **1 failed / 7065 passed** — **failure set IDENTICAL**, +129 passing
> - the single failure is main's own (03b archived reports naming `_BRIEF_PUBLISH_` without a
>   SUPERSEDED banner) — pre-existing, unrelated, still open
> - the 109 mypy errors §2 predicted would resolve **did resolve**; `ruff` clean, `scripts/` 329 passed
> - `git merge-tree` predicted **zero conflicts** and there were zero
>
> **§2's warning proved exactly right and is the reusable part:** the 394-failure baseline WAS an
> artifact of the branch point, and the post-merge diff was only readable because the baseline was
> captured from main *minutes* before merging. ⚠ **One thing §2 did not warn about, learned the hard
> way:** `git archive | tar -x` OVERLAYS a scratch copy — it never deletes — so the first "main"
> baseline was contaminated by our own added files and had to be re-taken with them excluded. It was
> caught only because an unexpected `ImportError` named one of ours.
>
> **§3b's deferred ledger hygiene is DONE:** #204/#207/#210/#211/#227 resolved with fix citations.
> **New since:** **#231** (this wave's own gate allowlists by pattern NAME, so it cannot exempt one
> site without blinding all) and **packet 42** (SHIPS NEXT — prevent the leak, delete the sanitizer).

Assembled by `lead-11i-b`, 2026-07-26. **This is the merge instruction sheet.** Packet 11-i's
design state lives in `STATE-2026-07-25.md`; this file covers only the fix wave that ran on top of
it, and the things a merge must not discover for itself.

---

## 1. What shipped

| finding | fix | commits |
|---|---|---|
| **#210** | `AGENT_NAME_PATTERN.match` → `fullmatch`; `"scout\n"` no longer passes the charset guard. Plus an **AST class instrument** asserting no `$`-anchored pattern is ever `.match`ed, with two evidence-backed allowlist exemptions. | `c32800d` `8b1343e` `5e99409` + reports |
| **#207** | Five un-jittered backoffs consolidated onto one shared full-jitter policy (`loresigil/backoff.py`, `tenacity.wait_random_exponential`). Post-fix AST scan finds only the fenced `_txn` seam. | inside `f65e062` (see §3) |
| **#211** | `SecretStr` from `resolve_secret` to the SDK seam, one `signin_credentials` unwrap point, 12 connection owners. Traceback rendering **and** scrubbing (the formatters discarded every traceback; 8 production `exc_info=True` sites logged nothing). | `f65e062` `a68cfe7` `20ea39a` `0b851a3` `7f11fc5` `a265aff` `e16f4c4` `0233999` |
| **#227** | Redactor no longer mangles path components / UUIDs in tracebacks. **Pre-dated the wave** — `_TOKEN_RE` byte-identical at `d0ee2be`. | `0233999` |

**Still open at the time of writing:** `fix-207-jitter`'s D2 (jitter `Retry-After`, additive-only
over the capped value) and D3 (jitter the eager-lease constant without changing the ladder shape).
Scoped, ruled, GO given.

---

## 2. ⚠ THE BASELINE IS AN ARTIFACT — read this before interpreting ANY number in this wave

Every gate figure produced by every agent in this wave is measured against **394 failing tests that
are a property of the branch point, not of the code.**

**Measured:** those 394 are packet-03b *contract* tests (`test_comms_promise_registry.py`,
`test_comms_tool.py`, …). They fail here because this branch was cut at `d0ee2be`, before 03b's
implementation existed. `_render_comms_send` / `_render_comms_drain` appear **6×** on
`feat/surreal-unification` and **0×** on this branch.

**Consequences for the merge, in order of how easily each is missed:**
1. **The 394 should largely vanish on merge** — the code they exercise will finally be present.
2. **"Failure set identical to the enumerated baseline" is a true statement about a fiction.** It
   was the right check to run *here*; it certifies nothing about the merged world.
3. **The post-merge run is the first honest measurement this work has had.**
4. ⚠ **Capture a pre-merge baseline FROM MAIN, immediately before merging, or the post-merge run is
   uninterpretable** — you will not be able to separate "03b tests that resolved" from "our changes
   broke something". Deliberately NOT captured in advance: a figure taken hours early is stale by
   merge time, and a stale baseline is worse than none because it reads as verified.

---

## 3. ⚠ `f65e062` CONTAINS TWO WAVES UNDER ONE NAME

59 files. Named `fix(#211): secrets are a TYPE, not a hope`; it also carries **the entirety of
`fix-207-jitter`'s backoff work**.

**Cause, and it is the lead's:** three builders shared one worktree, and therefore **one git index**.
`fix-207-jitter` staged its hunks; `fix-211-secrets` ran `git commit`, which commits the INDEX and
not the paths you `git add`. Neither agent did anything wrong — `fix-207-jitter` had explicitly
declined to sweep a sibling's work into its own commit, and `fix-211-secrets` ran the correct
pre-commit check.

**The transferable rule** (`fix-211-secrets`'s, and it is not obvious): *a pre-commit
`git diff --cached` check is TOCTOU. Only a post-commit `git show --name-only` is sound.*

**Deliberately not split.** The branch is local, a `reset --soft` re-stage across 59 interleaved
files risks losing the work it would protect, and a **disclosed** mixed commit is recoverable where
a silent one is not. Provenance recorded at `7251c77`.

---

## 3b. LEDGER HYGIENE OWED AT MERGE — deliberately not done early

Flagged by `coldaudit-fixwave-2`. **These are deferred to the post-merge docs step ON PURPOSE:** a
finding resolved against an unmerged branch reads, to anyone querying the ledger from main, as a
defect that is gone from production when it is not. Resolution follows the merge, not the fix.

| finding | state | action at merge |
|---|---|---|
| **#210** charset guard | fixed + audit GO | resolve, cite `c32800d` |
| **#204** loresigil zero jitter | fixed by the #207 wave | resolve, cite `f65e062` (⚠ the mixed commit — see §3) |
| **#207** five unjittered backoffs | fixed + audit GO, hardened at `eeba286` | resolve, cite both |
| **#227** redactor path mangling | ⚠ **LEAVE OPEN** — the fix is the audit's R1 blocker (it weakened the secret backstop 38–63%). Its body still says "awaiting GO", which is stale either way. | update body; resolve only after R1's remediation passes |
| **#199** `scripts/` ungated | **count stale AGAIN** | see below |

⚠ **#199's number has now moved three times, and the mechanism is worth more than the number.**
Filed as ~50 (a per-FILE count generalised to a directory — the lead's error). Corrected to **150**
by re-derivation. **Now 153**, because this wave added three pins to `scripts/`. Re-derived by the
lead 2026-07-26: `uv run pytest --collect-only -q scripts/` → `153 tests collected`.

That is exactly why **#224** requires a count to carry the command that produced it: a bare "150"
was stale within a day of being corrected, and nothing about the figure signals that it is a
snapshot of a moving quantity. The durable claim is *"`scripts/` is excluded from `testpaths`, so
none of its tests run in any gate"* — the count is a measurement, not a fact, and it belongs with
its command or not at all.

---

## 4. Merge preconditions — do not start without these

1. **A fresh cold audit on a frozen tree.** The existing one (`coldaudit-fixwave`) graded the wave
   twice, retracted one of its own rows, and should not grade its own corrections. Its Defect A and
   D findings stand on harness-independent receipts.
2. **HARD FREEZE during the audit.** The first audit's own NO-GO reason #1 was that HEAD moved SIX
   times while it ran. "Stand by" is not a freeze; say *no commits until explicit GO*.
3. **The pre-merge baseline from main** (§2.4).
4. **Conflict surface, measured:** 57 ahead / 64 behind; **six files touched on both sides** —
   `config.py`, `messages.py`, `server.py`, `store/surreal.py`, `test_comms_tool.py`, `uv.lock`.
   `server.py` and `config.py` are the real work: a `SecretStr` type migration has to be reconciled
   against 03b's comms surface **in the same functions**.

---

## 5. Bounds accepted deliberately — do not "fix" these thinking they were missed

- **Bare hex runs stay redacted** (#227). A 40-hex SHA and a 40-hex API key are indistinguishable by
  shape; the only discriminator is surrounding context, which is forgeable in log text. *A redacted
  SHA costs provenance; an un-redacted key costs a credential.* **Re-open trigger:** git provenance
  in logs becoming load-bearing for an investigation. Rhymes with #131.
- **`Retry-After` stays capped** at `RETRY_MAX_DELAY_S` (#223). Honouring it in full is a real
  behaviour change — a hostile server could park a worker for hours. D2's jitter is additive-only
  over the *capped* value and deliberately does not settle this.
- **`_txn.retry_on_conflict` was NOT churned** (#202). Proven, guarded, eleven mutation-proven
  consumers, runtime guard on `__code__` frames. Its re-open trigger has now FIRED (#207 created the
  shared policy), so consolidation is a wave of its own — with an owner, not an append.

---

## 6. What the grading caught that the building did not

Recorded because it is the argument for the cost of this process, and the numbers are exact.

**Four defects, none visible to any builder gate:**
- **A** — `_make_store` passing an unwrapped `SecretStr` username. **100% broken, live at the branch
  tip**, proven by live signin with a positive control. Invisible to three gates *simultaneously*:
  `scripts/` is outside `testpaths` (#199, 150 nodes), mypy never analyses `scripts/` (it is not in
  `MEMBERS`) and is blind through `dict[str, Any]` anyway (#221), and **the one covering test
  monkeypatches `_make_store` away**.
- **B** — a widened signature leaving an in-`testpaths` consumer passing `str`, under a commit
  message claiming baseline parity it did not have.
- **D/#227** — the redactor mangling path components. **Found only because the auditor ran from a
  directory whose own path tripped it.** "The test environment is a fiction", third instance this
  session — and this time the fiction was the repo's own filesystem path.
- **C** — RETRACTED. The auditor's own harness had read a mixed tree.

**Two independent retractions**, one by a builder and one by an auditor, each caught by checking
`loremaster.__file__` on a measurement that favoured them. Both retracted rather than defended, and
that is why the C dispute settled in twenty minutes instead of becoming a standoff.

**The through-line, stated once:** every defect this wave found is an instrument that does its
*visible* job and silently omits an *invisible* one — auth that authenticates but disables session
binding (#206), an overflow detector whose silent failure lets the index go stale while reporting
current (#209), a redactor that never saw tracebacks and then mangled them (#211/#227), a type gate
passing at zero delta while 119 tests were runtime-broken (#221), a test that monkeypatches away the
function it covers. In every case: a green result and a real hole, indistinguishable from outside.

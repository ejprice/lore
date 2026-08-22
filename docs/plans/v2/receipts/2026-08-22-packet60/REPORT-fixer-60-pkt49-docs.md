brief-base v14 read
brief project v7 read

# REPORT — fixer-60-pkt49-docs

## SUMMARY BLOCK
- state: **done**
- deviations: one — fixed a THIRD stale-emptiness surface in the same docstring the brief
  named (`set_expires`'s "the builder must SET it to NONE explicitly" clause, line 582 at
  `66ed1aa`); same #398 class, same file, in-scope per the brief's "if you find another
  genuinely-stale STUB-over-greened-code site, fix it".
- Packages considered: none — no mechanism specified (docs/comment-only edit).
- Reuse ledger: none — no new symbols introduced.
- Graded: N/A — fixer, no verdict rendered over another agent's artifact (I ran a scoped
  suite only to confirm the docs edit didn't break collection).
- decisions-needed: none.
- capability check: brief demanded edit of `loremaster/loremaster/principals.py`, ruff,
  scoped pytest, git status, lore comms/task tools — all available and exercised.
- receipt pointers: ground-truth §1 · fixes §2 · full bare sweep §3 · verify tails §4.
- base graded at HEAD `66ed1aa`.

## 1. Ground-truth (both methods are FULLY IMPLEMENTED, not stubs) — HEAD `66ed1aa`
- `PrincipalStore.set_expires` — body is a real two-branch UPDATE: the `expires_at is None`
  path issues `UPDATE … SET expires_at = NONE WHERE email = $email RETURN AFTER`; the else
  path binds a Python datetime `SET expires_at = $expires_at …`. Empty result → typed
  `PrincipalNotFoundError`; otherwise returns `_row_to_principal(rows[0])`. It is NOT
  `raise NotImplementedError`. → docstring `STUB (contract-49-1):` prefix is factually stale.
- `PrincipalStore.delete` — body reads the owning principal (`get_by_email`, `None` →
  `PrincipalNotFoundError`), counts owned `principal_key` rows, then runs a real
  `execute_transaction` cascade (children DELETE first, then the parent, one txn) and returns
  the cascaded count. It is NOT `raise NotImplementedError`. → docstring `STUB (contract-49-1):`
  prefix is factually stale.

Both prefixes contradict their live bodies — the #398 stale-prose class the earlier docs(49)
sweep (`3077d23`) missed on these two Store methods (it swept the `principal_key` schema slice).

## 2. The fix (docstrings ONLY in `loremaster/loremaster/principals.py`)
Style match: the greened siblings (`create`, `set_status`, `set_subject`) open with a plain,
capitalized imperative behavior line and carry NO stub prefix — so the fix strips the prefix
rather than adding a historical note, keeping the accurate behavior description intact.

1. `PrincipalStore.set_expires` first line:
   - before: `"""STUB (contract-49-1): set/clear a principal's ``expires_at`` — 49's`
   - after:  `"""Set or clear a principal's ``expires_at`` — 49's`
2. `PrincipalStore.set_expires` builder-directed clause (was stub-era instruction prose):
   - before: `… would leave it unchanged — the builder must SET it to NONE explicitly).`
   - after:  `… would leave it unchanged, so the clear path SETs it to NONE explicitly).`
   - (DEVIATION: not named line-by-line in the brief, but it is the same stale class — it
     instructs "the builder" in present tense over already-greened code. Reframed to describe
     the live code's behavior; the accurate rationale is preserved.)
3. `PrincipalStore.delete` first line:
   - before: `"""STUB (contract-49-1): HARD-delete a principal and CASCADE its keys — 49's`
   - after:  `"""HARD-delete a principal and CASCADE its keys — 49's`

No behavior change; all docstring text otherwise preserved (the accurate behavior descriptions,
the `⚠ CASCADE FORWARD-SCOPE` pin note, Args/Returns/Raises).

## 3. Full bare, anchor-free sweep (whole file) — every hit gets a verdict
Pattern set 1: `grep -nE "STUB|contract-49-1|NotImplementedError|emit|emits no|not yet"`

| line | excerpt | verdict |
|---|---|---|
| 179 | `subject` … "email-pre-created principal **not yet** bound to a login (Model B)" | accurate — present-tense Model-B unbound-subject description; unrelated |
| 248 | `# Opened on first use; None means "not yet connected / closed"` | accurate — connection-lifecycle comment; unrelated |
| 575 | `"""STUB (contract-49-1): set/clear a principal's expires_at …` | stale → FIXED (set_expires) |
| 617 | `"""STUB (contract-49-1): HARD-delete a principal and CASCADE its keys …` | stale → FIXED (delete) |
| 1078 | `# The ONLY time the raw secret is ever emitted — verbatim …` | accurate — matched "emit"; describes live `_cmd_mint_key` credential print; unrelated |
| 1116 | `create-keep emits (the _cmd_mint_key print-the-credential precedent …` | accurate — matched "emit"; describes live `create-keep` id print; unrelated |

Pattern set 2 (widened): `grep -nE "TODO|FIXME|placeholder|unimplemented|the builder|RED stub|raise NotImplemented|will be implemented|to be implemented|once implemented|stub"`

| line | excerpt | verdict |
|---|---|---|
| 582 | `… would leave it unchanged — **the builder must** SET it to NONE explicitly` | stale → FIXED (set_expires builder-directed clause; see §2.2) |

No other stale-emptiness prose remains. Line numbers cited above are pre-fix (HEAD `66ed1aa`).

### Keep-verb #398-cleanliness (brief asked to verify)
The packet-60 keep verbs in this file (`_cmd_create_keep` ~1103, `_cmd_add_household` ~1130,
`_cmd_remove_household` ~1138, `_cmd_set_rank` ~1147, and the `_dispatch_keep` handler ~1210)
carry only accurate present-tense docstrings — no STUB, no `NotImplementedError`, no
stub-era/"not yet"/"the builder" prose. The two "emit" hits above (1078, 1116) are their only
sweep matches and both describe live behavior. Confirmed #398-clean.

## 4. Verify receipts (docs/comment-only; no git mutation)
- residual sweep: `grep -nE "STUB|contract-49-1"` → **(no residual hits)** after fix.
- ruff: `uv run ruff check loremaster/loremaster/principals.py` → `All checks passed!`
- pytest: `uv run pytest -n auto loremaster/tests/test_principals_cli.py` →
  `45 passed in 5.12s` (45 items collected, clean collection — docs edit did not break it).
- `git status --short` → only `M loremaster/loremaster/principals.py` is mine (the `??`
  `REPORT-*.md` files pre-existed this task; this report adds one more `??`). No stage/commit
  performed — the lead commits as a separate docs(49) citing #398.

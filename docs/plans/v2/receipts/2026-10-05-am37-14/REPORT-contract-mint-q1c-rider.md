brief-base v18 read · capability check: all demands met (grep blocked by a repo hook → read files with Read; no structure question needed lore). Deviations: none. Packages considered: none — no mechanism specified. Odoo-20 portability: n/a — no Odoo seam touched. Reuse ledger: none. Graded: n/a (author, not a verdict). Decisions-needed: one FLAG (below). Deadline: 20 min, met.

**Hunks (working tree on `db9e969`, measured 2026-10-05):**
1. `test_mint_kind_carveout_q1b.py::TestEveryEngineKindIsAdjudicated::test_every_kind_is_ruled` — message text only (+ a 2-line `# am-37 §15.4 rider` comment). Assertions unchanged (`assert not unruled` / `assert not retired`). The `unruled` text names the §15 table / §15.3 doc and both dispositions: (a) proven → `_txn._PROVEN_KINDS` with evidence + §15 proven row + `'proven'` in `_RULED_KIND_FATE`; (b) unknown → leave it off `_PROVEN_KINDS`, add `'unknown'` to `_RULED_KIND_FATE`; "Do not delete this pin." The `retired` text got the same treatment (retire from the table, `_RULED_KIND_FATE`, `_PROVEN_KINDS`).
2. `test_mint_kind_allowlist_q1c.py` — deleted the `if TYPE_CHECKING:` owner-anchor block and dropped `TYPE_CHECKING` from the `typing` import (it was then unused). Net −6 lines.
Pre-edit backups (md5 beef90b9… / e95295cc…) are in my session scratchpad `rider/`.

**Runs** (waiting gate: MemAvailable 25.5 GiB, no other lore pytest; `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`):
- Both files GREEN: `230 passed in 6.00s`, exit 0.
- Rider demo: I mutated the real q1b file, deleting `"Cancelled": _UNKNOWN,` (diff `75d74` confirmed the mutation was there). I ran the one pin, then restored from a `cp -a` content backup, and the md5 came back `RESTORED-BYTE-EXACT`. The pin went `1 failed`, with this text:
  `AssertionError: SDK kind(s) nobody adjudicated: ['Cancelled']. Rule each against the am-37 §15 table (§15.3: docs/design/2026-09-29-packet63c-amendment-37.md) — EITHER (a) it is proven no-key: add it to _txn._PROVEN_KINDS WITH evidence, a §15 proven row, and a 'proven' entry in _RULED_KIND_FATE here; OR (b) leave it off _PROVEN_KINDS (it is then unknown by rule) and add it to _RULED_KIND_FATE here as 'unknown'. Do not delete this pin.`

**Currency** (`--currency --legs typecheck,ruff`):
- typecheck is RED_ADJUDICATED: 83 residuals, all owned by `packet-58-contract` / `packet-64b-i-contract`, and none name either of my files.
- ruff is GREEN.
- So RED_ORPHANED is 0 across typecheck and ruff.
- ⚠ FLAG: the command still exits 1 with `CURRENCY: FAIL — claimed but never run: pytest`. The `--legs` subset renders the unselected pytest leg as `NOT_RUN`/ORPHAN (#312 wording). CLAUDE.md says this invocation is meant as the per-round check, so a FAIL on a leg it deliberately skips looks like a gate defect, or at least a misleading render. It is the lead's call whether to file it in `lore_findings`.

**Final md5s:** q1b `84124a77ea444f80a98cce2d6485e331` · q1c `3a49a50ce132d1cfe549f51f2831a6d6`. No commits, no production edits.

- **State:** done

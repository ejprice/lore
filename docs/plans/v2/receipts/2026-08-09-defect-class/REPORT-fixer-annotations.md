# REPORT-fixer-annotations

brief-base v10 read
brief project v7 read

## SUMMARY
- state: **done**
- deviations: none
- Packages considered: none — no mechanism specified (pure local-variable rename)
- Graded: built/tested at working tree over `003a337` (HEAD unchanged; only `loremaster/loremaster/server.py` modified, uncommitted)
- decisions-needed: none
- THE FIX: renamed the local `annotations` → `tool_annotations` inside `partition_tools_by_posture` (server.py ~:9476–9478). Pure rename, byte-identical behaviour; the `from __future__ import annotations` module import is untouched. No scanner allowlisted.
- FULL SUITE: **9582 passed / 444 failed / 44 skipped / 3 xfailed** in 264.89s. New-failures vs the #333 auth-WIP baseline = **0**. All 444 failures are the pre-existing auth-WIP baseline; the 15 previously-RED exec-seam/cascade tests now PASS.
- ruff: **GREEN** (`All checks passed!`).
- currency gate: **PASS (exit 0)** — 15 `RED_ORPHANED` GONE; pytest(444) + typecheck(191) both `RED_ADJUDICATED` to packet-39-pending-build; no new orphan.
- receipt pointers: junit `/tmp/fixchk.xml`; suite tail `/tmp/fixchk.log`; currency `/tmp/currency.log`.

## Capability check
Brief demanded: one `server.py` edit + full-suite run + ruff + currency gate. I have Edit, Bash, and the lore MCP tools — all satisfiable. No gap.

## The change (file:line)
`loremaster/loremaster/server.py`, function `partition_tools_by_posture` (docstring at ~:9450, loop body ~:9475–9482).

Before:
```python
annotations = getattr(tool, "annotations", None)
read_only_hint = getattr(annotations, "readOnlyHint", None) if annotations else None
```
After:
```python
tool_annotations = getattr(tool, "annotations", None)
read_only_hint = (
    getattr(tool_annotations, "readOnlyHint", None) if tool_annotations else None
)
```

### Why this is the root fix (not a workaround)
The exec-seam scanner `shellout.py::_deny_namespace_doors` flags any `getattr(X, ...)`
where `X` is an imported name (`node.func.id in _NAMESPACE_BUILTINS and
node.args[0].id in imported`). The local `annotations` shadowed the module-level
`from __future__ import annotations`, so `getattr(annotations, "readOnlyHint", ...)`
read as "reaching into the namespace of the imported module `annotations`" — the exact
`#125/#131` door the scanner exists to close. Renaming the local removes the name
collision; the scanner stays correct and server.py is NOT allowlisted. The
`from __future__ import annotations` import is untouched (module-level, still present).

Only two references to that local existed in the function (assignment + `getattr`);
both renamed. No other `annotations` reference inside `partition_tools_by_posture`.

## Verification receipts

### 1. Full suite — `uv run pytest -q -n auto -o junit_family=xunit1 --junit-xml=/tmp/fixchk.xml`
Tail:
```
444 failed, 9582 passed, 44 skipped, 3 xfailed, 1 warning in 264.89s (0:04:24)
```
Junit total testcases: 10073 = 9582 + 444 + 44 + 3 (reconciles).

**All 444 failures are the #333 auth-WIP baseline** — every one in these 10 auth/posture
files (Posture / resolve_posture / HOSTED_REFUSAL unbuilt; packets 39/45/48/49), sum = 444:
```
 81 loremaster/tests/test_auth_composition.py
 75 loremaster/tests/test_google_token_verifier.py
 70 lorerunes/tests/test_posture.py
 57 loremaster/tests/test_hosted_readonly_posture.py
 46 loremaster/tests/test_allowlist_roster.py
 37 lorerunes/tests/test_roster_parser.py
 25 loremaster/tests/test_auth.py
 21 lorerunes/tests/test_email_normalisation.py
 18 loremaster/tests/test_auth_identity_seam.py
 14 loremaster/tests/test_permission_resolver_seam.py
```
Zero exec-seam / defect-class / shellout failures remain.

**Previously-RED tests now GREEN** (from junit, ran-and-passed — not "no tests ran"):
```
test_shellout_allowlist:       matched=77  failed=0
test_shellout_seam_perimeter:  matched=54  failed=0
test_workspace_probe:          matched=46  failed=0   (lore-deploy cascade)
```
Aggregate: shellout=131 ran / 0 failed; workspace_probe=46 ran / 0 failed.

### 2. `uv run ruff check .`
```
All checks passed!
```

### 3. `uv run python scripts/pending_contract_gate.py --currency`
```
  typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build
  ruff         GREEN
  pytest       RED_ADJUDICATED — 444 residual(s), owned by: packet-39-pending-build
CURRENCY   : PASS — every claimed gate is GREEN or OWNED    (exit 0)
```
No `RED_ORPHANED` line — the 15 previously-orphaned exec-seam failures are gone; the
remaining reds are the adjudicated auth-WIP baseline (owned by packet 39).

## Scope / flags
- Did not commit, stage, or mutate git state (lead commits). Only `server.py` edited.
- No unrelated defects noticed during the change.

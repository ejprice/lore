brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations (prose-only; nothing committed; measured 2026-09-25 over HEAD `cb2a215`).
- **Deviation D-1:** `_comms_fakes.py` — besides the two granted edits, the caller's inline comment `# None at HEAD only — see the helper's removal trigger` was reworded to `# dead since 63c-i-a — see the helper's docstring (amendment 12)`, because the granted docstring rewrite deleted the "removal trigger" that comment pointed at (a dangling reference MY edit created — brief-base §2 exception). Also dropped the word "guarded" from the adjacent FORK-C comment line ("ONE guarded helper" → "ONE helper"): there is no guard since 63c-i-a. Same hunk; comments only.
- **Deviation D-2:** `probe_governed_63c.py` — the brief names ONE comment ("agent deliberately has NO scope column"); a second COMMENT with the same claim (`_part_d`, "agent has NO scope column; the sidecar …") was corrected too. Two readings, stated: (a) only the named comment · (b) every comment carrying the claim. I picked (b) for comments only. The two PRINTED strings with the claim (`_part_d` fragment header, the summary line "REPORT — no scope col") and the module docstring's "NO ``scope`` column" were LEFT (changing printed output = changing the instrument's output bytes; the new header note dates all of that prose). Lead: if you want reading (a), revert the `_part_d` comment hunk.
- **Packages considered:** none — no mechanism specified.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none.
- **Graded:** n/a — no verdict rendered on another's artifact.
- **Decisions needed:** D-2 reading (a) vs (b) — default (b) stands unless ruled otherwise.
- **Receipts:** §1 diffs · §2 AST/ruff/py_compile · §3 scoped pytest (639 passed, 0 failed) · §4 backup (patch md5 `5ed71294a7c72627e7398218b74cc11c`).

## 0. Capability check
All demanded capabilities present: lore reachable (`lore_comms register` OK), Bash/uv/pytest, spike-surreal active. One combined Bash command (collect + patch + `git archive`/`git init` scratch check) was permission-denied; re-run split into simpler commands without `git init` / `rm -rf` — all receipts obtained. grep/rg not used (awk only, per #473).

## 1. Diffs
### 1a. `loremaster/tests/_comms_fakes.py` — final file vs the builder's backup copy (`…/a3c3f778-…/scratchpad/builder-63c-i-a-files/loremaster/tests/_comms_fakes.py`, md5 `82015012…`, equal to the pre-edit tree — verified). These are the ONLY differences; the rest of the file's diff vs HEAD is the builder's, byte-unchanged.
```diff
@@ -260,23 +260,8 @@ class FakeAgentRegistry:
     @staticmethod
     def _shared_identifier_predicate() -> Callable[[str], bool] | None:
-        """⚠ HEAD-RED ACCOMMODATION (amendment-5 FORK-C): ``lorerunes.is_legal_identifier`` — imported at
-        CALL time (so the identity-sweep mutation's patched ``lorerunes`` attribute is what is read) —
-        … (15 further lines: the try/except ImportError removal trigger, MP-3, MP-R4-5, MP-A1 history) …
-        rebind."""
+        """THE shared ``lorerunes.is_legal_identifier`` (module-top import). The ``| None`` return and the
+        caller's ``is not None`` branch are dead since 63c-i-a — collapse at i-b (amendment 12)."""
         return is_legal_identifier
@@ -301,12 +286,10 @@ class FakeAgentRegistry:
-        # cloned teaching message is #102 in a fake). HEAD-RED accommodation: ``is_legal_identifier`` does
-        # not exist until the i-a build (a module-top import would make
-        # every ``_comms_fakes`` consumer a COLLECTION error at HEAD), so it is read at CALL time.
-        # FORK-C (amendment-5, ratified): the identity leg reads the predicate through ONE guarded helper.
+        # cloned teaching message is #102 in a fake).
+        # FORK-C (amendment-5, ratified): the identity leg reads the predicate through ONE helper.
         identifier_decision = FakeAgentRegistry._shared_identifier_predicate()
-        if identifier_decision is not None:  # None at HEAD only — see the helper's removal trigger
+        if identifier_decision is not None:  # dead since 63c-i-a — see the helper's docstring (amendment 12)
```
(The elided middle of the deleted docstring is in the backup copy named above and in the pre-edit copy `…/d0f908a2-…/scratchpad/pre/_comms_fakes.py`.)
Note: the deleted docstring carried the MP-A1 allowlist rationale ("the name occurs ONLY as that module-top import and as bare reads …"). That rationale still lives in the pin itself (`test_agent_registry.py::test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists`); the brief's replacement text was used verbatim.

### 1b. `scripts/probe_governed_63c.py` — tracked, unmodified by the builder (working copy was md5 `b33e2013…` = `git show HEAD:` before my edit), so its full diff vs HEAD is mine:
```diff
@@ -1,4 +1,8 @@
 #!/usr/bin/env python3
+# HISTORICAL INSTRUMENT — measured the PRE-63c-i-a world. Its C-agent control is EXPECTED to
+# fail on >= 63c-i-a (the build implements what it measured); do not treat that failure as a
+# regression. (Its prose below — incl. "agent has NO scope column" — describes that pre-63c-i-a
+# world.)
 """Probe: packet-63c store + code FACTS (govern the comms REMAINDER — the ``brief``
@@ -230,8 +234,8 @@ async def _agent_dd3c(...)
-    # index in generate_agent_ddl (pkt 62), and agent deliberately has NO scope column
-    # (PART D measures that fact). The owner backfill needs only owner_principal.
+    # index in generate_agent_ddl (pkt 62), and — BEFORE 63c-i-a — agent deliberately had NO scope
+    # column (PART D measured that fact; 63c-i-a adds one). The owner backfill needs only owner_principal.
@@ -518,7 +522,7 @@ async def _part_d(...)
-    # Candidate fleet read-filters — REPORT-only (agent has NO scope column; the sidecar
+    # Candidate fleet read-filters — REPORT-only (agent had NO scope column before 63c-i-a; the sidecar
```
The header is a comment block (not a docstring paragraph) so the module docstring stays the first statement. "63c-i-a adds one" was checked against the build's `surreal_schema.py` diff (adds `scope` to agent, `option<>`, plus the `agent_scope` index).
Residual sites of the claim, each with a verdict (awk, case-insensitive "scope col"): comment `_agent_dd3c` → FIXED · comment `_part_d` → FIXED (D-2) · print in `_part_d` ("fragment (agent has NO scope column)") → LEFT (output bytes; covered by header) · print in the summary ("REPORT — no scope col") → LEFT (same) · module docstring PART D bullet → LEFT (covered by header) · `_governed_overlay(BRIEF_TABLE)` comment "scope col persists" → not the claim (brief table).

## 2. Prose-only proof + lint
- AST (pre-edit copy vs final): `_comms_fakes.py` full-AST-equal **False**, AST-equal with every docstring masked **True** (only the docstring constant changed; comments are not in the AST). `probe_governed_63c.py` full-AST-equal **True**.
- `uv run ruff check loremaster/tests/_comms_fakes.py scripts/probe_governed_63c.py` → `All checks passed!`
- `uv run python -m py_compile scripts/probe_governed_63c.py` → OK.
- All 9 other build files `cmp`-identical to the builder's backup copies.

## 3. Scoped pytest (measured 2026-09-25 20:05–20:06 EDT, tree = HEAD `cb2a215` + working tree)
Pre-launch: `free -g` available 58 GiB; no other pytest on the process table (comm-anchored awk); spike-surreal active. Provenance `loremaster.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`. Watchdog (kill by PID below 15 GiB, 5 s poll) never fired, lowest 56 GiB. Instrument pasted verbatim in §5.
```
exit=0 watchdog_fired=0 lowest=56GiB end=2026-09-25 20:06:01
639 passed in 55.40s
```
Collected set includes the row-3 allowlist / shape pin (`test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists`), the effect leg (`test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists`), the propagation legs, the try-positive-control and obfuscation legs, and the 63c-i-a governance classes.

## 4. Backup (refreshed)
- Patch: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d0f908a2-87c7-451f-aeec-4f6e8f28ad59/scratchpad/builder-63c-i-a-final.patch` — md5 **`5ed71294a7c72627e7398218b74cc11c`**. Same shape as the builder's: `git diff --binary` (10 tracked files now, +`scripts/probe_governed_63c.py`) + `git diff --binary --no-index /dev/null lorerunes/lorerunes/identifiers.py` (untracked new file; a bare `git diff --binary` would have silently dropped it). `git apply --check --binary` inside a `git archive HEAD` (`cb2a215`) extract → OK.
- Copies beside it: `_comms_fakes.py` md5 `70e7b52b58f8f489d2da96719fff60b8` · `probe_governed_63c.py` md5 `b0e9c972e30a0c9bb75dc2d3467040fb`. Pre-edit copies: `…/scratchpad/pre/`.
- HEAD moved during my run `5ce89cd` → `cb2a215` (lead report only; `REPORT-lead-63c.md`), no target file touched.

## 5. Instrument (verbatim) — `run_scoped.sh`
```bash
#!/usr/bin/env bash
# run_scoped.sh — prosefix-63c-i-a: the brief's scoped pytest (-n 8) with a PID watchdog (<15 GiB available -> kill by PID).
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d0f908a2-87c7-451f-aeec-4f6e8f28ad59/scratchpad
cd /home/ejprice/PycharmProjects/lore || exit 2
avail_gib() { awk '/^MemAvailable:/{printf "%d", $2/1048576}' /proc/meminfo; }
echo "provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
echo "launch $(date '+%F %T') avail=$(avail_gib)GiB"
uv run pytest -q -n 8 -p no:cacheprovider loremaster/tests/test_agent_registry.py loremaster/tests/test_comms_schema.py loremaster/tests/test_agent_governance_63c_i_a.py > "$S/scoped.log" 2>&1 &
PID=$!
low=$(avail_gib); fired=0
while kill -0 "$PID" 2>/dev/null; do
  a=$(avail_gib); [ "$a" -lt "$low" ] && low=$a
  if [ "$a" -lt 15 ]; then echo "WATCHDOG FIRED avail=${a}GiB — killing $PID"; kill "$PID"; pkill -P "$PID"; fired=1; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc watchdog_fired=$fired lowest=${low}GiB end=$(date '+%F %T')"
tail -3 "$S/scoped.log"
```

## 6. Flags
- F-A: the probe's two PRINTED "NO scope column" strings and its module docstring still state the pre-63c-i-a fact without a date (kept deliberately, §1b). If the lead wants them dated too, it is a string-literal change to the instrument's output — a separate ruling.
- F-B: `_shared_identifier_predicate`'s `| None` return + the caller's `is not None` branch remain as dead code (per amendment 12, collapse at i-b) — unchanged, as instructed.

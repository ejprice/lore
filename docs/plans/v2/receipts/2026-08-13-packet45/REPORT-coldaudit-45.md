# REPORT-coldaudit-45 — Cold audit of packet 45 (tool allowlist)

brief-base v13 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- **VERDICT: GO** — all gates re-confirmed with counts; full-set instructions byte-exact (independently); reduced (lore-dnd) surface coherent (0 disabled tokens served); no removed behavior beyond ruled-acceptable cosmetic description change; 2 mutation proofs re-verified. **Zero defects.**
- Graded: 92286c6 · HEAD-at-report: 92286c6 · SAME
- Packages considered: none — no mechanism specified (read-only audit)
- Reuse ledger: none (read-only audit, no new symbols)
- Gate counts: contract **30/30** · scoped `-n auto` **1646 passed** · ruff **clean** · typecheck exit 1 = **#333 baseline only, ZERO in server.py/config.py** (GREEN DELTA derived) · byte-exact instructions **3374==3374** · reduced surface **0 disabled tokens**
- decisions-needed: none blocking. 6 residuals below (R1 is a builder-report wording correction; R3/R4/R5 are ruled/accepted bounds; R2/R6 are deploy-awareness).
- receipt pointers: gates §Progress log; byte-exact §B2; reduced surface §C; removed-behavior §D; mutation proofs §E; residuals §Residuals table. Instruments pasted in §Instruments.

## Audit plan (from brief)
- A. GATES re-run with COUNTS (contract 30/30; scoped -n auto 1646; ruff clean; typecheck GREEN DELTA)
- B. BYTE-EXACT (CL3 green + not weakened; build_instructions(ALL) == original _INSTRUCTIONS)
- C. TRUST Leg-1 (render lore-dnd reduced surface, eyeball coherence)
- D. DIFF-FIRST / removed-behavior adjudication
- E. Re-verify 2 of 4 mutation proofs

## Progress log
- (start) registered coldaudit-45; HEAD=92286c6; working tree read-only for gates.
- **A1 CONTRACT re-run:** `test_tool_allowlist.py -p no:randomly` → **30 passed in 1.78s** ✓ (matches builder claim).
- **B1 CL3 not weakened:** `git diff cf2a7f7 HEAD -- loremaster/tests/test_comms_tool.py` → **EMPTY**. `_DECLARED_NON_COMMS_PARAGRAPHS` untouched. ✓
- **B2 INDEPENDENT byte-exact:** extracted original `_INSTRUCTIONS` literal from `cf2a7f7:server.py` (an f-string interpolating `_MESSAGE_BODY_MAX_CHARS`), bound the real constant (=4000), compared to live `build_instructions(_ALL_BUILTIN_TOOL_NAMES)` → **BYTE-EXACT MATCH, both 3374 chars** ✓. Instrument: `/tmp/coldaudit45_byteexact.py` (pasted in body §B2 instrument).
- **A2 SCOPED SET (`-n auto`):** `test_tool_allowlist test_mcp_server test_comms_tool test_mutating_set_derivation test_text_hygiene` → **1646 passed in 103.78s, exit 0** ✓ (matches builder's 1646 exactly).
- **A3 ruff:** `uv run ruff check .` → **All checks passed!** ✓
- **A4 typecheck GREEN DELTA (DERIVED, not trusted):** `scripts/typecheck.sh` exit 1 = the #333 baseline (loremaster leg: 102 errors in 8 files; lorerunes leg: 89 in 3 files — all packet-39 auth/posture/roster WIP). DERIVATION: (a) **zero** errors whose erroring file is `server.py` or `config.py`; (b) all 8 erroring loremaster files are **untouched** by the packet-45 diff (`git diff --name-only cf2a7f7..92286c6`); (c) the two touched test files (`test_mcp_server.py`, `test_tool_allowlist.py`) produce zero typecheck errors; (d) `build_mcp_server(server: LoreServer) -> Any` is **byte-identical** cf2a7f7↔HEAD, so the auth tests' `http_client`/`permission_resolver` kwarg errors are pre-existing packet-39 (tests ahead of impl), not packet-45-introduced. ⇒ packet 45 adds ZERO mypy errors. ✓

- **C TRUST Leg-1 (rendered lore-dnd surface, independent build):** instrument `/tmp/coldaudit45_gateC2.py` (pasted §Instruments). Registered builtins == lore-dnd exactly {diff,findings,index,read,search}. **Zero disabled `lore_` tokens** anywhere in served instructions/descriptions/params (word-boundary scan over all 10 disabled names). No gutted headers. Guarded surgery is clean: `lore_search` desc → "…never a raw dump. To read surrounding lines, follow up with lore_read." (drops the `lore_get_symbol` prefer-clause cleanly — NOT a "prefer , follow up" fragment); `lore_read` desc → "Reach for it after a lore_search hit…" (drops `/ lore_get_symbol`); `lore_findings.agent` param drops its lore_comms clause. LADDER collapses to `lore_search (locate) -> lore_read (exact def/span) -> write.` (no dangling arrow). ONLY over-claim = IDENTITY paragraph (Fork-A ruled bound → pkt54). ✓ PASS.
- **D DIFF-FIRST / removed-behavior (P8d dual).**
  - `config.py`: purely ADDITIVE — new `ToolsConfig` (`enabled: list[str] = []`), optional `tools: ToolsConfig | None = None` and `identity: str | None = None`, both default `None`. Existing `lore.yaml` still validates untouched. No removed behavior.
  - `server.py` mechanism: `_gated_tool` registers via `mcp.tool` IFF enabled, else no-op `_skip` — **annotations passed through (no annotation loss); no double-registration** (15 `@_gated_tool` sites, one per built-in). `_MESSAGE_BODY_MAX_CHARS` interpolation **survives** in `_instr_comms` (check 1 ✓). `_validate_tool_allowlist` = Fork B (unknown-name loud-fail naming unknown+known set; empty-total-surface loud-fail), wired BEFORE registration (check 2 ✓). Collision-guard **docstring matches code** — teaches the declared-universe reservation incl. a DISABLED built-in's name (check 3 ✓). Bespoke helpers (`_read_description`, `_comms_identity_agent_description`) never drop a param description — verified 0 empty tool/param descriptions across {full=15, subset=5, lore-dnd=5, single-drop-deadcode=14} (`/tmp/coldaudit45_paramdesc.py`, check 4 ✓). `_comms_identity_agent_description(full)` reproduces the deleted `_COMMS_IDENTITY_AGENT_DESCRIPTION` constant byte-exact across all 3 sites (`/tmp/coldaudit45_paramexact.py`).
  - **Removed-behavior adjudication:** INSTRUCTIONS full-set = **byte-exact preserved** (CL3 anchor) → *preserved-with-pin*. DESCRIPTIONS full-set: **exactly ONE of 15 tool descriptions changed** — `lore_search` (`"prefer lore_get_symbol; to read"` → `"prefer lore_get_symbol. To read"`); the other 14 tool descriptions, the shared `agent=` param (×3), and `lore_verify.qualified_name` are **byte-exact** (`/tmp/coldaudit45_descscope.py` + `_paramexact.py`). The one change is *dropped-deliberately*: design §2.4 explicitly rules **"No byte-exact pin governs descriptions"** and prescribes the cross-ref-into-own-segment restructure; the `;`→`. ` is the minimal edit that lets the `lore_get_symbol` clause drop cleanly on a reduced surface. Substantive content held by substring + token pins → *preserved-with-pin*. No spec-silent gaps. ✓ PASS.
- **E MUTATION RE-VERIFY (2 of 4, real tree, content backup `/tmp/coldaudit45-server.py.BAK` md5 `d86cb869…`, expected-RED declared from `--collect-only` FIRST, #196; restored byte-exact both times).**
  - **A — un-gate `lore_verify`** (`@_gated_tool`→`@mcp.tool`, site `server.py::_register_tools` lore_verify). Declared-RED: `test_registered_builtins_are_EXACTLY_the_enabled_set[subset]`, `[lore-dnd]`, `test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check` → **all 3 RED** (+3 more reduced-surface pins, same-direction). Must-stay-GREEN `[full]` + E1 → **GREEN**. 6 failed / 24 passed. Restored md5 `d86cb869…`, git diff empty. ✓
  - **B — drop a wrap-point space** in `_instr_citations` (`[S:...@hash6] `→`[S:...@hash6]`). Declared-RED: E1 `test_full_set_reproduces_todays_instructions_byte_exact` + CL3 `test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs` → **both RED** (2 failed). Restored md5 `d86cb869…`, git diff empty, contract re-confirmed **30/30**. ✓

## Findings (defects)
**NONE.** No correctness defect, no removed behavior beyond the ruled-acceptable cosmetic `lore_search` description change, no false byte-exact claim on the load-bearing surface (instructions ARE byte-exact). GO.

## Residuals table (noticed, not blockers — lead reads in full per the C1 lesson)
| # | Residual | Severity | Adjudication / action |
|---|---|---|---|
| R1 | Builder report §"What changed" says descriptions are "**Byte-exact on the FULL universe**". That is imprecise: `lore_search`'s full-set tool description changed (`;`→`. `). | trivial (report wording) | NOT a build defect — design §2.4 rules descriptions are substring-pinned, not byte-exact, and the builder's own parenthetical "(so every description substring pin stays green)" shows the real requirement is met. Correcting the record: **exactly 1/15 tool descriptions changed; the rest are byte-exact.** No code action. |
| R2 | On the next deploy the full-universe (dogfood) instance's `lore_search` description shifts `"prefer lore_get_symbol; to read surrounding lines"` → `"prefer lore_get_symbol. To read surrounding lines"`. Deployed surface change. | trivial | Within ruled scope (design §2.4). Instructions unchanged. Cosmetic; improves nothing, degrades nothing. Operator awareness only. |
| R3 | `_instr_freshness` hardcodes `"Impact / dead_code verdicts reflect the INDEX"`, emitted if EITHER `lore_impact` OR `lore_dead_code` is enabled. On a `_FULL − {dead_code}` config (impact on, dead_code off) it names the disabled tool by its **bare word** `dead_code` (not a `lore_` token, so it passes the biconditional). | low | Builder-disclosed (report flag #2). NOT on lore-dnd (both disabled → clause drops; confirmed §C). Accepted bound: grammar guaranteed clean on lore-dnd + byte-exact-on-full; other reduced configs best-effort. **Named re-open trigger:** a future reduced deploy that serves impact-without-dead_code. |
| R4 | On a comms-disabled instance (e.g. lore-dnd) the `agent=` param survives on `lore_findings` with "YOUR registered agent name. Omit it and lore says nothing…", but the whole `agent=` identity feature exists to drive the pending-traffic line pointing at `lore_comms` (disabled). So `agent=` is functionally inert yet still advertised. | low | Not a defect (no disabled token; grammatical; param genuinely exists on those tools). A future reduced-identity deploy might reconsider advertising it. No packet-45 action. |
| R5 | IDENTITY over-claim: default IDENTITY reads "code+docs+graph RAG, durable memory, and fleet ledgers" on lore-dnd — an over-claim uncatchable by any `lore_`-token pin. | ruled bound | Fork-A, RULED/accepted → operator authors `config.identity` at **pkt 54**. Default = today's exact string (no auto-generated over-claim; keeps CL3 byte-exact). Re-open trigger: first reduced deploy shipping a real instance. No packet-45 action. |
| R6 | Packet 45 performed **no deploy**; the #296 live demonstration (disabled tool absent from `list_tools()` AND uncallable) is a separate lead step. | info | Pinned green by `TestDisabledToolIsUncallableOnTheWire`; immune by construction (never-registration). No store/DDL touched. Lead owns the dogfood recreate. |

## Instruments (pasted per brief-base §1 — durable, re-runnable)
All read-only against the real tree except §E (real-tree mutate→content-restore→byte-verify). Paths: `/tmp/coldaudit45_byteexact.py` (B2), `/tmp/coldaudit45_gateC2.py` (C), `/tmp/coldaudit45_paramdesc.py` (D check 4), `/tmp/coldaudit45_descscope.py` + `/tmp/coldaudit45_paramexact.py` (D scope). Content pasted below.

### B2 — independent full-set byte-exact
```python
import ast, sys
from loremaster.server import build_instructions, _ALL_BUILTIN_TOOL_NAMES
from loremaster.messages import MESSAGE_BODY_MAX_CHARS
orig_src = open("/tmp/coldaudit45-server-orig.py").read()  # = git show cf2a7f7:loremaster/loremaster/server.py
tree = ast.parse(orig_src); orig_val = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "_INSTRUCTIONS":
                orig_val = eval(compile(ast.Expression(node.value), "<o>", "eval"),
                                {"_MESSAGE_BODY_MAX_CHARS": MESSAGE_BODY_MAX_CHARS})
live_val = build_instructions(_ALL_BUILTIN_TOOL_NAMES)
print("BYTE-EXACT:", orig_val == live_val, "| lens", len(orig_val), len(live_val))  # True 3374 3374
```
(Gate C/D instruments follow the same pattern: build a full/reduced server via `build_mcp_server(LoreServer(<config with tools.enabled=…>))`, then scan `mcp.instructions` + every `tool.description` + every `inputSchema.properties[*].description`. The lore-dnd config sets `tools.enabled = ["lore_diff","lore_findings","lore_index","lore_read","lore_search"]`; the reach-check confirms `{t.name for t in await mcp.list_tools()} & _ALL_BUILTIN_TOOL_NAMES == that set`.)

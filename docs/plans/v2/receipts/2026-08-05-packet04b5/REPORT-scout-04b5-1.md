# REPORT-scout-04b5-1 — INJECTION #321 "Link-5" render-site containment: terrain inventory

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** (read-only discovery; the only writable artifact is this report).
- Packages considered: none — no mechanism specified (scout inventory; I built/specified no mechanism).
- Graded: `5cedb38` · HEAD-at-report: `5cedb38` · **SAME** (lore index watches `/workspace`@`5cedb381`, `feat/surreal-unification`, last_sweep 235 s before I started — fresh).
- Tool honesty: lore tools loaded first try (no #334 flake). lore-first for structure (`lore_index`/`lore_findings`/`lore_read`); **grep is the honest tool for the `!r` sweep, Link-name string literals, and fence-site exhaustiveness** — used it there and say so per hit. No lore weakness forced a route-around; nothing filed.
- deviations: none.
- **DECISIONS-NEEDED (forks for the contract author / possibly operator — see §6):**
  1. **The existing fence-site invariant (`TestEveryFenceSiteInProductionResolvesToTheONEImplementation`, test_task_read_surface.py) will RED against B-2 as written, in ways its own self-destruct logic did not anticipate.** `fence_width` in `sanitise.py` makes `sanitise.py` a NEW width-rule fence site (a DOOR under `_FENCE_IMPLEMENTATION_MODULE = "render.py"`); and delegating only `search.py::_fence_width` leaves `search.py:1461`'s `_FENCE_CHAR *` construction, so the dated exemption does **not** self-destruct as the ruling expects, and `assert len(sites) == 2` breaks. §6.1.
  2. **The design's six-door hand-list is already a strict subset of the derived door set.** The code-RAG tool family (`symbols.py`, `impact.py`, `store_read.py`, and by class `search.py`/`read_file.py`/`map.py`/`diff.py`) reprs caller-supplied registered-tool params (`qualified_name`, `target`, `path`, `tier`) into served errors — same class as `task_id!r`, outside §B's named set. Is this IN B-1's partition (registered inputSchema universe ⊇ these) or does it need its own B-5 bound? §2.D / §5 / §6.2.
  3. **`_render_recalled_memories` renders `memory.text` fully BARE** (no sanitise, no fence) — a stored-free-text door that is not even control-char contained and is not in the injection registry. In scope for B-1 (it reads stored free text) but stronger than the sanitise_line doors. §2.C / §6.3.
- receipt pointers: Link chain §1 · door set §2 · seam+pins §3 · extraction/clone §4 · `!r` population §5 · tensions §6. Re-derivation greps pasted in §5.

---

## §1 · THE LINK CHAIN (Ruling 10 "forgery closure")

The chain is realised in **`server.py`** (mechanism) with pins in **`test_comms_footer.py`** and **`test_attribution_bound.py`**. There is **no `link 3`** anywhere in code or tests (`grep -rniE 'link[ -]?3'` → 0 hits in `loremaster/`). Links present in CODE are **0, 1, 1b, 2, 4**; #321 adds **5**. (If §B assumes a contiguous 0–4, flag: link 3 is design-doc-only or folded — I did not find its instrument.)

| Link | What it is | Where (file:symbol) | Layer |
|---|---|---|---|
| **0** | The identity-parameter surface is **DERIVED by AST scan, never listed** | `test_comms_footer.py::TestTheIdentityParameterSurfaceIsDERIVEDNotEnumerated` (≈:1656); declaration `LINK0_MEMBERS = ("lore_comms", *DISPATCHERS)` (:1573), `DISPATCHERS = ("lore_tasks","lore_findings","lore_claim_task")` (:190) | test-time coverage check |
| **1** | Registered names are charset-clean by construction | registration path; charset pattern `AGENT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")` (`agents.py:150`) | write-validation |
| **1b** | Charset-gate **every supplied identity at the TOOL seam, before any use** — widened (not cloned) to the optional `agent=` on the ledger tools | `server.py::AppContext._validate_comms_identities` (:5541) → `_validate_comms_charset` (:5590) → `_is_comms_charset_legal` (:5647). Called once, at `comms` dispatch entry (:5214) and at `claim_task` (:3606); the ledger tools (`tasks`/`findings`) route through it too | write-validation |
| **2** | Check on **our OWN registry**: after a resolve, `row.name == asked` | `server.py::_resolved_comms_traffic_line` (:5446) and `_comms_traffic_line` (:5406); pins `test_comms_footer.py` (:1411, :1504) | serving |
| **4** | A render of a caller/identity value routes through a **fence**, never bare; **`repr()` is NOT a neutraliser** | `server.py::_validate_comms_charset`'s reject rides `render_fenced` (:5620-5639); `_comms_identity_teaching` sanitises the registry error (:5474); checkable helper `test_comms_footer.py::_render_...` (≈:1631) | serving |
| **5 (NEW, #321)** | Every caller-supplied string reaching a served answer is **either** charset-gated (1b) **or** render-contained, via a new `render_attributed` | — (to build) | serving |

**What the Link-0 scan enumerates, exactly (`test_comms_footer.py::_scan`, :1697):** it walks **`server.py`'s AST** and collects every `FunctionDef`/`AsyncFunctionDef` that is a **public entry point** (`ENTRY_POINT = not name.startswith("_")`, :1688) AND either (a) declares a parameter named in **`IDENTITY_PARAMETERS = ("agent", "session")`** (:1581) OR (b) calls the registry's `get_agent`. Each such member must contain a call to the seam `_validate_comms_identities` (or be a *pure forwarder* — every identity mention is a keyword arg forwarded to another PUBLIC entry point, `_is_pure_forwarder` :1727); anything else is a **DOOR reported by `file:line`** (:1780).
- ⚠ **Stated bound (verbatim, :1672):** the scan reads `server.py` AST only; a dispatcher accepting an identity under a name **outside `IDENTITY_PARAMETERS`** is invisible. Note `IDENTITY_PARAMETERS` is only `("agent","session")` — **`name` (brief) and `to[]` (recipients) are validated by the seam but are NOT in the coverage scan's param set.**
- ⚠ **The "registered `inputSchema` universe" #321/B-1 names is a DIFFERENT, BROADER scan than this Link-0 identity scan.** This one is over `server.py` AppContext methods × `("agent","session")`. B-1's partition is over **every registered tool's `inputSchema.properties` string params** (the MCP tool registration). The two are not the same derivation; B-1 must build the broader one. Existing infra that already reads a registered tool's `inputSchema` (reusable): `test_task_read_surface.py:2086,2128,2205` (`(tool.inputSchema or {}).get("properties", {})`), enumeration primitive `await mcp.list_tools()` (`test_extension.py:704`, `test_workspace_status.py:971`). The tool→param declaration lives on the `@mcp.tool` wrappers; `ToolSpec.input_schema` at `extension.py:107` / `server.py:10333`.

**What EXACTLY Link 1b charset-gating is (LIVE):** `_is_comms_charset_legal` (`server.py:5647`) is the ONE predicate; `AGENT_NAME_PATTERN.fullmatch` (`fullmatch`, not `match` — finding #210, trailing-`\n` guard). It gates the parameters that **claim** to be identities: `agent`, `session`, `name` (brief), `to[]` (recipients) — refused with a `ValueError` (`_validate_comms_charset`). The SAME predicate is read a second way by `_comms_traffic_line` (:5396) as a cheap **skip** gate in front of the registry read for the free-text attribution columns (`owner`/`actor`/`created_by`) — those are legitimately free text and are **never refused** (docstring :5647-5665). So: **identities are on the charset-gated half; `owner`/`actor`/`created_by` and all other free text are NOT charset-gated and fall to render-containment (Link 5).**

---

## §2 · THE SERVED-ANSWER RENDER SURFACE (the door set)

Every `_render_*` producer is a `@staticmethod`/`@classmethod` on `AppContext` in `server.py` (full list via `grep 'def _render_'`). Containment vocabulary today falls in four tiers: **FENCED** (contained), **SAFE_STR/SANITISE_LINE** (control-char only → same-line forgery door), **BARE f-string** (no wrap → raw door), **`!r`** (repr door, §5). FRESH = a just-passed param echoed inline; STORED = read back from the store.

### A. Task renders (`server.py`)
| site (file:symbol:line) | field(s) | rendered as | tag | verdict |
|---|---|---|---|---|
| `_render_task_rows` :4445 | `subject` | `sanitise_line` | STORED | same-line door |
| `_render_task_rows` :4446 | `owner` | `safe_str` | STORED | same-line door (named #321) |
| `_render_task_rows` :4447 | `blocked_by[]` | `safe_str` per elt | STORED | contained-by-repr-shape (docstring :4437: list repr escapes ctrl; **not** forgery-safe but ids are opaque) |
| `_render_task_detail` :4060 | `description` | **`render_fenced`** | STORED | **contained** |
| `_render_task_detail` :4061 | `created_at` | `sanitise_line` | — | safe (ISO timestamp, not caller text) |
| `_render_task_detail` :4062 | `provenance` (incl. `created_by`) | `safe_str(dict)` | STORED | same-line door (named #321) |
| `_render_claim_result` :4641,:4646 | `owner` (win + owned-loss) | `safe_str` | FRESH/STORED | same-line door (named #321) |
| `_render_claim_result` :4649-4664 | `blocked_by`/`status`/superseded ids | bare | STORED | ids opaque; **docstring flags the BLOCKED branch as a residual gap** (:3634) |
| `_render_task_transition` :4175,:4176 | `actor` | **BARE f-string** | FRESH | **raw door** (no wrap) |
| `_render_supersede_result` :4160 | `dependents[]` | `safe_str` per elt | STORED | same-line door (opaque ids) |
| `_render_transitive_blockers` :4066 | (ids only; `task.id`, blocker ids) | bare | STORED | ids opaque — low risk |
| `_render_rollup` :4225 | composes task/finding rows | via row renders | STORED | inherits row-render doors |

### B. Finding renders (`server.py`)
| site | field(s) | rendered as | tag | verdict |
|---|---|---|---|---|
| `_render_finding_rows` :3397-3401 | `subject`,`kind`,`area`,`category`,`created_by` | `sanitise_line` each | STORED | same-line doors |
| `_render_finding_detail` :3443 | `body` | **`render_fenced`** | STORED | **contained** |
| `_render_finding_detail` :3444 | `created_at` | `_sanitise_line` | — | safe (ISO) |
| `_render_finding_detail` :3445 | `provenance` (agent notes) | `_sanitise_line(str)` | STORED | same-line door |
| `_render_finding_transition` :3258 | `actor` | **BARE f-string** | FRESH | **raw door** (no wrap) |
| `_format_finding_ref` :3272 | caller `id_or_number` (str form) | `_sanitise_line` | FRESH | same-line door |
| `_resolve_or_acknowledge_many` :3346 | `str(error)` (carries caller id/note) | `_sanitise_line` | FRESH | same-line door |
| `_resolve_or_acknowledge_many` :3351 | `actor` | `sanitise_line` | FRESH | same-line door |
| `_render_chain_head` :3368-3373 | delegates to `_render_finding_detail` + fork numbers (ints) | — | STORED | inherits detail doors |

### C. Memory render (`server.py`)
| site | field(s) | rendered as | tag | verdict |
|---|---|---|---|---|
| `_render_recalled_memories` :3562 | `memory.text` | **BARE f-string** | STORED | **RAW door — not even sanitised** (newline/row-forge capable). `kind` :3563 also bare. See §6.3 |

### D. Comms renders (`server.py`) — these DO route through the render seam (`render_line`/`render_join`/`safe_str`), which gives **structural single-line** safety but **NOT provenance containment** (still same-line-forgery-blind for free text).
| site | field(s) | rendered as | tag | verdict |
|---|---|---|---|---|
| `_render_comms_fleet_row` :6642,:6649 | `row.name` | `sanitise_line` | STORED | **charset-gated** (registered name) → not a door |
| `_render_comms_fleet_row` :6625-6634 | `role`,`model`,`status` | `sanitise_line` | STORED | constrained vocab — low risk |
| `_render_comms_fleet_row` :6634 | `last_note` | `sanitise_line` | STORED | **same-line door** (free-text heartbeat note) |
| `_render_comms_fleet_row` :6629 | `task_id[:8]` | `safe_str` | STORED | opaque id — low risk |
| `_render_comms_send` :6836,:6844 | `recipient_names` | `sanitise_line` | STORED | charset-gated names → not a door |
| `_render_comms_send` :6868 | `thread` | `sanitise_line` | FRESH | **same-line door** (`thread` is deliberately NOT charset-validated — `messages.py:641`) |
| `_render_comms_send` :6830,:6843 | `grade`,`session` | `sanitise_line` | — | grade closed-vocab; session charset-gated |
| `_render_comms_drain` :6976 | message `body` | **`render_fenced`** | STORED | **contained** (docstring :6907 "BODIES ARE ALWAYS FENCED") |
| `_render_comms_drain_row` :7088,:7099 | `sender_name` | `sanitise_line` | STORED | charset-gated → not a door |
| `_render_comms_drain_row` :7078,:7080 | `task_id`,`thread` | `sanitise_line` | STORED | thread = **same-line door**; task_id opaque |
| `_render_comms_drain_row` :7091,:7094 | `refs[]` | `safe_str` per elt | STORED | **same-line doors** (caller pointers) |
| `_comms_footer` :5523-5538 | `identity` | `sanitise_line` | STORED | charset-gated resolved name → not a door |
| `_comms_identity_teaching` :5474 | `str(error)` | `sanitise_line` (via `render_line`) | FRESH | registry error; input charset-clean by Link 1b → low risk |
| brief renders `_render_comms_brief_get` :6414 / `_render_comms_brief_publish` | brief `body` | **`render_fenced`** | STORED | **contained** |

**Containment summary:** the four multi-line **bodies** (`task.description`, `finding.body`, message `body`, brief `body`) are the ONLY things `render_fenced`-contained today. Everything else caller-origin is either `sanitise_line`/`safe_str` (control-char only → same-line door) or **bare** (`actor` in the two `*_transition` renders; `memory.text`). Registered identity names (`row.name`, `sender_name`, `recipient_names`, footer `identity`) are the charset-gated half and are NOT doors.

---

## §3 · THE RENDER SEAM + ITS PINS

**`render.py` verbs** (all mint `Rendered`/`SafeLine`; import `FENCE_CHAR`/`MIN_FENCE_WIDTH`/`SafeLine`/`max_backtick_run`/`CONTROL_CHAR_PATTERN` from `sanitise.py`):
- `render_line(template, /, **values: SafeLine|int) -> Rendered` (:147) — literal template + proven values; runtime `CONTROL_CHAR_PATTERN` reject on template + each value; exact placeholder/value key match.
- `render_fenced(body: str) -> Rendered` (:230) — **verbatim** body inside a backtick fence sized `FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)` (:243) — **the extraction target, §4**.
- `render_compose(*parts: Rendered) -> Rendered` (:247) — newline-join already-`Rendered` parts.
- `render_join(sep, parts: Iterable[SafeLine]) -> SafeLine` (:257) — join stays `SafeLine`.
- `Rendered(str)` :96 ; `sanitise.SafeLine(str)` :43 ; `sanitise.sanitise_line` :77 ; `sanitise.safe_str` :68 ; `sanitise.max_backtick_run` :97.

**Seam pins — `test_render_seam_pins.py`:**
- `TestSafeLineRenderedMintPin` (:266) — AST mint pin: any `SafeLine(...)`/`Rendered(...)` construction, `cast`, import-alias, or subclass **outside `sanitise.py`/`render.py`** is flagged. (This is why `render_attributed` must live IN `render.py` to mint `Rendered`.)
- `TestRenderLineTemplateLiteralPin` (:415) — AST template-literal pin: every `render_line`/`render_join` call in the production package passes a **literal `ast.Constant`** template/separator (positional or keyword).
- `TestAssertActionsCovered` (:578) — helper for the injection-registry per-action coverage assertion.

**The injection oracle #321 calls "blind but reads as complete":**
- `assert_render_injection_safe(baseline, hostile_out)` — `tests/render_injection_scaffold.py:82`. **Three assertions, all LINE-STRUCTURE only** (:117-134): (1) hostile output adds no line vs benign baseline; (2) no surviving `Cc/Cf/Zl/Zp` char (after stripping structural `\n`); (3) no `- [#99 open] forged`-shaped line. **None inspects what the surviving text SAYS** → blind to same-line instruction forgery. Threat corpus `_INJECTION_THREAT_CHARS` (:37) + row-forge payload `_ROW_FORGE_PAYLOAD` (:64). The docstring (:92-116) now **explicitly documents this bound** (#321 correction, was falsely "the acceptance oracle").
- `RenderCase` record (:67) + registries:
  - `test_mcp_server.py::TestRenderInjectionRegistry` (:7934); registered set `_INJECTION_REGISTERED_RENDERS` (:7891-7914) covers **rollup.{owner,created_by,kind,report_path,subject,summary}, batch.actor, finding_rows.{subject,kind,area,category,created_by}, task_rows.{subject,owner,blocked_by}, claim_result.{owner_won,owner_lost}**; per-action completeness set `_EXPECTED_INJECTION_REGISTERED_RENDERS = {rollup, batch, finding_rows, task_rows, claim_result}` (:7925).
  - `test_comms_tool.py` (:4132-4165) — a SECOND `RenderCase` registry for the comms renders: register/heartbeat/brief_get/brief_publish/brief_ack/fleet.{name,role,model,task_id,note,session}/send.{recipients,sender,thread,broadcast_session}/drain.{sender,thread}/ack.name. **`drain.body` is deliberately a FENCE case, tracked separately** (:4158 comment; `_FENCE_CASE_LABELS`).
- ⚠ **The bound is ALSO pinned by `test_attribution_bound.py`** (the #137/#138 "pin the miss" instrument, dated `cab7c12`): six measured doors (`_DOORS`, :129) — `claim_result.owner` (won/lost), `task_rows.owner`, `task_detail.owner`, `task_detail.provenance.created_by`, `TaskNotFoundError(task_id!r)` — asserted leaking (`FORGERY in _unfenced(door(FORGERY))`, :186) AND asserted green under the oracle (:232). **RE-OPEN TRIGGER (verbatim, :23): the 04b5 link-5 slice.** A RED here means the slice landed → **delete this file and say so in the wave report** (:26-27). ⚠ Note `_DOORS` is a self-labelled **HAND LIST**, "the artifact this repo has the most receipts against" (:29-35) — NOT the derived inventory.
- Renders NOT in ANY injection registry (neither contained nor oracle-pinned): `_render_task_detail`, `_render_finding_detail`, `_render_transitive_blockers`, `_render_task_transition`, `_render_finding_transition`, `_render_recalled_memories`, `_render_supersede_result`. (task_detail.owner IS pinned by `test_attribution_bound.py` though.)

---

## §4 · THE EXTRACTION + CLONE CHECK

**Extraction target (B-2):** the width rule is inline at `render.py::render_fenced:243`: `fence = FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)`. **`sanitise.fence_width` does NOT exist** (`grep -rn 'fence_width'` → only `search.py::_fence_width` + `test_comms_tool.py::fence_width` local; confirms lead's `not_found`). `sanitise.py` owns the constituents: `FENCE_CHAR` :13, `MIN_FENCE_WIDTH` :14, `max_backtick_run` :97.

**Clone check — BARE/anchor-free grep for `FENCE_CHAR *`, `max_backtick_run`, `MIN_FENCE_WIDTH` across production (per-hit verdict, P8d law):**

| file:line | what | verdict |
|---|---|---|
| `render.py:243` | `FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body)+1)` | **THE extraction target** (render_fenced) |
| `search.py:1430` | `_fence_width` → `max(_MIN_FENCE_WIDTH, _max_backtick_run(source_text)+1)` | **CLONE #1 — a THIRD private copy of the width rule** (`SearchPipeline._fence_width`) |
| `search.py:1461` | `fence = _FENCE_CHAR * self._fence_width(source_text)` (`_base_format`) | **CLONE #1's fence CONSTRUCTION** — the `_FENCE_CHAR *` here survives a mere `_fence_width` delegation (see §6.1) |
| `search.py:97-108` | re-exports `_FENCE_CHAR`/`_MIN_FENCE_WIDTH`/`_max_backtick_run` from `sanitise` (aliased) | re-export only, not a compute — safe |
| `server.py:2869` | `len(line.strip()) >= _MIN_FENCE_WIDTH and set(...) == {_FENCE_CHAR}` | **fence DETECTION** (parses/recognises a fence in text), NOT construction — not a width clone |

There is **already an AST invariant** governing this exact clone class: `test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation` (:3101). It derives all fence sites **name-blind** (calls to `max_backtick_run`/`_max_backtick_run`; `FENCE_CHAR`/`_FENCE_CHAR` multiplications; bare backtick-run literals ≥3) and requires each in `_FENCE_IMPLEMENTATION_MODULE = "render.py"` (:3098) OR the **dated exemption `_FENCE_SITE_EXEMPTION = "search.py"`, `_EXPIRES = "04b-3"`** (:3093-3094). It carries a self-destruct pin (:3205) that goes RED when search.py stops being a fence site. **This invariant + B-2 collide — see §6.1 (the top finding).** Note `search.py` unification was already scoped INTO this slice by the FALSIFIER-CHECK comment (:2730-2734): "`loremaster.sanitise` gains the shared helper, `SearchPipeline`'s private width rule delegates to it, `_render_finding_detail` calls it, and this render calls it." (`_render_finding_detail` already routes through `render_fenced` today, :3443 — that leg is done.)

---

## §5 · THE `!r` / BARE-F-STRING POPULATION REACHING SERVED ANSWERS

**Re-derived counts at `5cedb38` (grep — the honest tool for a non-symbol textual seam; pasted so re-runnable):**
```
grep -rn '!r}' loremaster/loremaster/ | wc -l            # → 291   (matches lead)
grep -rn 'task_id!r' loremaster/loremaster/tasks.py | wc -l  # → 19  (#321 said 8; GREW — hand-list already stale)
```
Per-file totals: server.py 57 · tasks.py 32 · findings.py 22 · agents.py 21 · floor_calibration/store.py 16 · shellout.py 14 · store/surreal.py 12 · briefs.py 11 · render.py 9 · memory/local.py 9 · calibration/baseline.py 9 · symbols.py 8 · store/_txn.py 7 · messages.py 7 · read_file.py 6 · diff.py 6 · impact.py 5 · config.py 5 · store/lease.py 4 · map.py 4 · index/{surreal_manifest,snapshots}.py 4 each · graph_surreal.py 4 · store_read.py 3 · index/indexer.py 3 · search.py 2 · calibration/engine.py 2 · {source/local_directory,scout,index/cli,floor_calibration/domain,auth}.py 1 each.

**The predicate for a DOOR:** an `!r` reaches a served-answer door iff (a) its enclosing string is **raised/returned onto a tool return** AND (b) the repr'd token is a **caller-supplied free-text value that is NOT charset-gated**. Identities (`agent`/`session`/`name`/`recipient`) are charset-gated → their `!r` is NOT a forgery door (no space/backtick/`=`/newline expressible).

### DOORS (caller free text → served answer, per-site verdict)
**tasks.py — all served via `TaskNotFoundError`/`ValueError` at the tool seam:**
- `:1488,:1637,:1689,:1707,:1912,:2456,:2534` `task_id!r` (7 × `TaskNotFoundError`) — **served / DOOR** (class-B teaching error, #321 named).
- `:1700,:1807,:1814,:1819,:1826,:1831,:1857,:1862,:1867,:1920,:1957,:2450` `task_id!r` in transition/supersede/walk ValueErrors — **served / DOOR** (caller id, 12 sites).
- `:1862,:1863,:1867` `target!r` (caller's illegal status string) — **served / DOOR** (caller free text).
- `:630,:2042` `limit!r` — **served / weak-DOOR** (caller value, usually int).
- `:1701,:1858,:1862,:1867` `current!r`/`fresh_status!r` (status **read from store**, closed vocab) — **served / not-a-door** (system value).
- `:1921,:1958` `row.get(_COL_SUPERSEDED_BY)!r` (stored RecordID) — **served / not-a-door**.
- `:844,:845,:853,:854` url/namespace/database (config) — **served / not-a-door** (config; B-5 OUT).
- `:2611` `_COL_CREATED_AT!r` (constant) — **not-a-door**.

**findings.py:**
- `:1014,:1029,:1116` `finding_id!r`/`id_or_number!r` (`FindingNotFoundError`) — **served / DOOR** (caller ref).
- `:1090,:1091,:1096` `target!r` (caller illegal status) — **served / DOOR**.
- `:591` `value!r` — **served / DOOR-candidate** (a validation reject of a caller field value; verify the field).
- `:782,:826` `limit!r` — **served / weak-DOOR**.
- `:890,:891,:897` `current_id`/`successor_id`/bare-id (stored ids, "chain is corrupt") — **served / not-a-door** (system ids).
- `:663` `finding_id!r vanished` (post-create system id) — **not-a-door**.
- `:1022,:1023,:1024` current/fresh_status/target closed-vocab — target=DOOR (above), current/fresh=not-a-door.
- `:455,:456,:464,:465` conn string / `:1220` `_COL_CREATED_AT` — **not-a-door** (config/const).

**messages.py:**
- `:672` `grade!r` (caller's illegal grade) — **served / DOOR** (caller free text — grade may be arbitrary before validation).
- `:691` `session!r` — **served / not-a-door** (charset-gated by Link 1b upstream).
- `:945` `message_id!r vanished` (system id) · `:502-510` conn string — **not-a-door**.

**agents.py:**
- `:800` `target!r` (caller illegal status) — **served / DOOR**.
- `:541,:549,:555,:636,:640,:650,:746,:811` `name!r` (agent name) — **served / not-a-door** (charset-gated identity).
- `:640,:641,:642,:650,:651,:652` `role!r`,`spawned_by!r`,`existing.role!r`,`existing.spawned_by!r`,`name+'2'!r` — **served / DOOR-CANDIDATE**: `role` and `spawned_by` are caller-supplied but **NOT in Link 1b's validated set** (`_validate_comms_identities` covers agent/session/name/to only). `spawned_by` is an identity-shaped value that is NOT charset-gated. **Verify with the contract author.**
- `:629,:679,:776,:936` `agent_id!r vanished`/`column!r` (system id/const) · `:416-424` conn — **not-a-door**.

**briefs.py:** `:687,:817,:836,:843,:910` `name!r` (brief name) — **served / not-a-door** (charset-gated). `:642` `brief_id!r vanished` (system) · `:443-451` conn · `:1290` `_COL_CREATED_AT` — **not-a-door**. → **briefs.py contributes NO doors.**

**config.py:** `:309,:318,:714,:796,:833` tier/env-var-name/api-key-env — **served / not-a-door** (config values; **B-5 OUT** with trigger).

**server.py (57):** the render-layer `!r` are mostly in ValueErrors for shape rejects. Notable: `:4214` `since!r` (rollup cursor, `_parse_rollup_since`) — **served / weak-DOOR** (caller cursor string); the comms foreign-param / set_status / limit rejects (:5211,:5241-5269) repr **action names and param names** (closed vocab / code constants) — **not-a-door**. (server.py `!r` warrants the contract author's own pass; I did not verify all 57 individually — stated bound.)

### CODE-RAG tool family — DOORS the six-door hand-list omits (major, §6.2)
- `symbols.py:724,:727,:730,:732` `qualified_name!r` (served by `lore_get_symbol`/`lore_verify` not-found) — **served / DOOR** (caller free text).
- `impact.py:462,:464,:479,:480` `target!r` (served by `lore_impact` not-found) — **served / DOOR**.
- `store_read.py:304,:318,:327` `path!r`/`tier!r` (served by `lore_read` guard/not-found) — **served / DOOR-candidate** (path caller-supplied; tier validated).
- By the same class (verify): `read_file.py` (6), `map.py` (4), `diff.py` (6), `search.py` (2), `scout.py:918` `kind!r` (internal command kind — **not-a-door**).

### Subsystem `!r` — per-FILE verdict (spot-checked; STATED SCOUT BOUND)
I did **not** render an individual verdict on all ~136 subsystem `!r` sites — a hand-table of 291 is exactly the artifact this repo has receipts against, and the reach-as-a-checked-variable enumeration is **B-3's derived runtime instrument**, which should own it. Per-file class from spot-check:
- `store/surreal.py`, `store/_txn.py`, `store/lease.py`, `graph_surreal.py`, `floor_calibration/*`, `calibration/*`, `index/*`, `memory/local.py`, `search.py` (conn strings), `logging_setup.py`: repr **internal values** — engine responses, RecordIDs, config paths/urls, DDL/SQL, column constants, calibration ids. **not-a-door class** (infra errors; not caller-comms free text). `shellout.py` (14): reprs **source-code symbol names** from the exec-seam AST gate — internal, **not-a-door**.
- **⚠ This is a per-file CLASS verdict, not a per-site clear.** The DOOR set the B-3 sweep must cover is: the tasks/findings/messages/agents domain doors above + the code-RAG family + the render-layer same-line/bare doors of §2. Anything in the "internal" files that turns out to surface a caller string is a B-3 finding, not a scout clear.

---

## §6 · TENSIONS / CONTRADICTIONS WITH §B'S PREMISES (surfaced prominently, per brief)

### 6.1 — TOP FINDING: the existing fence-site invariant collides with B-2 as written
`test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation` derives fence sites name-blind and requires each in `render.py` or the dated `search.py` exemption. **B-2 (extract `sanitise.fence_width`, unify search.py) trips it three ways:**
1. **`sanitise.py` becomes a NEW width-rule fence site.** `fence_width` in `sanitise.py` *calls* `max_backtick_run` (also in sanitise.py) → the AST scan records `sanitise.py` as a fence site (it scans CALLS, and `max_backtick_run`'s *definition* is a `FunctionDef`, not a Call, so sanitise.py is invisible today). Since `sanitise.py ∉ {render.py, search.py}`, the MAIN pin (`:3176`) reports it a **DOOR**. Fix requires editing `_FENCE_IMPLEMENTATION_MODULE` — but #321/B-2/the FALSIFIER comment all place `fence_width` in **`sanitise.py`**, while the invariant's ONE implementation is **`render.py`**. The width rule's home and the fence-construction's home become **two modules**; the invariant conflates them.
2. **The dated exemption does NOT self-destruct on a mere `_fence_width` delegation.** `search.py:1461` builds the fence with `_FENCE_CHAR * self._fence_width(...)`. Delegating `_fence_width` → `sanitise.fence_width` removes the `_max_backtick_run` CALL from search.py but **leaves the `_FENCE_CHAR *` construction at :1461** → `search.py` STAYS a fence site → the self-destruct pin's `assert search.py in sites` (`:3221`) stays GREEN (premise NOT gone), so the ruling's expected "RED → delete the exemption" never fires. To actually retire search.py from the scan, its **whole fence construction** must route through the shared implementation (e.g. call `render_fenced`), which is a bigger change than "delegate the width rule."
3. **`assert len(sites) == 2` (`:3228`) breaks.** After extraction: `{render.py (fence + width via render_attributed/render_fenced), sanitise.py (new width call), search.py (still FENCE_CHAR* at 1461)}` = **3 sites** → RED.

**Fork for the contract author (possibly operator):** (a) Does `fence_width` live in `sanitise.py` (per #321/B-2 — then rework the invariant to a SET of sanctioned modules distinguishing width-home from construction-home), or in `render.py` (contradicts the design text)? (b) Does 04b5 route `search.py`'s **entire** fence construction through the shared seam (retiring the exemption cleanly, satisfying the self-destruct), or keep the exemption and rework the count/premise? The design's B-2 mutation-proof scope is only "render_fenced + render_attributed"; the existing invariant + FALSIFIER comment scoped search.py INTO this slice. These disagree. **This must be settled in the contract, with the invariant's pins updated in the SAME diff (contract-first: the pins are the OLD world's certification — P8d rename-sweep law).**

### 6.2 — B-1's partition universe is broader than §B's six-door hand-list
The design derives the door set as "the complement of the Link-0 scan over the **registered `inputSchema` universe**." The **registered inputSchema universe includes the code-RAG tools** (`lore_get_symbol.qualified_name`, `lore_impact.target`, `lore_read.path`, `lore_search.query`, …), whose free-text params ALREADY reach served errors via `!r` (`symbols.py`, `impact.py`, `store_read.py` — §5). So a faithful B-1 partition pulls these in. Either they are **IN** (render-contained like the rest — a larger change than §B's task/finding/comms focus suggests) or they need an **explicit B-5 bound with a re-open trigger**. §B names config/indexed-source/older-rows as OUT but is silent on the code-RAG tool params. **The contract must state which half of the partition they fall in.** (Same class: this is exactly why #321 built the design derivation-based — the hand-list is already a strict subset.)

### 6.3 — `_render_recalled_memories` is a stronger door than the sanitise_line class
`memory.text` renders **fully bare** (`f"- {memory.text}"`, `server.py:3562`) — not sanitised, not fenced. It is stored caller free text (`lore_remember`) reaching a served answer (`lore_recall`), and it is in **no** injection registry, so it is not even control-char pinned. It IS in B-1's scope (a registered-tool-param stored value reaching a served answer). Flagging because it is materially worse than the `owner`/`actor` same-line doors (it can inject real newlines / forged rows today, which the design's fenced-or-attributed containment must cover).

### 6.4 — minor
- The `_render_finding_transition:3258` and `_render_task_transition:4176` **`actor`** fields are **bare** (no wrap at all) — not just same-line doors but raw. Both must route through `render_attributed`.
- `_render_claim_result`'s docstring (:3634) already self-flags the BLOCKED/UNOWNED branch's `blocked_by`/`status` as "a residual gap for the PKT-03 tree-wide sweep" — a pre-existing known door the design should absorb or re-scope.
- The dated-exemption message string still says `"04b-3"` (`_FENCE_SITE_EXEMPTION_EXPIRES`, :3094) while the executing packet is **04b5** — cosmetic, but the self-destruct message will name the wrong packet; update it in the same diff.
- `test_attribution_bound.py` is dated/measured at `cab7c12`; its class-B mirror pin (`:196`) asserts `tasks.py` still raises `f"no task with id {task_id!r}"` — still true at `5cedb38`. When B-2 routes that raise through `render_attributed`, that mirror pin AND the whole file must be **deleted with a wave-report note** (its own re-open instruction, :26).

---

## Appendix — files read (provenance)
`render.py` (full), `sanitise.py` (full), `test_attribution_bound.py` (full), `render_injection_scaffold.py` (full); `server.py` spans :3256-3460, :3549-3665, :4016-4235, :4418-4475, :5140-5270, :5330-5640, :6599-6730, :6801-7135; `test_task_read_surface.py` :2720-2870, :3060-3340; `test_comms_footer.py` :1655-1795; `search.py` :1420-1465. Greps (bare, anchor-free) for Link literals, charset, `FENCE_CHAR`/`max_backtick_run`/`MIN_FENCE_WIDTH`, `!r}`, `inputSchema`, `IDENTITY_PARAMETERS`, `DISPATCHERS`, `def _render_`. All dated at HEAD `5cedb38`.

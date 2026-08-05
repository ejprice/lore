# REPORT-sweep-desc-04b4-1

brief-base v10 read

## SUMMARY BLOCK
- state: **done**
- deviations: the dedicated Write tool is blocked for REPORT-*.md in this environment; brief
  mandates this path + an idle-gate hook checks it, so it was written via Bash and the findings
  are ALSO returned as text to the lead.
- **FALSE hits: 1** — `lore_findings.note` (description at `server.py:9925-9927`) claims the
  note is *"Ignored by the other actions"*, but the dispatcher forwards it to **`acknowledge`**
  (server.py:3214) and the ledger RECORDS it (findings.py:903-923). Stale since the PKT-06 §3
  widening (server.py:3207-3210 comment: *"previously dropped"*).
- UNSURE hits: 0
- Params swept: **100** across **15 served MCP tools** (every `Field(description=...)` on every
  built-in `@mcp.tool` in `server.py`). No `@mcp.tool` was excluded; no extension-contributed
  tools carry a `Field(description=...)` in `server.py` (they register via
  `_register_extension_tools`, server.py:10251, out of this file's scope).
- Tool used: this is a **non-symbol textual seam** (prose inside `Field(description=...)` string
  literals) — per the dogfood protocol §3b, **grep + Read was the honest instrument** and lore's
  symbol graph could not own it. Stated out loud as required. lore tools (`ToolSearch "+lore"`)
  were loaded and available; the cross-check of governing rules was done by reading the
  dispatchers directly.
- Packages considered: none — no mechanism specified (read-only enumeration).
- Graded: `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · HEAD-at-report:
  `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · **SAME** (same as my read; nothing moved).
- receipt POINTERS: FALSE hit -> section "FALSE / UNSURE hits"; full table -> section "Verdict
  table"; method -> section "Method & rule sources".

---

## FALSE / UNSURE hits (called out so they are not lost in the table)

### FALSE - `lore_findings.note`
- **Description** (`server.py:9925-9927`, in the `findings()` tool's `note` param):
  > "An optional free-text note recorded with a 'resolve' / 'wontfix' transition. **Ignored by
  > the other actions.**"
- **Actual rule**: the findings dispatcher forwards the top-level `note` to **THREE** status
  edges - `acknowledge` (server.py:3214), `resolve` (3221), `wontfix` (3228) - and
  `FindingLedger.acknowledge(id_or_number, actor, note=None)` **records it** (findings.py:903-923,
  docstring: "note: An optional free-text note recorded alongside the transition (PKT-06 §3 -
  mirrors resolve/wontfix's existing note)").
- **Why FALSE**: `acknowledge` is one of "the other actions", and it does **not** ignore `note` -
  it records it. The description omits `acknowledge` and affirmatively says it is ignored. This is
  the exact #319 class: a served param description that is FALSE vs the behavior it describes.
- **Corroborating tell**: the *tool-level* `lore_findings` description already says it right -
  `server.py:8829`: "'acknowledge' / 'resolve' / 'wontfix' (by id_or_number + actor, **with an
  optional note**)". So the tool blurb was updated for PKT-06 §3 and the `note` **param** blurb
  was not. (`note` IS correctly ignored by `report`/`query`/`get`/`chain_head`; the two batch
  edges use per-item notes from `items`, not this top-level param - so only `acknowledge` is the
  miss.)
- **Suggested fix** (for the contract author, not applied - read-only): change to "recorded with
  an 'acknowledge' / 'resolve' / 'wontfix' transition. Ignored by the other actions."

No UNSURE hits - every rule flagged was traced to its enforcing line.

---

## Method & rule sources (how each verdict was grounded)

Verdict vocabulary:
- **TRUE** - the description's acceptance/refusal/clamp/strict-to-action claim matches the enforced rule exactly.
- **FALSE** - the description claims a rule the code does not enforce, or contradicts it.
- **NO-RULE** - the param carries no acceptance/refusal/clamp/strict rule (free-form value, semantic filter, or default-only); nothing to be false about. (A NO-RULE row may still note a runtime guard the description does not *claim* - that is a signal for the contract author, not a defect.)

Governing-rule seams cross-checked (all at graded SHA):
- **Comms strict-param contract**: `_COMMS_ACTIONS` spec table `server.py:7230-7278` (each action's
  `params`/`required`/`limit_cap`); foreign-param + required enforcement `server.py:5172-5182`;
  `set_status` closed-vocabulary reject `5202-5208`; `limit` below-min raise + above-cap clamp
  `5193-5198`; `agent`/`session` universal-never-foreign `5174-5175`. Message caps enforced in
  `messages.py` - body `677-680`, refs count `790-792`, ref len `797-800`, thread/task_id len
  `804-808`, ack note `752-754`. Grades `surreal_schema.py:565`.
- **Tasks strict-param**: identity charset `server.py:3739`; `since` rollup-only `3747-3750`;
  `limit` rollup+query `3751-3756` (`_TASK_ACTIONS_ACCEPTING_LIMIT` = `(rollup, query)`,
  server.py:1179); `max_depth` blockers-only `3757-3762` (`_TASK_ACTIONS_ACCEPTING_MAX_DEPTH` =
  `(blockers,)`, 1186); `items` create_many-only `3763-3766`; required args via `_require_arg`
  (subject/description 3784-3785, created_by 3787, actor 3830, task_id 3808/3813/3828/3836);
  `summary`/`report_path` done-only via `_validate_done_summary` (tasks.py, rules 1-5).
- **Findings strict-param**: identity `server.py:3154`; `items` batch-only `3155-3162`; required
  via `_require_finding_arg` (subject/area/category/created_by 3178-3188, actor 3174/3213/3220/3227);
  `_require_finding_ref` for id_or_number `3201/3204/3212/...`; `note` forwarded to
  acknowledge/resolve/wontfix `3214/3221/3228`.
- **Numeric bounds** (search k/budget, recall k, dead_code max_results, impact depth, map budget):
  pydantic `ge=`/`le=` in the `Field(...)` itself - a reject, and the min/max text is f-string-
  DERIVED from the SAME constants, so it cannot drift.
- **read `tier`** `_validate_tier` (server.py read handler); **read `line_end`** clamp
  `store_read.py:23-24` (past EOF clamped; only non-positive/inverted/start-past-EOF is a hard
  error). **diff `limit`** clamp to `[_MIN_LIST_LIMIT=1, _MAX_LIST_LIMIT=500]` `diff.py:653` /
  clamp expr `max(1, min(500, limit))`. **index `tier`** raise-without-reconcile + `_validate_tier`
  (server.py index handler). **remember `kind`** `_VALID_MEMORY_KINDS` check (server.py; kinds =
  {fact, decision, gotcha, uncertainty, ongoing}, memory/backend.py:56-62); **`importance`**
  out-of-range reject (backend); **`trust`** `MemorySource` pydantic Literal
  {authoritative, experiential} (memory/backend.py TrustLevel).

Line numbers are at the graded SHA; a later edit above any of these shifts them.

---

## Verdict table

One row per (tool, parameter). `desc@` = the description text line(s). Description text trimmed.

### lore_search
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_search.query | 8850-8853 | "Natural-language description of what you're looking for... phrase it as intent" | none | NO-RULE | free-form NL query; no gate |
| lore_search.k | 8862-8865 | "Maximum hits (default 8, min 1, max 50)..." | 8860-8861 ge/le | TRUE | pydantic ge=_MIN_COUNT(1) le=_MAX_SEARCH_K(50); text derived from same constants |
| lore_search.path | 8872-8877 | "EXACT indexed file path... a miss teaches the nearest real indexed path..." | none | NO-RULE | free-form path; miss-teach is a response behavior, not an arg gate |
| lore_search.tier | 8884-8886 | "Optional exact source tier... Omit for unscoped" | none | NO-RULE | optional scope filter; not validated at this seam |
| lore_search.wait_for_fresh | 8893-8898 | "...bounded-wait... needs a 'path' filter to know what to wait on" | none | NO-RULE | bool flag passed to pipeline; "needs a path" is operational guidance (no reject) |
| lore_search.detail_level | 8905-8908 | "'auto'/'summary'/'source'... Only these three values are accepted" | type DetailSelector (Literal) | TRUE | pydantic Literal rejects other values |
| lore_search.budget | 8917-8922 | "Claude-token ceiling (default 1100, min 200, max 6000)..." | 8915-8916 ge/le | TRUE | ge=_SEARCH_BUDGET_FLOOR(200) le=_SEARCH_BUDGET_CAP(6000); text derived |
| lore_search.caller_model | 8929-8934 | "Optional Claude model name... no measured ratio => generation constant + honest notice" | none | NO-RULE | any string accepted; unknown => honest-notice behavior, not a reject |

### lore_get_symbol
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_get_symbol.qualified_name | 8968-8973 | "A Python dotted name - MODULE-QUALIFIED or BARE..." | none | NO-RULE | free-form name; "raises not-found" is a tool outcome, not an arg gate |

### lore_verify
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_verify.qualified_name | 8999-9004 | "A Python dotted name to verify..." | none | NO-RULE | free-form name |
| lore_verify.expected_file_path | 9011-9015 | "Optional... whole-path-segment suffix match... Omit to skip" | none | NO-RULE | optional; matching semantics, not a gate |
| lore_verify.expected_signature_fragment | 9022-9026 | "Optional... substring of the header... Omit to skip" | none | NO-RULE | optional; matching semantics |

### lore_remember
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_remember.text | 9052-9055 | "The note to remember... self-contained" | none | NO-RULE | free-form |
| lore_remember.refs | 9062-9066 | "Optional chunk Key:s... fold into the id... Omit if none" | none | NO-RULE | optional list; folds into id (behavior) |
| lore_remember.metadata | 9073-9076 | "DEPRECATED... flattened to key=value labels... Omit if none" | none | NO-RULE | accepted (deprecated); flattened |
| lore_remember.kind | 9083-9085 | "one of fact/decision/gotcha/uncertainty/ongoing (default 'fact'). An unknown kind is rejected by name." | server.py _VALID_MEMORY_KINDS check | TRUE | if kind not in _VALID_MEMORY_KINDS: raise ValueError(...naming value+valid set); set = those 5 (backend.py:56-62) |
| lore_remember.trust | 9092-9095 | "'authoritative' or 'experiential'... Omit to leave the backend default" | MemorySource Literal | TRUE | TrustLevel = Literal['authoritative','experiential']; a 3rd value => pydantic reject (server.py remember docstring confirms) |
| lore_remember.importance | 9102-9104 | "a fraction in [0,1]... An out-of-range value is rejected by name" | backend reject | TRUE | remember() docstring + backend: out-of-range importance raises ValueError naming it |
| lore_remember.supersedes | 9111-9113 | "Optional id of an existing memory this note replaces... Omit for a plain save" | none | NO-RULE | optional id |
| lore_remember.labels | 9120-9122 | "Optional flat labels... Omit if none" | none | NO-RULE | optional list |

### lore_recall
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_recall.query | 9154-9157 | "Natural-language description of the fact to recall..." | none | NO-RULE | free-form NL |
| lore_recall.k | 9166-9168 | "Maximum notes (default 5, min 1, max 100)" | 9164-9165 ge/le | TRUE | ge=_MIN_COUNT(1) le=_MAX_RECALL_K(100); text derived |
| lore_recall.kind | 9175-9177 | "Optional exact-match filter... one of fact/decision/... Omit to recall every kind" | none | NO-RULE | recall-side FILTER (no reject of unknown kind; unmatched => empty) |
| lore_recall.labels | 9184-9187 | "Optional ALL-semantics label filter... composes with 'kind'" | none | NO-RULE | filter semantics |

### lore_claim_task
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_claim_task.task_id | 9211-9213 | "opaque id... Must be an open, unblocked, unowned task to win" | claim CAS | NO-RULE | any id string; win/lose is a runtime compare-and-set outcome, accurately described (not an arg-shape gate) |
| lore_claim_task.owner | 9220-9222 | "Your agent/session identity to record as owner on a winning claim" | none | NO-RULE | free-form; also the sole footer attribution |
| lore_claim_task.agent | 9227 (_COMMS_IDENTITY_AGENT_DESCRIPTION, defn 1228-1237) | "YOUR registered agent name... any WRITE ends with a pending-traffic line... matched, never authenticated" | footer server.py:5245-5347; charset claim_task L36 | TRUE | every claim the blurb makes is enforced: write=>footer (_with_comms_footer on writes=int(result.claimed)), omit=>silence (R8(2)), exact-match-not-auth (row.name==attribution). Undescribed extra: agent IS charset-validated (_validate_comms_identities) - no false claim |
| lore_claim_task.session | 9230 (_COMMS_IDENTITY_SESSION_DESCRIPTION, defn 1238-1244) | "orchestration session your agent= is registered under... disambiguates a shared name" | registry resolution | TRUE | ambiguous-name behavior enforced by registry; charset-validated; no false claim |

### lore_tasks
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_tasks.action | 9263-9271 | "'create'/'create_many'/'query'/'get'/'blockers'/'transition'/'supersede'/'rollup'" | 3851-3854 | TRUE | 8 actions listed = _TASK_ACTIONS (1164-1173); unknown => raise naming valid set |
| lore_tasks.task_id | 9278-9281 | "required for 'transition','supersede','get','blockers'. Omit for create/query/rollup/create_many" | _require_arg 3808/3813/3828/3836 | TRUE | required-for enforced; unused (not refused) elsewhere, matching "Omit" guidance |
| lore_tasks.subject | 9288-9289 | "required for 'create' and 'supersede'" | _require_arg 3784/3839 | TRUE | enforced both actions |
| lore_tasks.description | 9296-9299 | "required for 'create' and 'supersede'" | _require_arg 3785/3840 | TRUE | enforced both |
| lore_tasks.created_by | 9305-9307 | "required for 'create','create_many','supersede'" | _require_arg 3779/3787/3841 | TRUE | enforced all three |
| lore_tasks.actor | 9314-9316 | "required for 'transition'" | _require_arg 3830 | TRUE | enforced |
| lore_tasks.status | 9323-9326 | "For 'transition' target status (done requires summary); For 'query' optional filter" | transition 3829, query 3800, _validate_done_summary | TRUE | consumed by transition (required) + query (filter); done=>summary cross-ref accurate |
| lore_tasks.owner | 9333-9335 | "For 'query', optional owner filter. Omit otherwise" | query 3800 | NO-RULE | query filter (also a footer attribution); no refusal, "Omit" is guidance |
| lore_tasks.blocked | 9342-9344 | "For 'query', optional blocked(True)/unblocked(False) filter" | query 3800 | NO-RULE | query filter; no refusal |
| lore_tasks.blocked_by | 9351-9353 | "For 'create', optional ids the new task depends on" | create 3786 | NO-RULE | optional create input; no refusal |
| lore_tasks.since | 9360-9364 | "For 'rollup' ONLY (rejected for every other action)..." | 3747-3750 | TRUE | if action != rollup and since is not None: raise |
| lore_tasks.limit | 9371-9376 | "For 'rollup' and 'query' ONLY (rejected for every other action)..." | 3751-3756 | TRUE | _TASK_ACTIONS_ACCEPTING_LIMIT=(rollup,query); this is the #319 acute case, corrected in 0ff05ed - now matches |
| lore_tasks.max_depth | 9383-9389 | "For 'blockers' ONLY (rejected for every other action)..." | 3757-3762 | TRUE | _TASK_ACTIONS_ACCEPTING_MAX_DEPTH=(blockers,); reject enforced |
| lore_tasks.items | 9396-9402 | "For 'create_many' ONLY (rejected for every other action)..." | 3763-3766 | TRUE | if action != create_many and items is not None: raise |
| lore_tasks.summary | 9409-9413 | "For 'transition' to status='done' ONLY: MANDATORY... Rejected for every other transition target" | _validate_done_summary rules 1-3,5 | TRUE | done requires non-blank single-line <=300; non-done rejects supplied summary |
| lore_tasks.report_path | 9420-9424 | "For 'transition' to status='done' ONLY: OPTIONAL single-line... Rejected for every other transition target" | _validate_done_summary rules 4,5 | TRUE | done: optional non-empty single-line; non-done rejects |
| lore_tasks.agent | 9428 (shared, 1228-1237) | shared identity blurb | footer + charset | TRUE | as claim_task.agent |
| lore_tasks.session | 9431 (shared, 1238-1244) | shared identity blurb | registry | TRUE | as claim_task.session |

### lore_comms  (every param is strict-to-action via _COMMS_ACTIONS 7230-7278 + foreign/required enforcement 5172-5182)
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_comms.action | 9480-9487 | "'register'/'heartbeat'/'brief_get'/'brief_publish'/'brief_ack'/'fleet'/'send'/'drain'/'ack'" | 5144-5148 | TRUE | 9 actions = _COMMS_ACTIONS keys; unknown => raise naming valid set |
| lore_comms.agent | 9494-9497 | "short identifier - REQUIRED for every action... Safe charset only: {pattern}" | type str (required) + _validate_comms_identities 5150 | TRUE | required positional; charset via AGENT_NAME_PATTERN; pattern rendered dynamically |
| lore_comms.session | 9504-9510 | "REQUIRED for 'register'... Optional for every other action... 'fleet' scopes the listing" | register.required 7234; universal 5174 | TRUE | required in register spec; universal-never-foreign; fleet scopes via session_scope |
| lore_comms.role | 9516-9519 | "REQUIRED for 'register'. Write-once..." | register.required 7234 | TRUE | in register.required; foreign elsewhere; write-once enforced registry-side |
| lore_comms.model | 9525 | "For 'register': the model identifier... Optional" | register.params 7233 | TRUE | register-only optional; foreign elsewhere |
| lore_comms.spawned_by | 9530-9532 | "For 'register': identity that spawned... Optional, write-once" | register.params 7233 | TRUE | register-only; foreign elsewhere |
| lore_comms.task_id | 9539-9543 | "For 'register': fleet task id... For 'send': label <= N chars" | register.params 7233; send.params 7262; len messages.py:804-808 | TRUE | accepted for register+send; foreign elsewhere; send label capped at _MESSAGE_POINTER_MAX_CHARS |
| lore_comms.note | 9550-9557 | "For 'heartbeat'... 'brief_publish'... 'ack' (<= N chars)" | heartbeat/brief_publish/ack .params; ack note cap messages.py:752-754 | TRUE | accepted for exactly those 3; foreign elsewhere; ack note cap enforced |
| lore_comms.status | 9564-9568 | "For 'heartbeat' ONLY... active/idle/input_required/retired... orphaned/STALE never legal" | heartbeat.params 7239 | TRUE | heartbeat-only (foreign elsewhere); value-set/derived-reject enforced registry-side (registry.touch - asserted by description, not independently re-run in this sweep) |
| lore_comms.name | 9575-9578 | "For brief_get/brief_publish/brief_ack... Optional for brief_get (default 'project'); REQUIRED for publish/ack" | brief_get.params; brief_publish/brief_ack .required 7247-7253 | TRUE | matches exactly: optional-get, required-publish/ack; foreign for others |
| lore_comms.body | 9585-9590 | "For brief_publish: REQUIRED non-blank. For send: REQUIRED non-blank, cap N (over-cap REJECTED)" | brief_publish/send .required 7248/7266; cap messages.py:677-680 | TRUE | required both; blank+over-cap => MessageBodyError |
| lore_comms.version | 9597-9599 | "For 'brief_ack' ONLY... REQUIRED" | brief_ack.required 7253 | TRUE | in brief_ack.required; foreign elsewhere |
| lore_comms.limit | 9607-9611 | "For 'fleet' and 'drain'... above the cap CLAMPS (fleet 200, drain 50)" | fleet/drain .params + limit_cap 7258/7271; clamp 5193-5198 + handlers | TRUE | accepted fleet+drain; below-min raises; above-cap clamps to 200/50; foreign elsewhere |
| lore_comms.to | 9618-9622 | "For 'send': recipient names... omit/[] => broadcast... resolved in YOUR session... all-or-nothing" | send.params 7262 | TRUE | send-only; broadcast + session-scoped + all-or-nothing enforced (_comms_send/_comms_resolve_recipients 5850-6000) |
| lore_comms.grade | 9629-9632 | "For 'send': REQUIRED, one of {sorted(_MESSAGE_GRADES)}..." | send.required 7266 | TRUE | required for send; value-set rendered dynamically from _MESSAGE_GRADES; validated in ledger (IllegalMessageGradeError) |
| lore_comms.thread | 9639-9643 | "For 'send': thread (defaults to session), <= N chars..." | send.params 7262; len messages.py:804-808 | TRUE | send-only; over-cap => MessagePointerError |
| lore_comms.refs | 9650-9656 | "For 'send': pointers, <= M entries, each <= N chars... Over either bound refused" | send.params 7262; messages.py:790-800 | TRUE | send-only; count>_MESSAGE_REFS_MAX_COUNT or entry>_MESSAGE_POINTER_MAX_CHARS => MessagePointerError |
| lore_comms.set_status | 9663-9668 | "For 'send': pass 'input_required'... Any other value is refused" | send.params 7262; reject 5202-5208 | TRUE | send-only; non-input_required => teaching ValueError |
| lore_comms.seqs | 9675-9678 | "For 'ack': REQUIRED - the message seqs to discharge..." | ack.required 7276 | TRUE | in ack.required; foreign elsewhere |
| lore_comms.peek | 9685-9688 | "For 'drain': read without stamping..." | drain.params 7270 | TRUE | drain-only; foreign elsewhere |

### lore_read
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_read.tier | 9738-9741 | "source tier... validated against configured tiers (an unknown tier lists the valid ones)" | _validate_tier (read handler) | TRUE | self._validate_tier(tier) raises ReindexTierError naming valid tiers |
| lore_read.path | 9748-9750 | "Tier-relative path... Containment-guarded - never absolute or '../'" | StoreReadTool containment | TRUE | containment guard rejects absolute/'../'/escaping symlink (store_read.py; StoreReadError) |
| lore_read.line_start | 9757-9758 | "First line, 1-based inclusive. Omit to start at line 1" | (guard exists, undescribed) | NO-RULE | states default only (accurate); non-positive/start-past-EOF hard-errors in _resolve_span but the description makes no false claim about it |
| lore_read.line_end | 9765-9767 | "Last line, 1-based inclusive. Omit => EOF; an end past EOF is clamped" | store_read.py:23-24 / _resolve_span | TRUE | end past EOF IS clamped (tolerant); matches the clamp claim |

### lore_diff
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_diff.since | 9792-9794 | "BASE snapshot id to diff FROM... Omit to LIST snapshots" | dispatch (list vs diff) | NO-RULE | free-form id; presence selects list-vs-diff mode (behavior), no value gate |
| lore_diff.until | 9801-9803 | "TARGET snapshot id... Omit => live 'now'. Ignored when 'since' omitted" | dispatch | NO-RULE | free-form id; "Ignored when 'since' omitted" is accurate mode behavior |
| lore_diff.limit | 9810-9813 | "For the LISTING... default 20; clamped to the engine's [1, 500] bound. Ignored when diffing" | diff.py:653 clamp | TRUE | clamped = max(1, min(500, limit)) (_MIN_LIST_LIMIT=1, _MAX_LIST_LIMIT=500); ignored on the diff path |

### lore_findings
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_findings.action | 9842-9847 | "'report'/'query'/'get'/'chain_head'/'acknowledge'/'resolve'/'wontfix'/'resolve_many'/'acknowledge_many'" | 3231-3235 | TRUE | 9 actions = _FINDING_ACTIONS (1384-1393); unknown => raise naming valid set |
| lore_findings.id_or_number | 9853-9855 | "number (int) OR opaque id (str). Required for get/chain_head/status edges" | _require_finding_ref 3201/3204/3212/3219/3226 | TRUE | required-for enforced |
| lore_findings.subject | 9862-9863 | "short title - required (non-empty) for 'report'" | _require_finding_arg 3178 | TRUE | required for report |
| lore_findings.body | 9870-9873 | "longer description - OPTIONAL for 'report'; None => empty string" | 3184 | TRUE | body if body is not None else "" - optional, defaults to "" |
| lore_findings.area | 9880-9882 | "required (non-empty) for 'report'; optional exact filter for 'query'" | _require_finding_arg 3186; query 3197 | TRUE | required-report + query-filter both accurate |
| lore_findings.category | 9889-9890 | "required (non-empty) for 'report'" | _require_finding_arg 3187 | TRUE | required for report |
| lore_findings.created_by | 9897-9899 | "required (non-empty) for 'report'" | _require_finding_arg 3188 | TRUE | required for report |
| lore_findings.kind | 9907-9909 | "For 'report' defaults 'friction'; For 'query' optional exact-kind filter" | 3185 default; query 3197 | TRUE | kind or _DEFAULT_FINDING_KIND on report; query filter |
| lore_findings.actor | 9916-9918 | "required for 'acknowledge'/'resolve'/'wontfix'" | _require_finding_arg 3213/3220/3227 (+batch 3174) | TRUE | required for status edges (and the batches) |
| **lore_findings.note** | **9925-9927** | **"recorded with a 'resolve' / 'wontfix' transition. Ignored by the other actions."** | **3214/3221/3228** | **FALSE** | **note is also forwarded to AND recorded by `acknowledge` (3214; findings.py:903-923). Description omits acknowledge and says it's ignored - stale since PKT-06 §3 (3207-3210)** |
| lore_findings.status | 9934-9937 | "For 'query', optional exact-status filter (open/acknowledged/resolved/wontfix). Omit otherwise" | query 3197 | NO-RULE | query filter; consumed only by query, ignored (not refused) elsewhere; "Omit" is guidance |
| lore_findings.limit | 9943-9945 | "For 'query', max findings (default 100), ordered by number ascending" | query 3197 | NO-RULE | query default; no bound/clamp/refusal claimed |
| lore_findings.supersedes | 9952-9954 | "For 'report', optional id/number of a finding this one reframes" | report 3189 | NO-RULE | optional report input; no refusal |
| lore_findings.items | 9961-9964 | "For 'resolve_many'/'acknowledge_many' ONLY (rejected for every other action)..." | 3155-3162 | TRUE | if action not in (resolve_many, acknowledge_many) and items is not None: raise |
| lore_findings.agent | 9969 (shared, 1228-1237) | shared identity blurb | footer + charset 3154 | TRUE | as claim_task.agent |
| lore_findings.session | 9972 (shared, 1238-1244) | shared identity blurb | registry | TRUE | as claim_task.session |

### lore_index
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_index.reconcile | 10017-10021 | "Force a reconcile sweep before status. False (default) = pure status read, NEVER sweeps" | index handler | TRUE | reconcile=False => status-only (never sweeps); True => sweep-then-status |
| lore_index.tier | 10028-10032 | "Limit sweep to one tier... Only honoured with reconcile=True - passing tier without reconcile=True raises" | index handler raise + _validate_tier | TRUE | if tier is not None and not reconcile: raise ReindexTierError; with reconcile => _validate_tier names valid tiers |

### lore_dead_code
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_dead_code.max_results | 10078-10083 | "default 100, min 1, max 1000... elided count returned" | 10075-10076 ge/le | TRUE | ge=_MIN_COUNT(1) le=MAX_DEAD_CODE_MAX_RESULTS(1000) (graph.py:132-133); text derived |

### lore_impact
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_impact.target | 10118-10122 | "symbol or module to profile... Raises not-found (naming target) if nothing indexed" | none | NO-RULE | free-form name; not-found is a tool outcome |
| lore_impact.depth | 10132-10136 | "default 1, min 1, max 4... depth>1 switches to per-module rollup" | 10129-10130 ge/le | TRUE | ge=_IMPACT_DEPTH_MIN(1) le=_IMPACT_DEPTH_MAX(4); rendered schema confirms 1/4; text derived |

### lore_map
| tool.param | desc@ | description (trimmed) | rule@ | VERDICT | evidence |
|---|---|---|---|---|---|
| lore_map.budget | 10165-10169 | "default 2500, min 200, max 6000... elision trailer" | 10162-10163 ge/le | TRUE | ge=_MAP_BUDGET_FLOOR(200) le=_MAP_BUDGET_CAP(6000); rendered schema confirms; text derived |
| lore_map.focus | 10176-10181 | "Optional bare/dotted symbol to re-center... Omit for whole-corpus" | none | NO-RULE | optional re-center input |
| lore_map.tests | 10188-10193 | "Include the [test]-marked section... default excludes test modules" | none | NO-RULE | bool toggle; behavior described, no gate |
| lore_map.changed_since | 10199-10205 | "Optional snapshot id... unknown id teaches lore_diff's listing rather than raising" | none | NO-RULE | free-form id; unknown => teach (not reject) - accurate |
| lore_map.full_symbols | 10212-10224 | "Serve full symbol roster instead of per-module cap... budget still applies" | none | NO-RULE | bool toggle; budget-honesty is behavior, not an arg gate |
| lore_map.caller_model | 10231-10237 | "Optional model name to re-denominate the budget... unmeasured => generation constant + honest notice" | none | NO-RULE | any string; unknown => honest-notice, not a reject |

---

## Counts
- Total params swept: **100**
- TRUE: **58**  ·  FALSE: **1**  ·  NO-RULE: **41**  ·  UNSURE: **0**
- Per-tool param counts: search 8 · get_symbol 1 · verify 3 · remember 8 · recall 4 ·
  claim_task 4 · tasks 18 · comms 20 · read 4 · diff 3 · findings 16 · index 2 · dead_code 1 ·
  impact 2 · map 6  = 100.

## Bounds of this sweep (so it does not over-claim about itself)
- Scope is server.py's built-in @mcp.tool param descriptions ONLY. Extension-contributed
  tools (_register_extension_tools, server.py:10251) register elsewhere and carry no
  Field(description=...) in this file - if a future extension adds served params, they are NOT
  in this table.
- Value-vocabulary enforcement delegated to ledgers/registry (comms status value set, grade
  values) was cross-read to its docstring/constant but NOT re-run live in this pass; the
  strict-to-action layer at the dispatcher WAS traced to its enforcing line for every comms param.
- Line numbers are exact at graded SHA 5c5ff7a; any edit above a cited line shifts it.

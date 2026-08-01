# 2026-08-01 — agent comms fix: the four measurement probes (findings #292 / #294)

Receipts for the session that measured **why agents cannot reach the lore MCP tools**, and
what actually works. Filed here because a `REPORT-*.md` at the repo root is an address that
stops resolving the moment the wave closes (repo `CLAUDE.md` §ARCHIVE REPORTS).

## What was believed before, and why it was wrong

Finding **#292** (packet 44) derived that agent types carrying an explicit `tools:` allowlist
get no MCP tools, and offered a two-way remedy: *"add the MCP surface to the affected
definitions, **or** widen them to `*`."* Its measured evidence covered only the `*` side. The
INDEX Log compressed this further, to *"an explicit `tools:` allowlist gets no MCP tools,
`Tools: *` does"* — a sentence that is **true of the cases tested and false as a general
rule**. #292 also asked, in its own "SUGGESTED (not ruled)" list, for the step #266 skipped:
*"spawn one agent of each type whose only job is to run the load line and report what it
gets."* These four probes are that step.

## The measured taxonomy — THREE cases, not two

| definition shape | agent types | deferred pool | MCP tools |
|---|---|---|---|
| `tools: *` / unrestricted | `general-purpose`, `claude` | full | present |
| **EXCLUSION** list (*"all tools except …"*) | `Explore`, `Plan` | **~130 names, every server** | **reachable via `ToolSearch`; no literal naming needed** |
| **ALLOWLIST** (explicit `tools:`) | 5 tdd-family, `contract-adversary`, `package-scout`, 2 odoo scouts | **EMPTY** | **only what is named LITERALLY** |

The broken population is exactly and only the **allowlist** shape.

## The probes

| report | cell measured | verdict |
|---|---|---|
| `REPORT-probe-literal-mcp-1.md` | `odoo-consumer-scout` (allowlist **with** 7 literal `mcp__odoo-code__*` names) · **sonnet** | **A** — present AND callable; live output pasted |
| `REPORT-probe-plain-allowlist-1.md` | `tdd-contract` (allowlist with **no** MCP name) · **opus** | **#294 confirmed** — zero MCP tools; deferred pool empty of *everything* |
| `REPORT-probe-confound-leg3-1.md` | `odoo-consumer-scout` · **opus** | **DEFINITION** — closes the model confound |
| `REPORT-probe-explore-grant-1.md` | `Explore` (exclusion list) | **GRANTED** — called `lore_index` and `lore_comms register` for real |

Every leg carried a negative control proving its grant was **enforced** rather than silently
widened (`Edit` absent while `Write` worked, etc.), so no result is a fallback-to-everything
false positive.

## Facts worth not rediscovering

1. **Literal fully-qualified MCP names in an allowlist WORK.** This is the option #292 did not
   know it had. `mcp__*` as a wildcard entry is accepted without error and grants **nothing**
   (packet 44's `REPORT-mcpwildcard-probe.md`).
2. **`ToolSearch` is not a gateway.** For an allowlist agent the deferred pool is empty, so
   `ToolSearch` reaches nothing at all. The comment in seven agent definitions asserting
   otherwise (*"ToolSearch = the gateway to deferred MCP tools … See lore finding #266"*) is
   false, and was never verified when written — #292's own headline.
3. **An allowlist entry does not guarantee the tool.** `Grep` and `Glob` are listed by seven
   definitions and delivered to none of them; they are disabled session-wide. **Only execution
   is evidence of possession** — "it is in the `tools:` list" is not.
4. **The harness emits three distinct error strings, and the difference is diagnostic** —
   discovered by `probe-plain-allowlist-1` after the discriminator its brief specified turned
   out to be undecidable:
   - `No such tool available: Grep. Grep is not available in this session — …` → disabled session-wide
   - `No such tool available: Edit. Edit exists but is not enabled in this context.` → known tool, withheld by grant
   - `No such tool available: mcp__odoo-code__odoo_code_search` *(bare, no second sentence)* → **name never enrolled**
   Every `mcp__*` name lands in the bare class. This is the cheapest instrument for the class
   and it works even when the deferred pool is empty.
5. **A second, independent breakage compounds it:** the canonical `ToolSearch` load line at
   `~/.claude/CLAUDE.md:344` names **three tools that do not exist**. Even a correctly-granted
   agent pasting it loads only `lore_get_symbol`. Derived by `scripts/lore_tool_name_currency.py`
   against a live `tools/list`: **35 dead names across 4 files**.

## ⚠ A false clear this session produced, and caught

The first version of `scripts/lore_tool_name_currency.py` reported **9** corpses and a **clean
`CLAUDE.md`**. Both of its patterns were anchored, and both anchors failed on the exact file
that motivated the script: `\blore_` cannot match `lore_search_code` inside
`mcp__lore_<slug>__lore_search_code` (`_` is a word character, so there is no word boundary),
and an *"only scan lines mentioning lore"* gate dropped bare prose lines like
`` - `search_code` — semantic code/doc search ``. Unanchored, the same script reports **35**.
The 26 it had been missing included every hit in `CLAUDE.md`.

This is repo `CLAUDE.md`'s instrument lesson reproduced inside the guard built for this class:
**when you anchor a pattern, you miss exactly the prose sites the gates cannot see.** The
script now scans unanchored and over-reports by design — a false positive costs one glance, a
false clear costs the whole guard.

# Runbook — the shortest path to WORKING Google Auth

**Status as of 2026-08-01 (`4e330a2`): Google Auth is NOT working. No implementation exists.**
A contract exists (480 pins / 444 RED / 36 GREEN) and a ruled design exists. This file is the
restart path, written so the next session re-derives nothing.

---

## Why it is not working — four blockers, ranked by who can move them

| # | Blocker | Who | Movable by an agent? |
|---|---|---|---|
| 1 | **The claude.ai connector's client secret** | operator | ❌ **Never.** It exists only in the GCP console and the operator's records. Google supports **no** Dynamic Client Registration (verified: its AS metadata has no `registration_endpoint`), so there is no automated path. This alone makes "working end-to-end" unreachable without a human. |
| 2 | **The hades SNI route** | operator / explicit authorization | ⚠ Deliberately not taken. `192.168.64.1` is the router; its Caddy also fronts Nextcloud, JupyterLab **and odoo-code's live claude.ai connector**. Outward-facing, shared blast radius, and its Caddyfile was unreadable from this session. |
| 3 | **Finding #296** — where per-principal tool gating lives | operator | ✅ **Now answerable.** See below. |
| 4 | **No implementation** | agent | ✅ Buildable, with the caveat below. |

---

## Blocker 3 is solved — but the answer arrived AFTER the contract was written

Four adversary passes defeated four attempts to gate tools inside FastMCP, all one root cause:
`_setup_handlers` binds handlers at construction, so a post-construction install is live
in-process and **dead on the wire**.

**The escape, verified at SDK source (`mcp` 1.27.2): never REGISTER the tool.**
`list_tools()` is `list(self._tools.values())`; `call_tool` is `get_tool(name)` raising
`ToolError("Unknown tool")` on a miss (`fastmcp/tools/tool_manager.py:41-43`, `:88-93`). Both are
bound at `__init__` and both read `ToolManager._tools` **at call time**. An unregistered tool is
absent from `tools/list` *and* uncallable, with no handler to shadow and no dispatch order to
author. **The class cannot recur through this door.**

Config is per-deploy and #296 is per-principal, so they reconcile by running **two processes** —
the hosted one's `lore.yaml` simply does not enable the mutating tools. Full scoping:
`docs/design/2026-08-01-multi-user-lore-proposal.md` §2.

⚠ **Consequence for the contract: its posture section is built against the OLD design** (a scoped
`ToolManager`, R13/R16). If the never-register path is ruled, those pins are reshaped a fifth
time — **do not build to them as they stand.** The rest of the contract is unaffected.

---

## The recommended restart order

### Step 1 — rule #296 (operator, one decision)
Options and recommendation: `2026-08-01-multi-user-lore-proposal.md`. Recommendation is the
role split, i.e. never-register.

### Step 2 — build the AUTH CORE, which is NOT blocked on #296
This is the part that survived four adversarial passes untouched, and it is most of the RED:

- Google token validation — POST to `oauth2.googleapis.com/tokeninfo` with the token **in the
  body** (never the URL; odoo-code leaked tokens into its journal that way), `email_verified`
  accepting bool `True` *and* string `"true"`, `aud` equality with **unset = hard error**.
- The **roster** — mtime-checked on **every** verification, no residual revocation window.
  Fail closed and loud on missing / unreadable / empty / malformed; a malformed line refuses the
  **whole** roster, never a silently-shorter one.
- **Identity minting (#206)** — Google branch sets `subject` (Google `sub`, falling back to the
  normalised email), `claims={"iss": "https://accounts.google.com"}`, `expires_at`. API-key branch
  sets `client_id=f"api_key:{name}"`, `subject=name`.
  ⚠ **Do NOT copy odoo-code's mint** — it uses a constant `client_id` and discards the login it
  holds, collapsing every principal to one identity.
- **Composition** — `AuthSettings` + `TokenVerifier`; delete `BearerAuthMiddleware` and the
  `AuthVerifier` ABC (its `verify()` is sync and it would 401 the discovery endpoint it wraps).
  One `EdgePolicy` derivation feeding both the Origin guard and `TransportSecuritySettings`.

Contract: `docs/plans/v2/receipts/2026-07-31-packet39/REPORT-contract-39-auth-1.md` §8 lists the
exact edits outside the contract's writable set (verified complete by adversary pass 2).

### Step 3 — the edge (this box only)
A dedicated `--network=host` Caddy for lore. **Measured: the mcp pod's Caddy CANNOT reach lore** —
`host.containers.internal` reaches the host's external addresses, never its loopback, and lore is
on `127.0.0.1:9202` and must stay there. Port `9443` was free; the wildcard cert and key are at
`~/docker/nginx/STAR_firehawktransam_org*` (⚠ **expires 2026-11-25** — a connector-availability
dependency with no ACME, since port 80 is closed).

### Step 4 — operator switches 1 and 2
The hades route, then the connector + secret. Only after these is auth *working*.

---

## Traps that will re-bite, each already paid for once

- **`lore.yaml` is gitignored** — "config rollback is a git operation" is FALSE for it. `cp -a`
  before editing. Baseline to restore: no `auth:` key at all; `server: {host: 127.0.0.1, path: /mcp,
  port: 9202}`; `.mcp.json` headerless.
- **#165 is open** — a container recreate re-mounts `/source` and re-breaks boot. The running
  `lore-lore` carries a hand-rolled fix. Capture
  `podman inspect lore-lore --format '{{.Config.CreateCommand}}'` **before** any recreate.
- **The posture flip 401s every local session** unless the `.mcp.json` key wiring ships in the same
  wave. One process, one posture — there is no hosted-only split until packet 36.
- **A refusal pin must observe the EFFECT, not the exception** (#295). Ask: *"if the guard ran
  AFTER the thing it guards, would this pin still pass?"*
- **Run the adversary.** It returned INSUFFICIENT on all four passes and found a real blocker every
  time — including a read-only posture that was green at 448/448 and refused nothing.

---

## Scratch trees (outside the repo, kept deliberately)

`/home/ejprice/adv39-4`, `/home/ejprice/scratch/adv39`, `/home/ejprice/scratch/adv39d`, plus
`scratch/adv39*.py`. These are the **executable** wrong builds behind WB30/WB48/WB93/WB100 — the
reports describe them, these run them. Fastest way to re-verify the class is dead once the
never-register path lands. Safe to delete if disk is needed; the findings survive in the reports.

# Packet 39 design — Google OAuth for lore (hosted read-only surface)

**Author:** design-sidecar-39-1 (Fable), 2026-07-31, at working tree `5a850c3` (branch
`feat/surreal-unification`).
**Authority:** operator override, verbatim: *"Goal set: working Google Auth. I'm going to bed,
do not prompt me for anything. Have the designer decide."* This doc therefore RULES the open
forks rather than recommending; every ruling carries rationale and a named re-open trigger.
**Amended same-session (2026-07-31), four lead pings:** R12 (a further operator override —
the allowlist substrate moves out of `lore.yaml`, §3-R12) · §7 (the annotations derivation
confirmed against the FastMCP signature; the test hand-list is deleted, not corrected;
filed as finding **#291**) · an R12 freshness revision (per-cache-miss floor) that the
fourth ping **REVERSED**: the strong per-verification ruling is RESTORED — no residual
window (§3-R12) — plus the §4 scope-check property fix, §8 row 15 (ruling S1), and §15
(contract-pass rulings S2–S6/B1/B4).
**Inputs:** the approved investigation (`~/.claude/plans/check-and-see-if-polymorphic-pebble.md`
— an unrecoverable address by standing law; its load-bearing content is restated or superseded
HERE, and this doc is the durable record) · `docs/plans/v2/39-hosted-security.md` ·
`loremaster/loremaster/auth.py` (read in full at `5a850c3`) · the INSTALLED `mcp` SDK
(`mcp[cli]>=1.27`, site-packages read 2026-07-31) · odoo-code's production verifier
(`~/PycharmProjects/pp-odoo/mcp/src/code_mcp/auth.py`, symbols cited below) · fresh edge
measurements (2026-07-31, §2 — they **falsify part of the investigation's Phase-0 topology**).

---

## 0. Ruling summary

| # | Fork | Ruling |
|---|---|---|
| R1 | packet 35 dependency | **Waived in full** (design AND build legs) for packet 39 |
| R2 | GCP OAuth client | **Reuse the Price Paper client now**; migration trigger named |
| R3 | Hostname | **`lore.firehawktransam.org`** |
| R4 | Edge shape | **hades SNI route → lore-caddy (host network, this box) → `127.0.0.1:9202`**. The podmanuser-nginx option is DEAD (not needed — see §2) |
| R5 | `client_id` config | **Inline `str`**, required, no default, never `SecretStr`/`resolve_secret` |
| R6 | Origin under M-1 uncertainty | Hosted posture ships `https://claude.ai` + `https://claude.com` as default allowed origins; absent-Origin stays allowed. Correct under both M-1 outcomes |
| R7 | Domain-shaped allowlist entry | **Unconstructible** — config validation error, never silent no-match |
| R8 | Read-only derivation | From the EXISTING typed per-tool `ToolAnnotations.readOnlyHint`, enforced via minted scopes; exhaustive-classification pin |
| R9 | Host/Origin validation (F5) | SDK `TransportSecuritySettings` enabled; ONE derivation feeds both it and `OriginValidationMiddleware` (which stays outermost) |
| R10 | Identity (F3) | Google branch mints `subject` + `claims={"iss": …}` + `expires_at`; api-key branch mints `client_id="api_key:<name>"`, `subject=<name>` |
| R11 | Allowlist fail mode (F4) | Fail CLOSED at every leg: blank path unconstructible; missing/empty/invalid roster at boot ⇒ refuse to boot; at runtime ⇒ deny ALL, loudly — each leg pinned separately |
| R12 | Allowlist substrate (operator override, 2026-07-31) | **mtime-watched flat file, outside the repo AND the image**, bind-mounted ro; `lore.yaml` carries only its PATH; add/revoke requires NO recreate and NO rebuild |

**What is operator-side and cannot be done without them:** §12. **Bounds of this design
(what I could not measure tonight):** §13.

---

## 1. Threat model — paste into the verifier module docstring verbatim

> **Who this gate is FOR:** an operator-curated set (≤50) of principals, each proving control
> of an **individually allowlisted** Google identity via a Google-verified access token,
> reaching lore's **read-only** tool surface over the public internet through the claude.ai
> web connector — plus the existing named-API-key principals (local agents and LAN clients),
> who retain the full surface. It exists so that an honest engineer cannot accidentally
> expose a writable or unauthenticated lore to the internet: every non-loopback path is
> token-gated, every Google principal is individually named, and every mutating tool refuses
> hosted principals **by construction** (derived from the tool registration, not a list).
>
> **Who it is NOT for / what it does NOT provide:**
> - **Per-content ACL.** Every admitted principal reads the WHOLE corpus of the project lore
>   serves — for this repo that includes `CLAUDE.md`, every packet, every receipt, project
>   memory, and the findings ledger, which is a written map of this system's known security
>   bounds. Admission is all-or-nothing per project. Do NOT reason from "the lore repo is
>   public" — this posture must hold for any project it is applied to (pp-odoo,
>   demand_intelligence), whose trees are not public.
> - **An allowlisted principal who turns hostile.** They can read everything and exfiltrate
>   it; the read-only posture only caps them at reading.
> - **Anthropic.** claude.ai holds the Google token server-side and proxies every call.
>   Accepted and written down; not a defect.
> - **Tenancy / DoS / per-caller rate limiting.** The real client IP is not recoverable at
>   this edge (measured, investigation M12). Ledgered bound.
> - **A hostile author with commit access** — findings #137/#138 govern that class and their
>   re-open triggers were consulted for this packet (see design doc §11).
>
> **Mechanical verdicts** (so an auditor need not re-litigate intent):
> - "a clever attacker forges an `Origin`" — NOT a defect (Origin was never a control
>   against non-browser clients; the token is the gate).
> - "an unlisted `@gmail.com` account gets in" — BLOCKER.
> - "`/.well-known/oauth-protected-resource/mcp` is world-readable" — REQUIRED (RFC 9728 §3.1).
> - "any hosted principal can call a mutating tool" — BLOCKER.
> - "an api-key principal can call mutating tools through the hosted port" — INTENDED
>   (api keys are the local/LAN trust anchor; leakage of a key is the same accepted risk
>   LAN_BEARER already carries, and rotation is the remedy).
> - "a Google-verified token whose `aud` is a different OAuth client is accepted" — BLOCKER
>   (the `aud` check is the only thing distinguishing OUR consent from any Google app's).
> - "a principal removed from the roster file is admitted on ANY later verification" —
>   BLOCKER. There is no residual window (R12, restored ruling): the roster mtime is
>   `stat`-checked on EVERY verification, cache hits included, and admission re-evaluates
>   against the live roster; the token cache caches GOOGLE's verdict, never admission.
> - **KNOWN BOUND — anonymous path enumeration in `LAN_BEARER`** (ruling S1, design §8
>   row 15): an unauthenticated request to an unknown path returns 404, not the old
>   blanket 401, so the (two-path, publicly documented) route surface is enumerable
>   wherever no edge fronts lore. Accepted: the disclosure is a route list, not data;
>   closing it would re-wrap the app in the blanket gate whose removal RFC 9728
>   discovery requires. Re-open trigger: the day lore serves a route whose mere
>   existence is sensitive, or a posture ships without an edge in front of it.

Self-check applied (the askable form): *"does this safety claim hold on every table/type/
branch this ruling touches, or only the one I derived it on?"* — the read-only claim is
derived over ALL registered tools via the exhaustive-classification pin (§7), not over a
sample; the fail-closed claim is pinned at both legs (§6).

---

## 2. Measured topology, 2026-07-31 — corrects the investigation's Phase-0

Commands and raw outputs are in the session report
(`docs/plans/v2/receipts/<archive-date>-packet39/REPORT-design-sidecar-39-1.md` once
archived). Findings, each dated 2026-07-31:

- **The real public edge is `hades.firehawktransam.org` = `192.168.64.1` — the router
  itself — NOT a listener on this box.** The investigation's Phase-0 narrowing ("the public
  edge is a listener on THIS box") is **falsified**: no process on this box listens on any
  `:443`; probes of `148.75.227.102:443` (the public wildcard A target) show **SNI-dependent
  backends** — SNI `labs.firehawktransam.org` answers as nginx/1.28.1 (jupyter-proxy,
  `.100:8443`), SNI `mcp-dev.pricepaper.com` answers with the `*.pricepaper.com` cert
  (mcp-caddy via the `.102:443→:8444` nft redirect), and ANY other SNI (probed: `lore.…`,
  `zzz-bogus.…`, `mcp-dev.firehawktransam.org`) gets a catch-all `HTTP/2 200` from a Caddy
  presenting the `*.firehawktransam.org` cert. Connecting directly to `192.168.64.1:443`
  reproduces the catch-all → the SNI edge runs ON hades.
- **hades is FreeBSD 14.3-RELEASE-p8**, Caddy at `/usr/local/bin/caddy`, config tree
  `/usr/local/etc/caddy/{Caddyfile, caddy.d/, certificates/}`, rc script
  `/usr/local/etc/rc.d/caddy`. **ejprice has key-auth ssh (BatchMode works) and is
  `uid=2000, groups=wheel`.** The Caddyfile CONTENT was not readable this session (the
  session's permission classifier denied the read, twice — bound recorded in §13).
- **Established idiom at the edge: L4 SNI passthrough, backend terminates TLS.** labs and
  mcp-dev both present their own certs, so hades is not terminating for them; only the
  catch-all terminates on hades.
- **`mcp-dev.pricepaper.com` is a CNAME to `mcp-dev.firehawktransam.org` → `148.75.227.102`**
  — odoo-code's proven connector already rides this same hades edge (corroborates
  investigation M21: the whole claude.ai-web → hades → mcp-caddy → Google-auth path is
  production-proven).
- **Public DNS for `lore.firehawktransam.org` already resolves** (wildcard A →
  `148.75.227.102`, queried at 1.1.1.1). **LAN DNS does NOT** (the local resolver returns
  labs → `192.168.64.1` but lore → NXDOMAIN — hades' split-horizon zone lists specific
  hosts). claude.ai is unaffected; local smoke needs `/etc/hosts` (or a hades DNS entry,
  §12).
- **Both wildcard certs are on disk, ejprice-owned:** `~/docker/nginx/STAR_firehawktransam_org-full.crt`
  + `.key` (cert expires **2026-11-25** per investigation M3/M4 — now a connector-availability
  dependency; calendar it).
- **`sudo` on this box is passwordless for ejprice** (probed `sudo -n true` → rc 0).
- lore serves `127.0.0.1:9202` (probed via ss) — unchanged, and it stays there.

---

## 3. The rulings, in full

### R1 — packet 35 dependency: WAIVED in full for packet 39
`INDEX.md` row 39 says `depends: 35`; packet 35 (trace-deepening) is open. Read against
packet 35's scope (`docs/plans/v2/35-trace-deepening.md`): per-stage retrieval records, a
friction backstop, trace aggregates. **Zero technical coupling to any auth surface** — the
dependency is external-review *ordering* ("traces before security/UI"), and the ordering's
own rationale ("UI ships after trace and authorization models stabilize") wants packet 39
BEFORE the UI packets — 39 IS the authorization model stabilizing. The operator's goal-set
directive ("working Google Auth", tonight) is an explicit operator scope ruling, which
outranks an INDEX ordering note. **Ruling: waive the dependency for both the design and
build legs; the lead records the waiver in the INDEX Log** (rider: the INDEX row 39
`depends` cell gains a `(35 waived 2026-07-31, operator goal-set override — see Log)` note
in the same commit that lands this doc, so the row and the Log cannot disagree).
**Re-open trigger:** if packet 35's build changes the registered tool surface (new tools or
verbs), nothing re-opens HERE — the exhaustive-classification pin (§7) forces the new tools
to be classified, by construction. That pin is the instrument that makes this waiver safe.

### R2 — GCP client: REUSE the Price Paper client now
Client `185677973635-e6jah4ogtbdv7k051550v4aj2r1ei288.apps.googleusercontent.com`
(public identifier per RFC 6749 §2.2; on disk as `GOOGLE_CLIENT_ID` in
`~/docker/mcp/.env`).
**Rationale:** the operator is asleep and minting a firehawk client is GCP-console work
only they can do — reuse needs NONE (redirect URIs for claude.ai/claude.com are proven
live by M21's end-to-end traffic). This is the only ruling consistent with "working Google
Auth" tonight.
**Costs, accepted with eyes open:**
1. **Deleting that client kills odoo-code too.** Rider: the kill-switch runbook (§10) is
   REWRITTEN in this design — "delete the GCP client" is REMOVED as a lore kill switch and
   replaced by lore-scoped switches; the client-deletion step survives only in a
   "shared-blast-radius" section that names odoo-code as co-casualty.
2. **Consent screen shows Price Paper branding** to lore principals. Cosmetic; accepted.
3. **Token interchangeability:** a Google access token minted through this client for the
   odoo-code connector passes lore's `aud` check too (same client). The identity is still
   the Google user and lore's allowlist still gates admission, so this widens replay
   surface only between two services we both own. Accepted — and it is exactly what the
   negative control in the proof ladder (§9, "token minted by a DIFFERENT OAuth client is
   denied") does NOT cover, so the contract must not claim it does. Pin the `aud` check
   with a different-client token fixture; document the same-client interchangeability as a
   KNOWN BOUND in the verifier docstring.
**Re-open trigger (named, two-sided):** mint a dedicated firehawk-project client **when the
operator is next doing GCP console work**, and MANDATORILY before either (a) a third
service adopts this client, or (b) lore's allowlist diverges from "people the operator
would also admit to odoo-code" (the shared client means shared consent surface). Migration
is config-only on our side (`client_id` swap + connector re-auth); write it as a runbook
line in §12.

### R3 — hostname: `lore.firehawktransam.org`
The operator stated a firehawktransam.org preference. The brief's worry — "the edge belongs
to another account (`podmanuser`)" — is **dissolved by measurement**: the real edge is hades,
not podmanuser's nginx, and **no podmanuser-owned file is touched anywhere in this design.**
Public DNS already resolves (wildcard A, measured). The pricepaper alternative would couple
lore to odoo-code's edge (`mcp-caddy`), require path-prefix multiplexing under the
`/.well-known` prefix odoo-code already owns wholesale there, and put the business
connector's edge in the blast radius of every lore edge change — strictly worse.
**Re-open trigger:** if hades cannot be edited (root escalation fails and the operator
declines the edit), the fallback is NOT pricepaper — it is the operator adding the hades
route themselves (§12); the hostname ruling stands regardless.

### R4 — edge shape: hades SNI-passthrough route → lore-caddy (host network) → loopback lore
```
claude.ai ──TLS──> hades:443 (SNI=lore.firehawktransam.org, L4 passthrough — mirrors labs/mcp-dev idiom)
                    └──> 192.168.64.100:9443  lore-caddy (ejprice quadlet, Network=host,
                          TLS-terminates with the firehawk wildcard cert from ~/docker/nginx/)
                          ├─ handle /mcp                                    → reverse_proxy 127.0.0.1:9202
                          ├─ handle /.well-known/oauth-protected-resource/mcp → reverse_proxy 127.0.0.1:9202
                          └─ everything else → 404 (close)
```
- **lore itself never leaves `127.0.0.1:9202`** (investigation M-2: `--network=host` + a
  wide bind = instant whole-LAN exposure; the pod-Caddy option is dead because a pod netns
  cannot reach host loopback).
- **lore-caddy** is a NEW quadlet container under ejprice (`lore-caddy.container`,
  `Network=host`, mirrors the systemd/quadlet management of the surreal stores). It binds
  `192.168.64.100` and `127.0.0.1` on port 9443 (build leg verifies the port is free; any
  free host port works — nothing downstream hardcodes it except the hades route). TLS with
  the wildcard cert; LAN-wide TLS+401-gated exposure is the SAME posture `mcp-caddy`
  already runs on `0.0.0.0:8444` — accepted precedent.
- **No path rewriting** (a `strip_prefix`/`uri replace` 404s RFC 9728 discovery). The two
  `handle` matchers mirror what the SDK serves; **rider:** the build leg verifies the exact
  matcher set against the RUNNING app with a curl matrix (`/mcp` GET/POST, the well-known
  path, a junk path → 404; if Starlette's mount 307-redirects `/mcp`→`/mcp/`, the matcher
  set gains the slash form — decided by the matrix receipt, not by prediction).
- **The lore-caddy Caddyfile and the quadlet unit are TRACKED IN THIS REPO** (`deploy/`),
  bind-mounted `:Z,ro` — the investigation's warning stands: an unversioned edge config
  makes the rollback story a lie. **Rider:** the wave that creates them commits them; the
  in-repo file IS the deployed file (mount, not copy).
- **hades route addition** (the one step outside this box): drop a route for SNI
  `lore.firehawktransam.org` → `192.168.64.100:9443` (L4 passthrough), mirroring the
  existing labs/mcp-dev idiom. Mechanics for the build leg, in order: (1) READ the existing
  `/usr/local/etc/caddy/Caddyfile` + `caddy.d/` and MIRROR the existing route idiom — this
  design could not read it (§13) and deliberately does not guess its syntax; (2) additive
  change only (a `caddy.d/` drop-in if the main file imports that dir, else a minimal
  insertion); (3) `caddy validate` before any reload; (4) reload via the rc script;
  (5) **regression probes: labs AND mcp-dev.pricepaper.com must still serve** (their exact
  probe commands are in the session report), then lore probes green; (6) rollback = remove
  the added block, validate, reload. If root on hades is not attainable from this session,
  this single step moves to §12 (operator-side) — everything else in this design still
  builds and smokes tonight via `/etc/hosts` + direct `https://192.168.64.100:9443`.
- **Local smoke** uses `--resolve lore.firehawktransam.org:443:192.168.64.1` (hairpin —
  measured working tonight) or `/etc/hosts`; LAN DNS for the new name is a nice-to-have
  (§12), not a gate.
**Re-open trigger:** the first time a SECOND hosted MCP service on this box needs a firehawk
hostname, revisit whether lore-caddy generalizes into a shared host-network edge (one Caddy,
N SNI sites) rather than cloning per-service Caddies — ONE-IMPLEMENTATION applies to edges
too.

### R5 — `client_id`: inline `str` in `lore.yaml`
Public by RFC 6749 §2.2. `SecretStr`/`resolve_secret` would redact the one log line where an
`aud` mismatch — the most likely misconfiguration — must be diagnosed, and env-indirection
buys nothing for a non-secret. **One mechanism only:** `client_id: str`, required, no
default, validated non-blank via `lorerunes.is_blank` (the one blankness implementation).
**Rider:** pin that a blank/whitespace `client_id` is unconstructible, and that the
`aud`-mismatch log line renders the configured `client_id` VERBATIM (a fixture asserts the
value appears in the laundered log — that is the diagnostic this ruling exists to protect).
**Re-open trigger:** if lore ever holds a CONFIDENTIAL OAuth artifact (a client_secret —
today held only by claude.ai's connector config and Google), THAT goes env-ref + SecretStr;
`client_id` stays inline even then.

### R6 — Origin policy under M-1 uncertainty (does claude.ai send `Origin`?)
Unmeasured tonight (needs the operator to drive the connector; investigation M-1 stands,
with its Claude-Code-CLI positive control). **Design so both outcomes are correct:**
- Absent `Origin` → **allowed** (existing `OriginValidationMiddleware` policy, unchanged —
  non-browser clients and server-side proxies send none; claude.ai's server-side proxy most
  plausibly sends none).
- In `HOSTED_OAUTH` posture the effective allow-set is `allowed_origins ∪
  {"https://claude.ai", "https://claude.com"}` — the union member is a module CONSTANT
  (`_HOSTED_DEFAULT_ORIGINS`), applied in the posture derivation, not written into anyone's
  yaml. If claude.ai DOES send Origin, it passes; if not, absent-allowed covers it. A
  hostile browser origin 403s either way, before any credential is parsed.
- **Rider (same bullet, per the rider law):** three pins — `Origin: https://claude.ai`
  passes in hosted posture; absent Origin passes; a hostile Origin 403s **with zero
  outbound Google calls** (spy transport asserts no tokeninfo request — Origin stays
  OUTERMOST precisely to make this property true).
**Re-open trigger:** when M-1 is finally measured (first operator connector session — the
lore-caddy access log will carry it; add `log` to the lore-caddy Caddyfile from day one so
the measurement is free), record the outcome in this doc's margin; if claude.ai sends a
THIRD origin value, it joins the constant.

### R7 — a domain-shaped allowlist entry is UNCONSTRUCTIBLE
The operator ruled explicit-email-list-only; there is no domain rule. An entry like
`firehawktransam.org` (no local part) is therefore always an operator ERROR — either a typo
or a belief that the domain rule exists. Silently matching nothing would hide that error
until an admission fails mysteriously (or worse, teach the operator the config "worked").
**Ruling** (restated for the R12 substrate): the roster PARSER refuses any line that does
not contain exactly one `@` with non-empty local part and non-empty domain — and a parse
refusal invalidates the WHOLE roster (at boot: refuse to boot; at runtime: deny ALL — R12's
never-a-silently-shorter-list clause), with a laundered error naming the offending line and
stating "lore has no domain rule; list each address individually."
**Rider:** pins for `firehawktransam.org`, `@firehawktransam.org`, `user@`, `""`-only, and
`a@b@c` lines each producing a parse refusal that names the line; plus one pin that the
runtime predicate STILL returns `False` for a domain-shaped probe handed to it directly —
the predicate leg must survive a future refactor that bypasses the parser (same
every-leg discipline as F4).
**Re-open trigger:** the operator asking for a domain rule — which is a new operator
decision, not a roster line.

### R12 — allowlist substrate: an mtime-watched flat file, outside the repo and the image
**Operator override (2026-07-31, verbatim):** *"I don't want the user allow list baked in
the image. That's so stupid it hurts."* This fires — up front — the re-open trigger the
investigation attached to its allowlist-substrate ruling, whose named answer was exactly
this file; the trigger's condition ("revocation must beat a container recreate") is now an
up-front requirement, so it is built NOW, not later.

Two facts stated accurately, because they shape the WHY: `lore.yaml` is currently
**untracked** and is **not** copied into the image (the Containerfile copies the four
workspace members; the container receives `lore.yaml` through the `/workspace` bind
mount). The objection is therefore not "addresses would be published today" — it is that a
user roster is **operational data, not deploy config**: it changes on operational cadence,
and revocation must never require a redeploy — especially while **#165 is open**
(verified `acknowledged`, routed to packet 19) and a recreate re-mounts `/source` and
re-breaks boot, making "recreate to revoke" actively dangerous.

Required shape (rider in the same bullet, throughout):
- **The roster lives outside the repo and outside the image**, bind-mounted READ-ONLY into
  lore-lore — host-side sibling of the VERIFIED `~/docker/mcp/lore-secrets/` idiom (that
  dir exists, `0700`, per-slug `0600` `.env` files, generated by `build_envfile.py`;
  `lore_deploy.py` already defines `LORE_SECRETS_DIR` and `_resolve_env_file`, the natural
  homes for the roster path resolution). Plain newline-delimited email addresses; `#`
  comments and blank lines ignored. **Rider:** the in-image conformance leg asserts the
  mount is present and read-only in the running artifact.
- **`lore.yaml` carries ONLY the path** (`allowed_emails_file`) — never an address. Blank
  path unconstructible (`lorerunes.is_blank`). Roster CONTENTS are runtime state, not boot
  config — but the boot check still runs once (next bullet).
- **Fail CLOSED and LOUD, at every leg:** boot — `HOSTED_OAUTH` refuses to boot unless the
  roster file loads with ≥1 valid entry (refusal names the path and the reason); runtime —
  a roster that is missing, unreadable, empty, zero-valid, or parse-refused (R7) denies
  **every** principal with a laundered ERROR log. **A parse error is a refusal of the WHOLE
  roster, never a silently-shorter list** — total denial until fixed is the operator's
  chosen trade (loud beats open), stated in the verifier docstring. This subsumes F4: the
  odoo-code fail-open shape is impossible in this substrate too.
- **Freshness: the roster mtime is `stat`-checked on EVERY verification — cache hits
  included — with a full re-read only when mtime changed. A revoked principal is denied
  on the FIRST verification after the roster drops them: there is NO residual window.**
  Ruling history, recorded because it reversed twice: this was the design's first
  instinct; an intermediate lead ping capped it at one stat per cache-miss (reading the
  override's "at most one stat per cache-miss" as binding), and the lead then RESTORED
  the strong form (2026-07-31), ruling that sentence a carelessly-written performance
  floor, never a licence to cap revocation speed — the point of this substrate is that
  revocation is immediate and needs no redeploy. Cost: one `os.stat` on a page-cached
  inode per request (microseconds) against a multi-minute revocation hole on an
  internet-facing service. Admission always evaluates against the freshly-checked
  roster; the token cache caches Google's verdict (token → subject/email/expiry), never
  admission. **Riders:** an uncached-principal fixture proves the next verification
  after a roster edit sees the new roster · a cached-token principal (fixture drives a
  cache HIT, asserted by transport call-count) is denied on the FIRST verification after
  the roster edit · mutation proof — move the stat to miss-only and the cached-hit pin
  goes RED (`scripts/mutation_proof.py`, expected-RED ids declared from
  `--collect-only`).
- **The acceptance test IS the point:** adding or revoking a principal requires NO
  container recreate and NO image rebuild. **Riders, verbatim from the override:** (a) a
  test mutates the roster file mid-process and asserts the next verification sees the new
  roster with no restart; (b) a test that a roster going empty/unreadable at runtime
  denies EVERY principal (a previously-admitted fixture principal is refused); (c)
  mutation proof — make the mtime check a no-op and (a) goes RED
  (`scripts/mutation_proof.py`, expected-RED ids declared from `--collect-only`).
- Normalisation (§5) applies per roster line at parse — same `lorerunes` normaliser, same
  mutation rider (change the normaliser → roster-parse pins AND admission pins redden).
**Re-open trigger:** the roster outgrowing a flat file (order hundreds of entries, or a
second WRITER needing coordination) — the store question then re-opens with #107's law in
force, and it is the operator's fork to rule.

### R8→R12 are woven through §§5–7 (identity, config, allowlist, posture, read-only).

---

## 4. Auth path — adopt the SDK, delete the hand-roll

Verified against the INSTALLED SDK this session (symbols, not memory):
`mcp.server.auth.provider.TokenVerifier` (Protocol, `async def verify_token(token) ->
AccessToken | None`) · `mcp.server.auth.provider.AccessToken` (has `subject`, `claims`,
`expires_at`, `resource`) · `mcp.server.auth.middleware.bearer_auth.authorization_context`
(derives session identity from exactly `client_id` + `claims["iss"]` + `subject` — F3
confirmed at source) · `mcp.server.auth.settings.AuthSettings` (`issuer_url`,
`resource_server_url`, `required_scopes`) · `RequireAuthMiddleware`'s 401 appends
`resource_metadata="…"` to `WWW-Authenticate` (upstream `# pragma: no cover` — so OUR
contract drives it through the assembled app) · `mcp.server.transport_security.
TransportSecuritySettings` (Host + Origin validation; absent-Origin allowed; `:*` port
wildcards; missing Host → 421).

- **Delete** `BearerAuthMiddleware` and the `AuthVerifier` ABC (adjudicated item-by-item in
  §8). **Keep** `ApiKeyVerifier` untouched (constant-time, all-keys-no-early-out, empty-key
  rejection, SecretStr holding) and `OriginValidationMiddleware` (stays in `auth.py`; the
  investigation's "re-homed" is dropped — a move is churn with no behavior).
- **One `LoreTokenVerifier.verify_token`, two branches, in this order:** (1) API key —
  constant-time via the kept `ApiKeyVerifier.verify`, no network; (2) Google. No
  `<login>:<api_key>` third path (Odoo-only). **Rider:** a pin proves the api-key branch
  actually routes through `ApiKeyVerifier.verify` (mutation: break `verify` → api-key auth
  pins red — ROUTING IS NOT SHARING).
- **Identity minting (F3), the load-bearing part:**
  - Google branch: `AccessToken(token=…, client_id=<configured client_id>,
    scopes=["lore:read"], expires_at=<derived from tokeninfo expiry — the build leg settles
    `exp` vs `expires_in` against Google's tokeninfo doc AND a live probe, per the
    READ-THE-DOCS-THEN-VERIFY law>, subject=<Google `sub`, falling back to the normalised
    email>, claims={"iss": "https://accounts.google.com", "email": <normalised email>})`.
  - API-key branch: `AccessToken(token=…, client_id=f"api_key:{name}",
    scopes=["lore:read", "lore:write"], subject=name)`.
  - **Rider:** the F3 pin — two distinct principals produce distinct
    `authorization_context` dicts, and a session created by X cannot be resumed by Y,
    driven through the ASSEMBLED app (the SDK's auth branch is uncovered upstream);
    mutation proof: delete `subject=` from the Google branch → RED.
- **Ports verbatim from odoo-code** (`code_mcp/auth.py::_validate_google_token`, production-
  proven; carry provenance in the docstring, do not re-derive): POST the token in the BODY
  to `https://oauth2.googleapis.com/tokeninfo` (never query params — httpx logs URLs at
  INFO; this leaked tokens into a journal once) · `email_verified` accepts bool `True` OR
  string `"true"` (Workspace variance) · `aud` must equal the configured `client_id`, and a
  MISSING `aud` is a hard reject, never a skip · SHA-512 of the token as the only cache
  key, raw tokens never stored · a negative cache.
- **Must CHANGE from the port** (each confirmed against the odoo-code source this session):
  - odoo-code negative-caches on ANY non-200 (`if resp.status_code != 200: _reject_token`)
    — a Google 5xx blip would lock a valid token out for the negative TTL. **Split:**
    401/400 (definitive invalid) → negative-cache; 5xx / timeout / transport error → return
    `None` WITHOUT caching in either direction. **Rider:** separate pins with DIFFERENT
    assertions — the 401 pin asserts the second call makes NO network request (spy
    transport, call-count 1); the 5xx pin asserts the second call DOES retry (call-count 2).
  - Malformed JSON on a 200 → `None`, no cache, laundered log (odoo-code lets `resp.json()`
    raise).
  - `expires_at` is minted (odoo-code ignores token expiry entirely) and **re-checked on
    positive-cache read** — a 60s token must not be served for a 300s cache TTL. Pin with a
    short-expiry fixture.
  - Caches are **per-verifier-instance** (odoo-code's are module-global — cross-instance
    leakage and test-state law both forbid that), `cachetools.TTLCache` under a lock with
    **no `await` while the lock is held** (pin via an instrumented lock).
  - **Real scope check — stated as a PROPERTY, not a literal, because the literal was a
    design bug (caught by the contract pass):** Google's `/tokeninfo` echoes scope values
    in the form GOOGLE chooses — plausibly full URIs
    (`https://www.googleapis.com/auth/userinfo.email`), not the bare `email` alias a
    client requested — so this doc's earlier sentence ("require `"email"` in the scope
    set"), implemented verbatim, would have refused EVERY real token. The check is: the
    granted scope set CARRIES the email scope in whichever form Google returns, pinned
    parametrised over BOTH the full-URI and bare-alias forms. ⚠ Neither this design nor
    the contract has verified which form production returns — the build leg's live probe
    (§13) settles it. (Comparing our own hardcoded request scopes to themselves —
    odoo-code's shape — remains a tautology either way.)
  - **Admission is never cached** (odoo-code evaluates its allowlist only on the
    cache-miss path, so a revoked principal rides their own cache entry for its full TTL).
    Here the roster is stat-checked and the predicate evaluated on EVERY verification
    (R12 restored ruling — no residual window); the cache holds Google's verdict only.
    **Rider:** R12's discrimination pins (uncached-edit, cached-HIT-immediate-denial,
    stat-to-miss-only mutation ⇒ RED).
  - Injected `httpx.AsyncClient` — surfaced as `build_mcp_server`'s NEW keyword-only
    `http_client=` parameter (B4, lead-accepted 2026-07-31: optional and additive, so
    existing callers are unaffected; without it there is no hermetic way to drive the
    ASSEMBLED app — the alternative is a live socket from the suite, which the repo's
    hermeticity pin forbids). Tests use `httpx.MockTransport`; production wiring uses
    bounded `httpx.Limits` + explicit timeout constants. **Lifecycle law rider:** a
    degradation pin — close the injected client, next `verify_token` recovers (lazily
    replaces it) rather than erroring forever; plus the state-leakage autouse reset.
- **Hardcoded, never config:** the issuer URL and the tokeninfo URL (a configurable issuer
  is a downgrade attack). `AuthSettings.issuer_url = "https://accounts.google.com"`.
- **Dependency addition:** `cachetools>=5` (direct dep of loremaster). Packages-considered
  verdict in §14.

### Extension seam (operator directive: seam only, Odoo resolver at supersede)
`AuthContext` (frozen dataclass: `subject: str`, `email: str | None`, `provenance:
Literal["api_key", "google"]`, `permitted: frozenset[str] | None` — `None` ⇒ unfiltered)
behind a `PermissionResolver` protocol (`async def resolve(AuthContext) -> AuthContext`)
with a fully-tested pass-through default — injected as `build_mcp_server`'s NEW
keyword-only `permission_resolver=` parameter (B4, lead-accepted 2026-07-31: optional,
additive, defaulting to pass-through). Derived at tool dispatch from
`mcp.server.auth.middleware.auth_context.get_access_token()`. The Odoo resolver
(`resolve_auth` ≈ 265 lines in odoo-code) lands at supersede into this proven seam.
**Rider:** the pass-through resolver's pin includes one NON-pass-through fake resolver in
the contract, so the seam is proven ABLE to filter (a seam only ever exercised as identity
is a seam nobody knows is broken — the "can the fake actually fail" law).

---

## 5. Config model

```python
class GoogleOAuthConfig(_StrictModel):
    client_id: str            # R5: inline, public, non-blank (lorerunes.is_blank)
    resource_server_url: str  # https-only validator; its PATH must equal server.path (cross-checked at LoreConfig level)
    allowed_emails_file: str  # R12: PATH to the roster (outside repo + image); non-blank; contents are RUNTIME state, never config

class AuthConfig(_StrictModel):
    enabled: bool = False
    mode: Literal["api_key", "google_oauth"] = "api_key"
    keys: list[AuthKey] = []              # in google_oauth mode: OPTIONAL — the api-key branch for local agents
    google: GoogleOAuthConfig | None = None
    allowed_origins: list[str] = []
    # tls_terminated_upstream: DELETED (item 12 in §8)
```

- **Normalisation, one implementation in `lorerunes` (stdlib-only ✓):**
  `normalize_email = NFKC → casefold → strip`, applied to BOTH roster lines (at parse,
  R12) and presented emails (at runtime). **Rider pins:** `JHarrington2005@Gmail.com`
  admitted against a lowercase roster line · a roster line with surrounding whitespace
  admitted after normalisation · a Cyrillic-homograph local/domain does NOT match its
  Latin lookalike (NFKC does not conflate those — the pin proves the non-match) · gmail
  dot/plus-aliasing is NOT implemented (documented bound in the docstring: the roster
  line must be the address Google reports, verbatim-after-normalisation).
- **F4, every leg, pinned separately (restated under R12):** the config leg
  (`allowed_emails_file` blank ⇒ unconstructible) · the boot leg (`HOSTED_OAUTH` refuses
  to boot unless the roster loads with ≥1 valid entry) · the runtime leg (a roster
  missing/unreadable/empty/parse-refused at runtime ⇒ deny ALL — and the bare predicate
  returns `False` on an empty set even when handed one directly, so the defense survives
  a future refactor that bypasses the parser). The parser + predicate live in `lorerunes`
  beside the normaliser; **mutation rider:** change the normaliser → the loremaster
  admission pins AND the lorerunes unit pins both redden (prove sharing by mutation).
- **`resolve_secret` untouched; nothing new is a secret.** API keys stay `*_env`.

### Posture derivation — allowlist the safe (three postures)

Pure function in `lorerunes` over primitives (`host_is_loopback: bool, enabled: bool,
mode: str, has_keys: bool, has_google: bool`) returning a `Posture` enum or a typed
refusal naming (a) the nearest posture and (b) the exact missing/conflicting fields, with
posture names enumerated FROM the enum (a fourth posture is a type error, not a prose
edit). Call sites: `build_asgi_app` · `lore_deploy.py::verb_start`/`verb_setup` (catches
the operator before `podman run`) · `load_config`.

| Posture | requires | serves |
|---|---|---|
| `LOOPBACK` | loopback host ∧ auth disabled | no auth middleware — unchanged local mode |
| `LAN_BEARER` | enabled ∧ `api_key` ∧ ≥1 key | `AuthSettings(resource_server_url=None)` (suppresses `.well-known` — no discovery fiction while sessions still bind), api-key verification |
| `HOSTED_OAUTH` | enabled ∧ `google_oauth` ∧ google complete ∧ **loopback host** (the proxy comes to us) — "complete" includes the R12 roster loading at boot with ≥1 valid entry | full `AuthSettings` + `.well-known` + both verifier branches |

Everything else — google block present in `api_key` mode, `google_oauth` with a
non-loopback host, enabled with no keys and no google, disabled with either — is a **boot
refusal** (the honest-failure idiom applied to the operator; a gate that refuses honest
configs gets switched off, so every refusal names its nearest posture and exact fix).
**Riders:** the table-driven cross-product test over all five inputs with expected-RED ids
declared from `--collect-only` BEFORE the run (`scripts/mutation_proof.py`, diffed both
ways) · an in-image conformance leg asserting NON-ZERO EXIT on an incoherent config
(#131/#139 — only the running artifact proves the cake).

**⚠ Operational consequence, stated where it bites:** in `HOSTED_OAUTH` the SDK gates
`/mcp` for EVERYONE — local agents on this box included. Local sessions therefore
authenticate with an API key (the `keys` list stays populated; `.mcp.json` gains the
Bearer header via the lore-deploy skill's wiring). "Local access unchanged" means
unchanged CAPABILITY (full surface), not unchanged config. **Rider:** the deploy step that
flips lore-lore to `HOSTED_OAUTH` ships in the SAME wave as the `.mcp.json`/lore-deploy
wiring, or every local session 401s — the wave plan lists this as one atomic cutover with
its rollback (`mode: api_key` + recreate).

### Host/Origin validation (F5) — one derivation, two enforcement points (R9)
The SDK's `TransportSecuritySettings` is ENABLED in every non-LOOPBACK posture (Host
validation is what actually matters behind a reverse proxy — lore's hand-rolled middleware
covers Origin only; leaving `transport_security` unset repeats #206's shape inside the
packet that cites it). To avoid TWO origin policies that must agree by memory
(ONE-IMPLEMENTATION), `build_asgi_app` computes ONE `EdgePolicy` (allowed origin set —
posture defaults ∪ config; allowed hosts — derived from `resource_server_url`'s netloc +
the loopback bind forms) and feeds BOTH `OriginValidationMiddleware` (outermost, absent-
allowed, the 403-before-credential-parse property) and `TransportSecuritySettings`
(`allowed_hosts`, `allowed_origins` incl. the loopback `:*` wildcard forms). **Riders:**
a pin asserts the settings object in the composed app was built FROM the derivation
(equality against `EdgePolicy.to_transport_security()`), plus behavioral pins at both
layers; mutation proof: change the derivation's output → BOTH layers' pins redden. A
wrong-Host request 421s; the lore-caddy MUST forward the original Host header (live-ladder
probe, §9).

---

## 6. Composition

```
OriginValidation( _EagerStartupLifespan( mcp.streamable_http_app() ) )   # no BearerAuthMiddleware, ever
```
- FastMCP is constructed with `token_verifier=LoreTokenVerifier(...)`, `auth=AuthSettings(
  issuer_url=<constant>, resource_server_url=<config | None per posture>,
  required_scopes=["lore:read"])`, `transport_security=<derived, §5>`. The SDK gates only
  the streamable route, so `.well-known` is anonymous in `HOSTED_OAUTH` (F2 fixed by
  construction) and ABSENT in `LAN_BEARER` (`resource_server_url=None` — investigation-
  executed and confirmed).
- Origin becomes OUTERMOST (today Bearer is). `test_eager_startup.py::
  test_composed_auth_app_is_bearer_outermost` asserts the OLD world and is **rewritten,
  not deleted** (§8 item 13): the new pin asserts a disallowed Origin 403s with ZERO
  outbound Google calls and no session touched.
- Scope constants `"lore:read"` / `"lore:write"` live in `lorerunes` beside the posture
  enum (shared policy: the verifier mints them, the dispatch guard checks them, the
  instructions renderer names them — one home).

---

## 7. Read-only hosted posture — derived, never hand-listed (R8)

**The classification already exists, typed, in production:** every tool registration in
`build_mcp_server` carries `ToolAnnotations` with `readOnlyHint` explicitly set
(`_READ_ONLY_ANNOTATIONS`, `_SAVE_MEMORY_ANNOTATIONS`, `_INDEX_ANNOTATIONS`,
`_TASK_TOOL_ANNOTATIONS`, `_FINDINGS_TOOL_ANNOTATIONS`, `_COMMS_TOOL_ANNOTATIONS`). Do not
invent a second `mutates: bool` beside it — that would be two classifications that must
agree by memory. **The rule: a tool is hosted-callable iff its registered
`annotations.readOnlyHint is True`.** Everything else — including `annotations is None` —
is refused for principals without `lore:write`. Fail-closed by construction: an
unclassified new tool is born refused.

- **Enforcement:** one guard installed once in `build_mcp_server` at tool dispatch: if
  `get_access_token()` yields a token lacking `"lore:write"` and the target tool's
  registered `readOnlyHint is not True` → a STRUCTURED tool error (never an unhandled
  exception) teaching: the posture name (from the enum), the tool name, why it is refused,
  and that the read surface remains available. No token at all (LOOPBACK posture) ⇒ full
  surface, unchanged.
- **Granularity is the TOOL, deliberately:** `lore_index` (can reconcile), `lore_tasks`,
  `lore_findings`, `lore_comms` are multiplexed read+write tools and are refused WHOLE for
  hosted principals — the annotation comment in `server.py` already states the law ("a
  tool that CAN write is not read-only merely because one call shape happens not to").
  Over-refusal is a UX cost with zero security cost; parameter-level carve-outs would be a
  second, hand-rolled classification. Confidentiality is NOT the argument (lore_search
  reaches the same corpus); write-prevention is. **Re-open trigger:** a hosted consumer
  demonstrably needing a read verb of a multiplexed tool → the answer is SPLITTING the
  tool at registration (two tools, two annotations), never a parameter carve-out in the
  guard.
- **The known-wrong hand-list — finding #291** (confirmed in-flight, independently twice:
  this design at source, the lead via the six annotation constants and the
  `FastMCP.tool()` signature; the defect's full statement lives in the finding, not
  restated here — `test_mcp_server.py::_MUTATING_TOOLS` omits two tools production
  annotates non-read-only). A hand-list beside derived metadata, already drifted: the
  repo's own ONE-IMPLEMENTATION failure living inside a gate.
  **Fix (lead-directed, #291): the hand-list is DELETED, not corrected** — the
  annotation-coverage pins derive their set as `{tool : annotations.readOnlyHint is not
  True}` from `await mcp.list_tools()`, killing the second source of truth. The
  non-tautology anchor moves where it belongs: the POSTURE pins name each mutating tool
  ONCE as behavior fixtures (`lore_remember` refused hosted, `lore_claim_task` refused
  hosted, …), so a wrongly-flipped annotation reds a BEHAVIOR pin by name instead of
  being blessed by a derived expectation. Derivation kills the drifting list; explicit
  behavior fixtures keep the spec anchored to values. Ask: *"if someone flipped
  `lore_remember`'s annotation to read-only, which pin reds?"* — its behavior fixture,
  by name.
- **Riders (the mutation proofs that make this real):** flip ONE read tool's registered
  annotations to `readOnlyHint=False` in scratch → its hosted-refusal pin reds; flip one
  mutating tool to `True` → the cross-product posture pin reds; both runs via
  `scripts/mutation_proof.py` with expected-RED ids from `--collect-only`.
- **Instructions honesty (Consumer Law):** in `HOSTED_OAUTH` the served `instructions`
  block gains a section GENERATED from the registered annotations (never prose beside
  them): the refused tool names, the reason, and the read-ladder that remains. The
  existing pins interact: `test_the_registered_surface_is_exactly_the_expected_set` and
  `test_instructions_names_every_tool` stay green (tools remain REGISTERED and listed —
  refusal happens at call, honestly taught). **Rider:** a hosted-posture instructions pin
  asserts each mutating tool name appears inside the refused-set section, with the
  expectation derived from the same test-side exhaustive mapping.
- **Ask mid-build (the askable form):** *"if I registered a new tool right now with no
  annotations, which pin reds and which guard refuses it?"* If either answer is "nothing",
  the derivation has been rebuilt as a list.

---

## 8. Removed-behavior inventory — adjudicated item-by-item

Derived by reading `loremaster/loremaster/auth.py` in full at `5a850c3` (the deleted
symbols: `BearerAuthMiddleware`, `AuthVerifier`; the retired field:
`tls_terminated_upstream`; the rewritten pin: Bearer-outermost). Consumers of the deleted
symbols (bare-pattern grep, this session): `auth.py`, `server.py`, `test_auth.py`,
`test_eager_startup.py`, `test_mcp_server.py` — the build's sweep re-runs this grep
anchor-free, prose included, and adjudicates every residual hit individually (no "all
remaining hits are X").

| # | Old behavior | Verdict |
|---|---|---|
| 1 | 401 + `WWW-Authenticate: Bearer realm="loremaster"` on missing/invalid credential | **preserved-with-pin**, shape superseded: SDK `RequireAuthMiddleware` 401s with `WWW-Authenticate` carrying `resource_metadata=` (RFC 9728 §5.1); pin asserts 401 + the header through the assembled app (upstream branch is `# pragma: no cover`) |
| 2 | Case-insensitive `Bearer ` scheme prefix (RFC 7235 §2.1) | **preserved-with-pin**: fixtures `bearer x` / `BEARER x` through the assembled app — if the SDK parses case-sensitively, that is a FINDING to surface, not a silent regression |
| 3 | latin-1 header decode ⇒ non-ASCII token reachable; `ApiKeyVerifier` byte-mode compare prevents `TypeError`→500 | **preserved-with-pin**: `ApiKeyVerifier` kept verbatim; hostile fixture (non-ASCII token) asserts clean 401, no exception |
| 4 | Non-HTTP ASGI scopes (lifespan) pass through ungated | **preserved**: SDK auth wraps HTTP routes only; Origin middleware keeps its scope check; existing eager-startup lifespan pins stay green |
| 5 | Presented credential value never logged | **preserved-with-pin**: caplog sweep on a failed verify asserts the raw token appears in NO record; cache keys are SHA-512 only |
| 6 | Fail closed BEFORE the wrapped app runs | **preserved-with-pin**: spy inner-app asserts not-called on 401 |
| 7 | The WHOLE app was Bearer-gated — including what is now the discovery path | **dropped-deliberately** (F2: RFC 9728 §3.1 requires anonymous discovery; the SDK gates only the streamable route); pins: `.well-known` 200 anonymous in `HOSTED_OAUTH`, absent in `LAN_BEARER`, `/mcp` 401 unauthenticated in both |
| 8 | 401 body `Unauthorized`, `text/plain` | **dropped-deliberately**: consumers key on status + `WWW-Authenticate`, not body prose; the SDK's shape governs |
| 9 | `AuthVerifier` seam: sync `verify(token) -> str \| None` | **dropped-deliberately**: replaced by the SDK `TokenVerifier` protocol (async). The docstring's claims that an OAuth backend "slots into the same BearerAuthMiddleware" and the seam is "async-friendly" were FALSE (F1) — **old-bug-not-re-pinned**, recorded here |
| 10 | `build_api_key_verifier` fails LOUD on unset/empty `key_env` at startup | **preserved-with-pin**: function kept verbatim; existing `test_auth` pins remain green |
| 11 | `ApiKeyVerifier` semantics: constant-time, all-keys-no-early-out, empty-key rejection, empty-token early reject, copy-on-init, SecretStr holding (#211) | **preserved-with-pin**: class untouched; existing pins remain; NEW pin that `LoreTokenVerifier`'s api-key branch routes through it (mutation: break `verify` → RED) |
| 12 | `AuthConfig.tls_terminated_upstream` (dead flag — read by nothing) | **dropped-and-wired**: deleted; its intent becomes the https-only validator on `resource_server_url`. ⚠ `extra="forbid"` ⇒ an external `lore.yaml` still carrying it now fails to load — pin asserts the failure MESSAGE names the field and the fix; CHANGELOG migration note |
| 13 | Bearer-outermost composition (`test_eager_startup.py::test_composed_auth_app_is_bearer_outermost`) | **dropped-deliberately, argued improvement**: Origin-outermost rejects cross-origin BEFORE credential parse, so a browser-borne attacker cannot force an outbound Google call. The pin is REWRITTEN (asserts the new order + zero-outbound property), never silently deleted |
| 14 | `auth.py.__all__` exports (incl. the `hmac` re-export) | **dropped-deliberately** for the deleted names; the sweep (header of this table) adjudicates every import site; `hmac` re-export kept only if a consumer proves live, else dropped with the same sweep receipt |
| 15 | EVERY path was Bearer-gated, so an unauthenticated `POST /anything` was 401; under the SDK composition an unknown path is 404 — anonymous callers can enumerate the path surface wherever no edge fronts lore (`LAN_BEARER`; the public edge's `everything else → 404` masks it) | **dropped-deliberately — ruling S1 (lead, 2026-07-31), surfaced by the contract pass as a row this table omitted.** The disclosure is a route list, not data; lore's surface is two paths, documented publicly in this very design; closing it would re-wrap the app in the blanket gate whose removal RFC 9728 discovery requires. Recorded as a KNOWN BOUND in the verifier docstring (§1) with its re-open trigger: a route whose mere existence is sensitive, or a posture shipping without an edge in front. (Row 7 adjudicated the discovery path; this row adjudicates the REST of the surface — they are different populations) |

"The old code did it" appears nowhere above as a reason — each preserved row cites the spec
clause or law that wants the behavior kept.

---

## 9. What the contract author must pin (sharpened groups)

Two ∀-properties govern everything (the quantifier law — pin outcomes over ALL inputs and
FORCE each fate with a fixture):
- **Auth ∀:** every `(token, tokeninfo-response, allowlist)` triple yields EITHER `None`
  OR an `AccessToken` whose email the allowlist admits and whose `subject`/`claims`/
  `expires_at` are populated — no third fate, regardless of WHICH field was hostile.
- **Posture ∀:** every registered tool is classified (readOnlyHint explicitly set), and in
  `HOSTED_OAUTH` every non-read-only tool is refused for every non-write principal — no
  tool unclassified, no principal-shape untested (google-token AND api-key AND no-token
  fixtures; the value-monoculture law: at least two distinct emails, two distinct key
  names).

Groups (each pin mutation-proven; expected-RED ids from `--collect-only` before the run):
1. **Allowlist predicate + roster substrate (R12)** — case-fold admission ·
   whitespace-line admission · NFKC homograph NON-admission · domain-shaped line ⇒ parse
   refusal naming the line (R7) · F4 at every leg pinned separately: blank path
   unconstructible / boot refusal on unloadable roster / runtime deny-ALL on
   missing-unreadable-empty-parse-refused · **the acceptance test:** mid-process roster
   edit visible on the next verification with NO restart · revoked-while-token-cached
   principal denied on the FIRST verification after the edit (cache-HIT fixture asserted
   by transport call-count; stat-to-miss-only mutation ⇒ RED — no residual window,
   restored R12) · mtime-check no-op mutation ⇒ RED · duplicate lines merge-and-report
   via `RosterParse(entries, merged)`, never a silent shortening (ruling S2, §15) ·
   dot/plus aliasing NOT stripped (documented bound, pinned as behavior).
2. **Google validation** — `aud` mismatch / absent / different-client-token · unconfigured
   client_id unconstructible · `email_verified` across all four shapes (True/"true"/
   False/"false") · missing email · missing scope `email` · 401-vs-5xx negative-cache
   SPLIT (different assertions: call-counts via spy transport) · malformed JSON on 200 ·
   expired token not served from cache (short-expiry fixture) · token never in URL
   (transport spy asserts POST body).
3. **Cache** — poisoning attempt with positive control proving the cache is live ·
   per-instance isolation (two verifiers, no bleed) · raw token absent from `repr`/`vars`/
   logs · no `await` under the lock (instrumented lock) · lifecycle: closed injected
   client → recovery (degradation law).
4. **Identity / #206 (F3)** — distinct principals ⇒ distinct `authorization_context`;
   session created by X not resumable by Y through the ASSEMBLED app; delete `subject=` ⇒
   RED (mutation receipt).
5. **Composition** — `.well-known` 200 anonymous WITH an `Origin: https://claude.ai`
   header · `.well-known` absent in `LAN_BEARER` · 401 carries `resource_metadata=` ·
   api-key still authenticates in `HOSTED_OAUTH` (write scope) · disallowed Origin 403s
   with ZERO outbound Google calls · wrong Host 421s (F5) · `bearer`/`BEARER` casing ·
   non-ASCII token → clean 401.
6. **Posture gate** — the cross-product table (§5) · each mutating tool refused for a
   google principal AND permitted for an api-key principal AND permitted with no auth
   (LOOPBACK) · the annotations-exhaustiveness pin (§7) · instructions honesty pin in
   hosted posture (§7) · refusal prose enumerates posture names from the enum.

The contract ships with a **satisfiability receipt** (0-failed against the adversary's
reference build, INCLUDING after the ruff-driven orphaned-import cleanup that deleting
`BearerAuthMiddleware` will force), and the **contract-adversary is mandatory** — brief it
on: the F3 subject collapse (the finding most likely to be "fixed" into a false clear),
F4's inherited fail-open, the 401-vs-5xx split, the SDK's uncovered auth branch (verifier-
level pins are insufficient — drive the assembled app), and the §7 derivation (build a
wrong implementation that hand-lists tools and see whether the contract catches it).

**Live proof ladder (build/deploy leg):** `.well-known` → 200 anonymous · `POST /mcp` →
401 + `WWW-Authenticate` whose `resource_metadata=` URL resolves · junk path → 404 at
lore-caddy · connector flow end-to-end (operator) · negative controls: an unlisted address
denied; a token minted by a DIFFERENT OAuth client denied (proves `aud` is not decorative
— and per R2 does NOT cover same-client interchangeability, which is documented, not
denied); a write tool refused for a hosted principal PAIRED with the same tool succeeding
via api-key (the probe can demonstrably see writes). In-image conformance run asserts
`loremaster.__file__` in site-packages and non-zero exit on an incoherent posture config.

---

## 10. Kill switches (rewritten under R2 + R12 — per-principal before whole-service)

**Per-principal revocation (the common case, and now the fastest path):**
1. Delete the principal's line from the roster file (R12) — no recreate, no rebuild, no
   restart, **effective on their NEXT verification: no residual window** (the restored
   per-verification stat ruling). Emptying or removing the file denies EVERY principal (fail
   closed — it can never fail open, unlike the inherited F4 shape; at the next boot it is
   a refuse-to-boot), so the per-principal switch and the all-principals switch are the
   same file. (The investigation's recreate-based revocation is superseded by the R12
   operator override.)

**Whole-service, ordered by speed:**
2. `systemctl --user stop lore-caddy` (this box, no root) — public reachability dies at
   once; local loopback service continues.
3. `podman stop lore-lore` — total stop.
4. Remove the hades SNI route (root on hades) — closes the path even if lore-caddy
   restarts.
5. Operator: remove the lore connector in claude.ai.
6. **Shared-blast-radius section (R2):** rotating the Google client secret or deleting the
   client revokes/kills BOTH lore and odoo-code. Never a lore-scoped switch; use only for
   a suspected client-credential compromise, with odoo-code's owner (the operator) aware.
- Cert expiry 2026-11-25 (§2) — renewal reaches BOTH the labs edge and lore-caddy;
  runbook line + calendar.

---

## 11. #137/#138 consultation (required by packet 39's own law)

#138's re-open trigger names wave S / hosted deployment explicitly. Consulted 2026-07-31:
- **The trigger does NOT fire.** Those bounds defend against a hostile AUTHOR with commit
  access; this packet adds hosted READERS, no contributors, and the hosted surface is
  read-only by §7. The exec-seam threat model is unchanged.
- **#137** (spawning dependency invisible to AST scans): this packet adds `cachetools`
  (pure Python, no spawn) — the bound's trigger ("the day we add ANY spawning dependency")
  does not fire either.
- Recorded here as the packet's consultation receipt.

---

## 12. Operator-side — honestly, what cannot happen without them

| Item | Why operator-only | Blocking go-live? |
|---|---|---|
| Create the lore connector in claude.ai (URL `https://lore.firehawktransam.org/mcp`, client_id from `~/docker/mcp/.env`, **client secret** — NOT on disk anywhere we can read (grepped the mcp deploy tree); it lives in GCP console / their records) | Their claude.ai account + the secret | **YES** — the final end-to-end step |
| M-1 measurement (does claude.ai send `Origin`) | Happens automatically at first connector use; lore-caddy logs from day one (R6) | No — design is correct under both outcomes |
| hades: SNI route + optional LAN DNS entry | ONLY if root escalation from ejprice-wheel fails (untestable this session — §13); otherwise the build leg does it with the §3-R4 ladder | Conditionally — fallback: full local build + smoke tonight, hades route as the last-mile switch |
| GCP console: NOTHING now (R2 reuse); later: mint the firehawk client (R2's migration trigger), confirm no unverified-app interstitial appeared for lore users | Console access | No (now) |
| Consent to the `.mcp.json`/local-key cutover wave (§5's atomic-cutover rider) — it changes every local session's connection config | It touches their daily workflow | The lead may build it; flipping lore-lore's posture ships with the wave |
| Roster curation beyond the seed (R12) | The membership list is operator data | No — the build seeds the roster file with the operator's known addresses for smoke; thereafter it is a file edit, no redeploy |

---

## 13. Bounds of this design (what was NOT measurable tonight — named, per the trust law)

- **hades' Caddyfile content is unread** (session permission classifier denied it twice).
  The SNI-routing MECHANISM is established behaviorally (probes, §2); the exact route
  syntax is not — hence R4's read-first-mirror-idiom instruction to the build leg.
- **Root escalation on hades untested** (same classifier). ejprice is in `wheel`; whether
  `su`/`doas` is passwordless is unknown. §12 carries the fallback.
- **M-1 (claude.ai `Origin`)** — unmeasurable without the operator; designed both-ways
  safe (R6).
- **True-WAN path**: my 443 probes traversed the router hairpin, not the internet. That
  the same SNI routing serves true-WAN traffic is INFERRED from mcp-dev's production
  connector traffic (M21) riding the identical edge — strong, but inference; the first
  external `.well-known` fetch in lore-caddy's log is the closing measurement.
- **Google tokeninfo response fields** (`exp` vs `expires_in`, `sub` presence, and the
  FORM of the returned `scope` values — full URIs vs bare aliases; §4's check and the
  contract's pins are parametrised over both until the probe settles it) — settled at
  build against the vendor doc + a live probe (READ-THE-DOCS-THEN-VERIFY), not assumed
  here.

## 14. Packages considered

| Mechanism | Package | What was READ | Verdict |
|---|---|---|---|
| Token verification protocol, 401/`resource_metadata` challenge, session identity, `.well-known` route | `mcp` SDK ≥1.27 (installed) | `mcp/server/auth/provider.py` (`TokenVerifier`, `AccessToken` incl. `subject`/`claims`), `bearer_auth.py::authorization_context`, `auth/settings.py::AuthSettings`, FastMCP `token_verifier=` wiring | **replace** (the hand-rolled `BearerAuthMiddleware`/`AuthVerifier` are deleted) |
| Host/Origin DNS-rebinding validation | `mcp.server.transport_security` (installed) | `TransportSecuritySettings` + middleware source (absent-Origin allowed, `:*` wildcards, 421 on bad Host) | **replace_with_adapter** (one `EdgePolicy` derivation feeds it AND the kept outermost Origin middleware — §5) |
| Token/negative caches with TTL | `cachetools.TTLCache` | odoo-code's production use of the same (`code_mcp/auth.py`); cachetools API | **replace** hand-rolled dict-with-timestamps (new direct dep `cachetools>=5`) |
| Google token validation transport | `httpx` (already a direct dep) | odoo-code's `_validate_google_token` POST-body idiom; httpx `MockTransport`/`Limits` | **keep** |
| Google claim validation | `google-auth` | Its `id_token` verifier targets ID-token JWTs; the connector presents opaque ACCESS tokens — tokeninfo introspection is the correct instrument (odoo-code production-proven) | **bespoke** (the gap only: tokeninfo call + claim checks; provenance carried in docstring) |
| Blankness / email normalisation / posture predicate / roster parser | `lorerunes` (in-repo shared home) | `lorerunes/blankness.py::is_blank` | **extend** (normaliser + posture enum + scope constants + roster parser join it; stdlib-only preserved) |
| Roster change detection (R12) | `watchdog` (already a dep) | Its observer model — a thread + event queue per watched tree, the indexer's instrument | **bespoke, deliberately minimal**: one `os.stat` mtime compare per cache-miss for a single file — an observer thread for one file is machinery without a gap to fill; re-open if the roster ever becomes a directory of files |

---

*Every ruling above carries its rider in the same bullet; the self-check ("did I implement
the clause before the 'and pin it like this' phrase and not after?") was applied to each
R-item before this doc was written. Where this doc and the investigation plan disagree
(Phase-0 topology, the kill-switch list, the podmanuser-nginx path), THIS DOC governs — the
disagreements are measurement-driven and dated 2026-07-31.*

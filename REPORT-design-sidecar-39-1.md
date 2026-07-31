brief-base v9 read
state: done
deviations: none — all seven forks RULED under the operator's explicit override; no code/config/test touched; sole writable path honored
Packages considered: mcp SDK ≥1.27 (replace — hand-rolled Bearer middleware/ABC deleted), mcp.server.transport_security (replace_with_adapter — one EdgePolicy derivation), cachetools.TTLCache (replace, new direct dep), httpx (keep), google-auth (bespoke gap — access tokens need tokeninfo, not id_token JWTs), lorerunes (extend). Full read-column table: design doc §14
decisions-needed: none for the design (operator override); operator-side go-live items listed honestly in design doc §12 (claude.ai connector + client secret is the one hard blocker)
receipt pointers:
- DELIVERABLE: docs/design/2026-07-31-packet39-google-oauth.md (rulings table §0 · threat model §1 · measured topology §2 · rulings §3 · verifier §4 · config/postures §5 · composition §6 · read-only derivation §7 · removed-behavior inventory §8 · contract groups §9 · kill switches §10 · #137/#138 receipt §11 · operator-side §12 · bounds §13 · packages §14)
- Probe instruments: this report §3 (verbatim, per brief-base instrument law)
- Key measurement: the investigation's Phase-0 "the public edge is a listener on THIS box" is FALSIFIED — the edge is hades (192.168.64.1), details §2 below

# design-sidecar-39-1 — packet 39 design, all forks ruled

## 1. Capability check (first, per brief-base §4)
Everything the brief demanded was satisfiable EXCEPT two reads, both denied by the session's
permission classifier (not by missing tools): (a) `cat /usr/local/etc/caddy/Caddyfile` on
hades via ssh — denied twice; (b) a hades process/OS listing variant — denied once. What I
did instead: established the edge's routing mechanism BEHAVIORALLY (SNI probes, §3) and wrote
the design so the build leg reads-then-mirrors the Caddyfile idiom under its own permissions
(design §3-R4, §13). What a lead must change: nothing — or grant `ssh 192.168.64.1 cat …`
if the build leg should inherit the read.

## 2. What was done
Ruled all seven forks + four derived rulings (R1–R11, design §0) under the operator's
verbatim override ("Have the designer decide"). Every ruling carries rationale + named
re-open trigger + its rider pins in the same bullet. Highlights that CHANGE the inherited
plan (each measurement-driven, dated 2026-07-31):

1. **The real public edge is `hades.firehawktransam.org` = 192.168.64.1 (FreeBSD 14.3,
   Caddy)** — not any listener on this box. SNI-dependent backends measured at the public
   IP's :443: labs→nginx (jupyter-proxy), mcp-dev.pricepaper.com→mcp-caddy (pricepaper
   cert; it is a CNAME onto the firehawk A record), any other SNI→hades' own catch-all 200
   with the firehawk wildcard cert. **Consequence: the podmanuser-nginx edit the brief
   worried about is NOT NEEDED AT ALL** — nothing owned by another user account is touched.
   ejprice has key-auth ssh to hades and is in wheel (root escalation untested — classifier).
2. **Hostname ruled `lore.firehawktransam.org`** (operator preference stands; public
   wildcard DNS already resolves — measured at 1.1.1.1; LAN split-horizon does NOT resolve
   it — smoke uses hairpin/--resolve, measured working).
3. **Edge shape: hades SNI-passthrough route → new ejprice-owned `lore-caddy` quadlet
   (Network=host, TLS with the on-disk firehawk wildcard cert, binds .100:9443+loopback,
   two handle blocks + 404) → 127.0.0.1:9202.** lore never leaves loopback. Caddyfile +
   quadlet tracked in-repo (`deploy/`), bind-mounted ro.
4. **GCP client: REUSE Price Paper's now** (operator asleep; M21 proves redirect URIs live;
   zero console work). Riders: kill-switch runbook REWRITTEN (client deletion is no longer
   a lore switch — it kills odoo-code; §10), same-client token interchangeability documented
   as a KNOWN BOUND the different-client negative control does NOT cover, migration trigger
   named (next operator GCP session; mandatory before a third service or allowlist
   divergence).
5. **Read-only hosted surface derived from the EXISTING typed `ToolAnnotations.readOnlyHint`**
   (production already classifies every tool at registration — verified in server.py) —
   enforced via minted scopes (`lore:read` google / `+lore:write` api-key), fail-closed on
   unclassified, tool-granularity (multiplexed tools refused whole; re-open = split the
   tool, never a parameter carve-out). `_MUTATING_TOOLS`' real defect is named: not that it
   is a list, but that nothing forced it exhaustive — fix = correct + exhaustiveness leg.
6. **F3/F4/F5 all land as construction:** subject+claims+expires_at minted (F3, SDK
   `authorization_context` source-verified); allowlist fail-closed both legs (F4); SDK
   TransportSecuritySettings enabled with ONE EdgePolicy derivation feeding it and the kept
   outermost Origin middleware (F5, no twin origin policies).
7. **M-1 both-ways-safe:** hosted posture unions `{https://claude.ai, https://claude.com}`
   into the origin allow-set as a constant; absent-Origin stays allowed; hostile origin
   403s with zero outbound Google calls (pinned).
8. **Domain-shaped allowlist entry: unconstructible** (validation error naming the entry),
   plus a runtime-leg pin that survives a validator bypass.
9. **Packet 35 dependency WAIVED in full** — read 35's scope: zero technical coupling to
   auth; the ordering rationale itself wants 39 before UI; operator goal-set outranks the
   INDEX note. Rider: INDEX row annotation + Log line in the same commit as this doc.
10. **Removed-behavior inventory: 14 items derived by me** from a full read of auth.py at
    5a850c3 (not the plan's uncounted "13") — every verdict cites a spec clause or law;
    "the old code did it" appears nowhere.
11. **HOSTED_OAUTH gates local agents too** — stated where it bites (design §5): the
    posture flip ships atomically with the `.mcp.json`/lore-deploy key wiring or every
    local session 401s.

## 3. Probe instruments (verbatim — these settle the topology; re-runnable)
```bash
# Public DNS (bypasses LAN split-horizon)
dig @1.1.1.1 +short labs.firehawktransam.org        # 148.75.227.102
dig @1.1.1.1 +short lore.firehawktransam.org        # 148.75.227.102 (wildcard A confirmed)
dig @1.1.1.1 +short mcp-dev.pricepaper.com          # CNAME mcp-dev.firehawktransam.org -> 148.75.227.102
dig +short lore.firehawktransam.org                 # (empty — LAN resolver has no record)
# SNI discrimination at the public IP's :443 (hairpin through the router)
curl -sI --resolve labs.firehawktransam.org:443:148.75.227.102 https://labs.firehawktransam.org/ejprice   # 301, server: nginx/1.28.1
curl -sI --resolve lore.firehawktransam.org:443:148.75.227.102 https://lore.firehawktransam.org/mcp       # 200, server: Caddy (catch-all)
curl -sv --resolve zzz-bogus.firehawktransam.org:443:148.75.227.102 https://zzz-bogus.firehawktransam.org/ 2>&1 | grep subject:  # CN=*.firehawktransam.org
curl -sv --resolve mcp-dev.pricepaper.com:443:148.75.227.102 https://mcp-dev.pricepaper.com/code/mcp 2>&1 | grep subject:        # CN=*.pricepaper.com (mcp-caddy)
curl -sk --connect-to lore.firehawktransam.org:443:192.168.64.1:443 https://lore.firehawktransam.org/probe -o /dev/null -w '%{http_code}\n'  # 200 — catch-all IS hades
# This box: no :443 listener; lore stays loopback
ss -tlnp | grep -w -E '443|8443|8444'   # only .100:8443 (jupyter-proxy) and *:8444 (passt/mcp-caddy)
sudo nft list ruleset | grep 443         # only: ip daddr 192.168.64.102 tcp/udp dport 443 redirect to :8444
# hades identity + access
ssh -o BatchMode=yes 192.168.64.1 'hostname; id; uname -sr; which caddy; ls /usr/local/etc/caddy/'
#   -> hades.firehawktransam.org · uid=2000(ejprice) groups=wheel · FreeBSD 14.3-RELEASE-p8
#      /usr/local/bin/caddy · Caddyfile caddy.d certificates
```
Regression probes for the build leg after any hades edit: the labs and mcp-dev lines above
must keep returning exactly those servers/certs.

## 4. Grep fallbacks (dogfood protocol §3 — said out loud)
Deleted-symbol consumer sweep (`BearerAuthMiddleware|AuthVerifier`, bare pattern) ran as
grep, not lore — sanctioned case (a), rename-exhaustiveness where one missed site
compiles-but-breaks. Hits: auth.py, server.py, test_auth.py, test_eager_startup.py,
test_mcp_server.py (each adjudicated in design §8's sweep header). Known-path file reads
(auth.py, config.py, server.py registration spans, installed SDK sources, odoo-code's
auth.py) used Read/sed directly — known addresses, not structure queries. No lore index
consulted for graph verdicts, so no staleness exposure; no friction to file.

## 5. Flags (everything noticed, nothing silently dropped)
- **The investigation plan's Phase-0 topology claim is falsified** (§2.1 above). The design
  doc §2 supersedes it; the plan file is an unrecoverable address (`~/.claude/plans/…`) so
  the correction lives in the tracked doc.
- **`test_mcp_server.py::_MUTATING_TOOLS` omission confirmed at source** (set lacks
  lore_claim_task/lore_tasks while `_TASK_TOOL_ANNOTATIONS` registers both non-read-only).
  In-scope for the build; named in design §7; filed by the lead as **finding #291**.
- **Cert expiry 2026-11-25** is now a connector-availability dependency (two consumers:
  labs edge + lore-caddy). Runbook + calendar line in design §10.
- **Client secret is on NO disk we can read** (grepped the mcp deploy tree) — the claude.ai
  connector form needs it; operator-side, the one hard go-live blocker (design §12).
- **Packet 44's dirty tree** (untracked REPORT-*.md at repo root) — untouched by me;
  standing blocker for starting 39's build on an uncommitted tree (investigation blocker 2;
  the lead sequences it).
- **hades Caddyfile unread + root escalation untested** — classifier denials, recorded as
  design bounds §13 with the build-leg read-first instruction.

## 6. Post-report deltas — two lead pings, applied 2026-07-31 (same session)
1. **Operator override — allowlist substrate (new R12).** The roster moves OUT of
   `lore.yaml` and out of the image: an mtime-watched, newline-delimited flat file,
   bind-mounted read-only; `lore.yaml` carries only its path (`allowed_emails_file`).
   Fail closed+loud at every leg (blank path unconstructible · boot refusal on an
   unloadable roster · runtime deny-ALL on missing/unreadable/empty/parse-refused — a
   parse error refuses the WHOLE roster, never a silently-shorter list). Acceptance test:
   add/revoke with NO recreate and NO rebuild. **One deliberate strengthening beyond the
   override's letter, decided under its no-prompt authority and stated in R12:** the
   mtime `stat` runs on EVERY verification (not only cache-misses) and admission is
   re-evaluated on cache HITS, because the override's own rider (a) demands the *next
   verification* see a roster edit — a miss-only stat would let a positive-cached token
   outlive revocation by the cache TTL. Doc sections amended: §0 (R11/R12 rows), §1 (new
   revocation verdict), §3 (R7 restated for the substrate; R12 added), §4 (admission-on-
   every-verify port change), §5 (config field + F4 every-leg), §9 (group 1), §10 (kill
   switch 3 is now the fastest per-principal switch), §12 (roster-seed row), §14 (roster
   parser in lorerunes; stat-vs-watchdog entry).
2. **Annotations derivation confirmed; the test hand-list is DELETED, not corrected**
   (§7 amended). My §7 already derived the hosted refusal set from
   `ToolAnnotations.readOnlyHint is not True`; the lead's ping confirms it against the
   `FastMCP.tool()` signature and directs the sharper fix for `_MUTATING_TOOLS`: derive
   the coverage set from `mcp.list_tools()` and delete the second source of truth. The
   non-tautology anchor is preserved as explicit per-tool BEHAVIOR fixtures in the
   posture pins (a wrongly-flipped annotation reds a named behavior pin, not a derived
   expectation). The `lore_claim_task`/`lore_tasks` omission stands recorded as a
   confirmed in-flight defect, found independently twice.

## 7. Revision ping (third lead message, 2026-07-31) — applied, with one ground-truth flag
**Flag, stated plainly because the comms record matters:** the revision asserted the R12
override "was silently lost" and that the doc still carried `allowed_emails: list[str]`,
the recreate-based kill switch, and the future-trigger sentence. **A grep of the actual
file immediately before revising showed otherwise** — the first override HAD landed and
was applied in the prior turn (receipt: `grep -n "allowed_emails" docs/design/2026-07-31-
packet39-google-oauth.md` → only `allowed_emails_file` at the config model and F4 legs;
19 `R12` references; §10 already roster-based). The lead's verification read was of a
stale state, not the file at revision time. Report §6 documents the original application.
No harm done — but the inverted narrative ("your ping was lost") should not enter the
packet record uncorrected.

**Genuinely new content in the revision, applied:**
- **Freshness floor adopted as ruled:** one `stat` per CACHE-MISS (my prior text
  deliberately exceeded the floor with a per-verification stat; that strengthening is
  withdrawn in favor of the override's letter). Admission still evaluates on every
  verification against the in-memory roster (zero syscalls), and the **residual exposure
  window is now stated as a FACT**: a revoked-but-cached principal is denied no later
  than the positive-cache TTL, sooner if any other miss reloads the roster. Two
  discrimination pins replace the old cached-token pin (design R12, §4, §9 group 1).
- **The verified `~/docker/mcp/lore-secrets/` idiom** (0700 dir, per-slug 0600 `.env`,
  `build_envfile.py`, `LORE_SECRETS_DIR`/`_resolve_env_file`) cited concretely in R12 as
  the mount-sibling home.
- **#165 status** ("acknowledged, routed to packet 19") added to R12's facts paragraph.
- **#291 cited** in design §7 in place of the restated defect.
- **Kill switches restructured** — per-principal roster edit is now switch 1, above all
  whole-service switches; §1's threat-model verdict reworded to match the TTL fact.

## 8. Contract-pass corrections (fourth lead message, 2026-07-31) — applied
1. **Strong R12 freshness ruling RESTORED** (the lead reversed its own per-cache-miss
   floor, calling it a carelessly-written performance sentence): stat on EVERY
   verification, cache hits included; a revoked principal is denied on the FIRST
   verification after the roster edit; **the residual-window "fact" is deleted from §1
   and R12** — replaced by the stronger property with the cache-HIT/call-count pin and
   the stat-to-miss-only mutation proof. The ruling's two reversals are recorded IN R12
   so the history cannot be re-litigated from stale copies. (Doc: §0 header, §1 verdict,
   §3-R12, §4, §9 group 1, §10 switch 1, §14 stat row.)
2. **§4 scope-check DESIGN BUG fixed** (contract-caught): "require `"email"` in the
   scope set" implemented verbatim would refuse every real token — Google's tokeninfo
   echoes scope values in its own form (plausibly full URIs). Now stated as the superset
   PROPERTY, parametrised over full-URI and bare-alias forms, with the honest bound that
   neither design nor contract verified which form production returns (build-leg live
   probe settles it; §13 extended).
3. **Ruling S1 recorded** — anonymous path enumeration (unknown paths 404 instead of the
   old blanket 401; observable in `LAN_BEARER`, masked at the public edge): ACCEPTED as
   a KNOWN BOUND with re-open trigger, added as §8 row 15 (my table already had 14 rows —
   the lead's "row 14" was off by one against the file; noted, not silently renumbered)
   and as a docstring bound in §1.
4. **Records:** B1 resolved (cachetools 7.1.6 installed, in pyproject — §14 updated) ·
   B4 accepted (`build_mcp_server` gains keyword-only `http_client=` +
   `permission_resolver=`, named in §4/§6) · S2/S3/S4/S6 ratified as the contract
   author's readings and recorded with their content in NEW §15 (read from
   `REPORT-contract-39-auth-1.md` §7 so the builder gets substance, not dangling ids) ·
   S5 superseded by the restored ruling (§15 notes the pin inversion the lead is
   directing separately).

STANDING BY for follow-up design questions via SendMessage, per brief.

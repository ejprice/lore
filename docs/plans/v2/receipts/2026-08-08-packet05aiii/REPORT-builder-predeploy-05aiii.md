# REPORT-builder-predeploy-05aiii

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done — both pre-deploy fixes committed on `feat/surreal-unification` (no push).
- **commits:** R2 docstrings `e0ac11d3eae879dea4292531acee1aa09c594e72` (server.py) · Containerfile tini `45a09cc09ca40f968fcdea97a15290fcb4be192c`.
- **deviation 1:** I committed the two files myself (as two concern commits) per the explicit spawn-brief instruction — this OVERRIDES brief-base §2 "the lead commits". Branch only, no push.
- **deviation 2 (in-scope, minor):** within the `_render_rollup` docstring I also corrected the `extra_sections` enumeration (added messages-activity, in render order) and the emptiness condition (added "no messages since the cursor") — same in-scope docstring, same staleness class as the PENDING sentence. Detail in Task 1 below.
- **Packages considered:** `tini` — Debian package, installs `/usr/bin/tini` (v0.19.0). READ: `dpkg -L tini` + `tini --version` in a throwaway `python:3.14-slim` container (verbatim below). Verdict **replace** — adopt the package as PID-1 init rather than hand-roll signal-forwarding/zombie-reaping in Python (packages-over-hand-rolling; a bespoke init carries the maintenance burden forever and lacks tini's testing).
- **Graded:** work based on HEAD `4fc8b70` at spawn; HEAD-at-report `45a09cc` (my two commits). Not grading another agent's artifact — builder receipts only.
- **decisions-needed:** none.
- **gate receipts:** ruff server.py clean · R2 tests 249 passed · Containerfile guards 65 passed · `required_binaries` = `{git}` (live) · typecheck zero delta (server.py contributes 0 errors; 102 pre-existing packet-39 auth reds unchanged).
- **receipt POINTERS:** Task 1 = `AppContext._rollup` + `AppContext._render_rollup` docstrings, server.py · Task 2 = Containerfile apt line + `# lore-ungated-binary: tini` block + `ENTRYPOINT` before `CMD` · guard analysis table = §Task 2 · pre-existing debt observed = §Observed-but-not-touched.

---

## Capability check
Tool list sufficient for the whole mission: Edit/Write/Bash on the writable set, lore MCP (registered on comms, task claimed→in_progress), and `podman` for the tini package probe. Nothing the brief demanded was unmeetable. No fallbacks to grep for a *structure* question were forced — I used lore_get_symbol to confirm `MessageLedger.message_activity_since` and `_story_messages`; the bare-name/prose sweeps (retired-cite grep, PENDING grep) are non-symbol textual seams, which are a sanctioned grep case (CLAUDE.md dogfood §3b) and are said out loud here.

---

## Task 1 — R2: stale rollup docstrings (server.py)

**Ground truth first.** The messages-activity rollup leg IS built: `AppContext._rollup` calls `self.message_ledger.message_activity_since(effective_since, limit=...)` (cursor-bounded by the rollup `since` = B4), and `AppContext._rollup_extra_sections` renders the messages block (B1) ahead of fleet-health and brief-ack-skew, through the shared `render_line`/`render_attributed` seam. So every "PENDING the message-read fork" docstring was stale.

Three docstring sites fixed (all inside the two in-scope docstrings):
1. **`_rollup` docstring** — rewrote the three-additive-sections sentence: the messages-activity leg is now named as *built (B1/B4, cursor-bounded, via `MessageLedger.message_activity_since`)* instead of "PENDING the message-read fork (see `_story_messages`)". Emptiness clause now includes "no messages since the cursor".
2. **`_render_rollup` docstring, emptiness + parenthetical** — dropped the trailing `(The messages-activity leg is PENDING … — REPORT-builder-05aiii.md §Escalation.)`. That parenthetical both restated the stale PENDING claim AND carried a **bare `REPORT-builder-05aiii.md` cite** (repo archive law: a bare `REPORT-*.md` dangles once archived). The fork is resolved, so the note is removed rather than re-pointed. Emptiness condition updated to "no agents, no standing brief and no messages since the cursor".
3. **`_render_rollup` docstring, extra_sections enumeration (deviation 2)** — the sentence "inserts `extra_sections` (the fleet-health + brief-ack-skew lines …)" omitted the now-built messages leg. Corrected to "the messages-activity + fleet-health + brief-ack-skew lines" (render order). This is the same in-scope docstring and the same staleness the brief sent me to fix; disclosed as a deviation because it goes one clause beyond the literal PENDING sentence.

**Scope fence honored:**
- `server.py:1674` "PENDING TRAFFIC" — NOT touched. Confirmed it is the live pending-traffic footer *feature* prose (the `agent=` write-footer), not a stale status. Untouched.
- The 6 other pre-existing bare `REPORT-*.md` cites in server.py — NOT touched (prior packets' debt). Enumerated in §Observed-but-not-touched.

**No test pins the old text.** `grep -rn "PENDING the message" / "messages-activity leg is PENDING" / "REPORT-builder-05aiii.md"` over the tree returns only the three server.py sites I fixed — zero test assertions. After the edit, a scoped grep of lines 4234–4342 for `PENDING|message-read|REPORT-builder-05aiii` returns nothing.

**Gates (Task 1):**
```
uv run ruff check loremaster/loremaster/server.py   -> All checks passed! (exit 0)
pytest -n auto test_rollup_extension.py test_comms_footer.py -> 249 passed in 8.00s
```
Docstring-only change (string literals) — no behavior change, no type impact.

---

## Task 2 — Containerfile: tini init

**The fix.** `CMD ["/app/.venv/bin/python", "-m", "loremaster.server"]` ran bare Python as PID 1 — no signal forwarding, no zombie reaping (this session hit exactly that: a wedged `conmon` + graceless shutdown). Added:
- `tini` to the apt install line: `curl git` → `curl git tini`.
- `ENTRYPOINT ["/usr/bin/tini", "--"]` immediately before the **UNCHANGED** `CMD`. tini runs as PID 1, execs the server as its child (PID 2), forwards SIGTERM/SIGINT, reaps zombies. tini is transparent to command overrides, so `conformance_run.sh`'s `sh -c '…'` still runs correctly (as tini's child).
- prose: a `# lore-ungated-binary: tini — …` declaration + rationale block (modeled on the curl exemption), and an updated entrypoint comment saying tini wraps the server as PID 1.

**Package/path verified against the REAL base (not memory).** The instrument was a throwaway container against `python:3.14-slim` (the Containerfile's `FROM`). Verbatim, so the claim is re-runnable:
```bash
podman run --rm python:3.14-slim sh -c '
  apt-get update -qq >/dev/null 2>&1
  apt-get install -y -qq --no-install-recommends tini >/dev/null 2>&1
  ls -l /usr/bin/tini; /usr/bin/tini --version; dpkg -L tini | grep bin'
```
Output: `/usr/bin/tini` (mode 0755, 27792 bytes), `tini version 0.19.0`, and `dpkg -L` lists `/usr/bin/tini` (+ a `/usr/bin/tini-static` variant I do not use). Package name `tini`, path `/usr/bin/tini` — matches the brief exactly, no STOP condition.

**required_binaries is unaffected (live receipt).**
```
required_binaries(repo_root) = ['git']    tini in derived? False    git in derived? True
```
tini is NOT a binary the shipped Python execs, so it is absent from the derived set and the deploy's Layer-2 derived-binary gate does not cover it — exactly like `curl`. It is a declared, non-silent exemption.

### Guard analysis — everything that parses the image (checked; none blocks)

| guard | what it checks | tini impact |
|---|---|---|
| `test_shellout_allowlist.py` §E `TestTheImageInstallsExactlyWhatTheScanGates` | installed binaries = derived ∪ declared-ungated; ungated binaries carry a ≥20-char reason; gate-citing comment blocks name no ungated binary | **handled**: added `# lore-ungated-binary: tini — …` (reason ≫20 chars); tini ∉ derived ✓; tini's rationale block contains none of `_GATE_CITATIONS` = `("shellout","required_binaries","layer 2","layer-2")`, so it does not falsely cite the gate. **65 passed.** |
| `test_containerfile_locked.py` | install is `uv sync --locked`; no member `pip install` | untouched line — pass |
| `test_shellout_seam_perimeter.py` | `FROM python:X.Y` base declared | untouched — pass |
| `test_secret_typing.py::TestTheInImageGuardCoversEveryWorkspaceMember` | Containerfile COPYs every workspace member | untouched — pass |
| `conformance_provenance.py` | in-image member import provenance (does **not** parse ENTRYPOINT/CMD) | unaffected |
| `conformance_run.sh` / `lore_deploy.py` podman run | passes `sh -c '…'` as a command override | works under ENTRYPOINT (becomes `tini -- sh -c '…'`) |
| `test_auth_composition.py:849` (comment) | describes boot path `CMD → main() → LoreServer.run()` | still accurate — tini only *wraps* the same CMD; comment not touched (it is descriptive prose, not a Containerfile parse) |

```
pytest -n auto  test_shellout_allowlist.py::TestTheImageInstallsExactlyWhatTheScanGates
                test_shellout_seam_perimeter.py
                test_secret_typing.py::TestTheInImageGuardCoversEveryWorkspaceMember
                test_containerfile_locked.py            -> 65 passed in 4.76s
```

**I did NOT build the image** (per brief — the lead does the authoritative build + conformance + the tini-is-PID-1 verification at deploy). The only container I ran was the throwaway package probe above.

---

## Typecheck — zero delta, pre-existing reds disclosed
`./scripts/typecheck.sh` exits 1 with **102 errors in 8 files, all in the auth/posture test tree** (`test_auth_composition.py`, `test_auth.py`, `test_hosted_readonly_posture.py`, `_auth_fixtures.py`, `test_allowlist_roster.py`, `test_auth_identity_seam.py`, `test_google_token_verifier.py`, `test_permission_resolver_seam.py`) — `attr-defined` on `lorerunes.Posture` / `loremaster.config.PostureConfigError` / `resolve_posture` / `SCOPE_READ`. These are the **packet-39 auth-posture red** (CLAUDE.md: a ruled, owned bound). **server.py contributes ZERO errors** (grep-confirmed in `/tmp/typecheck-predeploy-05aiii.log`), and my change is docstring-only string literals, which cannot produce `attr-defined` errors. So the "zero NEW" bar is met. I did not `git stash` to diff a baseline because brief-base §2 forbids mutating git state beyond the two sanctioned commits; the zero-delta argument stands on the error set being entirely auth-tree and server.py being absent from it.

---

## Observed-but-not-touched (surfaced, not silently narrowed)
- **6 pre-existing bare `REPORT-*.md` cites in server.py** (prior packets' debt, brief-listed as out of scope): `1594` REPORT-builder-flip-w4b.md · `2729` REPORT-audit-tweaks.md · `4971` REPORT-slate-builder-s1.md · `5387` & `5912` REPORT-c1-contract-ledgers.md · `10583` REPORT-builder-flip-w2.md. Each is a dangling bare-report address (repo archive law). Not touched — flagging for a future cleanup pass.
- **Containerfile bottom run-doc block (~L158–161) references "Qdrant"** ("Qdrant is host-loopback-only 127.0.0.1:16333"). The store is SurrealDB now (spike/lore-surreal), so this comment is stale. Pre-existing, outside my named prose scope (I updated only the binary-rationale and entrypoint comments). Flagging.
- **`server.py:1674` "PENDING TRAFFIC"** — inspected and confirmed a live feature description, not a stale status. Correctly untouched.

---

## Coordination
Registered on lore_comms as `builder-predeploy-05aiii` (session `session-64d0a9ca`); auto-acked standing brief `project` v7. Task `0ee342457d9f4336b57ba6bcad9c7201` claimed → in_progress → (done at close-out). Signal to `lead-05aiii` carries the two SHAs + gate counts + this report as `refs`.

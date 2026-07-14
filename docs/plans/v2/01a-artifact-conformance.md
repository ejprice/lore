# 01a — Artifact conformance: run the suite IN the deployed image (operator-minted 2026-07-14)
size ~0.25 wu (MEASURE-FIRST — see Scope) · pre-wave, runs BEFORE packet 02 · depends: packet 01 (done)
lead: Opus (roster is Opus end-to-end) · law: repo CLAUDE.md · DEPLOY: no (it GATES the deploy)
FIRST READS: finding **#139** (the design + both traps, already derived — do not re-derive) ·
`REPORT` history is gone, so the receipts live in #139, #131, #107, #24.

## Mission
**Our test suite runs on a dev host. Production is a container. Every difference between them is an
unguarded gap — and we have shipped TWO outages that lived in exactly that gap.**

- **#131**: the code shells out to `git`; the image had no git. The `OSError` was swallowed into a
  silent `(None, None)`. No test could see it — **tests run on a host that HAS git.** Months of empty
  snapshot provenance, invisible because nothing rendered the field.
- **#107**: a widened schema ASSERT never migrated. No test could see it — **every test mints a virgin
  throwaway DB**, and a fixture that guarantees a clean slate cannot test what only happens on a dirty
  one. A 100% production outage, with 1040 tests green, a cold audit GO, and a passing adversary.

Same root, twice: *the fixture guarantees the one condition under which the bug is invisible.*

Packet 01's deploy gate catches the #131 **instance** (binaries present; a `.git` root must serve a
non-null branch). This packet catches the **class**: the general property is *the artifact behaves the
way the tests assume it does*, and the only way to know that is to **run the tests IN the artifact**.

## The design (operator-ruled — it is settled; build to it)
An **EPHEMERAL container from the DEPLOYED IMAGE** (`podman run --rm localhost/lore:latest`), worktree
bind-mounted, test deps installed AT RUN TIME. Same pattern as the odoo-dev ephemeral test containers.
The image is never modified (packet 37's slimming is unaffected) and the read-only `/workspace` mount
stops being an obstacle.

## THE TRAP THAT DECIDES WHETHER THIS IS A GATE OR THEATRE
**Which `loremaster` do the tests import?** Bind-mount the repo, put it on `sys.path`, and
`import loremaster` resolves to **the MOUNTED SOURCE**, not the baked `site-packages` copy — you would
be testing the working tree again, inside a container, and learning NOTHING about the artifact.
This is finding **#24 in reverse**, and it is the ambiguity every packet-01 contract author defended
against by verifying `loremaster.__file__` before trusting a single run.

**The conformance run MUST ASSERT WHAT IT IS TESTING:** `loremaster.__file__` resolves into
`site-packages`, NOT `/workspace` — and FAILS LOUD if it does not. **Mount the TESTS; import the
ARTIFACT.** Without that assertion the gate silently passes over a broken image the day someone's
`PYTHONPATH` or `cwd` shifts — precisely the failure it exists to kill. Pin it, and mutation-prove the
pin (point the import at the mount; the harness must REFUSE to run).

## THE SECOND TRAP: do NOT curate a list of "environment-sensitive tests"
That is a NAME-LIST, and packet 01 is a three-round lesson in why the name-list always loses.
**Inversion: run the WHOLE suite in the container; host-vs-container DIVERGENCE is the signal.** A test
that passes on the host and fails in the container **is** an environment defect — nobody has to guess
in advance which. A test that genuinely cannot run in-container opts out with a **visible, reasoned
marker**; the DEFAULT is "runs". Allowlist-the-safe, applied to the suite.

## Ground truth (probed live in packet 01 — do NOT re-derive)
- The deployed image has **NO pytest** and no test deps (it installs only the three workspace members).
- The tests are **NOT baked into the image**; the source IS visible via the `:ro` `/workspace` mount (87 files).
- **spike-surreal `:18000` IS reachable from inside the container** (`--network=host`) — store-backed tests can run.
- `/workspace` is **READ-ONLY** in the deployed container — pytest cache + bytecode must be redirected.

## Scope IN — MEASURE FIRST (this is the sizing discipline, not a hedge)
1. **The harness**: ephemeral-container runner + the import-provenance assertion (above) + writable
   temp/cache redirection + test-dep install at run time. Contract-first, per repo law.
2. **RUN IT, and MEASURE.** Count and classify every host-vs-container divergence:
   **(a) a real ARTIFACT DEFECT** (the image is wrong — this is the payload) ·
   **(b) a test that legitimately cannot run in-container** (gets the visible opt-out marker + reason) ·
   **(c) a harness bug** (fix it).
   **That count is genuinely unknowable before it is measured.** Do NOT estimate the triage in advance —
   let the measurement scope it. If the classified triage exceeds the packet's remaining budget, SPLIT
   (01b) with the measurement as the receipt, per the sizing law.
3. **Wire it where it belongs**: at IMAGE-BUILD time (you have just produced an artifact — prove it
   behaves), NOT on every `start` (~3 min on a no-op deploy). Packet 01's cheap probes STAY on `start`
   to catch a stale or wrong image.

**PREDICTION, recorded so it can be checked: the first run WILL find real defects.** Two outages already
lived in this gap. **If it finds nothing, that is a finding about the HARNESS** — interrogate the harness
before believing the artifact is clean.

## Scope OUT
- Fixing every (a)-class defect the measurement uncovers, if it is large — that is 01b, scoped BY the
  measurement, not guessed at now.
- Image slimming (packet 37) · worktree deploys (#134 → packets 17/23) · the #102 runtime guard's
  out-of-tree blindness (#136 → the #102/#120 owner, and it must land BEFORE 17/23).

## Entry check
`podman images | grep lore` — an image exists · the deployed containers are on it · `lore_findings get 139`
matches this packet's premise. If ground truth contradicts the packet, STOP and surface.

## Exit
Harness green with counts · the import-provenance pin MUTATION-PROVEN · the divergence measurement
recorded (counts + per-item classification, no wholesale classification — every divergence gets an
individual verdict) · cold REFUTE audit · one-concern commits at natural boundaries · findings
resolved/filed · INDEX row + ≤5-line Log entry · ledger row done.

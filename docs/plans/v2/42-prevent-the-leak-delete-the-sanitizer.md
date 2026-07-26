# 42 — PREVENT THE LEAK, DELETE THE SANITIZER
size ~0.20 wu · wave L · depends: — (independent) · **DEPLOY: yes** (a served surface changes: logs)
law: DESIGN-LAW §1 (trust), CLAUDE.md "allowlist the safe", "one implementation"

## Mission
**Stop trying to DETECT secrets in arbitrary text. Make it structurally impossible for a secret to
be in the text in the first place — then delete the detector.**

The redactor's entropy catch-all is a heuristic guessing whether a ≥24-char run "looks like" a
credential. That is an unbounded classification problem over an unbounded input, and it has lost
every round: it mangled path components (#227), then function names (audit R2), then rendered source
lines, and it still redacts git SHAs and UUIDs by deliberate accepted bound. **Each fix spawned the
next mole, and each one paid for a guess with real diagnostic data.**

**Operator ruling, 2026-07-26 (verbatim intent):** *"You're playing whack-a-mole again on what might
work, while risking losing valuable data. The better option is to PREVENT the data leak in the first
place, and let the logger log. The root cause is leaked credentials. How do we prevent that? That
will eliminate the need for the sanitizer."*

## The measurement that makes this a deletion, not a rewrite
All measured 2026-07-26 by the lead at `79ceff9`. **Re-derive before building — these are the load-
bearing facts and every one is a query, not a recollection.**

| # | measured | consequence |
|---|---|---|
| M1 | A standard Python traceback renders the **source LINE**, never local variable **values**. A secret in a variable shows as `use(api_key)`. Only a secret written as a **literal at the call site** appears. | The traceback leak vector is *hardcoded secrets*, not *secrets in flight*. |
| M2 | `SecretStr` masks **completely** — f-string, `repr()`, `str()`, and interpolated into an exception message all render `**********`. | A typed secret cannot leak through any of the four normal paths. |
| M3 | **13** `.get_secret_value()` call sites across all production code. | The entire unwrap surface is small and **enumerable** — the safe set, not the forbidden set. |
| M4 | **Nothing** renders frame locals: no `rich.traceback`, no `show_locals`, no `better_exceptions`. | The "a traceback might contain locals" fear is not true of this codebase. |

⚠ **M4 is a property of the code TODAY and is exactly the kind of thing a future dependency change
silently breaks** (`rich` is already an indirect dependency). The gate in step 3 must pin it, not
assume it.

## Scope IN
1. **Complete the type coverage.** `loresigil`'s embedder keys are still bare `str`; `loremaster` is
   done (#211 Half A). Every secret is `SecretStr` from resolution to unwrap. **Resolves the type
   half of #222.**
2. **ONE entry point.** Three hand-rolled secret resolvers exist — `config.resolve_secret`,
   `loresigil/factory._resolve_api_key`, and `calibration/counting.load_api_key` ≡
   `scripts/token_survey.load_api_key`. Consolidate. ⚠ This is a **cross-package architecture call**
   (`loresigil` cannot import `loremaster`) — see #222 for the three candidate shapes; it needs a
   ruling before code. **Investigate `pydantic-settings` first** — it is already a declared-but-unused
   dependency (pkgscout P9), and the packages rule applies before anything is hand-rolled.
   **Resolves #226 with it (slotted 2026-07-26):** `resolve_secret` is today used on values that
   are NOT secrets — the `.get_secret_value()` unwrap exists at those sites only to undo a wrapping
   that should never have happened (its own author got 1 of 5 sites wrong). The consolidated seam
   wraps ONLY secrets; non-secret config reads stop routing through it, which also SHRINKS the
   step-3 allowlist rather than growing it.
3. **Gate the unwrap surface — ALLOWLIST THE SAFE.** An AST pin over the 13 `.get_secret_value()`
   call sites. Each entry is **evidence-backed**: the unwrapped value goes directly to a client call
   and is not logged, stored, interpolated, or bound to a name that outlives the expression. A new
   unwrap site with no entry is RED. This is `CLAUDE.md`'s own instrument law — *the forbidden set is
   unbounded; the safe set is small and enumerable.*
4. **Pin M4.** A test asserting no traceback formatter in the dependency closure renders locals, so a
   future `rich.traceback.install()` cannot silently reopen the vector.
5. **THEN DELETE `_TOKEN_RE` AND THE SHANNON-ENTROPY HEURISTIC.** Keep the **labelled** patterns
   (`Authorization: Bearer …`, `api_key=…`) — those are precise, structural, and do not
   false-positive. The catch-all is the entire false-positive engine.
   ⚠ **#235 RIDER (slotted 2026-07-26 — the rider is part of the ruling):** the labelled
   Authorization pattern this step KEEPS is itself broken — `_ASSIGNMENT_RE` eats the SCHEME as
   the value for every non-Bearer scheme, so today the catch-all is what (accidentally) covers
   `Basic`, and deleting it without the fix WIDENS the leak. Fix the labelled pattern **in the
   same commit** that deletes the catch-all, with a pin proving `Authorization: Basic <cred>` is
   scrubbed with the catch-all gone (that pin is the mutation proof for this rider).
6. **Retire what the catch-all forced.** #227's path-component exemption and its four conditions,
   the bare-hex/SHA bound, the UUID bound, and the audit's R2 — **all become unnecessary code and
   unnecessary bounds.** Delete them with it; do not leave them as vestigial guards.

## Scope OUT (surface to operator if encountered)
- The labelled patterns stay. This packet does not remove defence-in-depth; it removes a *guess*.
- Anything about WHAT gets logged (counts vs payloads). The discipline "callers never log a secret"
  is unchanged and remains the first line.

## What this eliminates, and it is the point
- **Audit R2** — 12.4% of function names (201 of 1,616) erased from every traceback frame, plus
  rendered source lines. **No decision needed; the cause is deleted.**
- **#227** in full, including both accepted KNOWN BOUNDs.
- Every future member of the family. There is no next mole, because there is no detector.

## Entry check
- #211 Half A landed (`SecretStr` through `loremaster`, one `signin_credentials` unwrap seam).
- #222 read — the cross-package resolver question is **ruled before step 2 starts**, not during.
- The four measurements above **re-derived**, with their commands, per #224.

## Exit
TDD per repo law. **The deletion in step 5 is the load-bearing change and needs the strongest
control available**: prove that with the catch-all gone, a credential in each of the four M1–M4
vectors still cannot reach a rendered log line — and mutation-prove each pin (remove the guard,
watch RED, restore). ⚠ Per #229, **any pin here that replaces a deterministic assertion with a bound
gets a both-ways mutation diff** — this wave produced four hollow pins and two of them were in
exactly this module.
⚠ **#221 RIDER (slotted 2026-07-26): the mypy gate is BLIND through `dict[str, Any]`** — the
SecretStr migration passed the type gate at ZERO DELTA while 119 tests were runtime-broken. Every
contract pin in this packet therefore needs a RUNTIME red, never a type-gate red; and where the
config seam can be narrowed from `dict[str, Any]` to a typed model in passing, do it (that is the
structural fix; #221 stays open for the general instrument if not fully closed here).

**Deploy required** (logs are a served surface). Report the recovered data as a receipt: the same
traceback rendered before and after.

## Provenance
Born from the audit's R2, which the operator refused to treat as a fix-or-accept fork. The finding
chain: **#211** (secrets in logs) → **#227** (the redactor mangling paths) → audit **R1** (its fix
leaked 100% of slashed base64) → audit **R2** (function names) → this packet. Four rounds against a
heuristic; the fifth move is to remove the heuristic.

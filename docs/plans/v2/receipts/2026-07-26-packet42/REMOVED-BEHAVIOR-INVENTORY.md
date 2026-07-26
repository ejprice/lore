# Packet 42 — REMOVED-BEHAVIOR INVENTORY (tdd Phase 0)

Mechanical enumeration of every observable behavior of the code packet 42 deletes or
replaces, at sub-path grain. One old code path can hold both a virtue to preserve and a
sin to drop, so branches, guards, side effects and per-field output provenance are listed
individually. This file feeds Phase 1 adjudication, the Phase 2 adversary's **stage 2**
(never stage 1 — the adversary enumerates independently first and the DIFF is the
instrument), and the Phase 7 deletion reconciliation.

Base: `6a21fb6` on `feat/surreal-unification`. Worktree `pkt42-prevent-the-leak`.

**Provenance note.** The packet's own measurement table says *"M3 — **13**
`.get_secret_value()` call sites"*. Re-derived at base: **13 grep hits, 10 real call
sites**. `config.py:725` and `_txn.py:964,967` are prose inside docstrings. The count in
the packet conflates two populations; the allowlist in step 3 is sized off the **10**.

---

## A. `loremaster/logging_setup.py` — the entropy catch-all (packet steps 5 + 6)

| # | behavior at base | adjudication |
|---|---|---|
| A1 | `_TOKEN_RE` = `[A-Za-z0-9+=_\-]{24,}` selects the candidate window; charset excludes `/` and `.` | **dropped-deliberately** — the candidate window exists only to feed A2 |
| A2 | a candidate whose Shannon entropy ≥ `_ENTROPY_BITS_THRESHOLD` (3.5) → `***REDACTED***` | **dropped-deliberately** — packet Mission; this IS the heuristic being removed |
| A3 | a candidate with entropy < 3.5 survives intact (e.g. a long repetitive run) | **dropped-deliberately** — falls out with A2 |
| A4 | `_is_safe_high_entropy_run`: path-component OR canonical UUID → exempt | **dropped-deliberately** — vestigial once A2 is gone (packet step 6, explicit) |
| A5 | `_is_absolute_path_component` cond. 1: maximal blob starts with `/` | **dropped-deliberately** — support for A4 |
| A6 | cond. 2: blob contains no `+` and no `=` | **dropped-deliberately** — support for A4 |
| A7 | cond. 3: run is not the FIRST component of the blob | **dropped-deliberately** — support for A4 |
| A8 | cond. 4: run is not MIXED CASE | **dropped-deliberately** — support for A4 |
| A9 | `_UUID_RE.fullmatch` exempts a canonical RFC-4122 UUID anywhere | **dropped-deliberately** — support for A4 |
| A10 | `_shannon_entropy_bits("")` returns `0.0` (empty-string guard) | **dropped-deliberately** — function deleted |
| A11 | `_PATH_BLOB_CHARS` deliberately INCLUDES `+`/`=` so A6 can observe them | **dropped-deliberately** — support for A6. ⚠ This constant's comment records that an earlier version made A6 **dead code**; the coupling dies with both |
| A12 | ORDER in `_scrub_text`: bearer → assignment → entropy, so labelled patterns win | **preserved-with-pin** — bearer→assignment order survives; pin that a labelled secret is still label-preservingly redacted |
| A13 | scrubbing is idempotent (`***REDACTED***` re-scrubs to itself) | **preserved-with-pin** — must still hold with only the labelled patterns |
| A14 | `_BEARER_RE` redacts `Bearer <token>`, preserving the label | **preserved-with-pin** — packet Scope OUT keeps labelled patterns |
| A15 | `_ASSIGNMENT_RE` redacts `api_key=…`/`token:…`/`password=…` etc., preserving label+separator | **preserved-with-pin** — same |
| A16 | KNOWN BOUND: a bare hex/git-SHA run outside a path is redacted (#227 residual) | **bound DISSOLVED** — no longer redacted. `TestBareHexRunsStayRedactedKnownBound` must be **deleted with a note**, not left green. Per "WHEN YOU CANNOT CLOSE A HOLE, PIN IT", a pin outlives its hole only as a lie |
| A17 | KNOWN BOUND: a secret in a URL path segment, or a UUID-shaped key, is NOT caught | **bound dissolved as a bound** — but see A18 |
| A18 | an UNLABELLED secret in free log text was caught by A2 | ⚠ **exposure genuinely widens — the deliberate trade.** This is the load-bearing risk of the packet and the reason its Exit clause demands the strongest control available. Replacement control: `SecretStr` typing (M2) + the allowlisted unwrap surface, so the value cannot be in the text |
| A19 | `RedactingFilter.filter`, `_scrub_value`, `scrubbed_exception_text` call `_scrub_text` | **preserved** — call sites unchanged; only `_scrub_text`'s body shrinks |

**Per-field output provenance for `_scrub_text`:** input string → output string. At base the
output is the input with three transforms applied in order (A14, A15, A2). After: the same
string with two (A14, A15). Every byte not matched by a labelled pattern is **copied through**
— that is the copied-through set, and it WIDENS by exactly the A2 population.

---

## B. `loresigil/factory.py` — resolver copy #2 (packet steps 1 + 2, operator-ruled)

Ruling 2026-07-26: push resolution UP to the composition root. `loresigil` stops resolving.

| # | behavior at base | adjudication |
|---|---|---|
| B1 | `_resolve_api_key` reads `os.environ.get(api_key_env)` | **dropped-deliberately** — the ruled shape; loresigil resolves nothing |
| B2 | `if not key` → `MissingApiKeyError` (covers BOTH unset and empty-string) | **preserved-with-pin as a PROPERTY** — "a missing/empty key fails loud and never builds a keyless embedder". The exception TYPE moves packages with the ruling |
| B3 | a WHITESPACE-ONLY env var is **accepted** and returned as the key | **old-bug — documented, NOT re-pinned.** `resolve_secret` rejects it (`.strip()` emptiness check). Adopting the canonical resolver fixes this incidentally; the new contract must not re-pin the old permissiveness |
| B4 | the value is passed byte-exact (no stripping) | **preserved-with-pin** — `resolve_secret` also never strips; a key with real leading/trailing whitespace must survive |
| B5 | the error message names the offending env var | **preserved-with-pin** — `resolve_secret`'s `KeyError` also names it |
| B6 | `MissingApiKeyError` is a `RuntimeError` subclass, publicly importable | **dropped-deliberately** — raised only by B1. Caught nowhere in production; 4 test files import it |
| B7 | resolution happens at `make_embedder()` time, i.e. embedder CONSTRUCTION | **dropped-deliberately** — moves EARLIER, to config translation. Failure is strictly sooner, never later |
| B8 | `EmbeddingConfig.api_key_env: str` — required; any string accepted, unvalidated | **dropped-deliberately** — replaced by `api_key: SecretStr` |
| B9 | `make_embedder` passes one resolved `api_key` into all three backend arms | **preserved-with-pin** — must still reach the wire byte-exact on EVERY arm, forced per backend |
| B10 | `loremaster.config.EmbeddingConfig.api_key_env` (the `lore.yaml` schema) | **preserved — NOT TOUCHED.** The env-var NAME belongs in config. `server.py`'s probe-gate message reads this field and stays valid |

**Per-field output provenance for `to_loresigil_config`:** every loresigil field is
**copied-through** from the loremaster config except `output_dimension` (forced from
`config.dim`) and, after this change, `api_key` (**derived** via `resolve_secret`, replacing
the copied-through `api_key_env`). The remaining ten copied-through fields must stay
copied-through — a reshape that drops one is a silent config regression no gate sees.

---

## C. `calibration/counting.py::load_api_key` ≡ `scripts/token_survey.py::load_api_key`

Operator-ruled 2026-07-26: declare `python-dotenv` and adopt it.

| # | behavior at base | adjudication |
|---|---|---|
| C1 | prefers an already-exported `ANTHROPIC_API_KEY` over the file | **preserved-with-pin** — precedence is policy |
| C2 | the exported value is `.strip()`ped | **spec-silent → operator ruling.** Conflicts with B4/`resolve_secret`, which never strips. Two of our three resolvers disagree on this TODAY; consolidation must pick one and say why |
| C3 | falls back to parsing `env_file` line-by-line | **preserved-with-pin** — behavior kept, mechanism replaced by `dotenv` |
| C4 | matches lines starting with `ANTHROPIC_API_KEY=` | **preserved-with-pin** |
| C5 | splits on the first `=`, strips whitespace, then strips `'` and `"` | **dropped-deliberately (mechanism)** — `dotenv` owns quote/escape handling and does it more correctly (it also handles `export ` prefixes and multiline values, which C5 does not) |
| C6 | an empty value after parsing → keeps scanning subsequent lines | **preserved-with-pin** — a later non-empty line still wins |
| C7 | raises `RuntimeError` naming both the env var and the file | **preserved-with-pin** |
| C8 | returns `SecretStr` | **preserved-with-pin** |
| C9 | an EMPTY exported env var falls THROUGH to the file | **old-bug candidate → operator ruling.** `resolve_secret` treats empty as fatal; this treats it as absent. #222 names exactly this ("is an empty env var the same as an unset one") as the security-relevant drift |
| C10 | the two twins are byte-divergent (different `RuntimeError` line wrapping) | **dropped-deliberately** — they collapse to one implementation |
| C11 | pkgscout measured one twin failing to honour `export KEY=…` | **old-bug — documented, NOT re-pinned.** Re-derive before claiming fixed |

---

## Open rulings this inventory surfaces (for the Phase 1 approval prompt)

1. **C2 / C9 — strip-and-emptiness semantics.** Three resolvers, three answers. Consolidation
   forces ONE. Recommendation: adopt `resolve_secret`'s semantics (never strip the value;
   treat unset/empty/whitespace-only as fatal) and pin it, because a key whose real bytes
   include whitespace must survive, while a blank variable is always operator error.
2. **A18 — the widened exposure.** Accepted by the operator ruling that authored this packet,
   but it is the packet's central risk and must be met with the strongest available control
   rather than assumed away.

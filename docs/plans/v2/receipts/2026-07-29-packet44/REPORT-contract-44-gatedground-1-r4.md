brief-base v9 read

# REPORT-contract-44-gatedground-1-r4 — answering the second adversary

*Answering `REPORT-adversary-44-gatedground-2.md` (INSUFFICIENT). Measurements 2026-07-29 in
worktree `.claude/worktrees/pkt44`, branch `pkt44/ungated-ground`, at **`f033a87`**. Prior
reports (`…-r2.md`, `…-r3.md`) stand for the record.*

---

## SUMMARY BLOCK

- `brief-base v9 read`
- **state: done-with-deviations** — all 8 pins built, the package row added, both "do not touch"
  boundaries honoured.
- **⚠ FIXED TARGET FOR THE RE-GRADE:** `scripts/test_gated_ground.py` · md5
  **`9fe25b1d42a8e8b101325b6f8c8f253a`** · **2755 lines** · **126 test functions → 197
  collected** · **195 green, 2 EXPECTED-RED by design**, three consecutive runs. No edits since.
  *(As it ships, running the file is a `ModuleNotFoundError: gated_ground` collection error —
  contract-first. The 197/195/2 figures are against a throwaway reference build, now deleted.)*
- **11 mutation proofs this wave, every observed column non-blank** (§3). **Three came back
  PROOF FAILED first**; one was a **real defect** — the P-4 pins were placed in the class my
  runs deselect, the *identical* mistake MP-N1 caught last wave (§3.1). Reported, not buried.
- **P-6 is the one that mattered and it is built:** `gg.unmodelled_pytest_configuration`, an
  allowlist over `[tool.pytest.ini_options]` *and over `addopts` tokens*, wired into **both**
  entry points. The correct build no longer serves a false clear under `norecursedirs`.
- **P-1 closed at the VERDICT:** every blind input now refuses through `ungated_ground` **and**
  `classify`; the reader-level pins stay as localisers.
- deviation: **I lost the roster-era reference build** by not re-saving it to scratch, and had
  to reconstruct it (§5.1). My own instrument-preservation failure; disclosed because it is the
  exact perversity brief-base §1 names.
- **`FROZEN_SHA` left at `f033a87`, seam untouched, as instructed** — but P-7's shape rule
  **does constrain the eventual anchor**, and you asked to be told rather than guessed at (§4.1).
- **capability gaps unchanged: no `mcp__lore_lore__*`, no `SendMessage`.**
- `Packages considered:` **one row added** — `git ls-tree -r -z --name-only` (READ: measured the
  quoted-vs-raw divergence on a newline path in a real repository; §6) → **replace** a
  line-oriented read. Rest of r2 §6 stands.
- **decisions-needed (2):** §4.1 the `FROZEN_SHA` anchor shape · §4.2 whether I am right that
  this is convergence rather than a design that should change.
- receipt pointers: pin-by-pin §2 · mutation proofs §3 · escalations §4 · deviations §5 ·
  package row §6.

---

## 1. On the verdict

The second adversary is the best artifact this packet has produced, and two things in it are
worth naming before the fixes. It **re-derived all eleven of the first pass's survivors instead
of relaying them**, and it **adjudicated two of its own twelve survivors as INERT and NOT
findings** — including one it expected to be a hole, killed by its own whole-tree control
(`292 paths compared, 0 divergent`). An adversary that strikes its own results is one whose
remaining results I can act on without re-deriving them. I did re-derive where it changed my
design (§3), and it agreed everywhere.

**The headline is correct and I had the wrong mental model.** I had been reading *"blind is not
clean"* as a property of the readers. It is a property of the **verdict** — and my own contract
already knew that, in one place: `test_an_unmodelled_setting_makes_the_WHOLE_VERDICT_refuse_not_
just_a_reader`, written two waves ago against exactly this shape. **I wrote the right pin once
and did not generalise it**, which is the quantifier law in its plainest form: I guarded the
door I had just been shown instead of the outcome over all doors.

---

## 2. The eight pins

| # | what shipped | mutation proof |
|---|---|---|
| **P-1** BLOCKER | `TestBlindIsNotCleanThroughTheWholeVerdict` — 4 blind inputs (unreachable sha · no `MEMBERS` · `"."` testpath · no `git`) routed through **both** `ungated_ground` and `classify`, plus a **healthy positive control** so a build that raises unconditionally cannot pass. `classify` now refuses every blind input in a prologue, before any per-file work | **MP-A1** (7 red), **MP-A3** (5 red) |
| **P-2** BLOCKER | `test_a_test_shaped_sibling_of_the_archived_receipts_root_is_not_exempt_on_execution` + a `receipts_live/test_promoted_tool.py` fixture. The existing sibling was not test-shaped, so the receipts site was discriminated on TYPES only | **MP-A4** |
| **P-3** BLOCKER | `test_a_file_added_after_the_freeze_is_flagged_on_the_execution_axis_too` — an `axis=EXECUTION` roster row + a file added after the freeze. Every roster fixture had been `axis=TYPES`, so the roster was **guarded by axis** and an EXECUTION row stayed an open-set exemption | **MP-A5** |
| **P-4** BLOCKER | `test_member_mypypath_returns_only_what_the_runner_declares` + `test_every_declared_mypypath_entry_reconstructs_a_line_of_the_real_runner`. **This is the false-gate shape I fixed one pin over and reproduced here** — the MYPYPATH pin asks about the RUNNER, so a fabricating reader answers it with the guard's opinion | **MP-A6** |
| **P-5** MEDIUM | `test_the_roster_filters_python_by_suffix_not_by_substring` — a substring filter admits `notes.py.txt`, which defeats the empty-roster anti-vacuity guard, so a tree with no Python reads as a working exemption | **MP-A7** |
| **P-6** BLOCKER | `TestPytestConfigurationThisGuardDoesNotModel` (6 params + a false-gate control + a whole-verdict leg) and the new `gg.unmodelled_pytest_configuration`. Allowlists `[tool.pytest.ini_options]` keys **and `addopts` tokens** — two params are settings "invented after this guard", the property a denylist cannot satisfy | **MP-A10**, **MP-A11** |
| **P-7** LOW | `frozen_sha` shapes `"ab"`, `"F033A87"`, `"deadbeefG"` added to the malformed-row matrix | **MP-A9** |
| **P-8** MEDIUM | `test_a_hostile_path_in_the_roster_survives_derivation_intact` — a `scripts/forged\nrow.py` present at the freeze. `git ls-tree` now `-z`; read line-wise the file falls OUT of the roster and is flagged: a **false positive** on ground the debt covers | **MP-A8** |

**Two extra bounds, from the adversary's §9 S4 and §6** (per *when you cannot close a hole, pin
it*): `conftest-collection-hooks` (LEG B models the manifest, not `collect_ignore*` in a
conftest) and `untracked-ground` (pinned as behaviour since r1, never *stated*, so no reader of
the guard met it). Both mutation-proven — **MP-A12**.

---

## 3. Mutation proofs — 11 runs, all observed columns filled

Declared from `--collect-only` before each run; `--deselect …TestThisInstrumentRidesTheTypeGate
Itself` (the two expected-REDs), stated rather than buried.

| # | mutation | declared | observed | verdict |
|---|---|---|---|---|
| MP-A1 | `classify`'s prologue swallows `GuardIsBlind` | 7 | `7 failed, 185 passed, 5 deselected` | **HELD** (after PROOF FAILED — §3.1) |
| MP-A2 | `_roster` swallows its own raise | 1 | `192 passed` — **no red** | **NOT A HOLE**, §3.2 |
| MP-A3 | AWB01 faithfully: unreachable sha falls back to the tree root | 5 | `5 failed, 187 passed, 5 deselected` | HELD |
| MP-A4 | receipts site `startswith`, EXECUTION axis only | 1 | `1 failed, 191 passed, 5 deselected` | HELD |
| MP-A5 | roster honoured on TYPES only, tree-root on EXECUTION | 1 | `1 failed, 191 passed, 5 deselected` | HELD |
| MP-A6 | `member_mypypath` fabricates the map | 1 | `1 failed, 193 passed, 3 deselected` | **HELD** (after PROOF FAILED — §3.1) |
| MP-A7 | roster `.py` by substring | 1 | `1 failed, 191 passed, 5 deselected` | HELD |
| MP-A8 | roster read line-wise (argv **and** parser, via anchor files) | 1 | `1 failed, 193 passed, 3 deselected` | **HELD** (after PROOF FAILED — §3.3) |
| MP-A9 | `frozen_sha` validation relaxed to `[0-9a-fA-F]{1,40}` | 2 | `2 failed, 190 passed, 5 deselected` | HELD |
| MP-A10 | pytest allowlist reverted to a denylist | 1 | `1 failed, 193 passed, 3 deselected` | HELD |
| MP-A11 | `addopts` tokens no longer inspected | 3 | `3 failed, 191 passed, 3 deselected` | HELD |
| MP-A12 | a required stated bound renamed away | 1 | `1 failed, 193 passed, 3 deselected` | HELD |

**Count, derived from the table (12 rows): 12 runs — 11 proofs held, 1 (MP-A2) adjudicated as
not-a-hole.** Cumulative across all waves the table rows are the only count; I am not restating
a running total, because every running total in this packet's history has drifted.

### 3.1 The real defect: I repeated MP-N1's mistake exactly

**MP-A6 came back `PROOF FAILED`, declared red stayed GREEN** — because I put both P-4 pins
inside `TestThisInstrumentRidesTheTypeGateItself`, the class every proof run deselects. That is
**the identical error the both-ways diff caught last wave**, in the same session, by the same
author, one wave after I wrote up why it mattered. Filing a rule does not install it; the
*checked expectation* is what worked, both times. Fixed by relocating both pins to
`TestConfigReadersComeFromTheRealFiles`, where reader-correctness pins belong; re-proved.

**Generalisable, and I would rather it be a guard than a memory:** *a pin that is green today
does not belong in a class that is red today.* If a future wave wants it mechanised, the shape
is an AST check that every test in the expected-RED class is expected-RED — I did not build it
because inventing a second instrument mid-fix-wave is how scope escapes.

### 3.2 MP-A2 is not a hole, and I say so rather than let a row look strong

Swallowing `frozen_roster`'s raise inside `_roster` reddens **nothing** — because P-1's prologue
already refuses the same input earlier. The property holds through a different door, which is
what defence in depth means; reporting it as a survivor would be my instrument lying the way the
adversary's could. MP-A3 is the faithful AWB01 and it discriminates cleanly.

### 3.3 MP-A8 needed a two-part mutation, and the one-part version was worthless

Dropping `-z` from argv alone made the NUL parser return one giant string, so the roster went
empty **everywhere** — 51 reds, a mutation that proves nothing about the pin. The faithful build
changes argv **and** parser together; `mutation_proof.py` takes one anchor, so I spanned both
with `--anchor-file`/`--replacement-file`. **A mutation that breaks everything is not a stronger
proof than one that breaks the right thing — it is a weaker one.**

---

## 4. SURFACED TO LEAD

### 4.1 P-7's shape rule DOES constrain the eventual `FROZEN_SHA` anchor — you asked to be told

`FROZEN_SHA` left at `f033a87`, seam untouched. But P-7 pins `re.fullmatch(r"[0-9a-f]{7,40}")`
on `frozen_sha`, so **any anchor that is not a lowercase hex object name is rejected by the
row's own validation**: an annotated tag (`pkt44-freeze`), a `refs/` name, `master~3`, or an
uppercase sha would all raise `InvalidExemption`. If the sidecar's answer to S1 is *"anchor it to
a tag or a ref so it survives the squash-merge"*, **P-7 must widen in the same commit** — and
widening it re-admits `"HEAD"`, which is currently rejected as a moving reference and should
stay rejected. **The narrow fix if that is the ruling: accept `[0-9a-f]{7,40}` OR a
`refs/tags/…` name, and keep rejecting bare `HEAD`/branch names.** I have not built it; it is
your seam.

### 4.2 Convergence or design change? — my honest read, since you asked plainly

**I think you are right that this is convergence, and here is the evidence rather than the
opinion.** The three passes found *different classes*: (1) a helper pinned at one call site of
four; (2) an exemption over an open set; (3) a property pinned at the reader rather than the
entry point. Each prior pass's survivors are independently confirmed closed. **Nothing has
recurred.**

**But I will name the one thing that does look like a design smell, so you have it:** all three
passes found the same *meta*-shape — **a property asserted at one member of a set that the
property is claimed over** (one call site of four; one axis of two; one entry point of two; one
mypy config but not pytest's). That is not a defect in this contract's subject matter; it is a
defect in how I have been *quantifying*, and it is exactly what a contract author is for. If a
third pass finds a fourth instance of the same meta-shape, **that is the signal to escalate the
design**, because it would mean the contract cannot be written by enumerating properties — and
the answer would be an instrument that derives the quantification (every public function × every
blind input; every membership site × every axis) rather than a person remembering to.

**What I do NOT think is that the contract is compensating for a design that should change.**
The one place that was true — the tree-root exemption — the sidecar already changed, and the
frozen roster is strictly better. The `FROZEN_SHA` branch-object problem (§S1) is the live
design question, and it is yours, not the contract's.

### 4.3 Untouched, as instructed

`scripts/test_forgery_door_sweep.py`: `grep -c forgery_door_sweep` on my contract → **0**.
`scripts/typecheck.sh`: not edited. `FROZEN_SHA`: unchanged.

---

## 5. Deviations

### 5.1 I lost the roster-era reference build

`/tmp/gatedground-reference-build.py` held the **pre-roster** copy: after the roster wave I
deleted the throwaway from the tree without re-saving it to scratch. Discovered when this wave's
first run produced `TypeError: Exemption.__init__() got an unexpected keyword argument
'frozen_sha'` across 93 tests. I reconstructed the roster layer from my own r2 §0 description
and re-verified (195 green), and I now re-save after every change.

**This is brief-base §1's perversity operating on me exactly as written** — *the better your
instrument, the more likely it dies unremarked*: the roster build worked first time, so I had
nothing to debug, so I never looked at it again. The reference build is pasted in r2 §9 in its
pre-roster form; **it should be read as superseded**, and the authoritative description of the
roster layer is r2 §0 plus §2 of this report.

### 5.2 A fixture defect my own new pin exposed

`pytest_ini_extra={"asyncio_mode": …}` collided with the base template's own `asyncio_mode`,
producing a duplicate TOML key — so the false-gate control failed for a *fixture* reason, which
is indistinguishable from a pin doing its job. Fixed by letting an override replace the base key
rather than duplicate it.

---

## 6. Package survey — the missing row

| mechanism | evaluated | what I READ | verdict |
|---|---|---|---|
| **frozen-roster derivation (the seam the ruling introduced)** | `git ls-tree -r -z --name-only <sha> -- <root>` | Measured in a real repository, the same way I measured `git ls-files`: with a path containing a newline, the line-oriented form emits a **quoted, backslash-escaped** name and `-z` emits the raw bytes — so a line-split roster silently loses a grandfathered file and flags it. `--name-only` because the roster needs paths, not modes/objects | **replace** a line-oriented read. ⚠ **This row was MISSING from r2 §6** — I added a mechanism and did not survey it, which is precisely the "one level down" position the protocol warns about, and it is where P-5 and P-8 both lived |

Everything else in r2 §6 stands unchanged.

---

## 7. Bounds

1. **The file is frozen** at md5 `9fe25b1d42a8e8b101325b6f8c8f253a`.
2. **I did not re-run the adversary's 44-build matrix.** My evidence that its survivors die is
   the 11 mutation proofs above, each reproducing a named survivor's shape.
3. `unmodelled_pytest_configuration(REPO_ROOT)` → `[]` on this checkout, measured: the new
   refusal does not fire on the real manifest, so it is not a gate that gets switched off.
4. Every number here has a command beside it; §3's count is that table's row count.

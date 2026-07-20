# REPORT-esc1-bound-pin — ESC-1 bound pinned, ESC-3 citation repointed

brief-base v5 read

## SUMMARY BLOCK

- **state:** done
- **Item 1 (ESC-1, pin the `use()`-leg bound):** DONE. New pin
  `test_the_use_leg_MISSES_a_DDL_LESS_bootstrap_on_an_oddly_named_handle`, with rationale,
  the KNOWN-BOUND message, the named re-open trigger, and a durable address (#150 +
  `2105c7e`). Mutation-proven RED, restored byte-exact, re-green.
- **Item 2 (ESC-3 + the `:108` addition):** DONE. `:27` `until audit-150` → `until fff1382`;
  `:108` now names `(#151)`. The other four provenance citations left alone, per your ruling.
- **deviations:** one, minor and disclosed: I also updated the `_executed_bootstrap_sites_in`
  docstring's `use()`-leg paragraph to point at the new EXECUTABLE pin instead of only at a
  docstring (§3). Same file, same concern, same commit.
- **decisions-needed:** none. One low-priority observation carried forward, not acted on (§8).
- **gates:** 468 passed (baseline 467 + 1) · 200 passed live-store · mypy 55/5 files, exit 1
  (floor, unchanged; **zero** in my two files) · ruff exit 0
- **production drift:** ZERO — `git diff --stat -- loremaster/loremaster/` empty (§7)
- **commits:** `a653705` (the pin) · `9e226e5` (the citations)
- receipts: pin text §2 · assertion-vs-message §4 · mutation proof §5 · gates §6 · drift §7

---

## 1. Position on the ruling (asked for, so stated)

I agree with it, and I did not comply badly. The DDL leg can afford blindness because
`DEFINE NAMESPACE` is the engine's own vocabulary and means exactly one thing; `use` is an
English verb and means whatever the author meant. Denying receiver-blind on it buys a hole
that is already covered in practice and pays for it in exactly the false positives that get
an instrument switched off. Pinning is the right disposition, and the previous wave's
refusal to ship on "zero sites today" was correct reasoning, not timidity.

## 2. The pin

`loremaster/tests/test_retry_seam.py:5169` (in `TestTheTestTreeRoutesThroughTheOneBootstrapToo`,
immediately after the `use()`-leg predicate pin it qualifies).

**Docstring carries four things**, per the brief:

1. **The bound, stated flatly** — a bootstrap that runs ONLY `use()`, on a handle the
   receiver predicate does not recognise, with NO DDL, is not seen.
2. **The rationale** — `use` is a generic English verb; a receiver-blind deny fires on
   `monkeypatch.use()`, `fixture.use()`, any unrelated helper. That is the false-positive
   class that gets an instrument switched off, "and then the next #150 ships with nothing
   watching at all". It explicitly records that blinding it measured zero sites *at the time*
   and that this was **declined as grounds to ship** — "zero-today on a token that generic is
   luck, not a property" — so a future reader cannot re-derive the zero and conclude the
   previous wave simply missed it.
3. **Why the exposure is narrow** — a hand-rolled bootstrap does not select a session it
   never defined; it runs the DDL too, and the receiver-blind DDL leg sees that regardless of
   naming. Control 1 in the pin body proves that on the very same handle.
4. **RE-OPEN TRIGGER, named** — *"the day a reconnect path selects a session without
   re-running the DDL"*, i.e. a resume/reconnect calling `use()` on an already-defined
   namespace. Stated with its consequence: that is when DDL-less selects stop being
   hypothetical and the narrowness argument in (3) stops holding.

**Durable address:** #150 (this is its residual) and commit `2105c7e`. The docstring states
in-line *why* it cites those and not the wave's reports — untracked scratch files at the repo
root that repo law requires be deleted before any image build. Verified both SHAs resolve:
`2105c7e` = the receiver-blind wave, `fff1382` = the count correction.

**Failure message** carries the repo's phrasing verbatim in bold: *"This is a KNOWN BOUND
(#150, commit 2105c7e) — if you closed it deliberately, delete this pin and say so in the
same diff."* It then splits the two ways a reader arrives at it: a deliberate close (→ check
`monkeypatch.use()` and every unrelated `.use()` still pass, or you built the gate that gets
switched off) versus the re-open trigger firing (→ the trade genuinely needs re-deciding).

## 3. DEVIATION — one docstring pointer, disclosed

`_executed_bootstrap_sites_in`'s `use()`-leg paragraph said the bound was *"disclosed in that
predicate's docstring"*. After this wave that is understated: it is now **asserted**. I
changed the sentence to point at the executable pin and to say it goes RED the day someone
closes it.

Reason it is not scope creep: repo law is "when a defect class is identified, ship the
INSTRUMENT in the same breath as the law — a rule people must remember is not a guard, it is
a hope". Leaving prose that routes a reader to a docstring when an executable pin now exists
reproduces exactly the diagnosis-without-instrument failure. Same file, same concern, same
commit. Reversible in one hunk if you disagree.

## 4. Assertion-vs-message interrogation (the false-gate class, not reintroduced)

Three assertions, each read against its own message. **What wrong build would this pin still
pass?** — a scan that returns `[]` for everything. That is precisely why the two controls
exist; without them the bound assertion is indistinguishable from a dead scanner.

| # | assertion | message claims | gap? |
|---|---|---|---|
| Control 1 | `_executed_bootstrap_sites_in('await db.query(f"DEFINE NAMESPACE …")')` is **non-empty** | the receiver-blind DDL leg still sees this handle; until it does, the bound assertion proves nothing "because a dead scan misses everything" | none — it asserts exactly liveness on this handle, and claims exactly that |
| Control 2 | `…('await connection.use(ns, database)')` is **non-empty** | the `use()` leg is live on a name the predicate DOES recognise; without it the bound is vacuous | none — asserts leg liveness, claims leg liveness. Does **not** claim the leg is correct in general (that is the neighbouring pin's job) |
| The bound | `…('await db.use(ns, database)')` is **empty** | the leg now sees an unrecognised receiver → KNOWN BOUND closed | none — the message describes the exact observation the assertion makes, and prescribes action for both arrival routes |

No assertion's message promises a check the assertion does not perform. In particular the
bound assertion does **not** claim "the gate is complete" or "no bootstrap escapes" — the
opposite; it claims a specific miss, which is what it tests.

**Honest redundancy note, raised rather than buried:** under the mutation, my pin and the
neighbouring `test_the_use_leg_still_reads_the_shared_receiver_predicate` both go RED (§5) —
its `monkeypatch.use()` negative control covers overlapping ground. They are not duplicates:
that pin asserts the leg is *receiver-keyed*; mine asserts the *consequence* — the specific
population that escapes — and carries the trade, the trigger and the instruction. A reader
who trips the negative control learns "don't widen this"; a reader who trips mine learns why,
what it costs, and when the answer changes. But the overlap is real and I would rather report
it than have you find it.

## 5. Mutation proof — wrong build → observed RED → restore → GREEN

Applied to the **real tree** (committed and clean), with a `cp -a` **content** backup and an
`md5sum -c` restore proof. **No scratch repo copy was made** — repo law #140 (a naive `cp -a`
copy silently runs the ORIGINAL checkout's code via the venv's absolute editable `.pth` and
preserved-mtime `__pycache__`). Nothing here ran outside the real checkout.

**Positive control — the pin GREEN on the shipped build (before mutating):**
```
uv run pytest tests/test_retry_seam.py -q -k "MISSES_a_DDL_LESS"
  -> 1 passed, 424 deselected in 0.89s
```

**The mutation** — the `use()` leg made receiver-blind, one line in
`_executed_bootstrap_sites_in`, i.e. the exact "helpful" close this pin exists to stop:
```python
-        if node.func.attr == _SESSION_SELECT_METHOD and _is_connection_receiver(node.func.value):
+        if node.func.attr == _SESSION_SELECT_METHOD:  # MUTATION: use() leg gone receiver-blind
```

**Observed RED, and on the right assertion** (the two controls passed — so the pin
discriminates rather than failing wholesale):
```
E  AssertionError: the use() leg now SEES `db.use(...)` on a receiver the predicate does not
   recognise. **This is a KNOWN BOUND (#150, commit 2105c7e) — if you closed it deliberately,
   delete this pin and say so in the same diff.** …
E  assert not [(1, 'connection.use()')]
E   +  where [(1, 'connection.use()')] = _executed_bootstrap_sites_in('await db.use(ns, database)\n')
tests/test_retry_seam.py:5226: AssertionError
1 failed, 424 deselected in 1.10s
```

**Whole file under the mutation** (which pins fire, for the record):
```
FAILED …::test_the_use_leg_still_reads_the_shared_receiver_predicate
FAILED …::test_the_use_leg_MISSES_a_DDL_LESS_bootstrap_on_an_oddly_named_handle
FAILED …::test_the_two_scans_SHARE_their_predicates_rather_than_cloning_them
3 failed, 422 passed, 1 warning in 13.58s
```

**Restore, proven byte-exact, then re-green:**
```
cp -a /tmp/esc1/BACKUP_test_retry_seam.py tests/test_retry_seam.py
md5sum -c /tmp/esc1/pre.md5     -> tests/test_retry_seam.py: OK
grep -c "MUTATION: use() leg"   -> 0   (exit 1: absent)
uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -n auto
                                -> 468 passed, 1 warning in 8.01s
```

## 6. Gates — every command, its passed-COUNT tail, its captured exit code

Typecheck run **from the repo root** with output captured to a variable and `$?` checked
before counting — the trap you named (invoked from the wrong cwd it does not launch, and a
`grep -c` over empty output returns `0`, which reads GREENER than the truth).

```
cd loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -n auto
  -> 468 passed, 1 warning in 7.97s        (baseline 467; +1 = the new pin, fully accounted)

cd /home/ejprice/PycharmProjects/lore && out=$(./scripts/typecheck.sh 2>&1); rc=$?
  EXIT=1                                   <-- the pre-existing floor, not a new failure
  -> Found 55 errors in 5 files (checked 146 source files)
  -> typecheck: loremaster FAILED / typecheck: one or more members failed
  grep -c "test_retry_seam\|_surreal_harness" over the CAPTURED output -> 0
     (and the capture is non-empty — the 55-error tail above is from that same variable,
      so this zero is a real absence, not the empty-output trap)

cd /home/ejprice/PycharmProjects/lore && uv run ruff check .
  EXIT=0
  -> All checks passed!

cd loremaster && uv run pytest tests/test_surreal_store.py tests/test_txn_contention.py -q -n auto
  -> 200 passed in 12.70s                  (live store, spike-surreal :18000 — :18500 never touched)
```

Every count above is read from a tail I inspected for a passed-COUNT; no "no tests ran"
behind a pipe.

## 7. Zero production drift

```
git diff --stat -- loremaster/loremaster/
  -> (empty)

git diff --stat                       (before commit)
  loremaster/tests/_surreal_harness.py |  6 +--
  loremaster/tests/test_retry_seam.py  | 73 +++++++++++++++++++++++++++++++++++-
  2 files changed, 74 insertions(+), 5 deletions(-)
```

Both files are inside the granted writable set. `_txn.py` untouched (#151 stays open per
operator ruling); `docs/` and `scripts/` untouched. The scratch backup lives in `/tmp/esc1/`,
outside the repo; no scratch file was created inside `loremaster/tests/`.

## 8. The two citation edits

| file:line | before | after |
|---|---|---|
| `_surreal_harness.py:27` | `…conflated them until audit-150 R2.` | `…conflated them until fff1382.` — verified: `fff1382 docs(test): #150 correct the retired 7e block's false count`. Re-wrapped the paragraph to stay under the 110-col limit; that is the only other change in the hunk. |
| `_surreal_harness.py:108` | `…holds nothing (blindreader-150 F1).` | `…holds nothing (#151, blindreader-150 F1).` |

`:344`, `:419`, `:454-455` **not touched**, per your ratification of the previous wave's
verdict: substance stated inline, following the citation adds nothing, and mechanical
rewrites cost a reviewer a diff for no gain.

**Carried forward, not acted on (previous wave's ESC-4, still open):** ~30 `blindreader F1/F2/F3`
citations across **production** files from the earlier #102/#108 wave — same non-durable-address
pattern, all with substance inline. Outside my writable set and outside this brief. I rate it
LOW and not urgent; noting it only so it does not disappear when these reports are deleted
before the next image build.

## 9. Tool honesty

The two edits and the pin placement were located with `grep` and `Read`, not lore. Declared
per protocol: both are non-symbol textual-seam work — prose inside docstrings and comments —
which is case (b) of the three grep-honest cases in `CLAUDE.md`. lore's symbol graph cannot
answer "where does this comment cite a scratch report". No lore weakness to file.

**There are 0 failing tests unrelated to our present scope.**

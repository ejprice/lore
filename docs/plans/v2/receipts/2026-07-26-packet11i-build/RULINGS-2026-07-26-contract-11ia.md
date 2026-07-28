# Packet 11-i-a — the contract's six escalations, RULED

**Ruled by `lead-11ia`, 2026-07-26**, on `REPORT-contract-11ia-1.md` §5 (this directory).
Contract committed BEFORE these rulings at `d6c0dd4`, so the graded artifact is fixed.

Three are ratifications of a recommendation the contract author derived and evidenced. Three are
lead calls, marked, and cheap to veto — say the number.

---

## E1 — `head_identity` pre-image encoding: **RATIFIED, reading (A)**

Flatten each `(axis_name, value)` pair and join **every element** with `\x00`; `sha512_hex` over
that. The golden digest `c52fce03…daf148cf` for `{"scope": "pooled", "statistic": "cosine_floor"}`
is pinned, with the three-line reference function written into the test.

**Why a golden vector here and a PROPERTY for the corpus digest (§4g) — the asymmetry is the
point:** a re-encoded *corpus* digest costs one extra measurement; a re-encoded *head id* is a
**record-identity migration**. F6 names this the one non-`OVERWRITE`-able freeze in 11-i-a, so it
settles before the table ships, not after.

**Also ratified: an axis value containing `\x00` is REFUSED, not escaped.** Refusal is checkable in
one assertion; an escape is one more encoding nobody pins — and §4g just showed what an unpinned
encoding costs.

## E2 — the lost-fence mechanism: **RATIFIED — classify from store STATE, never from message text**

On a rollback, re-read the lease row and raise `FenceLostError from error` **iff** `(holder,
fence_epoch)` no longer match; otherwise re-raise untouched.

**This is not a preference — the alternatives are barred by standing law.** Repo law and F8-C6
forbid matching engine message text, and this repo has the receipts: **#118**
(`_ERROR_CLASS_ASSERT_VIOLATION` has NEVER fired in production because the classifier greps for the
word "assert" while SurrealDB 3.1.5 says *"must conform to"*) and **#111** (retryable-conflict
detection can only be done by substring-matching English on this SDK). A state re-read is a
**semantic** classification: it survives any rewording the engine ships.

⚠ **Rider, and it is the half that gets dropped: pin the re-read's OWN failure.** If the
confirming read itself fails, the code must re-raise the original error untouched — it must never
report `FenceLostError` on the strength of a read it could not complete, and never swallow the
original. A classifier whose evidence-gathering step can fail silently is the same defect one level
up. Pin all three fates: fence moved · fence intact · re-read failed.

## E3 — library entry point: **RATIFIED — drive `try_acquire_or_renew()`, and pin the surface**

`LeaderElection.run()` blocks forever (`acquire()` loops on `time.sleep(retry_period)` with no stop
mechanism). R2.2's ruled ACQUIRE is *"empty result = lost race … **Never retried, never blocked
on**"*. These are incompatible, so the choice is **forced by the ruling**, not selected: a contract
calling `run()` could never assert a FOLLOWER's outcome.

The contract author is right that this **borders on #209's private-internals class** — the method
is public but is not the documented entry point. That is a real bound, so it gets the treatment
this repo gives real bounds rather than a shrug: **name it in the interface freeze, and pin the
library surface it depends on** (that `try_acquire_or_renew` exists, its arity, and that the
algorithm's own tick calls it), so a library upgrade that reshapes it goes RED here instead of
silently at runtime. **Named re-open trigger:** the day `kubernetes` ships a non-blocking public
entry point, drive that instead and delete the pin.

## E4 — the 30–49 ladder function: **11-i-b. [LEAD CALL]**

Store-side stays in 11-i-a and is already pinned: the `insufficient_corpus` predicate, the 30/15/30
constants, and `adopted_n` recording the ACTUAL adopted subsample size rather than a nominal rung.
The **ladder-generating function** (`[50,100,200,400,…]` truncated at pool size, final rung equal to
pool size) is runner arithmetic and goes to 11-i-b.

**Derivation:** the §A ruling split this packet **at the store/runner seam**. A rung generator
consumes no store and mints no row; putting it in `a` would move the line the operator drew. My
brief's "Row/state shapes" bullet was the source of the ambiguity — it should have said *state
domains and row shapes*, which is what its own text meant.

## E5 — §7's `note` vs F5's `non_adoption_cause`: **TWO DISTINCT FIELDS. [LEAD CALL]**

`note` is free text and follows §7's rule (mandatory unless `measured`). `non_adoption_cause` is the
F5 typed enum and appears **only** on `measured_not_adopted`.

**Derivation, from the enum's own semantics:** the domain is `FLOOR_NON_ADOPTION_CAUSES` — five
reasons *adoption did not happen*. A `measuring` row has not finished, so it has **no** non-adoption
cause; conflating the fields would force a bogus enum value onto every in-progress state, and
decision 4 adopted the two-degeneracy split precisely so that *an instrument artifact is never
projected into that sentence*. Fabricating a cause for a row that has not concluded is that same
projection wearing a different hat.

**So the five further pins E5 says are owed ARE owed** — for `note`, not for the cause enum. Add
them.

⚠ **Carried obligation for 11-ii, recorded here so it is not lost when this packet closes:** `note`
is **stored free text**. The day anything RENDERS it, it routes through the shared sanitiser seam
and its tests carry a hostile fixture (newlines + a row-shaped forgery line + backtick runs) —
standing repo law. Nothing renders it in 11-i (`DEPLOY: no`), which is exactly why this is easy to
forget.

## E6 — `CALIBRATION_POOL_COLUMNS`: **RATIFIED as declared**

A named constant, with the returned row keys pinned equal to it exactly, `embedding` pinned absent,
and the digest inputs pinned present. Membership beyond `point_id` + `content_hash` is **11-i-b's**
to fix, because the probe-derivation columns are its requirement.

**Both attached hazards are inherited by 11-i-b and must appear in its brief:**
1. Adding an `option<>` column under an **explicit projection** reads a missing column as `None`
   **silently**, where `SELECT *` omits it and raises `KeyError` (store reference §2's asymmetry).
2. Under an explicit projection, `ORDER BY id` requires `id` **in** the projection or the statement
   is a **parse error** (store reference §7's 2026-07-25 probe).

---

## The three design defects the contract caught — carried forward, because they are not 11-i-a's alone

Recorded here so 11-i-b and 11-ii inherit them as facts rather than rediscovering them:

1. **The lock's absent-`get` return is `LockAbsent`, never `(False, None)` and never
   `ApiException`.** The ruled design's literal sentence produces a lock that can never be created
   on a virgin store. Two differently-broken controls, because one would have licensed the wrong
   fix.
2. **The lock adapter must NOT decorate the returned `LeaderElectionRecord`.** The algorithm resets
   its observation clock on `old.__dict__ != observed.__dict__`, so any field that moves on an
   unrelated write makes a follower restart its expiry clock every poll — a dead leader's lease then
   never expires and the deployment **wedges permanently**, with every pin green.
3. **All four record fields reach the lock as STRINGS, and the times are naive local
   `datetime.fromtimestamp`.** A `datetime`-typed `renew_time` column would reject every renewal the
   library ever makes.

## Ledger note

**#199 is RESOLVED** (`scripts` is in `testpaths` at HEAD) — closed 2026-07-26 with the two riders
that are NOT closed by it: `scripts/` is still outside `scripts/typecheck.sh` (**#188**), and
`docs/eval/` has no `testpaths` entry at all.

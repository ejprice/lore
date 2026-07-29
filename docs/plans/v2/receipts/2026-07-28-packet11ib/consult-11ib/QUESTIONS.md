# Consult battery — packet 11-i-b, the R2 evidence package

You are an informant in a consumer consult.

**Parts 0 and 5 are answered BEFORE you open the package. Do not open it until Part 0 is
written.** Your administrator will give you the package path when Part 0 is in.

---

## Part 0 — PRE-REGISTRATION (answer before opening anything)

You are about to read an evidence package produced by a floor-calibration run. You will then be
asked to build 11-ii's input contract against it.

**0.1 — the re-run trigger.** Name, now, the one thing whose absence from that package would make
you demand a re-run rather than build against it. One sentence. This is recorded before you see
the package and it is not revisable afterwards.

**0.2 — what you expect to need.** List the data you expect to need from the package in order to
build a scheduler's input contract. Five to ten items. Be specific enough that you could later
tell whether each one was present.

---

*(stop — hand Part 0 to your administrator and receive the package path)*

> **Your package:** `⟨PACKAGE_PATH⟩`

## Before you read on

1. **Read only that package.** Do not open any other file in the repository: no packet files, no
   design reports, no scout reports, no contracts, no other consult material. If you find
   yourself wanting one, that is itself an answer to Part 3 — write it there instead of reading
   it.
2. **Answer Parts 1 → 4 in that order, and do not read ahead.**
3. **The package is a SYNTHETIC EXHIBIT.** Every value in it is a sentinel: deliberately
   implausible in magnitude, and not a measurement of anything. Treat its SHAPE as real (field
   names, artifact structure, which statement sits where) and its NUMBERS as placeholders. Never
   quote a value from it anywhere outside this consult.
4. **Answer from the package.** Where the package does not support an answer, say that, and say
   how you know. Refusing is a valid answer and is sometimes the correct one.
5. Quote the exhibit line you used, by its text, wherever a question asks you to cite.

---

## Part 1 — retrieval

1. Did the portable instrument pass its pre-registered acceptance? Name the two acceptance legs
   and their values.

2. Is the legacy↔portable divergence a scalar offset or a distribution-shape difference? Cite
   the exhibit line that told you.

3. Which determinism leg held, and what does that commit 11-ii's exact-skip scheduler to?

4. What was the self-retrieval drop rate, split by cause?

5. What fraction of live production queries would fire the absence verdict under the portable
   floor?

6. By how much did retrieval quality improve when the portable instrument replaced the legacy
   one? Give the figure and cite the line that supports it.

7. Was the portable floor's acceptance evaluated on data that was held out from the floor's
   selection? Cite the line.

8. Open `per-query-rows.jsonl`. Take the first row whose `absence_verdict_fired` is `true`. What
   is its rank-1 hit's cosine, how many of its captured hits are marked `shown`, and are both of
   those consistent with the floor and the shown-slice statements in the other artifacts?

9. Two artifacts report the below-floor slice per group and the acceptance rate over the human
   groups. Do they reconcile with each other, with the survivor count, and with the adopted row?
   Show the arithmetic.

---

## Part 2 — behaviour

Answer these about what you actually did, not about what a good reader would do. Separate what
you OBSERVED this run from what you BELIEVE about yourself, and label which is which.

- Which artifacts did you open?
- What did you read fully, and what did you skim?
- What was the single most useful line in the package?
- What would you DELETE from the summary?

---

## Part 3 — the audit question

Go back to your Part 0.2 list. For each item: was it present, and where?

Then: name any datum you needed that the package does not carry — **including anything not on
your Part 0.2 list that you only discovered you needed once you were reading.**

---

## Part 4 — the contract task

*Answer this only after Parts 1–3 are written.*

**Assume every number in the package is a real measurement.** You are 11-ii's contract author.

Write the input contract 11-ii needs from this package. For each of the **three** data your
scheduler must consume, give:

- **(a)** the datum,
- **(b)** its exact address in the package,
- **(c)** the bound that limits how you may use it.

**Any slot you cannot fill from the package is a ROUTE_AROUND reason — list every unfillable
slot before you state a verdict.**

Then state your verdict: **CALL_AGAIN** (consume this package as your evidence base) or
**ROUTE_AROUND** (re-derive, or demand a re-run). Say why, and say whether the trigger you
pre-registered in Part 0.1 was hit.

---

## Part 5 — legibility (COLD-READER informant only)

*Asked only of the informant briefed with no 11-i-b context. If you were given packet background,
skip this part.*

List every term, reference or abbreviation in this package that you cannot resolve from the
package itself. For each, say what you assumed it meant, if anything.

# 10-d — Weak-match confidence surfaces: DISARM NOW (#176, #179, #180)
size ~0.05 wu · wave L · depends: **none** (independent of 11-i; ships FIRST in wall-clock)
· **DEPLOY: yes (both containers)**
law: DESIGN-LAW §1 (client design law), §3 (weak-match) · CLAUDE.md → THE CONSUMER LAW +
THE TRUST DOCTRINE
ruling: `docs/design/2026-07-24-floor-calibration.md` **Addendum E1** — issued by the packet
10 design sidecar under authority the operator delegated to it 2026-07-24 ("put that
response to the design agent and follow its ruling").

## Mission
Turn the weak-match confidence surfaces DARK on every instance, immediately, using the
lever the code already designed for it. This is a REVERSIBLE, ~3-line serving change — not
a redesign. Packets 11-i / 11-ii then ARM the surfaces from each instance's own
measurement.

## Why now — the trust argument (this is the whole justification; read it before touching code)
lore is serving a confident-wrong per-hit judgement **today**, three source-verified ways:
- **#176** — the per-hit flag consults no drift state, so it compares live cosines against a
  floor measured in a **retired embedding space** (the schema fingerprint moved).
- **#179** — the floor is a constant measured on lore's own corpus, shipped in the image and
  served on **every foreign instance** with no validity claim there.
- **#180** — it is calibrated on **best-of-response** cosines (`max_cosine_of_response`) and
  applied to **every individual hit**, so mid-list hits are judged against a population they
  cannot belong to.

DESIGN-LAW §1.3 prices this: *"Under-claiming is nearly free; ONE confident-wrong costs
authority for the session (authority→witness, ~doubles calls)."* The disarm costs one beat
of scrutiny on hits whose raw magnitude the substrate line still shows. The aggregate
verdict is already dark on the only instance it was ever calibrated for, so its marginal
loss is nil.

⚠ **The edge nobody had named, and the reason this could not wait for 11-ii:** a foreign
corpus whose file count sits **within ±10% of 214** trips NEITHER drift leg — the shipped
fingerprint matches (same image) and the count bar is not crossed — so it serves lore's
floor **with full confidence** right now, indefinitely. Weeks of that against a ~0.05 wu
reversible change is not a close call.

## Scope IN
- **`_COSINE_WEAK_MATCH_FLOOR: float | None = None`** — the DESIGNED rollback lever; the
  constant's own docstring already names `None` "the disabled/rollback state, not a
  pre-measurement default". Setting it darkens BOTH the per-hit weak flag and the aggregate
  absence verdict on every instance, through gates that already exist.
- **The `_COSINE_WEAK_MATCH_FLOOR_STAMP` constant STAYS**, with its comment block, as the
  historical record of the 0.50649 measurement. Do not delete it — 11-i needs the
  provenance and the retirement is 11-ii's.
- **The per-hit cosine SUBSTRATE line stays ON** (`sim 0.62`). It is claim-free and
  D1-gated: a raw magnitude with no judgement attached is not a confident-wrong. Removing it
  would be under-claiming past the point of usefulness.
- **The `disabled` state's note stops being `null`** — this is the #4 lesson (a
  disabled-by-config state and a disarmed-pending-calibration state are different
  conditions and must not share a rendering). The drift check's disabled branch serves a
  constant string in the shape:
  *"weak-match confidence surfaces disarmed pending per-instance calibration (findings
  #83/#176/#179/#180; packets 11-i/11-ii) — per-hit similarity substrate remains served."*
  Failure admitted loudly with the next move named — §C5 family (a) by construction.

## Scope OUT (surface to operator if encountered)
- **Any wording change to the weak-match or verdict TEMPLATES.** They go dark UNCHANGED.
  Wording is ruled law and the F3 client consult owns any future change — no wording-law
  question arises from this packet precisely because nothing is reworded.
- Any calibration, measurement, store or schema work — that is 11-i.
- Retiring the stamp constants — that is 11-ii.

## Entry check
- Addendum E1 read at source (do not work from a summary of it).
- suite green at HEAD; **spike-surreal `:18000` is the TEST store — never `:18500`** (#177).

## Exit
TDD per repo law. **Test sweep per the rename-sweep law — this is the step most likely to
be under-done:**
- grep the test tree for pins that CERTIFY THE OLD SERVING (a green suite can be green
  because it still asserts the corpse). Pins that monkeypatch their own floor stay valid;
  pins that rely on the module constant being a float do not.
- Add the disarm pin: floor `None` ⇒ no per-hit flag line, no aggregate verdict, **substrate
  still renders**, and the disarm note serves. Mutation-prove it (restore the float, watch
  it go RED).
- `smoke_p8b` is render-shape-coupled — update in step.

Cold audit before the wave commit (builder ≠ grader). **DEPLOY BOTH containers.**
⚠ **Deploy landmines, both live:** rebuild + recreate, NEVER restart (the container bakes
the code); capture `podman inspect <name> --format '{{.Config.CreateCommand}}'` BEFORE `rm`.
**AND: `lore-lore` runs a hand-rolled `/source` mount and is NOT restart-durable — do NOT
`lore-deploy start` it until #165/#166 land** (a normal start re-mounts `/source` and
re-breaks boot; recreate manually). Confirm the landmine still applies before deploying —
if #165/#166 landed meanwhile, say so.

Smoke: a search on the deployed instance renders the substrate and **no** weak-match claim;
`lore_index` renders the disabled state WITH its note, not a null.

Findings #176 / #179 / #180 stay **OPEN** — this packet stops the bleeding, it does not fix
the calibration. They resolve in 11-ii when honest per-instance measurement actually serves.
Record in each row that the surface was disarmed here and by which commit.

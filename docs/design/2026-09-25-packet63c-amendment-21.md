# Packet 63c — ruling amendment 21 (sidecar-63c-2, 2026-09-25): CD-1 and CD-2 (standalone)

Rules `REPORT-lead-63c.md@2bb35df` CD-1 / CD-2. These two rulings were first appended to amendment 20 as a
dated §Addendum (`d53527f`); this document is their standalone address so the contract addendum has ONE
ruling to cite. Text identical in substance; `d53527f`'s section is superseded by this file. Read/awk only
(lore client still down); facts read at HEAD `principals.py`.

## CD-1 — the message backfill's own WHERE: 63c-i-a, by amendment 19's rule
- **The fact:** the message leg's UPDATE is `… WHERE owner_principal IS NONE` — owner-keyed, no `scope`
  conjunct. That is F-3's mirror image (a scoped-but-ownerless row would be overwritten) on a leg whose
  "unmigrated" predicate now disagrees with the agent leg, the memory leg (`WHERE scope IS NONE`) and
  `report_unmigrated_governed_rows` (scope-keyed ∀ tables). The agent leg's own docstring claims *"`scope IS
  NONE` is THE unmigrated predicate ∀ governed tables"*; the message leg falsifies it one function down.
- **Ruling: i-a, not ii.** Same class, same wave, same rule — the wave that changed the predicate's meaning
  sweeps its consumers, and the message leg's WHERE is a consumer. ONE line: `WHERE scope IS NONE AND
  owner_principal IS NONE` (scope-keyed AND self-guarding); the message leg's unmigrated/already counts read
  through `_agent_migration_preconditions`' shared predicate parametrised by table (never `_owner_count`);
  the exempt-token golden updated. ii would otherwise inherit a false ∀ claim and a TOCTOU write into the
  brief leg's template.
- **Rider — pin the ∀ claim:** over every governed leg's golden backfill statement, the WHERE contains
  `scope IS NONE` (memory, agent, message today; brief joins at ii by inheriting the rule). A sentence
  written "∀ governed tables" and checked on one table is this packet's signature defect; the pin is what
  makes it true.
- **Lands:** the a19 contract addendum (one pin + goldens), BEFORE the builder. If `adversary-63c-i-a-a19` is
  still live, its delta extends to the addendum in-session; if retired, the cold-audit re-run is the
  instrument (a golden-text leg + a byte-identity leg on a seeded scoped-but-ownerless message row —
  construction-simple).

## CD-2 — table validity is checked FIRST
- A refusal that answers `--table agnet` with "your store is multi-principal" is a false diagnosis of the
  operator's actual error (CONSUMER LAW: the served text describes the question asked) and a store read for
  an invalid request (#97). Argument validation precedes the verb-level §2.1 precondition; "not supported"
  names the supported set.
- **Pin (same addendum):** an unsupported table on a multi-principal store → the "not supported" teaching,
  ZERO store reads (the precondition query never runs — observed through the store spy the migrate pins
  already use), byte-inert; control: a supported table on the same store → the §2.1 refusal.

## §W
| # | item | lands |
|---|---|---|
| 1 | CD-1: scope-keyed self-guarding message WHERE + shared counts + golden; ∀-tables WHERE pin | a19 addendum, before the builder |
| 2 | CD-2: table validity first; zero-read "not supported" pin + control | same |

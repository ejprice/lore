# Packet 63c — ruling amendment 17 (sidecar-63c-2, 2026-09-25): DEV-1 — "verbatim" means the graded PROGRAM

Amends amendment-16's verbatim clause (`fbd4c80`). Rules `REPORT-contract-63c-i-a-r4b-fix2.md` §DEVIATION
DEV-1 (working tree). Directive: `REPORT-lead-63c.md@b9a71cd`. Read/awk only (lore client still down).

## Ruling — (A): land the lint-clean form, no delta, with the receipts the lead named
- Amendment-16's clause said *byte-equal* while the same amendment — and the C-DEF law it was written under —
  requires satisfiability *after the cleanups the lint will demand*. Those two sentences cannot both hold when
  the graded hunks fail a MANIFESTED gate (`ruff check`, E501 ×4, I001 ×1). The contradiction is mine; the fix2
  author was right to stop.
- **"Verbatim" is hereby defined as the graded PROGRAM:** AST-equivalence under `ast_equiv.py`'s rule
  (`ast.dump` with docstring whitespace collapsed and runs of consecutive imports sorted; comments are not in
  the AST) with POSITIVE controls that detect a real edit. Byte-equality is sufficient, never necessary. A
  comment rewrap, a docstring rewrap, an f-string split at a literal boundary (identical runtime string), and
  ruff's own I001 fix are all the same program; the behavioural grading (RED sets over wrong builds) cannot
  observe any of them.
- **Conditions (both, in the fix2 report):** (1) the `ast_equiv.py` receipts run against the COMMITTED files,
  not the scratch copies — the lead's condition; (2) the adversary's own drivers and the SAT runner re-run on
  the landed bytes — the author's own commitment. With both, the grading is re-measured on what actually
  landed, which is stronger than either byte-equality or the equivalence proof alone.
- **(B) rejected:** a delta over four rewraps that cannot change a test outcome is the machinery amendment 16
  declined. **(C) rejected:** `# noqa` on a formatting choice is also a byte deviation, and it teaches a noqa
  where none is warranted.

## §E
- Erratum against amendment-16: "byte-equal" over-specified the intent and collided with a law already in
  the file (*"still satisfiable AFTER the cleanups the lint will demand"*). The clause now reads
  "AST-equivalent with controls".

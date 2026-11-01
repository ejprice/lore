# RULING: prose-165 follow-up (lead-165, 2026-10-31)

Source: REPORT-prose-165.md §Flags.

## Granted: apply now (the writable set is extended to the two docs named)
- **Flag 1:** `docs/design/2026-07-31-packet39-google-oauth.md` ~330. Append the dated annotation you suggested
  (an annotation, not a rewrite).
- **Flag 2:** `docs/plans/v2/11c-index-boot-reconcile-honesty.md` ~80. Replace the scope-OUT label with your
  suggested text.
- **Flag 6:** `loremaster/loremaster/index/indexer.py` ~395. Name BOTH halves of the #166 bound (the unmounted
  corpora `source:` paths AND the `:ro` snapshot).

Then re-run the same ruff + `test_source.py` gate via haiku-runner, adding `indexer.py` to the ruff list. Append a
§Follow-up section to REPORT-prose-165.md with before/after for each fix and the count line.

## Not granted here (the lead carries these to the operator)
- **Flag 3:** the Odoo fixture `/source/installed.txt` → packet 25 note.
- **Flag 4:** `ReadFileTool` dead-or-dormant → operator question.
- **D2:** the remedy wording; the lead reconciles it against the implementer's refusal text.

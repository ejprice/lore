# RULING: audit-165 routed items A1, A8, T1 (lead-165, 2026-10-31)

Source: REPORT-audit-165.md §Cold findings (verdict GO). These are known defects in granted scope, so they are fixed
in this wave (global rule). A short tdd-light round: contract pins first, then an implementer, then lead
verification.

- **A1 (property: after teardown, every launch failure degrades to a loud `_EXIT_ERROR`, never a raw raise).**
  - On the recreate path, `_launch_container`'s own precondition re-check (or its config read) can raise
    `RuntimeError` after `podman stop` + `rm`. The handler catches only `CalledProcessError`.
  - Required: ANY launch failure after teardown returns `_EXIT_ERROR`, with the error's text on stderr. That covers
    `RuntimeError` from the re-check or the config read, as well as `CalledProcessError`.
  - The ∀ form: pin the property over the failure TYPES `_launch_container` documents (RuntimeError,
    CalledProcessError), not just the newly found one.
- **A8 (property: a paste-ready remedy runs as pasted).** This amends AMENDMENT-contract-r2 item 3, the lead's own
  adoption.
  - The refusal's remedy names the interpreter lore_deploy itself uses for loremaster (`_loremaster_python()`):
    `<that interpreter> -m loremaster.index --config <real config path>`, never bare `python`.
  - The pin derives the expected interpreter from production `_loremaster_python()` and never retypes it. The
    prose docs follow later, in a separate step.
- **T1 (contract smell: a substring check can false-fail).** The "healthy tier dir not named" assertion matches
  whole path components (or exact dir strings), so a tier name that is a prefix of another (`surrealdb` vs
  `surrealdb-docs`) cannot misfire. Add a fixture with such a pair, so the fix is exercised.

Not ruled here: T8 (the existing `test_lore_deploy` stubs dispatch on expression substrings) goes to the operator,
because it reshapes existing test infrastructure.

# RULING: #568 slug forks (lead-165 + operator, 2026-10-31)

Source: `REPORT-contract-568-slug-b.md` §Forks. The class: the slug is derived from the raw directory name at
8 sites in `lore_deploy.py`. Contract: `skills/lore-deploy/scripts/test_scaffold_slug.py`.

- **F1 (lead): python-slugify** (packages over hand-rolling), with `separator="_"` and lowercase.
  - Refuse only when the result is empty or still fails `SLUG_PATTERN`, loudly, naming the directory and the
    remedy (set `project.slug` by hand).
- **F2 (lead): the normaliser lives beside `SLUG_PATTERN` in `loremaster.config`**, as ONE function.
  - `lorerunes` is stdlib-only, so it cannot host a python-slugify dependency.
  - python-slugify is added to loremaster's declared dependencies (pre-approved; reported at close-out).
  - `lore_deploy.py` reaches it through `_loremaster_python()`, as the scaffold already does for validation.
- **F3 (lead): the config wins.**
  - When a `lore.yaml` exists, every verb uses its `project.slug`; the normaliser is used only when there is no
    config.
  - One source of truth; an operator's hand edit is honoured.
- **F4 (operator, "Refuse loudly"): a slug collision across project paths is refused.**
  - When `setup` derives a slug whose manifest or container already belongs to a DIFFERENT project path, it
    exits non-zero, naming both paths and the shared slug, and creates nothing.
  - Rider: pin it (the contract author adds the pins before the builder starts).
- **F5 (lead): refusals return `_EXIT_ERROR` with a stderr line**, never a traceback, matching every other setup
  refusal. Resolving the slug consumers in `main` (e.g. the env-file path) moves after the `project.is_dir()`
  guard, so a refusal is never pre-empted by a crash.

## Addendum: F4b and the class lift (lead, after contract-568-slug-b round 2)
- **F4b → (b):** `setup` records the project path it provisions as a manifest `meta` row (`project_path`).
  - `meta` is already a key/value table, so this is a new row, not a schema change.
  - A collision refusal names the holder's path from the manifest, or from the container when that shows it.
  - A legacy manifest without the row (every manifest today, e.g. `lore`, `demand_intelligence`):
    - when THIS project already has a `lore.yaml` declaring that slug, it is this project's own manifest.
      Setup BACKFILLS the row and proceeds, so re-running setup on an existing deployment is never refused;
    - only a FRESH setup (no `lore.yaml` yet) meeting an ownerless manifest is refused as "slug held by an
      unknown owner".
    (Lead correction to the first draft, which would have refused every existing deployment.)
  - Rider: pin that the row is written, and pin the refusal text for both the known and the unknown owner.
- **Class lift:** the collision rule is a property of the SLUG, not of how it was derived. A project whose
  `lore.yaml` hand-sets a slug held by a DIFFERENT project path is refused the same way. One check serves both
  doors.
- The test_lore_deploy.py fixture alignment (8 fixtures, no assertion changed) is ACCEPTED: the pre-existing
  fixtures contradicted F3 (the C-DEF trap).

# RULING: #572 contract addendum, the #568 audit's routed items (lead-165, 2026-11-01)

Source: `REPORT-audit-568-slug.md` §1, §4, §6 (audit of 99c2b8e, GO; its fixes committed as f247deb).
These pins join the #572 contract (`skills/lore-deploy/scripts/test_ledger_572.py`, or a sibling file), because the
#572 round rewrites `ManifestOwner` and every item touches the same refusal seams. One implementer builds both.

Pins to add (each a behaviour test, RED on f247deb unless noted):
- **C1 (F5, a defect):** `setup` over a corrupt (non-SQLite) `<slug>.db` returns `_EXIT_ERROR`, writes one stderr
  line naming the manifest file, and creates nothing. Measured today: an uncaught `sqlite3.DatabaseError`
  traceback. The ledger WRITE path (`record`) gets the same treatment.
- **C2 (F4 "manifest OR container"):** the container mounts THIS path and the manifest records ANOTHER path, so
  `setup` is refused, naming the other path. This kills the wrong build that short-circuits on the container.
- **C3 (Addendum literal):** the container mounts THIS path, the manifest is legacy (no owner row) and there is no
  lore.yaml, so `setup` is refused as an unknown owner.
- **C4:** a scaffolded lore.yaml has the umask-default mode (0644 under umask 022), not 0600. Green on f247deb
  (the A3 fix); it pins that fix.
- **C5:** with NO lore.yaml, `stop` / `status` on a hyphenated directory act on the DERIVED slug
  (`lore-odoo_custom`), not the raw name.
- **C6 (directive #18018):** `stop` / `status` on an unreadable lore.yaml keep refusing (`_EXIT_ERROR`; the slug is
  unknowable, and guessing from the directory name targets the wrong container for any hand-set slug). The stderr:
  - is a refusal line naming the file and the parse error;
  - is NOT the child interpreter's `Traceback (most recent call last)`;
  - ends with a remedy: fix lore.yaml, or `podman stop lore-<slug>` by hand.
  Measured today: exit 2 and a multi-line child traceback with no remedy.
- **S1 (fixture fiction):** the `PodmanShim` claim that "the real cold index creates `<slug>.db`" is false
  (RULING-572-ledger.md). The #572 contract's fixtures must not have the indexer create the ledger.

Lead decision on **A7** (low; listed at close-out): ACCEPTED as a residual. A project whose lore.yaml hand-sets
another project's slug can backfill that slug's ownerless legacy manifest when the other container is absent. Only
the pre-#568 manifests (`lore`, `demand_intelligence`) are ownerless, and each is backfilled by its own next setup.
The case needs a deliberate hand-set collision. It goes in the wave's residual finding with its re-open trigger:
any report of a slug being claimed across projects.

## Lead rulings on REPORT-contract-572-ledger.md forks (2026-11-01)
- **F-1 → (a):** the contract author (not the builder) rewrites the 7 C-DEF pins in `test_scaffold_slug.py` so that
  each arranges its ledger through a real successful `setup` and asserts no ledger count. The provisioned state
  comes from a real setup, not from `_write_manifest(owner=…)`. `PodmanShim._index_like_the_real_indexer` stops
  writing `<slug>.db` (S1 above).
- **F-2 → (a), accept the re-index.** It is the operator's ruling verbatim ("index state is never inferred from the
  ledger"). A legacy or owner-only ledger is unprovisioned, so the next `setup` on lore / demand_intelligence
  re-indexes and needs the secrets env-file. Acceptance uses `stop`/`start`, which never read the ledger. The
  re-index cost is unmeasured and is flagged to the operator at close-out. No migration (option (b) would be
  index state from a second source).
- **F-3:** already #565; no new finding.

## Round 3: the #572 audit's routed items (lead-165, 2026-11-01; source REPORT-audit-572-ledger.md §Items routed, §Findings)
The audit gave GO on 7d79115 (docs/docstrings committed ecc2829). One small round follows: contract → implementer → lead
verification in full (tests rerun + diff read; no separate audit, as for a small fix).
- **P-3 (central status property, ∀ container state):** status prints no file or chunk count from the ledger in EVERY
  container state (absent, stopped, running). Today it is pinned for absent only (the `DeployShim` monoculture), and a
  build that counts only when running passes 419/419.
- **P-2:** a ledger carrying the marker plus a DELETED lore.yaml does not make setup a no-op. Setup re-scaffolds and
  re-provisions, and never returns `_EXIT_OK` having merged `.mcp.json` from a missing config.
- **D-1 (defect):** every render of a ledger-stored or podman-reported path is ONE value. The hostile newline owner
  path (`HOSTILE_PROJECT_NAME`) cannot forge a line on setup's collision refusal stderr (`is held by …`), as it
  already cannot on status.
- **D-3 (defect, the F5 sibling of C1):** setup over a state dir that cannot be CREATED (absent, parent unwritable)
  refuses in one line naming it, with no traceback and nothing created.
- **P-OWNER-VALUE (tautology):** `test_status_shows_the_recorded_owner_path` expects `str(project.resolve())`, never
  the production reader's output.
- **D-5 (naming; the user rule calls cross-file naming drift a bug):** the host `<slug>.db` is "the ledger"
  everywhere. `ManifestOwner`, `MANIFEST_DIR`, `_manifest_path`, `_MANIFEST_META_DDL` and `.manifest` become ledger
  names. The served "manifest" strings (the `_slug_collision` refusals, `verb_stop`) become "ledger", and are pinned.
  The contract author renames the test side; the implementer renames the production side.
- **`ManifestOwner.record`:** the contract arranges the owner-only (#568) state with a raw sqlite write in the test
  harness, not through production. The implementer then deletes `record`, which has no production caller.
- Not this round, going to the residual finding: D-6 (double read), D-7 (`""` marker on a hand-edit), D-8
  (`datetime.UTC` ≥3.11, within the floor), D-9 (the post-index write-failure wording), the 3 stale test docstrings
  (the contract author fixes them while it is in those files), and lifecycle.md's Qdrant-era "Collections" bullet plus
  the SKILL.md "ten tools" count (the lead verifies these at close-out).
- **ROUND 3 CANCELLED (operator, 2026-11-01: "not really very important").** Only the in-flight mechanical symbol
  rename (D-5 production names) lands, behaviour-preserving and suite-verified. P-3, P-2, D-1, D-3, P-OWNER-VALUE,
  the served "manifest" strings, `Ledger.record` deletion and the MANIFEST_DIR / _DEFAULT_MANIFEST_DIR naming all
  go into the wave's residual finding, each with its wrong build / failure scenario from REPORT-audit-572-ledger.md.

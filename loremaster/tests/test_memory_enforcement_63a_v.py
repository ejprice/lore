"""Contract — packet 63a-v: F5 GOVERNED-TABLE WRITE-ENFORCEMENT COMPLETENESS, WHOLE-TREE REACH
(design §10.9-A CORRECTION). Authored by ``contract-63a-v`` (Opus 4.8 contract author; tests ONLY).

#446 (cold-audit-63a-iv §FINDING-1): F5's OWN reach was a hidden constant — L1 scanned
``memory/local.py`` ONLY (the ``_local_source`` hand-pick), so the governed ``scope`` write in
``principals.py::_migrate_memory_scope`` (the ``migrate-governed`` backfill, ``principals.py:1187``)
was INVISIBLE to all three F5 layers. That is the reach-as-hidden-constant CLASS §10.9 exists to
close, reproduced INSIDE the instrument built to close it. This module extends F5's reach from ONE
file to the WHOLE workspace tree (roots DERIVED from ``[tool.uv.workspace] members``) and adds
``migrate-governed`` as the allowlist's SECOND evidence-backed triple, classified via a NAMED
``governed.governed_exempt`` frame.

RED-AT-HEAD isolates the UNBUILT PRODUCTION MECHANISM (the builder's GREEN):
  - ``governed.governed_exempt`` / ``governed.active_exempt`` are UNBUILT ⇒
    ``test_the_governed_exempt_mechanism_is_built`` RED.
  - ``principals.py::_migrate_memory_scope`` does not enter ``governed_exempt("migrate-governed")`` ⇒
    ``test_migrate_memory_scope_enters_governed_exempt`` RED (L2a structural).
  - the LIVE migration write is observed UNCLASSIFIED (no exempt token) ⇒
    ``test_the_live_migration_write_is_attributed`` RED (L2b runtime, both-ways).
The whole-tree SCANNER + the both-ways OBSERVER are test infra (this contract, like 63a-iv's
substrate) — the from-truth / discriminator / classifier legs are GREEN once that infra works, and
mutation-prove that a WRONG build (a hand-list scanner, a borrowed exempt token) does NOT pass.

This is the F5 §3.2 promised 63b/64 — the scanner is parametrised by TABLE (memory is its first
parametrisation); the 63a-iv local.py coverage + L2a/L2b member pins stay GREEN, untouched (this
EXTENDS the reach, it does not replace it).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import loremaster.governed as governed_mod
import loremaster.memory.local as local_mod
import loremaster.principals as principals_mod
from _governed_contract import (
    MEMORY_TABLE,
    ObservedWrite,
    TreeMutationSite,
    TreeWriteAllowlistEntry,
    classify_tree_observed_write,
    declared_workspace_members,
    derive_member_source_roots,
    exempt_entry_is_self_contained,
    exempt_frame_raw_memory_mutations,
    function_calls_named,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
    seam_modules_for_tree_allowlist,
    store_handle,
)

# The migration fixture + the store handle idiom (DRY — the ONE migration world, never re-wired).
from test_governed_migration_63a import migration_world  # noqa: F401 (fixture used by name)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _rel(module: Any) -> str:
    """A module's repo-relative posix path — the key shape the whole-tree scanner emits (so an
    allowlist site.file MATCHES a derived TreeMutationSite.file, never a hardcoded string)."""
    return Path(module.__file__).resolve().relative_to(_REPO_ROOT).as_posix()


_LOCAL = _rel(local_mod)
_PRINCIPALS = _rel(principals_mod)


# --------------------------------------------------------------------------- #
# The WHOLE-TREE deny-by-default WRITE ALLOWLIST (design §10.9-A CORRECTION). Four (site,
# justification, pin, frames [, exempt_name, runtime_observed]) entries — the 3 local.py sites (the
# 63a-iv coverage, now file-keyed) + migrate-governed (the SECOND evidence-backed triple, #446).
# --------------------------------------------------------------------------- #

_UPSERT_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_upsert_fragment", "UPSERT"),
    justification=(
        "deterministic-id UPSERT; the CREATE caller folds the owner pair into the id (#439) so it "
        "cannot name a foreign row, the REPLAY caller uses the STORED id (RES-1)."
    ),
    pin="test_a_non_owner_reremember_mints_a_distinct_id_and_does_not_seize_or_rescope",
    frames=("remember", "_replay_record"),
)
_REINFORCE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_reinforce", "UPDATE"),
    justification="read-side-effect on the NON-governed importance column only (§10.9-C).",
    pin="test_the_reinforce_update_sets_only_the_importance_column",
    frames=("_reinforce",),
)
_RECREATE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_recreate_memory_table", "REMOVE"),
    justification="boot/admin table recreate, reachable ONLY via rebuild_embeddings (RES-1).",
    pin="test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings",
    frames=("_recreate_memory_table",),
    runtime_observed=False,  # #445 boot/admin bound — L2a structural coverage only, never a member verb
)
_MIGRATE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_PRINCIPALS, "_migrate_memory_scope", "UPDATE"),
    justification=(
        "the migrate-governed backfill (§10.9-A CORRECTION step 4). Evidence: admin-CLI-only "
        "reachability (no MCP tool path reaches it); the statement can only touch UNMIGRATED rows "
        "(WHERE scope IS NONE — a NONE-scope row has no owner to seize); idempotent + "
        "precondition-guarded (single-operator resolution or REFUSE, §2.1); R4 driver-routed. It is "
        "NOT member-reachable, so it attributes via a NAMED governed_exempt('migrate-governed') "
        "frame rather than write_guard — exempt-WITH-JUSTIFICATION, never silently dropped."
    ),
    pin="test_migrate_memory_scope_updates_only_none_scope_rows",
    frames=("_migrate_memory_scope",),
    exempt_name="migrate-governed",
)
MEMORY_TREE_ALLOWLIST: tuple[TreeWriteAllowlistEntry, ...] = (
    _UPSERT_ENTRY,
    _REINFORCE_ENTRY,
    _RECREATE_ENTRY,
    _MIGRATE_ENTRY,
)

_DERIVED = governed_table_raw_mutation_sites_in_tree  # shorthand; the from-truth whole-tree scan
_ALLOWLISTED_SITES = frozenset(entry.site for entry in MEMORY_TREE_ALLOWLIST)


def _principals_source() -> str:
    return Path(principals_mod.__file__).read_text(encoding="utf-8")


# =========================================================================== #
# L1 — the whole-tree derived set is an OUTPUT (design §10.9-A CORRECTION step 1).
# =========================================================================== #


class TestTheWholeTreeReachIsAnOutput:
    """§10.9-A CORRECTION step 1 — L1's file set is an OUTPUT of a whole-tree scan (roots DERIVED
    from the workspace members), NEVER a hand-picked file/list. A NEW file gaining a governed memory
    write anywhere in the tree GROWS the derived set and reds until classified (deny-by-default)."""

    def test_the_whole_tree_derived_set_is_the_known_four_sites(self) -> None:
        """⚠ ANTI-VACUITY (GREEN once the whole-tree scan works) — the scan derives a non-empty set
        and it is EXACTLY the four known sites (the 3 local.py sites + migrate-governed). Reddens a
        blind scanner (empty → the containment pin is vacuous) OR a raw memory write added/removed
        anywhere in the tree without re-adjudication."""
        derived = _DERIVED(MEMORY_TABLE)
        assert derived, "the whole-tree scan derived NO raw memory mutation — the scanner is blind"
        assert derived == _ALLOWLISTED_SITES, (
            f"whole-tree raw-mutation set moved. new (unadjudicated): "
            f"{sorted(derived - _ALLOWLISTED_SITES)};\n  gone: {sorted(_ALLOWLISTED_SITES - derived)}"
        )

    def test_migrate_memory_scope_is_now_within_f5_reach(self) -> None:
        """⚠ THE #446 CLOSE (GREEN once the whole-tree scan works) — the governed ``scope`` write in
        ``principals.py::_migrate_memory_scope`` (INVISIBLE to F5's old local.py-only reach) is now
        DERIVED across the whole tree. Reddens a build that reverts F5's reach to a single file."""
        derived = _DERIVED(MEMORY_TABLE)
        assert TreeMutationSite(_PRINCIPALS, "_migrate_memory_scope", "UPDATE") in derived, (
            f"the migrate-governed memory write in {_PRINCIPALS} is OUTSIDE F5's derived reach — "
            f"the #446 defect (a file-scoped hidden constant) is not closed. derived: {sorted(derived)}"
        )

    def test_every_whole_tree_site_is_in_the_allowlist(self) -> None:
        """⚠ GREEN at HEAD — deny-by-default containment over the WHOLE tree: every derived raw
        memory mutation is ∈ the allowlist (no orphan) and the allowlist has no GHOST. Reddens a new
        unclassified raw write anywhere in the tree (orphan) OR removing an allowlist entry (its
        derived site becomes an orphan — the migrate-governed triple's orphan-on-removal mutation)."""
        derived = _DERIVED(MEMORY_TABLE)
        orphans = derived - _ALLOWLISTED_SITES
        ghosts = _ALLOWLISTED_SITES - derived
        assert not orphans, (
            f"UNCLASSIFIED raw memory mutation(s) across the tree (deny-by-default): {sorted(orphans)}"
        )
        assert not ghosts, f"GHOST allowlist entry — no live raw mutation site: {sorted(ghosts)}"

    def test_the_scan_roots_are_derived_from_workspace_members_not_a_hand_list(self) -> None:
        """⚠ THE ANTI-HAND-LIST PIN (GREEN once the from-truth derivation works). The scan roots are
        the production package of EVERY ``[tool.uv.workspace] members`` entry — computed here
        INDEPENDENTLY from pyproject. A builder that hand-lists ``[local.py, principals.py]`` (or
        local.py only — relocating the hidden constant) makes this FALSE: its roots would not equal
        the member-derived set. This is the pin the adversary's REACH ATTACK builds a wrong scanner
        against."""
        expected = frozenset(
            (_REPO_ROOT / member / member).resolve()
            for member in declared_workspace_members()
            if (_REPO_ROOT / member / member).is_dir()
        )
        assert frozenset(derive_member_source_roots()) == expected, (
            "F5's scan roots are NOT the from-truth workspace-member production roots — a hand-list "
            "would relocate the #446 hidden constant instead of closing it"
        )

    def test_a_governed_write_in_any_member_grows_the_reach_and_the_scan_is_precise(
        self, tmp_path: Path
    ) -> None:
        """⚠ THE OUTPUT / WHOLE-TREE-REACH DISCRIMINATOR (GREEN once the scan works, design step 3).
        A SYNTHETIC workspace (its own pyproject declaring members ``alpha``/``beta``) exercises the
        from-truth root derivation END-TO-END: a governed write in the SECOND member (``beta``, not
        just the first) IS derived (whole-tree reach — a hand-list local-only scanner MISSES it); a
        SELECT-only file is NOT (precision); a concatenation-assembled write is NOT (the #444 static
        bound — SAYS SO); a write in a TEST tree is NOT (the test-tree exclusion)."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uv.workspace]\nmembers = ["alpha", "beta"]\n', encoding="utf-8"
        )
        _mkfile(tmp_path / "alpha" / "alpha" / "writes.py", _FSTRING_MEMORY_UPDATE)
        _mkfile(tmp_path / "alpha" / "alpha" / "reads.py", _SELECT_ONLY)
        _mkfile(tmp_path / "alpha" / "tests" / "test_x.py", _FSTRING_MEMORY_UPDATE)  # a test tree
        _mkfile(tmp_path / "beta" / "beta" / "concat.py", _CONCAT_MEMORY_UPDATE)
        _mkfile(tmp_path / "beta" / "beta" / "latewrite.py", _FSTRING_MEMORY_UPDATE)

        derived = _DERIVED(MEMORY_TABLE, repo_root=tmp_path)
        files = {s.file for s in derived}
        # whole-tree reach: BOTH members' idiomatic writes are derived (not just the first member).
        assert TreeMutationSite("alpha/alpha/writes.py", "_do_write", "UPDATE") in derived, (
            f"a governed write in the FIRST member was not derived: {sorted(derived)}"
        )
        assert TreeMutationSite("beta/beta/latewrite.py", "_do_write", "UPDATE") in derived, (
            f"a governed write in the SECOND member was not derived — F5 reaches only some members "
            f"(a hidden constant one level up): {sorted(derived)}"
        )
        # precision: a SELECT-only file, a concatenation-assembled write, and a TEST tree contribute
        # NOTHING (the #444 static bound + the prose/precision fix + the test-tree exclusion).
        assert "alpha/alpha/reads.py" not in files, "a SELECT-only file was wrongly flagged (imprecise)"
        assert "beta/beta/concat.py" not in files, (
            "a concatenation-assembled write was DERIVED — the #444 static bound is closed; if you "
            "widened the scan deliberately, re-adjudicate (it is L2b's job to catch this at runtime)"
        )
        assert not any(f.startswith("alpha/tests/") for f in files), (
            "a write in a TEST tree was scanned — production reach must exclude test trees"
        )


class TestTheScannerRejectsProseNamingAVerb:
    """The PRECISION invariant for the false-positive the whole-tree scan SURFACED (finding filed):
    principals.py's SF-63-5 refusal message *"…the delete is refused … they own N governed
    {MEMORY_TABLE} row(s)…"* was matched by F5's OLD loose statement regex (``delete`` + ``is``) AS A
    MEMORY DELETE — invisible while F5 scanned only local.py, a phantom the moment the whole-tree
    scan reached principals.py. Every audit-caught defect CLASS becomes a repo-local invariant
    (CLAUDE.md); this goes RED the day the scanner regresses to matching prose."""

    def test_a_prose_f_string_naming_a_verb_and_the_table_is_not_a_mutation_site(self) -> None:
        from _governed_contract import governed_table_raw_mutation_sites

        prose = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "class _S:\n"
            "    async def delete(self, x):\n"
            "        if x:\n"
            "            raise ValueError(\n"
            "                f\"cannot delete principal: they own {x} governed {MEMORY_TABLE} \"\n"
            "                f\"row(s) — until then the delete is refused (SF-63-5)\"\n"
            "            )\n"
        )
        derived = governed_table_raw_mutation_sites(prose, MEMORY_TABLE)
        assert not derived, (
            f"a PROSE f-string naming a verb ('delete') and the table in the same sentence was "
            f"derived as a mutation site (the SF-63-5 false-positive regressed): {sorted(derived)}"
        )


# =========================================================================== #
# migrate-governed — the allowlist's SECOND evidence-backed triple (design step 4).
# =========================================================================== #


class TestMigrateGovernedIsAnEvidenceBackedTriple:
    """§10.9-A CORRECTION step 4 — migrate-governed is classified by a NAMED
    ``governed.governed_exempt`` frame (not member-reachable → exempt-WITH-JUSTIFICATION), and its
    justification is PINNED by a statement-shape (WHERE scope IS NONE)."""

    def test_the_governed_exempt_mechanism_is_built(self) -> None:
        """⚠ RED at HEAD — the exempt attribution channel is UNBUILT. Split out so the RED reason is
        legible (the mechanism), distinct from the wiring RED below."""
        assert hasattr(governed_mod, "governed_exempt") and hasattr(governed_mod, "active_exempt"), (
            "governed.governed_exempt / governed.active_exempt are unbuilt — the migrate-governed "
            "L2 attribution channel (§10.9-A CORRECTION step 4) has no mechanism"
        )

    def test_migrate_memory_scope_enters_governed_exempt(self) -> None:
        """⚠ RED at HEAD (L2a structural) — ``_migrate_memory_scope`` runs its backfill UPDATE
        OUTSIDE any attribution frame. On the correct build it enters
        ``governed_exempt("migrate-governed")`` so its runtime mutation is attributable. Reddens a
        build that leaves the migrate write unattributed."""
        assert function_calls_named(_principals_source(), "_migrate_memory_scope", "governed_exempt"), (
            "principals._migrate_memory_scope does NOT enter governed.governed_exempt — its governed "
            "scope write is UNATTRIBUTABLE at the F5 runtime seam (§10.9-A CORRECTION step 4 / L2a)"
        )

    def test_migrate_memory_scope_updates_only_none_scope_rows(self) -> None:
        """⚠ GREEN at HEAD — the migrate-governed JUSTIFICATION pin (the statement-shape leg). WHAT IT
        ACTUALLY CHECKS: it reads the FIRST ``UPDATE … SET scope`` statement in ``_migrate_memory_scope``
        (``_migrate_backfill_update_statement``, first-match) and asserts that statement CONTAINS the
        ``WHERE scope IS NONE`` SUBSTRING. It catches an honest edit that drops/relocates the WHERE
        clause on the FIRST backfill UPDATE, at which point the migrate must route through guarded_write
        (design step 4).

        ⚠ TWO ACCEPTED BOUNDS (finding #449, adversary-63a-v3 §BASE3 — this is a first-match SUBSTRING
        presence check, NOT a proof the migrate touches only NONE-scope rows; the old docstring's
        "reddens the day the migrate grows a write that touches a NON-NONE-scope row" was a FALSE GATE):
        it does NOT red on (a) a co-located SECOND seizure write AFTER the blessed one (first-match
        shadows it — the R3 count leg ``TestTheExemptFrameHoldsOnlyItsGuardedMutation`` delivers THAT
        ∀-half), nor (b) an OR-extended FIRST statement ``WHERE scope IS NONE OR scope =
        $victim`` that seizes owned rows while still containing the substring (the #449 R4-a bound,
        pinned in ``TestTheAcceptedF5BoundsArePinned``). F5 is a static HONEST-DEVELOPER net; those are
        the #138 HOSTILE-AUTHOR class it does not defend; the runtime root-fix is 63b (task 571ef1a)."""
        update = _migrate_backfill_update_statement(_principals_source())
        assert update is not None, (
            "no raw memory UPDATE found in _migrate_memory_scope — the migrate-governed site moved; "
            "re-adjudicate the allowlist triple"
        )
        assert re.search(r"WHERE\s+scope\s+IS\s+NONE", update, re.IGNORECASE), (
            f"the migrate-governed UPDATE does not restrict to WHERE scope IS NONE — it can now touch "
            f"an OWNED row (seizure), so it may no longer ride the exempt frame: {update!r}"
        )

    def test_every_tree_allowlist_entry_has_a_real_evidencing_pin(self) -> None:
        """⚠ GREEN at HEAD — each allowlist entry's ``pin`` names a test DEFINED in the test tree (an
        entry whose evidencing pin is deleted leaves the allowlist — evidence, not opinion)."""
        defined = _defined_test_names()
        missing = [(e.site, e.pin) for e in MEMORY_TREE_ALLOWLIST if e.pin not in defined]
        assert not missing, f"allowlist entries whose evidencing PIN does not exist: {missing}"


# =========================================================================== #
# L1 ↔ L2 both-ways cross-check — the classifier controls + the LIVE migration attribution.
# =========================================================================== #


class TestTheClassifierDiscriminatesBothWays:
    """§10.9-A CORRECTION step 2 — the classifier (the uniform L2b rule) accepts a write_guard label
    OR a NAMED exempt token whose allowlist site MATCHES the stack origin, and REJECTS everything
    else. Pure-logic controls (both directions), GREEN at HEAD — they mutation-prove the classifier
    can SEE an escape and can catch a BORROWED token (design step 4)."""

    def _site(self) -> tuple[str, str]:
        return (_MIGRATE_ENTRY.site.file, _MIGRATE_ENTRY.site.function)

    def test_a_write_guard_label_classifies(self) -> None:
        observed = ObservedWrite(label="remember", verb="UPSERT", seam="execute_transaction")
        assert classify_tree_observed_write(observed, MEMORY_TREE_ALLOWLIST) is True

    def test_a_matching_exempt_token_classifies(self) -> None:
        observed = ObservedWrite(
            label=None, verb="UPDATE", seam="run_query",
            exempt="migrate-governed", origin_site=self._site(),
        )
        assert classify_tree_observed_write(observed, MEMORY_TREE_ALLOWLIST) is True, (
            "a migrate write carrying its OWN exempt token from its OWN site must classify"
        )

    def test_a_bare_unattributed_write_is_unclassified(self) -> None:
        """The observed-not-classified escape (an L1 blind spot, e.g. a concatenation-assembled
        write, running with no label and no exempt) — the RED signal."""
        observed = ObservedWrite(label=None, verb="UPDATE", seam="run_query")
        assert classify_tree_observed_write(observed, MEMORY_TREE_ALLOWLIST) is False, (
            "a memory mutation with NO label and NO exempt token must be UNCLASSIFIED (deny-by-default)"
        )

    def test_a_borrowed_exempt_token_is_unclassified(self) -> None:
        """THE #446 STEP-4 CONTROL — a site BORROWING the migrate-governed token from a DIFFERENT
        origin fails the (file, symbol) match, so it cannot launder a foreign write through the
        admin exemption."""
        borrowed = ObservedWrite(
            label=None, verb="UPDATE", seam="run_query",
            exempt="migrate-governed", origin_site=(_PRINCIPALS, "_some_other_function"),
        )
        assert classify_tree_observed_write(borrowed, MEMORY_TREE_ALLOWLIST) is False, (
            "a site borrowing migrate-governed's exempt token was CLASSIFIED — the (file, symbol) "
            "match is not enforced, so any site can launder a governed write through the exemption"
        )

    def test_the_observer_patch_set_is_derived_from_the_allowlist(self) -> None:
        """THE META-REACH PIN (GREEN at HEAD) — the L2b observer's patch-set (which modules' store
        seam it instruments) is DERIVED from the whole-tree allowlist files, NOT a hand-list. So a
        NEW allowlisted site in a NEW file joins the observer's reach by the SAME derivation that
        classifies it (F5's OWN reach a checked variable — the #446 lesson). Reddens the day
        ``principals`` (the migrate seam's module) drops out of the derived patch-set."""
        modules = seam_modules_for_tree_allowlist(MEMORY_TREE_ALLOWLIST)
        names = {m.__name__ for m in modules}
        assert principals_mod.__name__ in names, (
            f"the migrate-governed seam module (principals) is NOT in the observer's DERIVED "
            f"patch-set {sorted(names)} — the observer would never see the migration write"
        )
        assert local_mod.__name__ in names, "the local.py seam module dropped out of the derived patch-set"


class TestTheLiveMigrationWriteIsAttributed:
    """§10.9-A CORRECTION step 2 (the LIVE both-ways leg) — the observer's reach extends to
    ``principals`` and the real migrate-governed backfill write is CLASSIFIED. ⚠ RED at HEAD: the
    migration write is observed UNCLASSIFIED (no exempt token), the exact three-layer gap the cold
    audit found (F5 blind to a governed write live in a sibling module)."""

    async def test_the_live_migration_write_is_attributed(self, migration_world: Any) -> None:  # noqa: F811
        """⚠ RED at HEAD — drives the REAL ``migrate_governed`` (a NONE-scope legacy row, alice the
        operator) inside the instrumented seam and asserts the backfill UPDATE is (1) OBSERVED with
        origin ``principals::_migrate_memory_scope`` (the observer's reach genuinely extends to
        principals — the coverage the cold audit found MISSING) and (2) CLASSIFIED. At HEAD the write
        carries NO exempt token (``active_exempt`` unbuilt) ⇒ UNCLASSIFIED ⇒ RED. On the correct
        build the ``governed_exempt("migrate-governed")`` frame classifies it."""
        principal_store, keep_store, connection, env = migration_world
        handle, _calls = store_handle(connection, url=env.url)
        modules = seam_modules_for_tree_allowlist(MEMORY_TREE_ALLOWLIST)
        with observe_governed_table_writes(MEMORY_TABLE, extra_modules=modules) as observed:
            await principals_mod.migrate_governed(
                table=MEMORY_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
        # ANTI-VACUITY: the migration actually issued the backfill UPDATE and the observer SAW it
        # originating in _migrate_memory_scope (proving the observer's reach extends to principals —
        # the L1-blind-spot / coverage gap the cold audit named).
        migrate_writes = [
            o for o in observed if o.origin_site == (_PRINCIPALS, "_migrate_memory_scope")
        ]
        assert migrate_writes, (
            f"the observer did NOT see the migrate-governed backfill UPDATE originating in "
            f"principals._migrate_memory_scope — its reach does not extend to principals (observed: "
            f"{[(o.seam, o.verb, o.origin_site) for o in observed]})"
        )
        # DENY-BY-DEFAULT: every observed migration write is CLASSIFIED (label OR valid exempt).
        unclassified = [
            (o.seam, o.verb, o.origin_site)
            for o in migrate_writes
            if not classify_tree_observed_write(o, MEMORY_TREE_ALLOWLIST)
        ]
        assert not unclassified, (
            f"the migrate-governed backfill ran UNATTRIBUTED at the F5 seam (§10.9-A CORRECTION L2b "
            f"deny-by-default — no write_guard label, no valid exempt token): {unclassified}"
        )


# =========================================================================== #
# Table parametrisation — the scanner is reusable for 63b/64 (design step 5, ONE implementation).
# =========================================================================== #


class TestTheScannerIsTableParametrised:
    """§10.9-A CORRECTION step 5 — the whole-tree scanner is parametrised by TABLE (memory is its
    first parametrisation; 63b passes message/relation, 64 task/finding). No MEMORY_TABLE hardcode."""

    def test_scanning_for_a_different_table_finds_that_table_not_memory(self, tmp_path: Path) -> None:
        """A synthetic workspace with a governed ``message`` write: scanning for ``message`` (with
        its own table constant hint) DERIVES it and scanning for ``memory`` does NOT — so the scanner
        is genuinely table-keyed, not a memory-hardcoded clone (the 63b/64 reuse the design promises)."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uv.workspace]\nmembers = ["gamma"]\n', encoding="utf-8"
        )
        _mkfile(
            tmp_path / "gamma" / "gamma" / "writes.py",
            'MESSAGE_TABLE = "message"\n\n\n'
            "async def _do_write(x):\n"
            "    await _q(f\"UPDATE type::record('{MESSAGE_TABLE}', $id) SET ack = true\", {})\n",
        )
        as_message = governed_table_raw_mutation_sites_in_tree(
            "message", repo_root=tmp_path, table_const_hint="MESSAGE_TABLE"
        )
        as_memory = governed_table_raw_mutation_sites_in_tree(MEMORY_TABLE, repo_root=tmp_path)
        assert TreeMutationSite("gamma/gamma/writes.py", "_do_write", "UPDATE") in as_message, (
            f"the scanner did not derive a governed MESSAGE write when asked for the message table — "
            f"it is not table-parametrised (63b/64 reuse broken): {sorted(as_message)}"
        )
        assert not as_memory, (
            f"the scanner derived a MEMORY site from a message-only tree — it is not table-keyed: "
            f"{sorted(as_memory)}"
        )


# =========================================================================== #
# R1 (design §10.9-A CORRECTION step 6, adversary-63a-v §MISSING-PINS) — the EXEMPT-ENTRY
# SELF-CONTAINMENT VALIDITY pin. The exempt-origin (file, symbol) match in
# classify_tree_observed_write is SOUND only for SELF-CONTAINED entries (literal site == seam-call
# site). Pin the premise ∀ exempt entries so a future NON-self-contained candidate (a
# fragment-builder: literal in _build_X, seam in _drain — 63b/64) REDS the check and surfaces the
# design question, INSTEAD of the match being quietly loosened. This makes the exempt-match's
# soundness condition — the hidden constant the adversary's REACH ATTACK named, one level up inside
# the exempt channel — a CHECKED VARIABLE.
# =========================================================================== #


class TestEveryExemptAllowlistEntryIsSelfContained:
    """§10.9-A CORRECTION step 6 R1 — the exempt-origin match's SOUNDNESS PREMISE (self-containment)
    is a CHECKED VARIABLE ∀ exempt entries, not a hidden constant verified for migrate-governed
    alone. migrate-governed IS self-contained today (its ``UPDATE {MEMORY_TABLE} … WHERE scope IS
    NONE`` literal AND its ``run_query`` both live in ``_migrate_memory_scope``), so the LIVE pin is a
    TEST-INFRA INVARIANT (GREEN now); the discrimination — that the check is NOT vacuous — is proven
    by a SYNTHETIC non-self-contained entry (the second test, the adversary's own construction)."""

    def test_every_exempt_allowlist_entry_is_self_contained(self) -> None:
        """⚠ GREEN at HEAD (a test-infra invariant) — every exempt allowlist entry's L1-derived
        literal site IS its seam-call site (``function_calls_named``: the enclosing function of the
        raw mutation literal ALSO calls ``run_query``/``execute_transaction`` in its own file).
        ANTI-VACUITY: at least one exempt entry (migrate-governed) exists, so the ∀ is non-empty.
        Reddens the day a NON-self-contained exempt entry joins the allowlist (a fragment-builder
        whose literal and seam call live in DIFFERENT symbols) — at which point the exempt-origin
        (file, symbol) match is UNSOUND and design step 6 R1 must be re-adjudicated, NOT the match
        quietly loosened."""
        exempt_entries = [e for e in MEMORY_TREE_ALLOWLIST if e.exempt_name is not None]
        assert exempt_entries, (
            "R1 anti-vacuity: no exempt allowlist entry to check — migrate-governed must be present, "
            "else the self-containment premise pin is vacuous (design §10.9-A CORRECTION step 6 R1)"
        )
        for entry in exempt_entries:
            source = (_REPO_ROOT / entry.site.file).read_text(encoding="utf-8")
            assert exempt_entry_is_self_contained(entry, source=source), (
                f"exempt allowlist entry {entry.site} (token {entry.exempt_name!r}) is NOT "
                f"self-contained: its enclosing function {entry.site.function!r} does not call the "
                f"store seam (run_query/execute_transaction) in {entry.site.file}. The exempt-origin "
                f"(file, symbol) match in classify_tree_observed_write is therefore UNSOUND for it "
                f"(the runtime origin ≠ the L1 literal site). Re-adjudicate per design §10.9-A "
                f"CORRECTION step 6 R1 — do NOT loosen the match."
            )

    def test_the_self_containment_check_reds_a_non_self_contained_exempt_entry(self) -> None:
        """⚠ THE R1 DISCRIMINATION MUTATION-PROOF (the adversary's own construction) — the check is
        NOT vacuous: a SYNTHETIC exempt entry whose literal (``_build_fragment``) and seam call
        (``_drain``) live in DIFFERENT symbols FAILS the self-containment predicate, while a
        self-contained control (literal AND seam call in ``_do_write``) PASSES. Both synthetics carry
        the SAME exempt token, so a predicate that special-cased the token name — or returned a
        constant — fails one of the two legs (a probe needs a POSITIVE CONTROL — CLAUDE.md PKT-28
        C1). This excludes the wrong build the adversary warned of: a check that passes only
        migrate-governed but does not red a genuine non-self-contained entry."""
        # A fragment-builder shape: the raw memory UPDATE literal is BUILT in _build_fragment, but the
        # seam call fires from a DIFFERENT frame (_drain) — the exact non-self-contained future
        # candidate design step 6 R1 names (literal in _build_X, seam in _drain).
        non_self_contained_source = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "def _build_fragment(x):\n"
            "    return f\"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'k'\"\n\n\n"
            "async def _drain(x):\n"
            "    await run_query(statement=_build_fragment(x))\n"
        )
        self_contained_source = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "async def _do_write(x):\n"
            "    await run_query(f\"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'k'\")\n"
        )
        token = "fragment-builder"  # the SAME token on both — defeats a name-special-cased predicate
        non_self_contained = TreeWriteAllowlistEntry(
            site=TreeMutationSite("synthetic/pkg/frag.py", "_build_fragment", "UPDATE"),
            justification="synthetic — the literal is in _build_fragment, the seam fires from _drain",
            pin="test_the_self_containment_check_reds_a_non_self_contained_exempt_entry",
            frames=("_drain",),
            exempt_name=token,
        )
        self_contained = TreeWriteAllowlistEntry(
            site=TreeMutationSite("synthetic/pkg/whole.py", "_do_write", "UPDATE"),
            justification="synthetic positive control — literal AND seam call both in _do_write",
            pin="test_the_self_containment_check_reds_a_non_self_contained_exempt_entry",
            frames=("_do_write",),
            exempt_name=token,
        )
        assert exempt_entry_is_self_contained(
            non_self_contained, source=non_self_contained_source
        ) is False, (
            "a NON-self-contained exempt entry (literal in _build_fragment, seam call in _drain) "
            "PASSED the self-containment check — R1's premise pin is vacuous (the exempt-origin match "
            "would be unsound for it and NOTHING would catch the mis-siting)"
        )
        assert exempt_entry_is_self_contained(
            self_contained, source=self_contained_source
        ) is True, (
            "the self-containment POSITIVE CONTROL failed — the predicate cannot recognise a genuinely "
            "self-contained entry, so its False above is for the WRONG reason (a probe needs a control)"
        )


# =========================================================================== #
# R3 (design §10.9-A CORRECTION step 6, adversary-63a-v2 §R3 / finding #448) — the EXEMPT-FRAME
# SINGLE-SHAPE ∀-pin, the SIBLING premise R1 left open. R1 pinned that the exempt-origin match is
# SOUND (literal site == seam-call site). But the both-ways classifier trusts the WHOLE frame: ANY
# mutation co-located in ``_migrate_memory_scope``, running under the ``migrate-governed`` token,
# has runtime origin == the registered site BY CONSTRUCTION, so it classifies True. The frame's
# raw-mutation SET was still a HIDDEN CONSTANT (assumed = its one blessed ``WHERE scope IS NONE``
# write). A SECOND co-located memory ``UPDATE`` (a seizure, ``WHERE scope = <owned>``) an HONEST
# developer could add — believing F5 covers it — launders past ALL layers: L1 collapses the two
# SAME-VERB UPDATEs to ONE (file, function, verb) site, the base-3 first-match WHERE-none pin is
# SHADOWED by the blessed write, and the exempt token classifies the seizure. This pin makes the
# frame's raw-mutation SET a CHECKED VARIABLE ∀ — the reach-as-hidden-constant class ONE LEVEL DOWN,
# inside the exempt channel R1 hardened. TEST-INFRA INVARIANT (GREEN now — the real frame holds
# exactly its one write), NOT a production hook: it REDS the day the frame grows, forcing the
# design question to be re-adjudicated before the laundering can ship.
# =========================================================================== #


class TestTheExemptFrameHoldsOnlyItsGuardedMutation:
    """§10.9-A CORRECTION step 6 R3 — the both-ways classifier blesses the WHOLE exempt frame (a
    co-located mutation has runtime origin == the entry's registered site by construction), so the
    frame's ENTIRE raw-mutation set — not just the ONE statement the allowlist adjudicated — must be
    a CHECKED VARIABLE. Today ``_migrate_memory_scope`` holds EXACTLY its one ``WHERE scope IS NONE``
    UPDATE, so the LIVE pin is a TEST-INFRA INVARIANT (GREEN now); the discrimination — that it is
    NOT count-blind, verb-collapsing, or first-match — is proven by a SYNTHETIC exempt frame carrying
    a SECOND co-located SAME-VERB UPDATE (the adversary's own construction, finding #448)."""

    def test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation(self) -> None:
        """⚠ GREEN at HEAD (a test-infra invariant) — ∀ exempt allowlist entries, the entry's frame
        holds EXACTLY ONE raw memory mutation AND it is ``WHERE scope IS NONE``-restricted (the
        allowlisted shape). ANTI-VACUITY: ≥1 exempt entry (migrate-governed) exists, so the ∀ is
        non-empty. Reddens the day the exempt frame grows a SECOND co-located memory write — a seizure
        (``WHERE scope = <owned>``, caught by BOTH legs) OR even a benign second ``WHERE scope IS
        NONE`` write (caught by the count leg): EITHER voids the exemption's soundness, because the
        classifier blesses the WHOLE frame, not the one adjudicated statement — so the design question
        must be re-adjudicated, NOT the frame silently trusted. This closes adversary-63a-v2 §R3: the
        base-3 ``test_migrate_memory_scope_updates_only_none_scope_rows`` reads only the FIRST
        ``UPDATE … SET scope`` shape (a blessed write shadows a co-located seizure); this walks ALL
        co-located memory mutations, not the first."""
        exempt_entries = [e for e in MEMORY_TREE_ALLOWLIST if e.exempt_name is not None]
        assert exempt_entries, (
            "R3 anti-vacuity: no exempt allowlist entry to check — migrate-governed must be present, "
            "else the exempt-frame single-shape ∀-pin is vacuous (design §10.9-A CORRECTION step 6 R3)"
        )
        for entry in exempt_entries:
            source = (_REPO_ROOT / entry.site.file).read_text(encoding="utf-8")
            mutations = exempt_frame_raw_memory_mutations(entry, source=source)
            assert len(mutations) == 1, (
                f"exempt frame {entry.site.function!r} in {entry.site.file} holds "
                f"{len(mutations)} raw memory mutations, not EXACTLY ONE: {mutations!r}. The "
                f"both-ways classifier blesses the WHOLE frame (a co-located write has runtime "
                f"origin == the registered site BY CONSTRUCTION), so a SECOND co-located memory "
                f"write launders past L1 (two same-verb UPDATEs collapse to one site) and the "
                f"first-match WHERE-none pin (the blessed write shadows it). Re-adjudicate the "
                f"exemption per design §10.9-A CORRECTION step 6 R3 — do NOT trust the frame."
            )
            only = mutations[0]
            assert re.search(r"WHERE\s+scope\s+IS\s+NONE", only, re.IGNORECASE), (
                f"the exempt frame {entry.site.function!r}'s raw memory mutation does not restrict "
                f"to WHERE scope IS NONE — it can touch an OWNED row (a seizure), so it may no "
                f"longer ride the exempt frame and must route through guarded_write: {only!r}"
            )

    def test_the_single_shape_pin_reds_an_exempt_frame_with_a_second_seizure_write(self) -> None:
        """⚠ THE R3 DISCRIMINATION MUTATION-PROOF (the adversary's own construction, finding #448) —
        the pin is NOT count-blind, verb-collapsing, or first-match: a SYNTHETIC exempt frame carrying
        a SECOND co-located SAME-VERB UPDATE (the blessed ``WHERE scope IS NONE`` write + a SEIZURE
        ``WHERE scope = <owned>``) yields TWO statements — so the exactly-one leg reds AND the seizure
        fails the WHERE-none leg — while a single-mutation positive control yields ONE WHERE-none
        statement (so it passes). Both synthetics use the SAME frame name AND the SAME exempt token,
        so an extractor that special-cased the token or function name, returned a CONSTANT one-element
        list, or COLLAPSED the two same-verb UPDATEs (the exact L1 bug §R3 walks around) is CAUGHT (a
        probe needs a POSITIVE CONTROL — CLAUDE.md PKT-28 C1). ⚠ The second write is a SAME-VERB
        UPDATE deliberately: the adversary's P0 showed a DIFFERENT verb (DELETE) already reds at L1
        (the derived set grows); the same-verb UPDATE is the one L1 COLLAPSES — the whole of R3."""
        token = "second-write-frame"  # the SAME token on both — defeats a name/token-special-cased build
        # A seizure co-located with the blessed write: TWO same-verb UPDATEs in the ONE exempt frame.
        # The blessed WHERE-none write must NOT shadow the seizure (collect-ALL, never first-match).
        two_write_source = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "async def _do_write(x):\n"
            "    await run_query(f\"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE\")\n"
            "    await run_query(f\"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim\")\n"
        )
        one_write_source = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "async def _do_write(x):\n"
            "    await run_query(f\"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE\")\n"
        )
        second_write = TreeWriteAllowlistEntry(
            site=TreeMutationSite("synthetic/pkg/seize.py", "_do_write", "UPDATE"),
            justification="synthetic — a second co-located seizure UPDATE launders through the frame",
            pin="test_the_single_shape_pin_reds_an_exempt_frame_with_a_second_seizure_write",
            frames=("_do_write",),
            exempt_name=token,
        )
        one_write = TreeWriteAllowlistEntry(
            site=TreeMutationSite("synthetic/pkg/one.py", "_do_write", "UPDATE"),
            justification="synthetic positive control — the frame holds exactly its one blessed write",
            pin="test_the_single_shape_pin_reds_an_exempt_frame_with_a_second_seizure_write",
            frames=("_do_write",),
            exempt_name=token,
        )

        seized = exempt_frame_raw_memory_mutations(second_write, source=two_write_source)
        assert len(seized) == 2, (
            f"the extractor did NOT see BOTH same-verb UPDATEs co-located in the exempt frame — it "
            f"collapses / first-matches / returns a constant (the exact §R3 laundering door): {seized!r}"
        )
        # The exactly-one leg reds (2 ≠ 1) AND the seizure fails the WHERE-none leg — either alone
        # excludes the wrong build; both fire on the adversary's seizure construction.
        assert not all(
            re.search(r"WHERE\s+scope\s+IS\s+NONE", shape, re.IGNORECASE) for shape in seized
        ), (
            f"a seizure (WHERE scope = <owned>) co-located in the exempt frame passed the WHERE-none "
            f"∀-check — the shape leg is vacuous: {seized!r}"
        )

        control = exempt_frame_raw_memory_mutations(one_write, source=one_write_source)
        assert len(control) == 1 and re.search(
            r"WHERE\s+scope\s+IS\s+NONE", control[0], re.IGNORECASE
        ), (
            f"the single-mutation POSITIVE CONTROL did not yield exactly one WHERE-none statement — "
            f"the extractor cannot recognise a compliant frame, so its len==2 above is for the WRONG "
            f"reason (a probe needs a control): {control!r}"
        )


# =========================================================================== #
# R2 (design §10.9-A CORRECTION step 6, adversary-63a-v §MISSING-PINS) — the #138-class
# HAND-SET-LABEL accepted bound, NAMED in the instrument docstring. A production site that hand-sets
# a write_guard LABEL without calling guarded_write passes BOTH F5 layers — an ACCEPTED bound under
# the gate's threat model (the honest developer, not the hostile author). RED-until-built: the
# classifier's docstring does not name it yet (grep = 0 hits at fold).
# =========================================================================== #


class TestTheHandSetLabelBoundIsNamedInTheInstrumentDocstring:
    """§10.9-A CORRECTION step 6 R2 + "A GATE NEEDS A THREAT MODEL — WRITE DOWN WHO IT IS FOR"
    (CLAUDE.md). ``classify_tree_observed_write`` returns True on ANY write carrying a write_guard
    label (``if observed.label is not None: return True``) — so a site that hand-sets the label
    WITHOUT routing through ``guarded_write`` is CLASSIFIED. That is an ACCEPTED bound under the
    gate's threat model (the honest developer, not the hostile author — the #138 class), never closed
    by false positives. A gate whose accepted bound is UNNAMED is one the next engineer meets by an
    outage, or "helpfully" closes — re-opening a settled trade. ⚠ RED-until-built: the docstring must
    NAME the bound; at fold it does not."""

    def test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound(self) -> None:
        """⚠ RED-until-built (a NON-TRAPPING named-bound docstring pin) — the classifier's docstring
        must NAME the #138-class hand-set-label bound + its threat model. Non-trapping: it requires
        ONLY the three load-bearing concept tokens the design + CLAUDE.md gate-law use — the mechanism
        symbol (``guarded_write``, the seam a hand-set label BYPASSES), the threat-model term of art
        (``honest`` [developer], not the hostile author), and the finding CLASS (``138`` — WHEN YOU
        CANNOT CLOSE A HOLE, PIN IT) — never an exact phrasing. GREEN once the builder adds the bound
        to ``classify_tree_observed_write``'s docstring in ``_governed_contract.py`` (design step 6
        R2). ⚠ COORDINATION: that file must be in the builder's writable set (see REPORT §DECISIONS)."""
        doc = (classify_tree_observed_write.__doc__ or "").lower()
        required = {
            "guarded_write": "the mechanism — a hand-set write_guard LABEL bypasses guarded_write",
            "honest": "the threat model — the honest developer, not the hostile author",
            "138": "the accepted-bound CLASS (#138 — WHEN YOU CANNOT CLOSE A HOLE, PIN IT)",
        }
        missing = {token: why for token, why in required.items() if token not in doc}
        assert not missing, (
            "classify_tree_observed_write's docstring does NOT name the #138-class hand-set-label "
            f"accepted bound (design §10.9-A CORRECTION step 6 R2). Missing concept(s): {missing}. "
            "Add a NAMED BOUND clause: a production site that hand-sets a write_guard label WITHOUT "
            "calling guarded_write passes BOTH F5 layers — an ACCEPTED bound under this gate's threat "
            "model (the honest developer, not the hostile author — the #138 class), never closed by "
            "false positives."
        )


# =========================================================================== #
# R4 — THE PINNED ACCEPTED BOUNDS (finding #449, operator OPTION A 2026-09-02, via lead-63).
# Adversary-63a-v3's R4 hunt found TWO reach-recessions that launder past R1+R2+R3 on the reference
# build: (a) the exempt-frame single-shape pin AND the base-3 justification pin match ``WHERE scope
# IS NONE`` by SUBSTRING, so a single OR-extended seizure passes; and (c) the raw-mutation VERB-SET
# (``_raw_mutation_of_table`` + the runtime ``_mutation_verb_for_table``) is a bounded enumeration
# UPSERT/UPDATE/DELETE/REMOVE, so an INSERT/CREATE/RELATE memory seizure is invisible end-to-end.
# The operator ACCEPTED BOTH as BOUNDS in 63a: F5 is a static HONEST-DEVELOPER net (it catches the
# honest mistake at the shapes/verbs it enumerates); the substring/exotic-verb laundering is the
# #138 HOSTILE-AUTHOR class F5 explicitly does NOT defend (R2's already-named threat model). THE
# RUNTIME ROOT-FIX (verb/shape-AGNOSTIC mutation detection as a PROPERTY + a statement-scoped
# exemption of the exact adjudicated statement) is DEFERRED to 63b (task 571ef1a), its natural home.
#
# These are PIN-THE-MISS bounds (CLAUDE.md WHEN YOU CANNOT CLOSE A HOLE, PIN IT), NOT discriminating
# security pins: each asserts the bound EXISTS TODAY and carries the deliberate-DELETION instruction
# for when the 63b root-fix closes it — so the bound cannot be silently inherited nor silently
# "fixed" (finding #449). Each also carries a probe-honesty POSITIVE CONTROL proving the matcher is
# not blind, so the GREEN witness is a genuine laundering path (CLAUDE.md PKT-28 C1).
# =========================================================================== #


class TestTheAcceptedF5BoundsArePinned:
    """finding #449 (operator OPTION A) — the two adversary-63a-v3 R4 reach-recessions, pinned as
    ACCEPTED BOUNDS. GREEN at HEAD (the bounds are REAL today); each REDS the day the 63b runtime
    root-fix closes it — at which point delete the pin + the named-bound docstring it points at and
    say so. NOT a discriminating security pin: F5 is a static honest-developer net, and these are the
    #138 hostile-author holes it does not defend (design §10.9-A CORRECTION step 6 R2 threat model)."""

    def test_r4a_the_shape_leg_matches_where_scope_is_none_by_substring(self) -> None:
        r"""⚠ KNOWN ACCEPTED BOUND #449 (R4-a) — the exempt-frame single-shape pin
        (``test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation``) and the base-3
        justification pin (``test_migrate_memory_scope_updates_only_none_scope_rows``) both check the
        blessed shape by the SUBSTRING ``re.search(r"WHERE\s+scope\s+IS\s+NONE")``, not by an exact
        ``WHERE == scope IS NONE``. So a SINGLE OR-extended statement ``… WHERE scope IS NONE OR scope
        = $victim`` — ONE statement (R3 count leg passes), CONTAINING the substring (R3/base-3 shape leg
        passes) — LAUNDERS while seizing OWNED rows (adversary-63a-v3 §R4-a; the wrong build went 22
        passed / 0 failed on the full 63a-v suite). F5 is a static HONEST-DEVELOPER net; this substring
        bound is the #138 HOSTILE-AUTHOR class F5 does not defend; the runtime root-fix is 63b (task
        571ef1a). If you closed this deliberately (the 63b root-fix), DELETE this pin + the R4-a bound
        docstring on ``exempt_frame_raw_memory_mutations`` and say so."""
        # An OR-extended seizure, co-located as the frame's ONE mutation — the R3 extraction path.
        seizure_source = (
            'MEMORY_TABLE = "memory"\n\n\n'
            "async def _do_write(x):\n"
            "    await run_query(\n"
            '        f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE OR scope = $victim"\n'
            "    )\n"
        )
        seizure_entry = TreeWriteAllowlistEntry(
            site=TreeMutationSite("synthetic/pkg/r4a.py", "_do_write", "UPDATE"),
            justification="#449 R4-a bound witness — an OR-extended seizure that keeps the substring",
            pin="test_r4a_the_shape_leg_matches_where_scope_is_none_by_substring",
            frames=("_do_write",),
            exempt_name="r4a-bound",
        )
        mutations = exempt_frame_raw_memory_mutations(seizure_entry, source=seizure_source)
        # R3 COUNT leg would PASS — the seizure is ONE statement (the count leg's blind spot).
        assert len(mutations) == 1, (
            f"expected the OR-extended seizure to be ONE co-located statement; got {mutations!r}. If "
            f"the extractor changed, the #449 R4-a bound may be closing — re-adjudicate, do not "
            f"silently repair this pin."
        )
        only = mutations[0]
        # R3/base-3 SHAPE leg (the SUBSTRING matcher) still classifies the seizure as the allowlisted
        # shape — the accepted bound. The positive control below proves the matcher is NOT blind.
        assert re.search(r"WHERE\s+scope\s+IS\s+NONE", only, re.IGNORECASE), (
            "the WHERE-scope-IS-NONE SUBSTRING matcher no longer accepts an OR-extended seizure — the "
            "#449 R4-a accepted bound has been CLOSED. If you closed it deliberately (the 63b runtime "
            "root-fix: exact-shape / statement-scoped exemption), DELETE this pin + the R4-a bound "
            f"docstring on exempt_frame_raw_memory_mutations and say so. statement: {only!r}"
        )
        # PROBE-HONESTY POSITIVE CONTROL (adversary-63a-v3 §R4-a) — the substring matcher CAN see a
        # MISSING substring, so the GREEN above is a genuine laundering path, not a blind check.
        no_substring_seizure = "UPDATE memory SET scope = $scope WHERE scope = $victim"
        assert not re.search(r"WHERE\s+scope\s+IS\s+NONE", no_substring_seizure, re.IGNORECASE), (
            "the substring matcher matched a statement with NO `scope IS NONE` clause — the probe is "
            "blind, so the bound witness above is vacuous (CLAUDE.md PKT-28 C1)"
        )

    def test_r4c_the_raw_mutation_verb_set_is_a_bounded_enumeration(self) -> None:
        """⚠ KNOWN ACCEPTED BOUND #449 (R4-c) — the static extractor ``_raw_mutation_of_table`` (reused
        by the whole-tree scan AND ``exempt_frame_raw_memory_mutations``) and the runtime observer
        ``_mutation_verb_for_table`` both count only the verb-set UPSERT/UPDATE/DELETE/REMOVE. An
        ``INSERT … ON DUPLICATE KEY UPDATE`` / ``CREATE`` / ``RELATE`` memory seizure is INVISIBLE to
        BOTH: the extractor returns None (so L1/R3 never count it) and the observer returns None (so it
        is never RECORDED → deny-by-default cannot fire) — end-to-end blind (adversary-63a-v3 §R4-c;
        SurrealDB supports INSERT..ON DUPLICATE KEY UPDATE, surrealql-tests 5776). F5 is a static
        HONEST-DEVELOPER net; this verb-set bound is the #138 HOSTILE-AUTHOR class F5 does not defend;
        the runtime root-fix (mutation detection as a PROPERTY, not a verb enumeration) is 63b (task
        571ef1a). If you closed this deliberately (the 63b root-fix), DELETE this pin + the R4-c bound
        docstrings on ``_raw_mutation_of_table`` / ``_mutation_verb_for_table`` and say so."""
        from _governed_contract import _mutation_verb_for_table, _raw_mutation_of_table

        exotic = (
            "INSERT INTO memory (id, scope) VALUES ($id, 'x') ON DUPLICATE KEY UPDATE scope = 'x'",
            "CREATE type::record('memory', $id) SET scope = 'seized'",
            "RELATE $principal->owns->type::record('memory', $id)",
        )
        for statement in exotic:
            # STATIC extractor: not derived → L1/R3 never count it.
            assert _raw_mutation_of_table(statement, MEMORY_TABLE, "MEMORY_TABLE") is None, (
                f"the static extractor now counts an exotic-verb memory mutation — the #449 R4-c bound "
                f"is closing. If deliberate (63b), delete this pin + the bound docstrings: {statement!r}"
            )
            # RUNTIME observer: None → never recorded → deny-by-default cannot fire.
            assert _mutation_verb_for_table(statement, MEMORY_TABLE) is None, (
                f"the runtime observer now records an exotic-verb memory mutation — the #449 R4-c bound "
                f"is closing. If deliberate (63b), delete this pin + the bound docstrings: {statement!r}"
            )
        # PROBE-HONESTY POSITIVE CONTROL (adversary-63a-v3 §R4-c) — an IN-SET verb (UPDATE) IS seen by
        # BOTH, so the None above is a genuine verb-set miss, not a blind extractor/observer.
        in_set = "UPDATE type::record('memory', $id) SET scope = 'x'"
        assert _raw_mutation_of_table(in_set, MEMORY_TABLE, "MEMORY_TABLE") == "UPDATE", (
            "the static extractor cannot see an in-set UPDATE — the probe is blind, so the R4-c bound "
            "witness above is vacuous (CLAUDE.md PKT-28 C1)"
        )
        assert _mutation_verb_for_table(in_set, MEMORY_TABLE) == "UPDATE", (
            "the runtime observer cannot see an in-set UPDATE — the probe is blind, so the R4-c bound "
            "witness above is vacuous (CLAUDE.md PKT-28 C1)"
        )


# --------------------------------------------------------------------------- #
# helpers — synthetic sources + the migrate-UPDATE extractor + defined-test-name derivation.
# --------------------------------------------------------------------------- #

# A governed memory write via the MEMORY_TABLE constant (the idiomatic, DERIVED shape).
_FSTRING_MEMORY_UPDATE = (
    'MEMORY_TABLE = "memory"\n\n\n'
    "async def _do_write(x):\n"
    "    await _q(f\"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'\", {})\n"
)
# A SELECT-only file (no mutation — the precision control).
_SELECT_ONLY = (
    'MEMORY_TABLE = "memory"\n\n\n'
    "async def _do_read(x):\n"
    "    return await _q(f\"SELECT * FROM type::record('{MEMORY_TABLE}', $id)\", {})\n"
)
# A concatenation-assembled write (the #444 static bound — NOT derived, caught at runtime by L2b).
_CONCAT_MEMORY_UPDATE = (
    'MEMORY_TABLE = "memory"\n\n\n'
    "async def _do_write(x):\n"
    "    stmt = \"UPDATE type::record('\" + MEMORY_TABLE + \"', $id) SET scope = 'seized'\"\n"
    "    await _q(stmt, {})\n"
)


def _mkfile(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _migrate_backfill_update_statement(source: str) -> str | None:
    """The raw memory UPDATE STATEMENT string inside ``_migrate_memory_scope`` (the shape the
    allowlist justification pins). Reconstructed from the AST so it is robust to reformatting."""
    from _governed_contract import _statement_shape  # the substrate's shape reconstructor

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_migrate_memory_scope":
            for inner in ast.walk(node):
                if isinstance(inner, (ast.Constant, ast.JoinedStr)):
                    shape = _statement_shape(inner)
                    if shape and re.search(r"\bUPDATE\b.*\bSET\s+scope\b", shape, re.IGNORECASE):
                        return shape
    return None


def _defined_test_names() -> frozenset[str]:
    """Every ``def test_*`` name defined in the tests dir — DERIVED by AST (never a hand-list)."""
    tests_dir = Path(__file__).resolve().parent
    names: set[str] = set()
    for path in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                names.add(node.name)
    return frozenset(names)

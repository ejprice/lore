"""Contract for packet **58**, Scope IN 2 — the TASK-side guarded-append shell, extracted ONCE.

*Every claim in this file is scoped to the tree at ``1206233`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/plans/v2/58-supersede-reanchor.md`` Scope IN 2 (*"extract a TASK-side guarded-append
shell … that ``_transition_fragment``, the supersede stamp and the new re-anchor note ALL route
through.  Never a 4th hand-rolled clone.  Prove sharing by MUTATION"*); kickoff rulings
``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241`` §3 (the AST one-producer pin), §4
(the shell's shape — the seam packet 64a governs through ``where_conjuncts``; claim routes through it
and GAINS a ``claim`` event), §6 row "the shell", §7 items 3/4/6.  Finding **#489** ledgers the
cross-module unification (findings + tasks → one ``loremaster.store`` builder) — NOT built here; until
it is, EACH ledger module is pinned to exactly ONE producer.

At HEAD ``tasks.py`` hand-rolls the guarded shell twice (``_transition_fragment``,
``_supersede_fragment``) and ``_claim_fragment`` has no THROW at all (a losing claim commits an empty
UPDATE) — ``lore_verify loremaster.tasks.TaskLedger._guarded_append_fragment`` → ``not_found``.

⚠ ROUTING IS NOT SHARING (CLAUDE.md).  Calling the shell is necessary, not sufficient: the sharing pins
below PERTURB the shell in-suite and demand that EVERY caller's observable behaviour moves with it.  A
caller that keeps working under the perturbation is a private copy wearing the shared name.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from pathlib import Path
from typing import Any, cast

import pytest
from _reanchor_58_support import (
    ACTION_CLAIM,
    ACTION_REANCHORED,
    CLAIMANT,
    OTHER_CLAIMANT,
    WORKER,
    column,
    create,
    drive_to,
    events_of,
    ledger58,
    raw,
    successor_of,
    supersede,
    updated_at_of,
)
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_BLOCKED, STATUS_WONTFIX, TaskLedger

__all__ = ["ledger58"]

#: The shell's name — kickoff §4, and the one symbol packet 57's contract and 64a's cite.  The ONE
#: name-keyed mutation point in this file (a mutation point has a name, unavoidably).
SHELL = "_guarded_append_fragment"
#: The keyword-only parameters 64a governs through (kickoff §4: "Nothing in this signature changes
#: at 64a").  ``where_conjuncts`` is THE extension point.
SHELL_KEYWORD_ONLY = ("event", "set_parts", "params", "where_conjuncts", "preamble", "throw_message")

#: Where the one-producer scan starts: the shipped package root, DERIVED from the imported module
#: (never a hand-typed path), so the scan covers whatever tree is actually under test.
PACKAGE_ROOT = Path(importlib.import_module("loremaster").__file__ or "").parent

#: The zero-row THROW guard, as it appears in any string a producer emits.
_THROW_TOKEN = re.compile(r"\bTHROW\b")
#: The guarded WRITE a compare-and-set THROWs over.  A producer is a CAS-shell producer only when it
#: emits BOTH a THROW and an UPDATE: amendment 1's R1 closing guard (``IF (SELECT count() …) > 0
#: { THROW … }``) is a count check over the snapshot, not a guarded write, and is NOT a shell clone.
_UPDATE_TOKEN = re.compile(r"\bUPDATE\b")
#: The server-side append clause (``provenance.events += [$ev]``) as a string STATIC PART.
_APPEND_TOKEN = "+= ["
#: The zero-check inside the guard — the perturbation point of the always-THROW sharing mutation.
_ZERO_CHECK = re.compile(r"array::len\((\$\w+)\)\s*==?\s*0")


# =========================================================================== #
# THE AST ONE-PRODUCER SCAN (kickoff §3) — derived reach, checked coverage.
# =========================================================================== #


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def guarded_shell_producers(source: str) -> dict[str, dict[str, bool]]:
    """Map each guarded-CAS PRODUCER in ``source`` (emits a THROW AND an UPDATE) → ``{"appends": bool}``.

    A producer is the innermost enclosing function's qualified name (``Class.method``), or
    ``"<module>"`` for a module-level constant.  Docstrings are excluded (prose about THROW is not a
    producer).  ``appends`` records whether the SAME producer also emits the server-side append clause
    — the guarded-APPEND policy #489 names.  Reach: every function and every module-level statement
    of the source — derived, not listed.
    """
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    producers: dict[str, dict[str, bool]] = {}
    #: strings emitted OUTSIDE any function, pooled per scope ("<module>" / "Class.<class-body>"),
    #: so a constant pair split across two module-level assignments is still ONE producer.
    loose: dict[str, list[str]] = {}

    def _strings(node: ast.AST) -> list[str]:
        return [
            c.value
            for c in ast.walk(node)
            if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in docstrings
        ]

    def _record(name: str, strings: list[str]) -> None:
        if any(_THROW_TOKEN.search(s) for s in strings) and any(_UPDATE_TOKEN.search(s) for s in strings):
            producers[name] = {"appends": any(_APPEND_TOKEN in s for s in strings)}

    def _visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                _visit(child, f"{child.name}." if scope == "<module>" else f"{scope}{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _record(child.name if scope == "<module>" else f"{scope}{child.name}", _strings(child))
            else:
                key = "<module>" if scope == "<module>" else f"{scope}<class-body>"
                loose.setdefault(key, []).extend(_strings(child))

    _visit(tree, "<module>")
    for key, strings in loose.items():
        _record(key, strings)
    return producers


def _package_modules() -> list[Path]:
    return sorted(path for path in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in path.parts)


class TestTheScannerSeesAHandRolledClone:
    """GREEN at HEAD — the discriminator (kickoff §3): a scanner that cannot FIND a clone certifies
    nothing.  Synthetic sources, both spellings the tree uses."""

    CLONE_PAIR = '''
class Ledger:
    @staticmethod
    def _guarded_append_fragment(row_id, *, event):
        return [f"LET $v = (UPDATE t SET provenance.events += [$ev] WHERE x)",
                f"IF array::len($v) == 0 {{ THROW 'lost' }}"]

    @staticmethod
    def _assign_fragment(row_id, owner):
        """A docstring that says THROW must NOT count."""
        guard = f"IF array::len($a) == 0 {{ THROW '{row_id}' }}"
        return [f"LET $a = (UPDATE t SET owner = $o, provenance.events += [$e])", guard]
'''

    def test_a_second_hand_rolled_producer_is_FOUND_by_name(self) -> None:
        found = guarded_shell_producers(self.CLONE_PAIR)
        assert set(found) == {"Ledger._guarded_append_fragment", "Ledger._assign_fragment"}, found
        assert all(entry["appends"] for entry in found.values()), found

    def test_a_docstring_mentioning_THROW_is_NOT_a_producer(self) -> None:
        source = 'def f():\n    """We THROW on zero rows."""\n    return 1\n'
        assert guarded_shell_producers(source) == {}

    def test_a_module_level_THROW_constant_is_attributed_to_the_module(self) -> None:
        source = (
            '_WRITE = "LET $x = (UPDATE t SET a = 1)"\n'
            '_GUARD = "IF array::len($x) == 0 { THROW \\"x\\" }"\n'
        )
        assert set(guarded_shell_producers(source)) == {"<module>"}

    def test_a_COUNT_guard_with_no_guarded_UPDATE_is_NOT_a_shell_producer(self) -> None:
        """Amendment 1 R1's closing guard — a snapshot count check, not a CAS over a write."""
        source = (
            "def closing():\n"
            "    return \"IF (SELECT count() FROM t WHERE b CONTAINS $o GROUP ALL)[0].count > 0"
            " { THROW 'straggler' }\"\n"
        )
        assert guarded_shell_producers(source) == {}


class TestEachLedgerModuleHasExactlyONEGuardedAppendProducer:
    """RED at HEAD for ``tasks.py`` (two producers: ``_transition_fragment`` + ``_supersede_fragment``).

    ∀ modules of the shipped package (DERIVED by walking ``PACKAGE_ROOT``): a module whose guarded
    THROW producers include one that also APPENDS server-side is a *guarded-append ledger* (#489's
    policy class), and EVERY THROW producer in it must be the module's ONE shell.  Coverage is CHECKED:
    the derived class must include both known ledgers — a scanner that stops seeing them reddens.
    """

    def _ledger_modules(self) -> dict[str, dict[str, dict[str, bool]]]:
        found: dict[str, dict[str, dict[str, bool]]] = {}
        for path in _package_modules():
            producers = guarded_shell_producers(path.read_text(encoding="utf-8"))
            if any(entry["appends"] for entry in producers.values()):
                found[str(path.relative_to(PACKAGE_ROOT))] = producers
        return found

    def test_the_derived_class_covers_both_known_ledgers(self) -> None:
        modules = self._ledger_modules()
        assert {"tasks.py", "findings.py"} <= set(modules), (
            f"the guarded-append scan found {sorted(modules)} — it no longer sees the task and finding "
            f"ledgers, so its ∀ verdict below covers nothing (reach is a CHECKED variable)"
        )

    def test_every_guarded_append_ledger_has_ONE_producer(self) -> None:
        offenders = {
            module: sorted(producers)
            for module, producers in self._ledger_modules().items()
            if len(producers) != 1
        }
        assert not offenders, (
            f"a guarded-append ledger module carries MORE THAN ONE THROW-guard producer: {offenders}. "
            f"ONE IMPLEMENTATION (#102; kickoff §3; #489): route every guarded write through the "
            f"module's `{SHELL}` — a second producer is a 4th hand-rolled clone. If a THIRD ledger now "
            f"needs one, that is #489's trigger: unify into loremaster.store, do not clone"
        )

    def test_the_task_ledgers_one_producer_IS_the_shell(self) -> None:
        producers = guarded_shell_producers((PACKAGE_ROOT / "tasks.py").read_text(encoding="utf-8"))
        assert set(producers) == {f"TaskLedger.{SHELL}"}, (
            f"tasks.py THROW-guard producers = {sorted(producers)}; allowed = exactly "
            f"{{TaskLedger.{SHELL}}} (allowlist the safe)"
        )


# =========================================================================== #
# THE SHELL'S SHAPE — the seam 64a governs (kickoff §4).
# =========================================================================== #


class TestTheShellIsTheSeam64aGoverns:
    """RED at HEAD (``not_found``)."""

    def test_the_signature_carries_the_keyword_only_extension_points(self) -> None:
        shell = getattr(TaskLedger, SHELL)
        parameters = inspect.signature(shell).parameters
        missing = [name for name in SHELL_KEYWORD_ONLY if name not in parameters]
        assert not missing, f"{SHELL} lacks {missing} (kickoff §4 signature)"
        positional = [
            name for name, p in parameters.items()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and name not in ("self", "cls")
        ]
        assert len(positional) == 1, f"exactly one positional (the row id) — got {positional}"
        wrong_kind = [
            name for name in SHELL_KEYWORD_ONLY if parameters[name].kind is not inspect.Parameter.KEYWORD_ONLY
        ]
        assert not wrong_kind, f"must be KEYWORD-ONLY so 64a can add a conjunct without a break: {wrong_kind}"

    async def test_where_conjuncts_are_each_PARENTHESISED_and_AND_joined(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """Semantic, not textual: conjunct A is an ``OR`` that is TRUE, conjunct B is FALSE.  Correct
        ``(A) AND (B)`` matches nothing → THROW → no write.  An unparenthesised join
        (``… OR … AND …``) binds the OR loosest and MATCHES — 64a's guard would be bypassable."""
        ledger, _env = ledger58
        task_id = await create(ledger, "a row the shell addresses")
        before = await events_of(ledger, task_id)
        fragment = getattr(TaskLedger, SHELL)(
            task_id,
            event={"actor": WORKER, "action": "probe58", "at": "2026-09-26T00:00:00+00:00"},
            set_parts=["subject = $w58_subject"],
            params={"w58_subject": "WRITTEN", "w58_open": "open", "w58_nope": "no-such-status",
                    "w58_ghost": "nobody-58"},
            where_conjuncts=["status = $w58_open OR status = $w58_nope", "owner = $w58_ghost"],
            throw_message="w58 guard matched zero rows",
        )
        with pytest.raises(Exception):  # noqa: B017, PT011 - the rollback is the assertion
            await ledger._apply([fragment])  # noqa: SLF001
        assert (await ledger.get_task(task_id)).subject != "WRITTEN"
        assert await events_of(ledger, task_id) == before

        control = getattr(TaskLedger, SHELL)(
            task_id,
            event={"actor": WORKER, "action": "probe58", "at": "2026-09-26T00:00:00+00:00"},
            set_parts=["subject = $w58_subject"],
            params={"w58_subject": "WRITTEN", "w58_open": "open", "w58_nope": "no-such-status"},
            where_conjuncts=["status = $w58_open OR status = $w58_nope", "owner IS NONE"],
            throw_message="w58 guard matched zero rows",
        )
        await ledger._apply([control])  # noqa: SLF001
        after = await ledger.get_task(task_id)
        assert after.subject == "WRITTEN", "CONTROL: a matching guard must write"
        events = await events_of(ledger, task_id)
        assert len(events) == len(before) + 1 and events[-1]["action"] == "probe58"
        assert await updated_at_of(ledger, task_id) is not None, "the shell stamps updated_at"

    async def test_event_None_appends_NOTHING(self, ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "a row")
        before = await events_of(ledger, task_id)
        fragment = getattr(TaskLedger, SHELL)(
            task_id, event=None, set_parts=["subject = $w58n_subject"],
            params={"w58n_subject": "renamed"}, where_conjuncts=[], throw_message="w58n zero",
        )
        await ledger._apply([fragment])  # noqa: SLF001
        assert (await ledger.get_task(task_id)).subject == "renamed"
        assert await events_of(ledger, task_id) == before


# =========================================================================== #
# SHARING BY MUTATION (kickoff §4 rider i) — in-suite, per caller.
# =========================================================================== #


class _ShellPerturbation:
    """Wrap the shell; perturb ONLY the calls whose ``event['action']`` is ``target_action``.

    Selective, so each caller is proven INDIVIDUALLY: a caller that does not route through the shell
    is never seen, its behaviour never moves, and its pin reddens.  Fails CLOSED: ``seen`` records every
    action the wrapper observed, and the zero-check rewrite asserts it found the guard to perturb.
    """

    def __init__(self, target_action: str, mode: str) -> None:
        self.target_action = target_action
        self.mode = mode
        self.seen: list[str | None] = []
        self.perturbed = 0
        self._original = getattr(TaskLedger, SHELL)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from loremaster.store._txn import TxnFragment

        event = kwargs.get("event")
        action = event.get("action") if isinstance(event, dict) else None
        self.seen.append(action)
        if action != self.target_action:
            return self._original(*args, **kwargs)
        if self.mode == "mark_event":
            kwargs["event"] = {**cast(dict[str, Any], event), "mutation58": True}
            self.perturbed += 1
            return self._original(*args, **kwargs)
        fragment = self._original(*args, **kwargs)
        rewritten = [_ZERO_CHECK.sub(r"array::len(\1) >= 0", s) for s in fragment.statements]
        assert rewritten != list(fragment.statements), (
            "the always-THROW perturbation found no `array::len($x) == 0` guard in the shell's output "
            "— the mutation point moved; update _ZERO_CHECK (a naming mismatch, not a behaviour one)"
        )
        self.perturbed += 1
        return TxnFragment(statements=rewritten, params=fragment.params)


def _install(monkeypatch: pytest.MonkeyPatch, perturbation: _ShellPerturbation) -> None:
    monkeypatch.setattr(TaskLedger, SHELL, staticmethod(perturbation), raising=True)


class TestSharingIsProvenByMutationALWAYSTHROW:
    """RED at HEAD.  Perturb the shell's zero-check so it THROWs on SUCCESS too, for ONE caller's
    action at a time: that caller's LEGAL write must now FAIL.  A private copy keeps succeeding."""

    async def test_TRANSITION_routes_through_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "a row to block")
        perturbation = _ShellPerturbation("transition", "always_throw")
        _install(monkeypatch, perturbation)
        with pytest.raises(Exception):  # noqa: B017, PT011
            await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
        assert perturbation.perturbed >= 1, f"transition never reached the shell (saw {perturbation.seen})"
        assert (await ledger.get_task(task_id)).status != STATUS_BLOCKED

    async def test_the_SUPERSEDE_STAMP_routes_through_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "a row to reframe, no dependents")
        perturbation = _ShellPerturbation("supersede", "always_throw")
        _install(monkeypatch, perturbation)
        with pytest.raises(Exception):  # noqa: B017, PT011
            await supersede(ledger, task_id)
        assert perturbation.perturbed >= 1, f"the stamp never reached the shell (saw {perturbation.seen})"
        assert (await ledger.get_task(task_id)).superseded_by is None

    async def test_the_REANCHOR_routes_through_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        perturbation = _ShellPerturbation(ACTION_REANCHORED, "always_throw")
        _install(monkeypatch, perturbation)
        with pytest.raises(Exception):  # noqa: B017, PT011
            await supersede(ledger, old)
        assert perturbation.perturbed >= 1, f"the re-anchor never reached the shell (saw {perturbation.seen})"
        assert await column(ledger, dependent) == [old] and (await ledger.get_task(old)).superseded_by is None

    async def test_CLAIM_routes_through_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "a claimable row")
        perturbation = _ShellPerturbation(ACTION_CLAIM, "always_throw")
        _install(monkeypatch, perturbation)
        won = False
        try:
            won = (await ledger.claim_task(task_id, CLAIMANT)).claimed
        except Exception:  # noqa: BLE001 - raising IS a non-win (B6: an inexplicable rollback is LOUD)
            won = False
        assert perturbation.perturbed >= 1, f"claim never reached the shell (saw {perturbation.seen})"
        assert not won and (await ledger.get_task(task_id)).owner is None, (
            "a claim of a perfectly claimable row must NOT WIN when the shared guard always throws — "
            "else the claim's CAS is a private copy (kickoff §4: claim routes, P58 item 2). Raising "
            "or losing are both non-wins; a correct build RAISES here (the row is still claimable, so "
            "the rollback is inexplicable — TestAClaimThatFailsForANonCASReasonIsLOUD)"
        )

    async def test_CONTROL_an_unperturbed_action_is_untouched(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The wrapper itself must not break callers it does not target (else every leg above passes
        for the wrapper's reason)."""
        ledger, _env = ledger58
        task_id = await create(ledger, "a row")
        _install(monkeypatch, _ShellPerturbation("no-such-action-58", "always_throw"))
        await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
        assert (await ledger.claim_task(await create(ledger, "claimable"), CLAIMANT)).claimed
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        successor = successor_of(await supersede(ledger, old))
        assert await column(ledger, dependent) == [successor]


class TestSharingIsProvenByMutationTHEAPPEND:
    """RED at HEAD.  Mark every event the shell appends: each event-bearing caller's NEW event must
    carry the mark — an event appended beside the shell (routing without sharing) does not."""

    async def test_transition_stamp_claim_and_reanchor_events_all_come_from_the_shell(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        transitioned = await create(ledger, "transition me")
        claimed = await create(ledger, "claim me")
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        rows = {
            "transition": transitioned,
            ACTION_CLAIM: claimed,
            "supersede": old,
            ACTION_REANCHORED: dependent,
        }
        before = {action: await events_of(ledger, task_id) for action, task_id in rows.items()}
        original = getattr(TaskLedger, SHELL)
        marked: list[str] = []

        def _mark(*args: Any, **kwargs: Any) -> Any:
            event = kwargs.get("event")
            if isinstance(event, dict):
                kwargs["event"] = {**cast(dict[str, Any], event), "mutation58": True}
                marked.append(str(event.get("action")))
            return original(*args, **kwargs)

        monkeypatch.setattr(TaskLedger, SHELL, staticmethod(_mark), raising=True)
        await ledger.transition(transitioned, STATUS_BLOCKED, actor=WORKER)
        assert (await ledger.claim_task(claimed, CLAIMANT)).claimed
        await supersede(ledger, old)
        for action, task_id in rows.items():
            new = (await events_of(ledger, task_id))[len(before[action]):]
            assert len(new) == 1 and new[0].get("mutation58") is True, (
                f"the {action!r} event on {task_id} was not appended through the shell (new events: "
                f"{new}; the shell saw {marked}). A caller that appends its own event — or a second "
                f"one — beside the shell is ROUTING without SHARING"
            )


    async def test_the_BOOT_HEAL_note_comes_from_the_shell_too(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Amendment 1 R2: the heal uses *"the SAME re-anchor fragment … through the ONE shell"*."""
        from _reanchor_58_support import new_ledger, raw_relate, raw_seed_row

        ledger, env = ledger58
        head = await create(ledger, "the successor a legacy blocker moved to")
        legacy = "sharedhealblocker00000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        straggler = "sharedhealstraggler000000000000"
        await raw_seed_row(ledger, straggler, blocked_by=[legacy])
        await raw_relate(ledger, legacy, straggler)
        original = getattr(TaskLedger, SHELL)

        def _mark(*args: Any, **kwargs: Any) -> Any:
            event = kwargs.get("event")
            if isinstance(event, dict):
                kwargs["event"] = {**event, "mutation58": True}
            return original(*args, **kwargs)

        monkeypatch.setattr(TaskLedger, SHELL, staticmethod(_mark), raising=True)
        booted = new_ledger(env)
        try:
            await booted.ensure_ready()
        finally:
            await booted.close()
        assert await column(ledger, straggler) == [head], "fixture: the boot did not heal the straggler"
        notes = [e for e in await events_of(ledger, straggler) if e.get("action") == ACTION_REANCHORED]
        assert len(notes) == 1 and notes[0].get("mutation58") is True, (
            f"the boot heal's note was not appended through the shell: {notes}"
        )


# =========================================================================== #
# CLAIM THROUGH THE SHELL — the served result is byte-unchanged (kickoff §4, §7.3/7.4).
# =========================================================================== #


class TestClaimWinGainsAnEventLossWritesNothing:
    """RED at HEAD for the win-event leg (a claim writes no provenance event today)."""

    async def test_a_WIN_appends_ONE_claim_event_naming_the_owner_and_stamps_updated_at(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "claimable")
        before = await events_of(ledger, task_id)
        result = await ledger.claim_task(task_id, OTHER_CLAIMANT)
        assert result.claimed and result.task.owner == OTHER_CLAIMANT
        new = (await events_of(ledger, task_id))[len(before):]
        assert len(new) == 1, new
        assert new[0].get("action") == ACTION_CLAIM and new[0].get("actor") == OTHER_CLAIMANT, new
        assert await updated_at_of(ledger, task_id) is not None

    @pytest.mark.parametrize("shape", ["owned", "blocked", "superseded", "wontfix"])
    async def test_a_LOSS_is_a_RESULT_with_ZERO_writes_and_NO_event(
        self, ledger58: tuple[TaskLedger, SurrealEnv], shape: str
    ) -> None:
        """GREEN at HEAD (preserved-with-pin, §7.4): the loss mechanism CHANGES (THROW + rollback
        instead of an empty UPDATE) but the served ``ClaimResult`` and the zero-write fact must not."""
        ledger, _env = ledger58
        if shape == "owned":
            task_id = await create(ledger, "held")
            assert (await ledger.claim_task(task_id, OTHER_CLAIMANT)).claimed
        elif shape == "blocked":
            task_id = await create(ledger, "blocked", [await create(ledger, "an open blocker")])
        elif shape == "superseded":
            task_id = await create(ledger, "to be reframed")
            await supersede(ledger, task_id)
        else:
            task_id = await create(ledger, "abandoned")
            await drive_to(ledger, task_id, STATUS_WONTFIX)
        row_before = await raw(ledger, f"SELECT * FROM type::record('{TASK_TABLE}', $id)", {"id": task_id})
        result = await ledger.claim_task(task_id, CLAIMANT)
        assert result.claimed is False, f"{shape}: a loss must be a RESULT, never an exception"
        assert result.task.id == task_id
        row_after = await raw(ledger, f"SELECT * FROM type::record('{TASK_TABLE}', $id)", {"id": task_id})
        assert row_after == row_before, (
            f"{shape}: a losing claim WROTE to the row: {row_before} → {row_after}"
        )


class TestAClaimThatFailsForANonCASReasonIsLOUD:
    """GREEN at HEAD (a store rejection inside the claim transaction propagates today).  Removed-behaviour
    item B6 (``REPORT-contract-58.md`` §DUAL): routing claim through the shell makes a LOSS a THROW +
    rollback, and ``claim_task`` must now CATCH a store rejection to serve ``ClaimResult(False)``.  A
    catch that swallows EVERY rollback turns a broken claim path into *"not claimed: … unowned but not
    claimable (status open)"* for a row that IS claimable — a false clear (TRUST, leg 2).  The rollback
    is injected server-side (a ``DEFINE EVENT`` that THROWs on the claim's UPDATE of a claimable row)."""

    async def test_an_injected_rollback_on_a_CLAIMABLE_row_raises_rather_than_losing(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "claimable, but the claim write will be refused")
        await raw(
            ledger,
            f"DEFINE EVENT inject58c ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
            f"record::id($after.id) = '{task_id}' THEN {{ THROW 'injected-58-claim' }}",
        )
        with pytest.raises(Exception) as caught:  # noqa: PT011 - LOUD is the property, not the class
            await ledger.claim_task(task_id, CLAIMANT)
        assert not isinstance(caught.value, AssertionError)
        await raw(ledger, f"REMOVE EVENT inject58c ON TABLE {TASK_TABLE}")
        assert (await ledger.claim_task(task_id, CLAIMANT)).claimed, (
            "CONTROL: without the injection the same row IS claimable — so the failure above was not a "
            "legitimate loss, and serving it as one would have been a false clear"
        )


class TestUpdatedAtIsStampedByTheShellForEveryCaller:
    """RED at HEAD for the re-anchor leg only (the other three stamp today — preserved)."""

    async def test_transition_claim_stamp_and_reanchor_all_stamp_updated_at(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        transitioned = await create(ledger, "t")
        claimed = await create(ledger, "c")
        old = await create(ledger, "X")
        dependent = await create(ledger, "Y", [old])
        await ledger.transition(transitioned, STATUS_BLOCKED, actor=WORKER)
        await ledger.claim_task(claimed, CLAIMANT)
        await supersede(ledger, old)
        stamped = (("transition", transitioned), ("claim", claimed), ("stamp", old), ("re-anchor", dependent))
        for label, task_id in stamped:
            assert await updated_at_of(ledger, task_id) is not None, f"{label} did not stamp updated_at"


class TestParamNamesDoNotCollideAcrossComposedShells:
    """RED at HEAD (no re-anchor fragments exist to collide).  Kickoff §4 rider iii: N re-anchors + the
    stamp + the CREATE + the successor RELATEs compose into ONE transaction — ``compose`` refuses a
    param collision loudly, so a green supersede of N≥3 with K≥2 IS the proof.  The spy asserts the
    composition really contained ≥ N+1 shell outputs (so the pin is not green because the shell was
    bypassed)."""

    async def test_three_reanchors_the_stamp_and_two_successor_edges_compose(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, _env = ledger58
        old = await create(ledger, "X")
        dependents = [await create(ledger, f"Y{i}", [old]) for i in range(3)]
        blockers = [await create(ledger, f"B{i}") for i in range(2)]
        calls: list[str | None] = []
        original = getattr(TaskLedger, SHELL)

        def _count(*args: Any, **kwargs: Any) -> Any:
            event = kwargs.get("event")
            calls.append(event.get("action") if isinstance(event, dict) else None)
            return original(*args, **kwargs)

        monkeypatch.setattr(TaskLedger, SHELL, staticmethod(_count), raising=True)
        successor = successor_of(await supersede(ledger, old, blocked_by=blockers))
        assert calls.count(ACTION_REANCHORED) == 3 and calls.count("supersede") == 1, calls
        for task_id in dependents:
            assert await column(ledger, task_id) == [successor]


class TestTheClaimCASStillDecidesOnlyOnce:
    """GREEN at HEAD — required-green (the claim CAS): ≥8-way racers, exactly one winner, and the
    winner's ``claim`` event is the ONLY one appended (a rolled-back loser appends nothing)."""

    async def test_eight_way_claim_race_one_winner_one_event(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        import asyncio

        from _reanchor_58_support import new_ledger

        ledger, env = ledger58
        task_id = await create(ledger, "contended")
        racers = [new_ledger(env) for _ in range(8)]
        try:
            results = await asyncio.gather(
                *(racer.claim_task(task_id, f"racer-{index}") for index, racer in enumerate(racers))
            )
        finally:
            for racer in racers:
                await racer.close()
        winners = [r for r in results if r.claimed]
        assert len(winners) == 1, [r.claimed for r in results]
        claim_events = [e for e in await events_of(ledger, task_id) if e.get("action") == ACTION_CLAIM]
        assert len(claim_events) <= 1, f"a losing racer appended a claim event: {claim_events}"

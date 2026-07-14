"""Provenance guard for a scratch copy of this repo — finding #140.

It answers ONE question and refuses to guess: does ``import loremaster`` — in the
interpreter this script is *run with* — resolve to code INSIDE the scratch tree, or to
the ORIGINAL checkout?

That question is not rhetorical.  A ``cp -a`` copy of this repo **never runs its own
production code**: the copied ``.venv`` carries editable installs
(``_editable_impl_loremaster.pth`` &c.) whose contents are ABSOLUTE ORIGINAL PATHS, so
``import loremaster`` in the copy resolves to the original checkout — and ``cp -a``
preserves mtimes, so the copied ``__pycache__`` is reused and its bytecode carries the
ORIGINAL ``co_filename`` too.  The copy *looks* isolated.  ``git diff`` shows your
mutation.  The tests run.  They are simply not running your code.

Run it with the SCRATCH COPY'S OWN interpreter (this is the whole point — the guard's
code comes from the original repo, but the *interpreter* is the copy's, so what it
observes is exactly what the copy will run)::

    <scratch>/.venv/bin/python scripts/scratch_provenance.py <scratch>

Exit 0 with a per-member receipt when every workspace member resolves inside
``<scratch>``.  Exit non-zero, loudly, otherwise.  ``scripts/scratch_copy.sh`` is the
front door: it makes the copy, installs it, and then calls this.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

# The workspace members whose code a scratch copy must actually be running.  Mirrors
# ``[tool.uv.workspace] members`` in pyproject.toml.
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")

# Printed on ANY failure.  The wording is load-bearing: an agent that sees this must
# understand that the tree it just "isolated" is grading the original.
POISON_HEADLINE = (
    "SCRATCH COPY IS POISONED — IT IS GRADING THE ORIGINAL TREE (finding #140).\n"
    "Do NOT trust any mutation proof, reference build, or test run made in it."
)


@dataclass(frozen=True)
class MemberProvenance:
    """Where one workspace member's code actually came from, as observed by an import.

    ``module_file`` is the module's ``__file__``.  ``None`` is NOT a neutral value: it
    means the name resolved to an implicit *namespace package* (the bare member
    directory) rather than the real package — i.e. nothing of that member's production
    code is loaded at all.
    """

    name: str
    module_file: str | None = None
    import_error: str | None = None


class ProvenanceGuard:
    """Decides whether a scratch tree actually runs its OWN workspace code.

    The verdict is deliberately separated from the import that produces the evidence, so
    the decision rule is testable without a 108M virtualenv in the loop.
    """

    def __init__(self, scratch_root: Path) -> None:
        self.scratch_root = scratch_root.resolve()

    def verdict(self, member: MemberProvenance) -> str | None:
        """Return ``None`` when the member's provenance is honest, else the reason it is not."""
        if member.import_error is not None:
            return (
                f"{member.name} is NOT IMPORTABLE in this interpreter ({member.import_error}). "
                f"The copy has no working install — run `uv sync --all-packages` inside it."
            )
        if member.module_file is None:
            return (
                f"{member.name}.__file__ is None — it imported as an implicit NAMESPACE PACKAGE "
                f"(the bare member directory), not the real package, so NONE of its production "
                f"code is loaded. The copy has no editable install: run `uv sync --all-packages` "
                f"inside it (plain `uv sync` does NOT install the workspace members)."
            )
        resolved = Path(member.module_file).resolve()
        if not resolved.is_relative_to(self.scratch_root):
            return (
                f"{member.name} resolves to {resolved} — OUTSIDE the scratch tree "
                f"{self.scratch_root}. The copy is running the ORIGINAL checkout's code. A stale "
                f"`.venv` (its editable .pth files name absolute ORIGINAL paths) or a PYTHONPATH / "
                f"VIRTUAL_ENV naming the original tree will do this."
            )
        return None

    def audit(
        self,
        resolver: Callable[[str], MemberProvenance],
        members: Sequence[str] = WORKSPACE_MEMBERS,
    ) -> tuple[list[str], list[MemberProvenance]]:
        """Audit every member, returning ``(failure reasons, honest receipts)``.

        Every member is audited even after the first failure: a partial answer would let
        an agent "fix" one member and re-run into the next surprise.
        """
        failures: list[str] = []
        receipts: list[MemberProvenance] = []
        for name in members:
            member = resolver(name)
            reason = self.verdict(member)
            if reason is None:
                receipts.append(member)
            else:
                failures.append(reason)
        return failures, receipts


def import_member(name: str) -> MemberProvenance:
    """Import a workspace member in THIS interpreter and report where it came from."""
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 — any import failure is a provenance failure
        return MemberProvenance(name=name, import_error=f"{type(exc).__name__}: {exc}")
    return MemberProvenance(name=name, module_file=getattr(module, "__file__", None))


def main(argv: Sequence[str] | None = None) -> int:
    """Audit ``<scratch_root>`` and return a process exit code (0 honest, 1 poisoned)."""
    parser = argparse.ArgumentParser(
        prog="scratch_provenance.py",
        description="Assert that a scratch copy of this repo runs its OWN code (finding #140).",
    )
    parser.add_argument("scratch_root", type=Path, help="absolute path of the scratch copy")
    args = parser.parse_args(argv)

    scratch_root = args.scratch_root.resolve()

    # Emulate what the agent's OWN runs will see: `uv run pytest` / `python -c` from the
    # copy root put the copy root on sys.path.  Inserting it here means the guard resolves
    # imports the same way the agent's work will — it can never bless a path the agent's
    # own run would not take.
    sys.path.insert(0, str(scratch_root))

    failures, receipts = ProvenanceGuard(scratch_root).audit(import_member)

    if failures:
        print(POISON_HEADLINE, file=sys.stderr)
        for reason in failures:
            print(f"  x {reason}", file=sys.stderr)
        return 1

    for receipt in receipts:
        print(f"  {receipt.name:<11} -> {receipt.module_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

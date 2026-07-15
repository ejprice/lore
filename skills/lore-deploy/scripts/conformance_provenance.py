#!/usr/bin/env python3
"""Conformance provenance guard — finding #139 (the same root as #140/#131/#107).

The conformance harness runs the BAKED test suite INSIDE the deployed image against
the ``:ro`` ``/workspace`` mount of this repo. The one trap it exists to close: a test
run that imports the MOUNTED source instead of the BAKED artifact proves the *recipe*,
never the *cake*. A green suite over the mount is worse than a red one — it certifies
code the deployed container does not run.

This guard answers ONE question per workspace member and refuses to guess: does
``import <member>`` — in the interpreter this guard is *run with* — resolve to code
BAKED into the image (``/app/...`` editable OR site-packages), or to the ``:ro``
``/workspace`` MOUNT?

It is the exact INVERSE of ``scripts/scratch_provenance.py`` (finding #140), which asks
"is this INSIDE the scratch tree?"; here the honest answer is "NOT under the mount".
That sibling's shape is the model — ``MemberProvenance`` / ``ProvenanceGuard.audit`` /
``import_member`` — but this module is DELIBERATELY SELF-CONTAINED and must not import
it (design doc LAYOUT: a skill importing repo-root ``scripts/`` is fragile). ``verdict``
resolves ``__file__`` BEFORE comparing — ``.resolve()`` then ``is_relative_to`` — because
``__file__`` is not trustworthy as written (a ``..`` segment or a symlink can spell a
mount path non-canonically); that is the whole reason #140 exists.

Unlike the sibling, this guard NEVER manipulates ``sys.path``: it imports each member as
the baked interpreter would, so a ``PYTHONPATH=/workspace/...`` that forces an import to
the mount is DETECTED, not laundered away.

Run inside the container with the baked interpreter::

    /app/.venv/bin/python \\
      /workspace/skills/lore-deploy/scripts/conformance_provenance.py --mount-root /workspace

Exit 0 with a per-member receipt when every member is baked; exit non-zero, loudly, with
a headline that NAMES the mount, otherwise.

To DEMONSTRATE the gate is real (the in-container mutation proof), force an import to the
mount and confirm this guard refuses. ``PYTHONPATH`` must name the MEMBER directory, NOT
the repo root: ``PYTHONPATH=/workspace/loremaster`` shadows the baked ``loremaster``, but
``PYTHONPATH=/workspace`` does NOT (the image's editable meta-path finder resolves the
member to ``/app`` before ``PathFinder`` consults ``PYTHONPATH``, so the run passes and a
future engineer would wrongly cry "theatre"). The durable pin
(``test_conformance_provenance.py``) constructs a ``/workspace`` ``__file__`` directly and
is depth-independent; only this informal re-run recipe has the depth footgun.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

# The three uv-workspace members whose code the conformance run must prove it is actually
# running. Mirrors ``[tool.uv.workspace] members`` in the root pyproject.toml.
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")

# The deploy topology binds the project tree read-only at /workspace (design doc
# "In-container run topology"). A parameter, not a hardcoded literal, so the guard is
# testable off a non-default mount and future-proof.
DEFAULT_MOUNT_ROOT = "/workspace"

# Printed on ANY failure. The wording is load-bearing: an engineer who sees this must
# understand that a green suite here would certify code the container does not run.
# Mirrors ``scratch_provenance.POISON_HEADLINE``, inverted for the #139 direction.
CONFORMANCE_FAILURE_HEADLINE = (
    "CONFORMANCE RUN IS GRADING THE WRONG CODE — a workspace member did NOT resolve to "
    "the BAKED artifact (finding #139).\n"
    "Do NOT trust this suite run: a green result over the :ro /workspace mount certifies "
    "code the deployed container does not run."
)


@dataclass(frozen=True)
class MemberProvenance:
    """Where one workspace member's code actually came from, as observed by an import.

    ``module_file`` is the module's ``__file__``. ``None`` is NOT a neutral value: it
    means the name resolved to an implicit *namespace package* (the bare member
    directory) rather than the real package — i.e. nothing of that member's production
    code is loaded at all.
    """

    name: str
    module_file: str | None = None
    import_error: str | None = None


class ConformanceGuard:
    """Decides whether an in-image test run actually imports its OWN BAKED workspace code.

    The verdict is deliberately separated from the import that produces the evidence, so
    the decision rule is testable without a container / interpreter in the loop.
    """

    def __init__(self, mount_root: Path) -> None:
        self.mount_root = mount_root.resolve()

    def verdict(self, member: MemberProvenance) -> str | None:
        """Return ``None`` when the member's provenance is honest, else the reason it is not.

        HONEST iff the member imported (no ``import_error``), loaded real code
        (``module_file`` is not ``None``), and that file — RESOLVED — is NOT under the
        ``:ro`` mount. A member resolving under the mount is grading the source, which is
        the #139 defect; the refusal NAMES the mount so the operator knows why.
        """
        if member.import_error is not None:
            return (
                f"{member.name} is NOT IMPORTABLE in the image interpreter "
                f"({member.import_error}). The baked artifact is broken — none of the "
                f"member's production code loaded, so the suite would run against nothing."
            )
        if member.module_file is None:
            return (
                f"{member.name}.__file__ is None — it imported as an implicit NAMESPACE "
                f"PACKAGE (the bare member directory), not the real package, so NONE of its "
                f"production code is loaded. The image was built without installing the "
                f"workspace members (`uv sync --all-packages` / `--locked`)."
            )
        resolved = Path(member.module_file).resolve()
        if resolved.is_relative_to(self.mount_root):
            return (
                f"{member.name} resolves to {resolved} — UNDER the read-only mount "
                f"{self.mount_root}. The in-image test run is grading the MOUNTED source, "
                f"not the BAKED artifact (finding #139): a green suite here certifies code "
                f"the deployed container does not run. A PYTHONPATH naming the mount, or an "
                f"image that never baked the members, will do this."
            )
        return None

    def audit(
        self,
        resolver: Callable[[str], MemberProvenance],
        members: Sequence[str] = WORKSPACE_MEMBERS,
    ) -> tuple[list[str], list[MemberProvenance]]:
        """Audit every member, returning ``(failure reasons, honest receipts)``.

        Every member is audited even after the first failure: a partial answer would let
        an operator "fix" one member and re-run straight into the next surprise. Each
        rejected member is NAMED in its failure reason; no input vanishes silently.
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
    """Import a workspace member in THIS interpreter and report where it came from.

    Never manipulates ``sys.path`` — the whole point is to observe exactly what the baked
    interpreter resolves ``import <name>`` to, so a mount-shadowing PYTHONPATH is detected
    rather than papered over.
    """
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 — any import failure is a provenance failure
        return MemberProvenance(name=name, import_error=f"{type(exc).__name__}: {exc}")
    return MemberProvenance(name=name, module_file=getattr(module, "__file__", None))


def main(argv: Sequence[str] | None = None) -> int:
    """Audit every workspace member against ``--mount-root``; 0 all-baked, non-zero + loud.

    Drives the audit through the module-level :func:`import_member` (so a test can
    monkeypatch it and never touch a real container). On any failure it prints a loud
    headline plus each named reason to stderr and returns 1; the exit binds to ANY
    rejection cause (mount hit, namespace package, or import error), not only a mount hit.
    """
    parser = argparse.ArgumentParser(
        prog="conformance_provenance.py",
        description=(
            "Assert an in-image test run imports the BAKED workspace members, not the "
            ":ro /workspace mount (finding #139)."
        ),
    )
    parser.add_argument(
        "--mount-root",
        type=Path,
        default=Path(DEFAULT_MOUNT_ROOT),
        help=f"the read-only project mount root (default {DEFAULT_MOUNT_ROOT}).",
    )
    args = parser.parse_args(argv)

    failures, receipts = ConformanceGuard(args.mount_root).audit(import_member)

    if failures:
        print(CONFORMANCE_FAILURE_HEADLINE, file=sys.stderr)
        for reason in failures:
            print(f"  x {reason}", file=sys.stderr)
        return 1

    for receipt in receipts:
        print(f"  {receipt.name:<11} -> {receipt.module_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

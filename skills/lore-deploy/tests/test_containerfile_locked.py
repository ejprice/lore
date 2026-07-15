"""Contract — packet 01a §D1: the #141 lock regression pin.

#141: the old ``uv pip install ./members`` in the Containerfile resolved dependencies
FRESH from the index and DRIFTED from ``uv.lock`` — measured 2026-07-15, the image shipped
mcp/starlette/uvicorn/sqlglot NEWER than the locked closure the suite tested. The fix
(commit c90df55) installs via ``uv sync --locked``, which mirrors the developer's own
``uv sync`` byte-for-byte and FAILS the build if the lock is stale.

This pin is the standing-law instrument for that audit-caught class (repo CLAUDE.md: "every
audit-caught defect CLASS becomes a repo-local invariant test"). It is GREEN today — a
REGRESSION guard, not a red-until-built pin — and goes RED the day someone reintroduces the
fresh-resolve.

The check reads only the Containerfile's INSTRUCTION lines: comment-only lines are stripped,
because the string ``uv pip install`` legitimately appears in the file's COMMENTS (the ones
that explain why it was retired). A bare substring scan over the whole file would false-fail
on its own documentation.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# skills/lore-deploy/tests/<this file> -> repo root (mirrors test_workspace_probe.py).
REPO_ROOT = Path(__file__).resolve().parents[3]
CONTAINERFILE = REPO_ROOT / "Containerfile"

# The retired, drift-prone install verb (#141). A revert reintroduces this token in a RUN
# line; the comments that explain its retirement are stripped before the check.
_DRIFTING_INSTALL = "uv pip install"
# The locked install the fix mandates: installs the EXACT uv.lock closure, fails on a stale lock.
_LOCKED_INSTALL = "uv sync --locked"


def _instruction_text() -> str:
    """The Containerfile with comment-only lines removed.

    Dockerfile ``#`` comments are full-line only (no inline comments), so dropping every
    line whose first non-blank char is ``#`` leaves exactly the RUN/COPY/ENV instructions —
    the code the image actually executes, not the prose that documents it.
    """
    lines = CONTAINERFILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.lstrip().startswith("#"))


def _workspace_members() -> tuple[str, ...]:
    """The uv-workspace members, read from the SAME source of truth as production.

    Sourcing from ``[tool.uv.workspace] members`` in the root ``pyproject.toml`` — rather
    than hardcoding ``("loremaster", …)`` — means this regression pin cannot drift from the
    real member set: a member added to the workspace is automatically covered by the
    "no member is pip-installed" check below (repo law: shared conventions come from the
    production source of truth, never a hand-copied literal that can drift silently).
    """
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    members = data["tool"]["uv"]["workspace"]["members"]
    return tuple(members)


class TestContainerfileLockRegressionGuard:
    """The image must install the LOCKED closure and never the fresh-resolve (#141)."""

    def test_containerfile_exists(self) -> None:
        """A missing Containerfile would make the pins below pass vacuously."""
        assert CONTAINERFILE.is_file(), f"Containerfile not found at {CONTAINERFILE}"

    def test_members_install_via_uv_sync_locked(self) -> None:
        """The install must be ``uv sync --locked`` — the byte-for-byte locked closure."""
        assert _LOCKED_INSTALL in _instruction_text(), (
            f"the Containerfile no longer installs via `{_LOCKED_INSTALL}` — the image's "
            f"dependency set can drift from uv.lock again (#141: a fresh resolve shipped "
            f"mcp/starlette/uvicorn/sqlglot NEWER than the tested lock)"
        )

    def test_containerfile_does_not_reintroduce_uv_pip_install(self) -> None:
        """No RUN line may ``uv pip install`` the members — the exact #141 drift path."""
        assert _DRIFTING_INSTALL not in _instruction_text(), (
            f"the Containerfile reintroduced `{_DRIFTING_INSTALL}` in an instruction line — "
            f"the fresh-index resolve that drifted from uv.lock (#141). Members must install "
            f"via `{_LOCKED_INSTALL}`. (If this was deliberate, delete this regression pin "
            f"and say why in the commit.)"
        )

    def test_members_are_installed_only_by_uv_sync_locked_never_pip_installed(self) -> None:
        """PIN 4 (adversary §RESIDUALS D3) — ALLOWLIST THE SAFE (repo law #102): the members
        reach the image ONLY via ``uv sync --locked``; NO instruction line may ``pip install``
        a workspace member, however it is spelled.

        ``test_containerfile_does_not_reintroduce_uv_pip_install`` forbids only the literal
        ``uv pip install`` TOKEN. A differently-spelled fresh-resolve — a bare
        ``pip install ./loremaster`` kept alongside the locked sync — slips past it
        (adversary §RESIDUALS D3) and reintroduces the #141 drift. This pin closes that door
        the "allowlist the safe" way: (1) assert the safe install mechanism IS present, then
        (2) forbid a ``pip install`` of ANY member (bare OR ``uv pip``), with the member set
        sourced from the workspace's own manifest so it cannot drift.

        The forbid is MEMBER-scoped, NOT a blanket ``pip`` ban: the legitimate
        ``RUN pip install --no-cache-dir uv`` line (bootstrapping uv itself, naming no member)
        is deliberately untouched — a blanket ban would false-fail the correct Containerfile.
        """
        instructions = _instruction_text()

        # (1) The allowlisted-safe mechanism must be present, else the forbid below is vacuous.
        assert _LOCKED_INSTALL in instructions, (
            f"members must install via the allowlisted `{_LOCKED_INSTALL}`; without it this "
            f"pin's forbid is vacuous"
        )

        # (2) No instruction line may pip-install a member (the D3 differently-spelled drift).
        members = _workspace_members()
        offending = [
            line
            for line in instructions.splitlines()
            if "pip install" in line and any(member in line for member in members)
        ]
        assert not offending, (
            f"a workspace member is `pip install`-ed in an instruction line — the fresh-index "
            f"resolve that drifted from uv.lock (#141), spelled to dodge the "
            f"`{_DRIFTING_INSTALL}` token pin. Members must come only from `{_LOCKED_INSTALL}`. "
            f"Offending lines: {offending}. (If deliberate, delete this pin and say why.)"
        )

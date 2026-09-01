"""Contract — packet 63a-iv: STALE-PROSE currency for the #439 owner fold (design §10.9-B,
P8d prose-currency class). RED before the 63a-iv build. Authored by ``contract-63a-iv`` (tests ONLY).

The owner fold changes the id scheme from content-address (``text`` + ``refs_stamp``) to
per-owner (``owner_principal`` + ``owner_agent`` + ``text`` + ``refs_stamp``). Two surfaces teach the
OLD scheme and must be corrected WITH the derivation (P8d — served/rendered prose no code gate checks):
  1. SERVED (trust doctrine — an agent LEARNS the contract from it): the ``lore_remember`` tool
     description's *"Re-saving the same text dedups (same id)"* must gain a per-agent qualifier.
  2. INTERNAL docstring: ``derive_memory_id``'s own docstring + the backend module prose still
     describe ``memory:{text}:{refs_stamp}`` / claim the "id scheme is UNCHANGED".

The bare-grep sweeps use the P8d idiom (anchor-free pattern, each residual hit reported file:line —
"all remaining hits are X" is BANNED). Non-trapping BY CONSTRUCTION: the retired FORMAT literal
``memory:{text}:{refs_stamp}`` is NOT a substring of the owner-inclusive rewrite
``memory:{owner_principal}:{owner_agent}:{text}:{refs_stamp}`` (there ``memory:`` is followed by
``{owner_principal}``, not ``{text}``), so a correct fix removes the hit.

Store-free (source scan + tool-description build).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import loremaster.memory.backend as backend_mod
import loremaster.memory.ledger as ledger_mod
import loremaster.memory.local as local_mod
from loremaster.memory.backend import derive_memory_id
from test_mutating_set_derivation import _build_tools

# The retired teachings, as BARE anchor-free patterns (P8d). Each is a CLAIM/FORMAT the owner fold
# retires and a correct rewrite REMOVES (never a substring the owner-inclusive form re-contains).
_RETIRED_ID_FORMAT = "memory:{text}:{refs_stamp}"  # owner-less uuid5 name literal
_RETIRED_UNCHANGED_CLAIM = re.compile(r"scheme is UNCHANGED", re.IGNORECASE)

# The memory-package modules whose prose describes the id scheme.
_MEMORY_MODULES = (backend_mod, ledger_mod, local_mod)


def _hits(pattern: Any, module: Any) -> list[str]:
    """Every ``path:line`` where ``pattern`` (a compiled regex OR a plain substring) occurs in a
    module's SOURCE — the bare, per-hit-reported P8d sweep (never a wholesale 'all remaining are X')."""
    path = Path(module.__file__)
    out: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        matched = pattern.search(line) if hasattr(pattern, "search") else (pattern in line)
        if matched:
            out.append(f"{path.name}:{lineno}: {line.strip()}")
    return out


class TestTheServedRememberDescriptionQualifiesDedupPerAgent:
    """Trust doctrine (Leg 1) — the SERVED ``lore_remember`` description must not teach a global
    content-address dedup once the id is per-owner. It gains a per-agent/owner qualifier (design
    §10.9-B: *'for the same agent'*)."""

    async def test_lore_remember_description_scopes_dedup_to_the_owning_agent(
        self, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD — the description reads *'Re-saving the same text dedups (same id).'* with NO
        owner qualifier (server.py ~11227). Post-fix it scopes the dedup to the same agent/owner.
        REDDENS a build that ships the owner fold but leaves the global-dedup teaching standing (an
        agent would learn a contract the code no longer honours)."""
        tools = {tool.name: tool for tool in await _build_tools(tmp_path)}
        description = tools["lore_remember"].description or ""
        lowered = description.lower()
        assert "dedup" in lowered, "setup: the description must still teach dedup"
        # tolerant of the exact wording the builder chooses (design says 'for the same agent').
        qualifiers = ("same agent", "same owner", "per agent", "per-agent", "owning agent", "your agent")
        assert any(q in lowered for q in qualifiers), (
            "the lore_remember description teaches a global content-address dedup ('dedups (same "
            f"id)') with NO per-agent qualifier — stale under the #439 owner fold: {description!r}"
        )


class TestTheDeriveMemoryIdDocstringReflectsTheOwnerFold:
    """The FUNCTION that folds the owner must SAY it folds the owner (its docstring is the first thing
    a maintainer reads). Non-trapping: any mention of the owner passes."""

    def test_derive_memory_id_docstring_mentions_the_owner(self) -> None:
        """⚠ RED at HEAD — the docstring says the id is ``uuid5(..., "memory:{text}:{refs_stamp}")``
        with no owner. Post-fold it describes the owner-inclusive scheme."""
        doc = (derive_memory_id.__doc__ or "").lower()
        assert "owner" in doc, (
            "derive_memory_id's docstring does not mention the owner — the #439 owner fold is "
            f"undocumented (stale prose, P8d): {derive_memory_id.__doc__!r}"
        )


class TestNoMemoryProseTeachesTheOwnerLessIdScheme:
    """The bare-grep P8d sweep: no memory-package docstring still teaches the retired owner-less id
    scheme. Every residual hit is reported file:line (banned: 'the rest are fine')."""

    def test_no_module_prints_the_owner_less_uuid5_name_literal(self) -> None:
        """⚠ RED at HEAD — ``memory:{text}:{refs_stamp}`` appears in backend.py's module prose +
        derive_memory_id docstring. A correct rewrite folds the owner in, so the exact owner-less
        literal is gone (the owner-inclusive form is NOT a superset-substring of it)."""
        residual = [hit for module in _MEMORY_MODULES for hit in _hits(_RETIRED_ID_FORMAT, module)]
        assert not residual, (
            "the retired owner-less id-format literal 'memory:{text}:{refs_stamp}' still teaches the "
            "pre-#439 scheme — correct each WITH the owner fold:\n" + "\n".join(residual)
        )

    def test_no_module_claims_the_id_scheme_is_unchanged(self) -> None:
        """⚠ RED at HEAD — backend.py claims the 'id scheme is UNCHANGED'. The #439 fold CHANGES it
        (owner folded), so the claim is retired."""
        residual = [hit for module in _MEMORY_MODULES for hit in _hits(_RETIRED_UNCHANGED_CLAIM, module)]
        assert not residual, (
            "a memory module still claims the id 'scheme is UNCHANGED' — false under the #439 owner "
            "fold:\n" + "\n".join(residual)
        )

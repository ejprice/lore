"""Packet 66 (SDK3) — REQ-E: the shared stamp validator reaches EVERY store-row stamp reader (R34).

Sidecar RULING-11 (FORK-B1 = B) put ONE check-never-convert validator pair in the store seam —
``loremaster.store._txn.required_datetime`` / ``stored_datetime`` — and R34 routed every store-row stamp
reader through it. Rider 2 asks for the sharing to be PROVABLE BY MUTATION with reach as a CHECKED
variable; this file drives that sharing:

* **Reach: a NAMED BOUND, not a standing scanner (operator ruling on REQ-E, lead #19045).** The caller
  modules below were DERIVED BY GREP on 2026-11-08 at 2c0d5ee (grep -rlE
  "required_datetime\(|stored_datetime\(" loremaster/loremaster, minus store/_txn.py, which defines
  them): agents, briefs, diff, findings, floor_calibration.store, index.surreal_manifest, keeps, memory.local,
  messages, principal_keys, principals, tasks — 12. Each is driven below. RE-OPEN TRIGGER: a new store
  datetime reader. The cold audit re-derives the set by grep and diffs it against these 12 (an audit-time run:
  sharing proven by mutation at audit, not by a standing test); the AST derivation that once pinned it is kept
  in the packet scratchpad (build66/reqE/scanner_instrument_test_stamp_validator_reach_66e.py) as that
  audit's instrument.
* **Each caller module is driven through its OWN row mapper**, store-free, on a forged row dict: a
  healthy row maps (the control — it proves the forged row is otherwise complete, so a refusal below is
  about the stamp and nothing else), then the same row with ONE required stamp column naive, missing,
  or a string is refused by NAME: a ``SurrealStoreError`` whose text carries the row's id and the column.
  The refusal TEXT itself is pinned once, at the helper
  (``test_sdk3_retirement_pins_66d::TestARequiredDatetimeColumnIsCheckedNeverCoerced``).

Mutation proof (rider 2): drop the ``tzinfo`` clause from ``required_datetime`` so a naive datetime
passes — EXACTLY the ``naive`` node of each module reddens (plus the helper's naive nodes); the
``missing`` / ``string`` legs and the controls stay green. A module whose ``naive`` node stays green under
that mutation holds a private copy of the policy or is not routed — a finding, either way.

Bounds (stated, so this file does not over-claim about itself):
* ONE stamp column through ONE mapper per module. A module's OTHER call sites (e.g. ``messages``'
  ``_row_to_inbox_entry`` / ``_stamps_by_message`` / ``awaiting_answer``, ``agents._verify_capability_owner``,
  ``memory/local.invalidate``, ``keeps._row_to_membership``, ``principal_keys.verify``) are NOT driven here.
* The named set is the modules that CALL the validator. A stamp reader that never calls it — a new
  private ``isinstance(…, datetime)`` copy — is outside the set by construction; rider 1's audit sweep
  (bare ``isinstance`` + ``datetime`` reads of store rows) is the instrument for that, not this file.
* A call reached only dynamically (``getattr(_txn, name)``) is not derived.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from loremaster.agents import AgentRegistry
from loremaster.briefs import BriefLedger
from loremaster.diff import DiffEngine
from loremaster.findings import FindingLedger
from loremaster.floor_calibration import domain as floor_domain
from loremaster.floor_calibration.store import FloorCalibrationStore
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.keeps import KeepStore
from loremaster.memory.local import LocalMemoryBackend
from loremaster.messages import MessageLedger
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore
from loremaster.store._txn import SurrealStoreError
from loremaster.tasks import TaskLedger
from loresigil.testing import FakeEmbedder
from pydantic import SecretStr
from surrealdb import RecordID

# The stamps a forged row carries. AWARE is what SDK 3.0 decodes every ``datetime`` column as; the other
# three are the corrupt states rider 2 names: a naive datetime, an absent column, a legacy ISO string.
_AWARE = datetime(2026, 11, 8, 12, 0, 0, tzinfo=UTC)
_NAIVE = datetime(2026, 11, 8, 12, 0, 0)  # noqa: DTZ001 - the corrupt value under test
_LEGACY_STRING = "2026-11-08T12:00:00Z"
_CORRUPT_LEGS: tuple[str, ...] = ("naive", "missing", "string")

# Offline construction kwargs: every ledger connects lazily, so these never reach a socket.
_OFFLINE: dict[str, Any] = {
    "url": "ws://reqe66.invalid/rpc",
    "namespace": "reqe66",
    "database": "reqe66",
    "user": "reqe66",
    "password": SecretStr("reqe66"),
}

# The floor head's axes (both always-serialised axes; the identity is derived, never typed).
_MEMORY_DIM = 8  # the memory backend's embedding width (no embed runs: the mapper reads a stored row)
_FLOOR_AXES: dict[str, str] = {"scope": "reqe66-scope", "statistic": "reqe66-statistic"}


# ------------------------------------------------------------------------------------------------------
# The derivation.
# ------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------------
# One reader per caller module: its own mapper, a healthy forged row, the stamp column it must refuse.
# ------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _StampReader:
    """A caller module's real row mapper, driven store-free.

    ``read`` maps one forged row through the module's OWN mapper (sync or async); ``row_text`` is the row's
    id as the refusal must name it; ``column`` is the REQUIRED stamp column the forged rows corrupt.
    """

    module: str
    entry_point: str
    healthy_row: Callable[[], dict[str, Any]]
    column: str
    row_text: str
    read: Callable[[dict[str, Any]], Any]


async def _read_floor_head(row: dict[str, Any]) -> Any:
    """``FloorCalibrationStore.read_adopted_head`` over a fake ``_query`` that answers ``[row]``."""
    store = FloorCalibrationStore(**_OFFLINE)

    async def _answer(_statement: str, _params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [row]

    store._query = _answer  # type: ignore[method-assign, assignment]
    return await store.read_adopted_head(_FLOOR_AXES)


def _memory_backend() -> LocalMemoryBackend:
    async def _no_chunks(_keys: Any) -> set[str]:
        return set()

    return LocalMemoryBackend(
        **_OFFLINE,
        dim=_MEMORY_DIM,
        embedder=FakeEmbedder(dim=_MEMORY_DIM),
        existing_chunks=_no_chunks,
    )


_READERS: tuple[_StampReader, ...] = (
    _StampReader(
        module="loremaster.agents",
        entry_point="AgentRegistry._row_to_agent",
        healthy_row=lambda: {
            "id": RecordID("agent", "reqe66agent"),
            "name": "reqe66",
            "session": "reqe66",
            "role": "builder",
            "status": "active",
            "registered_at": _AWARE,
            "heartbeat_at": _AWARE,
        },
        column="registered_at",
        row_text="agent:reqe66agent",
        read=lambda row: AgentRegistry(**_OFFLINE)._row_to_agent(row),
    ),
    _StampReader(
        module="loremaster.briefs",
        entry_point="BriefLedger._row_to_brief",
        healthy_row=lambda: {
            "id": RecordID("brief", "reqe66brief"),
            "name": "reqe66",
            "version": 1,
            "body": "reqe66",
            "created_by": "reqe66",
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="brief:reqe66brief",
        read=lambda row: BriefLedger(**_OFFLINE)._row_to_brief(row),
    ),
    _StampReader(
        module="loremaster.diff",
        entry_point="DiffEngine._row_to_summary",
        healthy_row=lambda: {
            "id": RecordID("snapshot", "snreqe66"),
            "created_at": _AWARE,
            "files_total": 1,
            "chunks_total": 1,
        },
        column="created_at",
        row_text="snapshot:snreqe66",
        read=DiffEngine._row_to_summary,
    ),
    _StampReader(
        module="loremaster.findings",
        entry_point="FindingLedger._row_to_finding",
        healthy_row=lambda: {
            "id": RecordID("finding", "reqe66finding"),
            "number": 1,
            "kind": "friction",
            "status": "open",
            "subject": "reqe66",
            "body": "reqe66",
            "area": "reqe66",
            "category": "reqe66",
            "created_by": "reqe66",
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="finding:reqe66finding",
        read=lambda row: FindingLedger(**_OFFLINE)._row_to_finding(row),
    ),
    _StampReader(
        module="loremaster.floor_calibration.store",
        entry_point="FloorCalibrationStore.read_adopted_head (fake _query)",
        healthy_row=lambda: {
            "revision": 1,
            "measurement": RecordID("floor_measurement", "reqe66measurement"),
            "adopted_at": _AWARE,
            "axes": dict(_FLOOR_AXES),
        },
        column="adopted_at",
        row_text=floor_domain.head_identity(_FLOOR_AXES),
        read=_read_floor_head,
    ),
    _StampReader(
        module="loremaster.index.surreal_manifest",
        entry_point="SurrealManifest._row_to_model",
        healthy_row=lambda: {
            "id": RecordID("file", ["reqe66tier", "reqe66/file.py"]),
            "sha512": "0" * 128,
            "mtime_ns": 1,
            "size": 1,
            "n_chunks": 0,
            "chunk_ids": [],
            "state": "indexed",
            "updated_at": _AWARE,
        },
        column="updated_at",
        row_text="file:['reqe66tier', 'reqe66/file.py']",
        read=SurrealManifest._row_to_model,
    ),
    _StampReader(
        module="loremaster.keeps",
        entry_point="KeepStore._row_to_keep",
        healthy_row=lambda: {
            "id": RecordID("keep", "reqe66keep"),
            "id_text": "keep:reqe66keep",
            "keeper": RecordID("principal", "reqe66principal"),
            "type": "dm",
            "name": None,
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="keep:reqe66keep",
        read=lambda row: KeepStore(**_OFFLINE)._row_to_keep(row),
    ),
    _StampReader(
        module="loremaster.memory.local",
        entry_point="LocalMemoryBackend._row_to_recalled",
        healthy_row=lambda: {
            "id": RecordID("memory", "reqe66memory"),
            "note_text": "reqe66",
            "kind": "fact",
            "valid_from": _AWARE,
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="memory:reqe66memory",
        read=lambda row: _memory_backend()._row_to_recalled(row, set()),
    ),
    _StampReader(
        module="loremaster.messages",
        entry_point="MessageLedger._row_to_stored_message",
        healthy_row=lambda: {"id": RecordID("message", "reqe66message"), "seq": 1, "created_at": _AWARE},
        column="created_at",
        row_text="message:reqe66message",
        read=lambda row: MessageLedger(**_OFFLINE)._row_to_stored_message(row),
    ),
    _StampReader(
        module="loremaster.principal_keys",
        entry_point="PrincipalKeyStore._row_to_key",
        healthy_row=lambda: {
            "id": RecordID("principal_key", "reqe66key"),
            "principal": RecordID("principal", "reqe66principal"),
            "name": "reqe66",
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="principal_key:reqe66key",
        read=lambda row: PrincipalKeyStore(**_OFFLINE)._row_to_key(row),
    ),
    _StampReader(
        module="loremaster.principals",
        entry_point="PrincipalStore._row_to_principal",
        healthy_row=lambda: {
            "id": RecordID("principal", "reqe66principal"),
            "email": "reqe66@example.invalid",
            "status": "active",
            "role": "member",
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="principal:reqe66principal",
        read=lambda row: PrincipalStore(**_OFFLINE)._row_to_principal(row),
    ),
    _StampReader(
        module="loremaster.tasks",
        entry_point="TaskLedger._row_to_task",
        healthy_row=lambda: {
            "id": RecordID("task", "reqe66task"),
            "subject": "reqe66",
            "description": "reqe66",
            "status": "open",
            "created_at": _AWARE,
        },
        column="created_at",
        row_text="task:reqe66task",
        read=lambda row: TaskLedger(**_OFFLINE)._row_to_task(row),
    ),
)
_READER_BY_MODULE: dict[str, _StampReader] = {reader.module: reader for reader in _READERS}


async def _map(reader: _StampReader, row: dict[str, Any]) -> Any:
    """Drive ``row`` through the reader's mapper, awaiting it when the entry point is async."""
    mapped = reader.read(row)
    if inspect.isawaitable(mapped):
        awaited: Awaitable[Any] = mapped
        return await awaited
    return mapped


def _corrupted(reader: _StampReader, leg: str) -> dict[str, Any]:
    """The healthy row with ONLY its stamp column corrupted (``missing``: absent, as ``SELECT *`` omits)."""
    row = reader.healthy_row()
    if leg == "missing":
        del row[reader.column]
    else:
        row[reader.column] = {"naive": _NAIVE, "string": _LEGACY_STRING}[leg]
    return row


# ------------------------------------------------------------------------------------------------------
# The pins.
# ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("module", sorted(_READER_BY_MODULE))
class TestEachStampReaderRefusesACorruptStampByName:
    """∀ caller module: its own mapper maps a healthy row, and refuses a corrupt REQUIRED stamp naming the
    row and the column — never serving a coerced or defaulted value."""

    async def test_control_a_healthy_row_maps(self, module: str) -> None:
        reader = _READER_BY_MODULE[module]
        assert await _map(reader, reader.healthy_row()) is not None, f"{reader.entry_point} mapped nothing"

    @pytest.mark.parametrize("leg", _CORRUPT_LEGS)
    async def test_a_corrupt_stamp_is_refused_by_name(self, module: str, leg: str) -> None:
        reader = _READER_BY_MODULE[module]
        try:
            mapped = await _map(reader, _corrupted(reader, leg))
        except SurrealStoreError as error:
            text = str(error)
        except Exception as error:  # noqa: BLE001 - the WRONG refusal class is the finding, named below
            pytest.fail(
                f"{reader.entry_point} refused a {leg} {reader.column!r} with {type(error).__name__} "
                f"({error}) — a corrupt store row is a SurrealStoreError (R34, RULING-11 rider 3)"
            )
        else:
            pytest.fail(f"{reader.entry_point} SERVED a {leg} {reader.column!r} stamp: {mapped!r}")
        assert reader.row_text in text, f"the refusal names no row ({reader.row_text!r}): {text}"
        assert reader.column in text, f"the refusal names no column ({reader.column!r}): {text}"

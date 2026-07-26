"""GC driver for legacy pre-P8b index snapshots in a lore SurrealDB store.

All snapshots stamped BEFORE the P8b snapshot-fidelity fix carry collapsed
chunk ledgers (a P5 write-time bug, unrecoverable) — ``lore_diff`` renders them
with legacy markers. The first post-fix snapshot is the P8b boot stamp; that
snapshot AND everything newer must be KEPT, everything strictly older is
GC-eligible. This driver partitions the store's snapshots on an epoch boundary
and, only under an explicit ``--execute`` flag, deletes the eligible ones.

STRICT dry-run by default: it lists every snapshot, partitions KEEP vs DELETE
on ``--epoch`` (keep ``created_at >= epoch``, INCLUDING the epoch snapshot
itself), prints the manifest, and deletes NOTHING unless ``--execute`` is
passed. It is loud on any anomaly — an unclassifiable timestamp, a connection
failure, a missing credential, or a misconfigured epoch that would wipe every
snapshot — and exits non-zero rather than guess.

The store-touching work reuses the tested, cascade-safe machinery rather than
issuing raw DELETEs (record links do NOT auto-clean on delete, so a hand-rolled
delete would orphan ``snapshot_entry`` rows):

* :meth:`~loremaster.diff.DiffEngine.list_snapshots` — the bounded, newest-first
  snapshot listing (a read-only connection; no DDL).
* :meth:`~loremaster.index.snapshots.SnapshotStamper.delete_snapshot` — the
  scoped, child-entries-first cascade delete.

Credentials use env-var indirection via
:func:`~loremaster.config.resolve_secret` — the CLI carries the env-var NAMES,
never the values, and the values are never printed.

Usage::

    # dry run (default) — prints the KEEP/DELETE manifest, deletes nothing:
    set -a; . /home/ejprice/docker/mcp/lore-secrets/lore.env; set +a
    uv run python scripts/snapshot_gc.py

    # after reviewing the manifest, actually delete the eligible snapshots:
    uv run python scripts/snapshot_gc.py --execute
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from loremaster.config import resolve_secret
from loremaster.diff import DiffEngine, SnapshotSummary
from loremaster.index.snapshots import SnapshotStamper
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.store.surreal import SurrealConnectionError, SurrealStore
from pydantic import SecretStr

__all__ = [
    "GcPlan",
    "SnapshotClassificationError",
    "is_total_wipe",
    "main",
    "parse_args",
    "parse_epoch",
    "partition_snapshots",
    "render_manifest",
    "run_gc",
]

# The P8b snapshot-fidelity boundary: the first post-fix snapshot (the P8b boot
# stamp) was created 2026-07-04T22:42Z. A floor of 22:42:00Z keeps that stamp
# and everything newer; the operator can pin it to the stamp's exact
# ``created_at`` after reading the dry-run manifest.
DEFAULT_EPOCH = "2026-07-04T22:42:00Z"

# Live store coordinates (this repo's lore.yaml). The URL carries the ``/rpc``
# suffix the SurrealDB SDK connects with.
DEFAULT_URL = "ws://127.0.0.1:18500/rpc"
DEFAULT_NAMESPACE = "lore"
DEFAULT_DATABASE = "lore"
DEFAULT_USER_ENV = "SURREAL_USER"
DEFAULT_PASSWORD_ENV = "SURREAL_PASS"

# The store constructor requires an embedding dim; the listing / delete paths
# never read it (they touch only the snapshot tables), but it must be a valid
# value. Mirrors the repo's lore.yaml ``embedding.dim``.
DEFAULT_DIM = 2048

# One SELECT returns every snapshot: == ``diff._MAX_LIST_LIMIT`` (the listing's
# hard ceiling), far above the ~20 snapshots the live store holds.
_LIST_LIMIT = 500

_EXIT_OK = 0
_EXIT_ERROR = 1

_PROGRAM = "snapshot_gc"


class SnapshotClassificationError(RuntimeError):
    """A snapshot whose ``created_at`` cannot be parsed into an instant.

    Raised instead of silently treating an unparseable timestamp as
    GC-eligible — an anomaly the operator must resolve before any deletion.
    """


@dataclass(frozen=True)
class GcPlan:
    """The partition of a store's snapshots against an epoch boundary.

    Attributes:
        keep: Snapshots at or after the epoch (``created_at >= epoch``),
            including the epoch snapshot itself — never deleted.
        delete: Snapshots strictly older than the epoch — GC-eligible.
        epoch: The (timezone-aware, UTC) boundary the partition used.
    """

    keep: list[SnapshotSummary]
    delete: list[SnapshotSummary]
    epoch: datetime


def _to_aware_utc(value: datetime) -> datetime:
    """Normalise a datetime to timezone-aware UTC (a naive value is UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_iso8601(text: str) -> datetime:
    """Parse an ISO-8601 timestamp, tolerating a trailing ``Z`` (UTC).

    Raises:
        ValueError: The text is not a valid ISO-8601 timestamp.
    """
    normalised = text.strip()
    if normalised.endswith("Z"):
        normalised = f"{normalised[:-1]}+00:00"
    return datetime.fromisoformat(normalised)


def parse_epoch(text: str) -> datetime:
    """Parse the ``--epoch`` boundary into a timezone-aware UTC datetime.

    Accepts a trailing ``Z`` and a naive timestamp (interpreted as UTC).

    Raises:
        ValueError: The text is not a valid ISO-8601 timestamp (the message
            names the offending value).
    """
    try:
        parsed = _parse_iso8601(text)
    except ValueError as exc:
        raise ValueError(f"invalid --epoch {text!r}: {exc}") from exc
    return _to_aware_utc(parsed)


def _snapshot_instant(summary: SnapshotSummary) -> datetime:
    """The snapshot's ``created_at`` as a timezone-aware UTC instant.

    Raises:
        SnapshotClassificationError: ``created_at`` cannot be parsed — the
            snapshot cannot be classified and must not be swept into DELETE.
    """
    try:
        parsed = _parse_iso8601(summary.created_at)
    except ValueError as exc:
        raise SnapshotClassificationError(
            f"snapshot {summary.id} has an unparseable created_at "
            f"{summary.created_at!r}: {exc}"
        ) from exc
    return _to_aware_utc(parsed)


def partition_snapshots(
    summaries: Sequence[SnapshotSummary], epoch: datetime
) -> GcPlan:
    """Partition ``summaries`` into KEEP (``>= epoch``) and DELETE (older).

    Pure given its inputs. The epoch snapshot itself (``created_at == epoch``)
    is KEPT — the boundary is inclusive on the keep side. ``epoch`` is
    normalised to timezone-aware UTC so a naive boundary still compares
    correctly against the stored (aware) timestamps.

    Args:
        summaries: The snapshot summaries to classify (any order).
        epoch: The boundary instant; snapshots at or after it are kept.

    Returns:
        The KEEP / DELETE partition, preserving each side's input order.

    Raises:
        SnapshotClassificationError: A snapshot's ``created_at`` cannot be
            parsed — the whole partition is refused, never partial.
    """
    boundary = _to_aware_utc(epoch)
    keep: list[SnapshotSummary] = []
    delete: list[SnapshotSummary] = []
    for summary in summaries:
        if _snapshot_instant(summary) >= boundary:
            keep.append(summary)
        else:
            delete.append(summary)
    return GcPlan(keep=keep, delete=delete, epoch=boundary)


def is_total_wipe(plan: GcPlan) -> bool:
    """True when the plan would delete every snapshot (keep nothing).

    A safety sentinel: an epoch that keeps NOTHING while deleting something is
    almost certainly a fat-fingered boundary (the P8b stamp and everything
    newer are supposed to survive), so the driver refuses to execute it.
    """
    return not plan.keep and bool(plan.delete)


def _render_row(disposition: str, summary: SnapshotSummary) -> str:
    return (
        f"  [{disposition:<6}] {summary.id}  created={summary.created_at}  "
        f"files={summary.files_total} chunks={summary.chunks_total}"
    )


def render_manifest(summaries: Sequence[SnapshotSummary], plan: GcPlan) -> str:
    """Render the KEEP/DELETE manifest, newest-first as listed.

    Every snapshot is shown with its disposition and its id / created_at /
    file+chunk counts, preceded by a summary line naming both partition sizes.
    """
    delete_ids = {summary.id for summary in plan.delete}
    total = len(summaries)
    lines = [
        f"snapshot GC manifest (epoch {plan.epoch.isoformat()})",
        f"  KEEP {len(plan.keep)} / DELETE {len(plan.delete)} / total {total}",
        "",
    ]
    for summary in summaries:
        disposition = "DELETE" if summary.id in delete_ids else "KEEP"
        lines.append(_render_row(disposition, summary))
    return "\n".join(lines)


def _build_store_and_manifest(
    *, url: str, namespace: str, database: str, dim: int, user: str, password: SecretStr
) -> tuple[SurrealStore, SurrealManifest]:
    """Construct the store/manifest collaborators the reuse targets require.

    Both :class:`DiffEngine` and :class:`SnapshotStamper` take a store and a
    manifest as constructor dependencies, but the listing / delete paths never
    touch them (they operate on the snapshot tables via their own connection).
    They are constructed here but never ``ensure_ready``-ed, so no connection of
    their own is ever opened.
    """
    store = SurrealStore(
        url=url, namespace=namespace, database=database, dim=dim,
        user=user, password=password,
    )
    manifest = SurrealManifest(
        url=url, namespace=namespace, database=database,
        user=user, password=password,
    )
    return store, manifest


async def _list_snapshots(
    *, url: str, namespace: str, database: str, dim: int, user: str, password: SecretStr
) -> list[SnapshotSummary]:
    """List every snapshot in the store, newest-first (READ-ONLY).

    Opens the diff engine's own connection (no DDL), reads the snapshot table,
    and closes the connection. Raises :class:`SurrealConnectionError` if the
    store is unreachable or rejects auth.
    """
    store, manifest = _build_store_and_manifest(
        url=url, namespace=namespace, database=database, dim=dim,
        user=user, password=password,
    )
    engine = DiffEngine(
        url=url, namespace=namespace, database=database,
        user=user, password=password, store=store, manifest=manifest,
    )
    await engine.ensure_ready()
    try:
        return await engine.list_snapshots(limit=_LIST_LIMIT)
    finally:
        await engine.close()


async def _delete_snapshots(
    plan: GcPlan,
    *,
    url: str,
    namespace: str,
    database: str,
    dim: int,
    user: str,
    password: SecretStr,
    project_root: Path,
) -> None:
    """Cascade-delete every snapshot in ``plan.delete`` via the stamper.

    Each delete removes the ``snapshot`` row AND its ``snapshot_entry`` children
    (children first — record links do not auto-clean), scoped to that snapshot.
    """
    store, manifest = _build_store_and_manifest(
        url=url, namespace=namespace, database=database, dim=dim,
        user=user, password=password,
    )
    stamper = SnapshotStamper(
        url=url, namespace=namespace, database=database,
        user=user, password=password, store=store, manifest=manifest,
        project_root=project_root,
    )
    await stamper.ensure_ready()
    try:
        for summary in plan.delete:
            await stamper.delete_snapshot(summary.id)
    finally:
        await stamper.close()


async def run_gc(args: argparse.Namespace) -> int:
    """List, partition, print the manifest, and (only with ``--execute``) delete.

    Returns a process exit code. Raises the underlying typed errors
    (:class:`SnapshotClassificationError`, :class:`SurrealConnectionError`,
    :class:`KeyError`, :class:`ValueError`) for :func:`main` to launder.
    """
    epoch = parse_epoch(args.epoch)
    # The USERNAME is deliberately not carried as a secret (#211): it is a public
    # default named by SURREAL_DEFAULT_USER_ENV, so it is unwrapped here while
    # the password stays a SecretStr all the way to the SDK seam.
    user = resolve_secret(args.user_env).get_secret_value()
    password = resolve_secret(args.password_env)

    summaries = await _list_snapshots(
        url=args.url, namespace=args.namespace, database=args.database,
        dim=args.dim, user=user, password=password,
    )
    plan = partition_snapshots(summaries, epoch)
    print(render_manifest(summaries, plan))

    if not args.execute:
        print(
            f"\nDRY RUN — nothing deleted. Re-run with --execute to delete "
            f"{len(plan.delete)} snapshot(s).",
            file=sys.stderr,
        )
        return _EXIT_OK

    if is_total_wipe(plan):
        print(
            f"{_PROGRAM}: REFUSING to execute — the epoch keeps NO snapshots "
            f"while deleting {len(plan.delete)}; this would wipe every snapshot. "
            f"Check --epoch.",
            file=sys.stderr,
        )
        return _EXIT_ERROR

    if not plan.delete:
        print(f"{_PROGRAM}: nothing to delete — all snapshots are kept.", file=sys.stderr)
        return _EXIT_OK

    await _delete_snapshots(
        plan, url=args.url, namespace=args.namespace, database=args.database,
        dim=args.dim, user=user, password=password, project_root=args.project_root,
    )
    print(f"\nDELETED {len(plan.delete)} snapshot(s).", file=sys.stderr)
    return _EXIT_OK


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Partition a lore store's index snapshots on an epoch boundary and, "
            "only with --execute, cascade-delete the pre-epoch (legacy) ones. "
            "Dry-run by default."
        )
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="SurrealDB RPC URL")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE, help="SurrealDB namespace")
    parser.add_argument("--database", default=DEFAULT_DATABASE, help="SurrealDB database")
    parser.add_argument(
        "--user-env",
        default=DEFAULT_USER_ENV,
        help="env-var NAME holding the SurrealDB user (never the value)",
    )
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help="env-var NAME holding the SurrealDB password (never the value)",
    )
    parser.add_argument(
        "--epoch",
        default=DEFAULT_EPOCH,
        help=(
            "ISO-8601 keep boundary; snapshots at or after it are KEPT "
            f"(default: {DEFAULT_EPOCH}, the P8b fidelity fix)"
        ),
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=DEFAULT_DIM,
        help="embedding dim for the store constructor (unused by list/delete)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="project root for the stamper constructor (unused by delete)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="ACTUALLY delete the pre-epoch snapshots (default: dry run)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return asyncio.run(run_gc(args))
    except SnapshotClassificationError as exc:
        print(f"{_PROGRAM}: ANOMALY — {exc}", file=sys.stderr)
        return _EXIT_ERROR
    except KeyError as exc:
        # resolve_secret raises KeyError (already a naming message) on a
        # missing/empty credential env var.
        print(f"{_PROGRAM}: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return _EXIT_ERROR
    except ValueError as exc:
        print(f"{_PROGRAM}: {exc}", file=sys.stderr)
        return _EXIT_ERROR
    except SurrealConnectionError as exc:
        print(f"{_PROGRAM}: cannot reach the store — {exc}", file=sys.stderr)
        return _EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())

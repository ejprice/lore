"""Cold-audit probe #4 — §9.6: is ``create_many`` REALLY atomic?

The C3 build sets ``writes = len(batch)`` for ``create_many`` on the strength of a
DOCSTRING calling it all-or-nothing. The builder flagged that it did not prove it.
This proves it, against the LIVE test store: force a mid-batch failure and count
the rows that survived.

The risk being tested is precise: ``writes`` is only ever compared ``< 1``, so an
over-count is harmless UNLESS a batch can return NORMALLY having written ZERO rows
(which would footer a call that wrote nothing) or write PARTIALLY while claiming
all-or-nothing.

Run:  uv run python scratchpad/coldaudit_wavec_r2_probe4.py
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")

OK, BAD = "PASS", "**FAIL**"


class _Malformed:
    """A duck-typed spec that satisfies TaskSpecLike shallowly then EXPLODES."""
    blocked_by = None
    description = "d"

    @property
    def subject(self) -> str:
        raise RuntimeError("malformed spec: subject exploded mid-batch")


_MALFORMED = _Malformed()
_FAILURES: list[str] = []


def show(label: str, verdict: bool, detail: str = "") -> bool:
    if not verdict:
        _FAILURES.append(label)
    print(f"  [{OK if verdict else BAD}] {label}" + (f"  :: {detail}" if detail else ""))
    return verdict


async def main() -> None:
    from _surreal_harness import PRODUCTION_DIM, drop_database, make_env, unique_database
    from loremaster.tasks import TaskLedger, TaskSpec

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    await ledger.ensure_ready()
    try:
        print("\n=== §9.6 : create_many atomicity, MEASURED ===")

        # --- POSITIVE CONTROL: a clean batch writes exactly len(items) --------
        before = len(await ledger.query_tasks())
        good = [
            TaskSpec(subject=f"clean {i}", description="d") for i in range(4)
        ]
        await ledger.create_many(good, created_by="coldaudit")
        after = len(await ledger.query_tasks())
        show(
            "CONTROL: a clean 4-item batch writes exactly 4 rows",
            after - before == 4,
            detail=f"{before} -> {after}",
        )

        # --- THE TEST: a batch whose LAST item is malformed -------------------
        for label, bad_batch in (
            (
                "blocked_by names a PHANTOM task (engine-side ENFORCED refusal)",
                [
                    TaskSpec(subject="atomic a", description="d"),
                    TaskSpec(subject="atomic b", description="d"),
                    TaskSpec(subject="atomic c", description="d",
                             blocked_by=["does_not_exist_anywhere"]),
                ],
            ),
            (
                "an item missing a required field (client-side refusal)",
                [
                    TaskSpec(subject="atomic d", description="d"),
                    TaskSpec(subject="atomic e", description="d"),
                    _MALFORMED,
                ],
            ),
        ):
            baseline = len(await ledger.query_tasks())
            outcome = "returned normally"
            try:
                # bad_batch DELIBERATELY carries a protocol-violating _Malformed spec —
                # feeding create_many a non-TaskSpecLike item IS the atomicity probe.
                await ledger.create_many(bad_batch, created_by="coldaudit")  # type: ignore[arg-type]
            except Exception as error:  # noqa: BLE001
                outcome = f"{type(error).__name__}"
            settled = len(await ledger.query_tasks())
            written = settled - baseline
            print(f"  -- {label}")
            print(f"     outcome={outcome}  rows written={written} (of {len(bad_batch)})")
            show(
                f"     ALL-OR-NOTHING held (0 or {len(bad_batch)} rows, never partial)",
                written in (0, len(bad_batch)),
                detail=f"written={written}",
            )
            show(
                "     a batch that wrote ZERO did NOT return normally "
                "(so writes=len(items) can never footer an empty write)",
                not (written == 0 and outcome == "returned normally"),
                detail=f"written={written} outcome={outcome}",
            )
    finally:
        try:
            await drop_database(env)
        except Exception:  # noqa: BLE001,S110
            pass

    print(f"\n[done] failures: {len(_FAILURES)}")
    for failure in _FAILURES:
        print(f"   - {failure}")


if __name__ == "__main__":
    asyncio.run(main())

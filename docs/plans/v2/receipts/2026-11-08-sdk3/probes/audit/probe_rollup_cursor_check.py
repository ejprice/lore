"""Audit probe (packet 66 cold audit; NOT a repo test): is the rollup cursor's exclusive boundary kept
when the cursor travels as the SERVED text (`next cursor: <datetime.isoformat()>`, server._render) and is
parsed back by the server (`datetime.fromisoformat`), as every agent actually uses it?
CONTROL leg = the existing pin's shape (the in-process PreciseDatetime re-bound): must EXCLUDE the row."""
from datetime import datetime

from test_task_ledger import AGENT_A, DESCRIPTION_XML, SUBJECT_XML, _create  # noqa: F401  (fixture module)
from test_task_ledger import *  # noqa: F403 — the task_ledger fixture and its dependencies


async def test_control_in_process_cursor_excludes_its_own_row(task_ledger) -> None:
    task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
    claimed = await task_ledger.claim_task(task_id, AGENT_A)
    window = await task_ledger.updated_since(claimed.task.updated_at, limit=20)
    assert task_id not in {t.id for t in window.rows}


async def test_served_text_cursor_excludes_its_own_row(task_ledger) -> None:
    task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
    claimed = await task_ledger.claim_task(task_id, AGENT_A)
    stamp = claimed.task.updated_at
    served = stamp.isoformat()                      # what server._render serves as `next cursor:`
    parsed = datetime.fromisoformat(served)         # what server's `since` parser binds
    ns = getattr(stamp, "isoformat_with_nanoseconds", lambda: "n/a")()
    window = await task_ledger.updated_since(parsed, limit=20)
    reserved = task_id in {t.id for t in window.rows}
    print(f"\nstamp_ns={ns} served={served} reserved={reserved}")
    assert not reserved, f"cursor {served!r} (true stamp {ns}) re-serves the very row it was read from"


async def test_production_codec_cursor_excludes_its_own_row(task_ledger) -> None:
    """R43 re-check: the SAME round trip through PRODUCTION's codec — `served_instant_text` (what
    `_render_rollup` serves) and `AppContext._parse_rollup_since` (the server's own `since` parser)."""
    from loremaster.server import AppContext
    from loremaster.store._txn import served_instant_text
    task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
    claimed = await task_ledger.claim_task(task_id, AGENT_A)
    stamp = claimed.task.updated_at
    served = served_instant_text(stamp)
    parsed = AppContext._parse_rollup_since(served)
    window = await task_ledger.updated_since(parsed, limit=20)
    reserved = task_id in {t.id for t in window.rows}
    print(f"\nPRODUCTION codec: stamp_ns={getattr(stamp, 'isoformat_with_nanoseconds', lambda: 'n/a')()} served={served} reserved={reserved}")
    assert not reserved

"""delta-r17-66 probe: render the rollup for two truncated legs whose resume points differ.

Constructs TaskActivityWindow / FindingActivityWindow via model_construct (no store) with the
#593 pin's page-1 shape: task leg truncated at HIGH, finding leg truncated at LOW (LOW < HIGH).
Prints the task-leg header and the served next cursor, to check h3's claim on the task leg.
"""
from types import SimpleNamespace
import loremaster
from loremaster.server import AppContext
from loremaster.store._txn import parse_served_instant
from loremaster.tasks import TaskActivityWindow
from loremaster.findings import FindingActivityWindow

print("loremaster.__file__", loremaster.__file__)
since = parse_served_instant("2031-01-01T00:00:00.000000001Z")
low = parse_served_instant("2031-05-06T07:08:09.186697100Z")
high = parse_served_instant("2031-05-06T07:08:09.186697900Z")
task = SimpleNamespace(status="open", summary=None, subject="task page tail", id="t1", owner="o",
                       report_path=None)
finding = SimpleNamespace(number=1, status="open", subject="finding page tail", kind="bug", created_by="c")
tw = TaskActivityWindow.model_construct(rows=[task], total=2, resume_at=high, held_group=None)
fw = FindingActivityWindow.model_construct(rows=[finding], total=2, resume_at=low, held_group=None)
AppContext._task_status_marker = staticmethod(lambda t: "[open]")
out = AppContext._render_rollup(since, tw, fw, extra_sections=[], subject=None, message_window=None,
                                serve_message_leg=False)
print(out)

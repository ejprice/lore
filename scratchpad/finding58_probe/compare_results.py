"""Asserts the finding #58 fix contract against pre_fix_results.json /
post_fix_results.json (produced by run_probe.py against pre_fix/ and
docs/eval/ respectively). See REPORT-fixer-harness.md for the pasted output.
"""

import json
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent

pre = json.loads((PROBE_DIR / "pre_fix_results.json").read_text())
post = json.loads((PROBE_DIR / "post_fix_results.json").read_text())

# (c) byte-equivalence: a single tool_use turn must be identical pre vs post.
assert pre["single"] == post["single"], "single-tool_use scenario diverged!"
print("PASS (c): single-tool_use scenario byte-identical pre-fix vs post-fix")

# (a) both tools executed in order, post-fix.
expected_order = [
    ["lore_search", {"query": "foo"}],
    ["lore_read", {"tier": "custom", "path": "x.py"}],
]
assert post["parallel"]["tool_call_order"] == expected_order, post["parallel"]["tool_call_order"]
print("PASS (a): post-fix parallel scenario executed both tools, in order:",
      post["parallel"]["tool_call_order"])

# (b) history pairs BOTH ids with tool_results, post-fix.
followup_user_msg = post["parallel"]["api_calls_messages"][1][-1]
assert followup_user_msg["role"] == "user"
ids = [block["tool_use_id"] for block in followup_user_msg["content"]]
assert ids == ["toolu_parallel_a", "toolu_parallel_b"], ids
print("PASS (b): post-fix history pairs both tool_use ids with tool_result blocks:", ids)

# Contrast: demonstrate the pre-fix defect this replaced (for the record).
pre_assistant_msg = pre["parallel"]["api_calls_messages"][1][1]
pre_followup_user_msg = pre["parallel"]["api_calls_messages"][1][2]
tool_use_ids = [b["id"] for b in pre_assistant_msg["content"] if b["type"] == "tool_use"]
tool_result_ids = [b["tool_use_id"] for b in pre_followup_user_msg["content"]]
dangling = set(tool_use_ids) - set(tool_result_ids)
assert dangling == {"toolu_parallel_b"}, dangling
assert pre["parallel"]["tool_call_order"] == [["lore_search", {"query": "foo"}]], (
    "pre-fix should never have executed lore_read"
)
print(
    f"CONFIRMED DEFECT (pre-fix): tool_use ids {tool_use_ids} vs tool_result ids "
    f"{tool_result_ids} -- dangling id(s) {dangling} (lore_read never even executed) "
    "-- exactly the shape the real Anthropic API 400'd on (finding #58)."
)

print("\nALL PROBE ASSERTIONS PASSED")

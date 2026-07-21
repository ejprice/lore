"""Probe (T4 honesty): the notice says 'raise budget to ~N to see all K'.
Confirm that re-running enforcement at N actually reveals all K entries with
NO elision notice — i.e. N is honestly the minimum no-elision budget, and the
calibrated counter is applied consistently (no off-by-calibration-factor)."""
import re

from loremaster.server import AppContext, NOTICE_KIND
from loremaster.search import SearchResult
from loresigil.testing import FakeEmbedder


class Probe:
    def __init__(self, emb: FakeEmbedder) -> None:
        self.embedder = emb

    _count_tokens_single = AppContext._count_tokens_single
    _enforce_search_budget = AppContext._enforce_search_budget
    _search_elision_notice = staticmethod(AppContext._search_elision_notice)
    _result_identity = staticmethod(AppContext._result_identity)


def _sr(fmt: str, kind: str, key: str = "") -> SearchResult:
    return SearchResult(formatted=fmt, chunk_key=key, detail_level="summary",
                        stale=False, score=0.7, kind=kind)


def main() -> None:
    probe = Probe(FakeEmbedder(dim=256))
    results = [
        _sr(f"[SOURCE:pkg/hit_{i}.py:1-9@abcd12]\nKey: hit-{i}\n" + "x" * 200, "hit", f"hit-{i}")
        for i in range(5)
    ]
    # A tight budget that elides several.
    kept = probe._enforce_search_budget(list(results), 200, None)
    notice = next(r for r in kept if r.kind == NOTICE_KIND and "elided" in r.formatted)
    print("NOTICE:", notice.formatted)
    m = re.search(r"raise budget to ~(\d+)", notice.formatted)
    assert m, "no suggested budget in notice"
    suggested = int(m.group(1))
    print("suggested N =", suggested)

    # Re-run at exactly N.
    kept_at_n = probe._enforce_search_budget(list(results), suggested, None)
    notices_at_n = [r for r in kept_at_n if r.kind == NOTICE_KIND and "elided" in r.formatted]
    hits_at_n = [r for r in kept_at_n if r.kind == "hit"]
    print(f"at N={suggested}: hits kept={len(hits_at_n)}/5, elision notices={len(notices_at_n)}")
    ok = len(hits_at_n) == 5 and not notices_at_n
    print("HONEST (all revealed, no elision at N):", ok)

    # Also probe N-1 to confirm N is the MINIMUM (N-1 should still elide).
    kept_below = probe._enforce_search_budget(list(results), suggested - 1, None)
    hits_below = [r for r in kept_below if r.kind == "hit"]
    notices_below = [r for r in kept_below if r.kind == NOTICE_KIND and "elided" in r.formatted]
    print(f"at N-1={suggested-1}: hits kept={len(hits_below)}/5, elision notices={len(notices_below)}")


if __name__ == "__main__":
    main()

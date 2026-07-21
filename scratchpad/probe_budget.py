"""Probe: can _enforce_search_budget leave the `memories:` header dangling
(header kept, zero memory entries beneath it) under a tight budget?

Mirrors the real list shape SearchPipeline.search_code produces post-T3:
    [*partitioned_hits, header, mem1, mem2, mem3, (mem_elision_notice)]
fed straight into AppContext._enforce_search_budget (server.py:1633).
"""
from loremaster.server import AppContext, NOTICE_KIND
from loremaster.search import SearchResult
from loresigil.testing import FakeEmbedder

_MEMORY_SECTION_HEADER = "memories:"


class Probe:
    def __init__(self, emb: FakeEmbedder) -> None:
        self.embedder = emb

    _count_tokens_single = AppContext._count_tokens_single
    _enforce_search_budget = AppContext._enforce_search_budget
    _search_elision_notice = staticmethod(AppContext._search_elision_notice)
    _result_identity = staticmethod(AppContext._result_identity)


def _sr(formatted: str, kind: str, key: str = "") -> SearchResult:
    return SearchResult(
        formatted=formatted, chunk_key=key, detail_level="summary",
        stale=False, score=0.5, kind=kind,
    )


def build_list() -> list[SearchResult]:
    hit = _sr("[SOURCE:pkg/router.py:1-10@abc123]\n" + "h" * 40, "hit", "hit-key-0")
    header = _sr(_MEMORY_SECTION_HEADER, NOTICE_KIND)
    mems = [
        _sr("[MEMORY] remembered correction number " + str(i) + " " + "m" * 30,
            "memory", "")
        for i in range(3)
    ]
    return [hit, header, *mems]


def main() -> None:
    probe = Probe(FakeEmbedder(dim=256))
    base = build_list()
    dangling_budgets = []
    for budget in range(1, 120):
        kept = probe._enforce_search_budget(list(base), budget, None)
        kinds = [(r.kind, r.formatted[:20]) for r in kept]
        has_header = any(r.formatted == _MEMORY_SECTION_HEADER for r in kept)
        n_mem = sum(1 for r in kept if r.kind == "memory")
        if has_header and n_mem == 0:
            dangling_budgets.append(budget)
            if len(dangling_budgets) <= 3:
                print(f"DANGLING HEADER at budget={budget}: {kinds}")
    print(f"\nTotal dangling-header budgets in [1,120): {len(dangling_budgets)}")
    if dangling_budgets:
        print(f"range: {dangling_budgets[0]}..{dangling_budgets[-1]}")


if __name__ == "__main__":
    main()

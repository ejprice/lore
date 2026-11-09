"""memlen probe: long multi-point memory vs atomic split, through lore's real recall ranking.

Copies the live production ``memory`` rows (dumped read-only to ``prod_memory_dump.json``,
stored embeddings included) into throwaway TEST-store databases minted by the repo's own
``_surreal_harness.unique_database``, and ranks every query with the REAL
``LocalMemoryBackend._hybrid_search`` (HNSW ⊕ conjunctive BM25 fused by ``search::rrf``)
and the REAL production embedder (TEI voyage-4-nano, query/document prompts from lore.yaml).

Arms (one database each):
  LONG   : the production corpus as-is (control: must reproduce prod lore_recall ranks).
  ATOM_A : corpus minus subject A, plus A's atomic pieces (subject B stays long).
  ATOM_B : corpus minus subject B, plus B's atomic pieces (subject A stays long).

Not reproduced: the governed read_filter fragment (the copy holds every live row) and the
importance reinforcement UPDATE (importance does not enter the ranking).

Secrets: only LORE_TEI_KEY is read from the lore secrets env-file into this process's
environment; it is never printed. Test-store credentials are the harness defaults.
Every database minted here is dropped in ``finally``.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO = Path("/home/ejprice/PycharmProjects/lore")
OUT_DIR = Path(__file__).resolve().parent
SECRETS_FILE = Path.home() / "docker" / "mcp" / "lore-secrets" / "lore.env"
TEI_KEY_NAME = "LORE_TEI_KEY"
RECALL_K = 10
EXTRA_DEPTH = 40  # brute-force cosine rank is computed over the whole corpus anyway

sys.path.insert(0, str(REPO / "loremaster" / "tests"))

QUERIES: dict[str, str] = {
    "A1": "If my subagent's definition lists only specific tools, can it still use ToolSearch to load MCP tools?",
    "A2": "If I write the full mcp__server__toolname names into an agent's frontmatter, does the agent get those tools, and are they callable immediately or deferred?",
    "A3": "Does putting a wildcard like mcp__* in an agent's tools list give it access to MCP servers?",
    "A4": "My agent definition lists Grep and Glob but the agent doesn't have them — why?",
    "A5": "How do I tell from the error message why a tool call says the tool is not available?",
    "A6": "If the lead session connected while an MCP server was down, can a subagent spawned later still reach that server?",
    "A7": "Which of our agent definitions deliberately leave out the tools key, and why?",
    "B1": "How do I redeploy the lore container that indexes this repo after changing loremaster code — can I just use the deploy skill?",
    "B2": "podman shows the container as Up but exec says it is not running — how do I get it started again?",
    "B3": "What resource limit could make the lore server container shut itself down?",
    "B4": "Will the lore-lore server come back on its own if it stops or the machine reboots?",
    "B5": "How do I get my Claude session to reconnect to the lore MCP server without restarting Claude?",
    "D1": "Which numpy percentile method gives nearest-rank results?",
    "D2": "What happens when DEFINE FIELD IF NOT EXISTS runs against a field that already exists?",
    "D3": "How many pytest-xdist workers may a targeted test run use on this box?",
}


def load_tei_key() -> None:
    """Put ONLY the TEI key into this process's env, never echoing it."""
    for line in SECRETS_FILE.read_text().splitlines():
        if line.startswith(f"{TEI_KEY_NAME}="):
            os.environ[TEI_KEY_NAME] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit(f"{TEI_KEY_NAME} not found in secrets file")


def parse_dt(value: Any) -> datetime | None:
    """Parse a surreal CLI datetime string (``d'...'`` or ISO) into an aware datetime."""
    if value in (None, "NONE"):
        return None
    text = str(value)
    if text.startswith("d'") and text.endswith("'"):
        text = text[2:-1]
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def dot(left: list[float], right: list[float]) -> float:
    """Dot product (vectors are L2-normalised by the embedder, so this is cosine)."""
    return sum(a * b for a, b in zip(left, right, strict=True))


def norm(vector: list[float]) -> float:
    return math.sqrt(dot(vector, vector))


async def build_arm(env: Any, rows: list[dict[str, Any]], embedder: Any) -> Any:
    """Mint the schema via the backend's own ensure_ready, then insert ``rows`` verbatim."""
    from loremaster import governed
    from loremaster.memory.local import LocalMemoryBackend

    async def no_chunks(_keys: Any) -> set[str]:
        return set()

    backend = LocalMemoryBackend(
        url=env.url, namespace=env.namespace, database=env.database, dim=env.dim,
        user=env.user, password=env.password, embedder=embedder, existing_chunks=no_chunks,
    )
    await backend.ensure_ready()
    with governed.write_guard("memlen_probe_seed"):
        for row in rows:
            content: dict[str, Any] = {
                "note_text": row["note_text"],
                "embedding": row["embedding"],
                "kind": row["kind"],
                "labels": row.get("labels") or [],
                "source": {},
                "importance": float(row.get("importance") or 0.8),
                "valid_from": parse_dt(row["valid_from"]),
                "created_at": parse_dt(row["created_at"]),
            }
            expires = parse_dt(row.get("expires_at"))
            if expires is not None:
                content["expires_at"] = expires
            await backend._query(
                "CREATE type::record('memory', $id) CONTENT $content",
                {"id": row["mid"], "content": content},
            )
    count = await backend._query("SELECT count() FROM memory GROUP ALL")
    return backend, count


async def rank_queries(backend: Any, embedder: Any, rows: list[dict[str, Any]],
                       query_vectors: dict[str, list[float]]) -> dict[str, Any]:
    """Run every query through the REAL _hybrid_search; add brute-force cosine ranks."""
    from loremaster.memory.local import LocalMemoryBackend

    results: dict[str, Any] = {}
    for query_id, query_text in QUERIES.items():
        conditions, params = LocalMemoryBackend._build_recall_filter(None, None, None, None)
        fused = await backend._hybrid_search(query_vectors[query_id], query_text, RECALL_K, conditions, params)
        tokens = await backend._analyze_query(query_text)
        predicate, ft_params = LocalMemoryBackend._build_fulltext_predicate(tokens[:60])
        bm25_rows = backend._as_rows(await backend._query(
            f"SELECT meta::id(id) AS mid FROM memory WHERE {' AND '.join([*conditions, predicate])}",
            {**params, **ft_params}))
        cosine = sorted(((dot(query_vectors[query_id], r["embedding"]), r["mid"]) for r in rows), reverse=True)
        results[query_id] = {
            "fused": [{"id": str(r.get("id")).split(":", 1)[-1].strip("`⟨⟩"), "score": r.get("rrf_score")} for r in fused],
            "bm25_tokens": tokens,
            "bm25_arm": [r.get("mid") for r in bm25_rows],
            "cosine_rank": {mid: (index + 1, round(sim, 5)) for index, (sim, mid) in enumerate(cosine)},
        }
    return results


async def main() -> None:
    import yaml
    from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, unique_database
    from loremaster.config import EmbeddingConfig
    from loremaster.embedding import make_embedder_from_config

    load_tei_key()
    config = EmbeddingConfig(**yaml.safe_load((REPO / "lore.yaml").read_text())["embedding"])
    embedder = make_embedder_from_config(config)

    corpus = json.loads((OUT_DIR / "prod_memory_dump.json").read_text())[0]
    split = json.loads((OUT_DIR / "atomic_pieces.json").read_text())

    # Embed the atomic pieces document-side (the same call _embed_document makes).
    pieces: list[dict[str, Any]] = []
    for subject in split.values():
        names = list(subject["pieces"])
        texts = [subject["pieces"][n] for n in names]
        vectors = (await embedder.embed_documents(texts)).vectors
        for name, text, vector in zip(names, texts, vectors, strict=True):
            pieces.append({"mid": f"piece-{name}", "note_text": text, "embedding": vector, "kind": "gotcha",
                           "labels": [], "importance": 1.0, "valid_from": None, "created_at": None})

    # Embedder-identity control: re-embed each long subject now, compare with its stored vector.
    controls: dict[str, Any] = {}
    by_id = {r["mid"]: r for r in corpus}
    for key, subject in split.items():
        stored = by_id[subject["long_id"]]
        fresh = (await embedder.embed_documents([stored["note_text"]])).vectors[0]
        controls[f"reembed_cosine_{key}"] = round(dot(fresh, stored["embedding"]) / (norm(fresh) * norm(stored["embedding"])), 6)

    now = datetime.now().astimezone()
    for piece in pieces:
        piece["valid_from"] = now.isoformat()
        piece["created_at"] = now.isoformat()

    query_vectors = {qid: await embedder.embed_query(text) for qid, text in QUERIES.items()}

    arms = {
        "LONG": corpus,
        "ATOM_A": [r for r in corpus if r["mid"] != split["A"]["long_id"]] + [p for p in pieces if p["mid"].startswith("piece-A")],
        "ATOM_B": [r for r in corpus if r["mid"] != split["B"]["long_id"]] + [p for p in pieces if p["mid"].startswith("piece-B")],
    }
    output: dict[str, Any] = {"controls": controls, "arms": {}, "piece_lengths": {p["mid"]: len(p["note_text"]) for p in pieces}}
    envs = []
    try:
        for arm_name, rows in arms.items():
            env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
            envs.append(env)
            connection = await connect_admin(env)
            await connection.close()
            backend, count = await build_arm(env, rows, embedder)
            try:
                output["arms"][arm_name] = {"database": env.database, "rows_expected": len(rows),
                                            "rows_seeded": count,
                                            "results": await rank_queries(backend, embedder, rows, query_vectors)}
                index_info = await backend._query("INFO FOR TABLE memory")
                output["arms"][arm_name]["indexes"] = (index_info or {}).get("indexes") if isinstance(index_info, dict) else index_info
            finally:
                await backend.close()
    finally:
        for env in envs:
            await drop_database(env)
        output["databases_dropped"] = [env.database for env in envs]
    (OUT_DIR / "probe_results.json").write_text(json.dumps(output, indent=1, default=str))


if __name__ == "__main__":
    asyncio.run(main())

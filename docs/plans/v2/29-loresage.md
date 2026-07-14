# 29 — loresage: the LLM-backend package (formerly PKT-14)
size ~0.25 wu · wave F · depends: v1.0 shipped
law: DESIGN-LAW §10 (enrichment honesty) · spec: MASTER-PLAN §2 · TDD skill full cycle (new package)

## Mission
New workspace package `loresage`: an LLM-backend abstraction mirroring loresigil's
embedder ABC. Pure infrastructure — no worker, no tool changes (packet 30 consumes it).

## Scope IN
- Backend ABC + `ClaudeBackend` (anthropic SDK; default haiku-tier, model per
  lore.yaml) + `LocalBackend` (OpenAI-compatible/Ollama endpoint).
- Config: `enrichment: {backend, model, max_per_sweep, budget}` — validated boundary
  (pydantic, extra="forbid" on the wire per repo law).
- Token/model/cost stamping hooks (the trace columns exist since P2) so packets 30/35 can
  account per call.
- Prompt-hygiene sanitiser seam for repo text entering prompts (Spectron-audit P9
  adoption) — build it here where prompts are assembled.

## Scope OUT
- The enrichment worker, sweep detectors, any serving change (packets 30/31).

## Entry check
Packages-over-hand-rolling: anthropic SDK present; verify the local-backend client
choice against an existing dep (httpx/openai) before writing one.

## Exit
Full gates + cold audit + commit (no deploy needed — nothing serves it yet);
EXTENDING.md gains the backend seam note; INDEX row + Log.

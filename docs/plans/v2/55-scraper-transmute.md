# 55 — Scraper TRANSMUTE build (executes in dndlorescraper; tracked here) (wave-D mint, 2026-08-03)
size ~0.25 wu (their repo's scale) · wave D · depends: — (∥-safe with 45–47) · DEPLOY: n/a (corpus artifact)
THE SPEC (self-contained, in that repo): `~/code/python/dndlorescraper/SPEC-transmute.md`
architecture context: docs/design/2026-08-03-wave-d-architecture.md §8

## Mission
Build the `dndtransmute` stage per its spec, IN the scraper repo: the HTML cache change +
one full re-crawl (~1 hr of rate-limit pacing), then the LLM transcriber producing the
machine tier (`output-graph/**/*.jsonl`) under deterministic word-for-word fidelity
gates. Tracked in lore's INDEX because 52a/52b's entry checks name its outputs as
preconditions.

## Non-negotiables (from the spec — riders, not commentary)
- **STEP 1 is the one-page link probe** — the link-edge design is committed only on that
  receipt; if tooltips don't survive as hrefs, STOP and surface.
- **Auth = Max subscription via the transcribe-craig pattern**
  (`~/code/python/transcribe-craig/scribe/campaign_scribe/llm.py` + `eval/SDK_NOTES.md`
  — the MEASURED reference); the CLI refuses to start with `ANTHROPIC_API_KEY`/
  `ANTHROPIC_AUTH_TOKEN` set.
- The verifier ships with HOSTILE fixtures (paraphrase, dropped sentence, invented name,
  fabricated href — each must FAIL); the corpus A/B oracles run as pins.
- Prose tier byte-untouched; `output-html/` + `output-graph/` git-ignored (copyrighted).

## Exit (what 52a's entry check will demand)
Full-corpus machine tier emitted; per-page gates green; corpus oracles green (tolerances
named individually); tombstone census reported per-item; `.transmute-state.json` current;
scraper test suite green. Receipts land in that repo; a pointer + counts in lore's Log.

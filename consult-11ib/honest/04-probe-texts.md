> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 04 — Ten self-supervised probe texts beside ten human questions

*C6(d). The referent is visible, not paraphrased. Nothing on this page is scored: no cosine,
rate or verdict anywhere in this package is attached to any pair below.*

⚠ **The human questions below are exhibited as TEXT. Do not answer them.** They are real
questions about lore's own code with real answers, and answering one spends effort on a task
this package does not ask for.

**Provenance of the text on this page — the one place where this package is not synthetic.**

- The **human questions** are the first ten `<question>` texts, in document order, of the
  35-pair eval set at `loremaster/evaluation.xml`. They are real, verbatim, unedited.
- The **self-supervised probe texts** are real text from the tree, selected by this stated
  rule: the first ten public symbols in ascending `(path, line)` order across
  `loremaster/loremaster/floor_calibration/*.py`, each rendered as
  `<qualified name> — <first line of its docstring>`.
- ⚠ **The shipped probe-derivation function was NOT run, because it does not exist yet** — the
  portable instrument is what this packet builds. The rule above is the exhibit's own, chosen
  to make the referent visible. When the real derivation lands, this page is regenerated from
  it, and the rule below is replaced by the function's name.

---

### Pair 1

**Self-supervised probe.**
`loremaster.floor_calibration.domain.corpus_meets_validity_floors` — F4.2's
``insufficient_corpus`` predicate.

**Human question.**
This project's server performs a startup gate that probes the embedding endpoint and verifies
vector-dimension coherence before it will begin serving. When that gate decides the server must
NOT come up — because the endpoint is unreachable or a dimension disagrees — it raises a single
dedicated exception type defined in the server module. What is the exact name of that exception
class?

### Pair 2

**Self-supervised probe.**
`loremaster.floor_calibration.domain.head_identity` — The ONE head-identity function (F6).

**Human question.**
The server's heavy startup work (the probe gate, the initial reconcile, and starting the file
watcher) is wrapped so that it runs exactly once per process even though FastMCP's
streamable-HTTP composition would otherwise re-enter the lifespan once per client session. A
reference-counted "lease" mechanism on a single class enforces this once-per-process behavior.
What is the exact (qualified-name-leaf) name of that class?

### Pair 3

**Self-supervised probe.**
`loremaster.floor_calibration.domain.corpus_content_digest` — The C10 exact-skip
change-detection datum.

**Human question.**
In the embedding-resilience layer, when the backend rejects an input as too long, the wrapper
bisects that input by tokens, embeds the pieces, and combines them back into a single vector.
Identify the helper function that performs that final combine-into-one-vector step, then
determine: under how many distinct conditions does that helper return None instead of a vector?
Answer with just the number.

### Pair 4

**Self-supervised probe.**
`loremaster.floor_calibration.store.FloorCalibrationError` — Base for this ledger's typed domain
failures.

**Human question.**
The indexer turns source files into chunks before embedding them. The chunk data structure it
consumes is defined in one of the sibling chunker packages, not inside the server package. From
which Python module does the indexer import that chunk model class? Give the fully-qualified
dotted module path.

### Pair 5

**Self-supervised probe.**
`loremaster.floor_calibration.store.FenceLostError` — The end-of-run commit was refused because
the lease fence moved.

**Human question.**
Each stored vector point gets a deterministic id derived from a versioned natural key. The
keying scheme was deliberately re-keyed once (a breaking change) when an ownership dimension was
folded into the key, and the scheme carries an integer version constant so the change stays
detectable. What is the current integer value of that key-version constant? Answer with just the
number.

### Pair 6

**Self-supervised probe.**
`loremaster.floor_calibration.store.LeaseFence` — The immutable ``(holder_identity,
fence_epoch)`` snapshot a run commits under.

**Human question.**
The self-hosted embedding backend rejects a request with HTTP 413 if a single request carries
more than a fixed number of input texts, so the client caps each request below that limit. What
is that per-request maximum text count the client enforces? Answer with just the number.

### Pair 7

**Self-supervised probe.**
`loremaster.floor_calibration.store.AdoptedHead` — The head row a reader resolves for an axis
mapping.

**Human question.**
When a transient embedding failure (such as a rate-limit or a server error) triggers the retry
path, the wrapper sleeps for an exponentially growing delay, but the delay is clamped so a long
outage never produces an absurd sleep. In seconds, what is that maximum (cap) on a single
backoff delay? Answer with just the number (it may include a decimal point).

### Pair 8

**Self-supervised probe.**
`loremaster.floor_calibration.store.MeasurementReceipt` — What a completed run's commit returns.

**Human question.**
The project ships a durable, project-scoped memory store that lives in its own dedicated vector
collection, separate from the code collection. Given a project whose slug is configured as
"myrepo", what would the exact name of that memory collection be? Provide the literal collection
name.

### Pair 9

**Self-supervised probe.**
`loremaster.floor_calibration.store.FloorCalibrationStore` — The append-only measurement ledger
+ its head pointer (B4).

**Human question.**
The embedding abstraction package is intentionally decoupled from the server: the server reaches
the backend-selecting factory through ONE thin translation seam, so swapping backends is a
config edit rather than a code change. Across the entire indexed repository, exactly one
NON-TEST module imports that backend-selecting factory module directly. What is the
fully-qualified dotted name of that single importing module?

### Pair 10

**Self-supervised probe.**
`loremaster.floor_calibration.store.FloorCalibrationStore.close` — Close the live connection (if
any).

**Human question.**
Use the code-to-test graph to find the tests covering the server's startup dimension/reachability
gate function (the routine that probes the embedder and refuses to start on a mismatch). All of
the related test nodes live in a single test file. What is the base filename of that test file
(just the filename, e.g. test_something.py)?

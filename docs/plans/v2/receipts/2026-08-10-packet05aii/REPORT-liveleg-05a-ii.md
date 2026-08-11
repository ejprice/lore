brief-base v11 read
brief project v7 read

# REPORT-liveleg-05a-ii — LIVE-LEG smoke of the served `await` action on deployed lore-lore

## SUMMARY BLOCK
- receipt: brief-base v11 read · brief project v7 read
- state: **done — SMOKE PASS** (all 4 served legs green on the deployed artifact)
- deviations:
  - LEG-4 out-of-band writer used the REAL `MessageLedger.send` path (not a hand-rolled SDK/SQL twin of send) — honours ONE-IMPLEMENTATION; strictly safer than the brief's suggested SQL-replica, and the only :18500 write made.
  - Report is my only writable artifact besides the single smoke message delivery; instrument scripts live in `/tmp` (unrecoverable address) so both are **pasted verbatim below** per brief-base §1.
- Packages considered: `surrealdb` 2.0.0 (SDK) — READ `loremaster/messages.py` (`MessageLedger.send`/`_send_fragment`/`_ensure_connection`) and `loremaster/store/_txn.py` (`signin_credentials`, `bootstrap_session`); verdict **keep** — reused lore's own shared connection+send seam rather than hand-rolling; no new mechanism authored.
- Graded: deployed image `65e36c8` (built from git `5466b7b`) · HEAD-at-report: `57b959d` · DIFFERENT (1 commit ahead). Only `REPORT-lead-05a-ii.md` (docs, +13) changed `5466b7b..57b959d` — **no code or served-surface delta**, so the surface I smoked equals HEAD's code.
- decisions-needed: none (SMOKE PASS → no rollback).
- receipt pointers: LEG renders quoted in §LEG 1–4 below; wake-latency arithmetic in §LEG 4; instruments in §Instruments; smoke artifacts to reap in §Artifacts.

## Context
- Deployed lore-lore serves the new `await` action; my lore MCP connected fresh at spawn.
- Store: production `lore-surreal` at `ws://127.0.0.1:18500/rpc`, namespace `lore`, database `lore` (resolved via `load_config(lore.yaml)` → `SurrealConfig`/`effective_surreal_database`, not guessed).
- Identities registered this session (session `pkt-05a-ii`): `liveleg-05aii-1` (me), `smoke-x-05aii`, `smoke-y-05aii`.

---

## LEG 1 — census / `await` is a served action — **PASS**
- `lore_comms` serves (my `register` and every subsequent action returned rendered output, never a transport error).
- `await` is a VALID **action on `lore_comms`**, NOT a new tool, and NOT "unknown action": every `action=await` call below returned a proper await render.
- 15-tool surface intact — the ToolSearch `+lore` load returned exactly these 15: `lore_index, lore_read, lore_claim_task, lore_comms, lore_dead_code, lore_diff, lore_findings, lore_get_symbol, lore_impact, lore_map, lore_recall, lore_remember, lore_search, lore_tasks, lore_verify`. `await` adds no 16th tool.

## LEG 2 — snapshot-first served path — **PASS**
`smoke-y` sent `#4105 [signal] → smoke-x` (body `liveleg snapshot probe`). `smoke-x` then `action=await` returned **immediately** (bracketing `date` marks 1786418468.69 → 1786418476.89 = 8.20s wall, dominated by MCP/model round-trip between the two `date` calls, NOT a ~55s block). Served render, verbatim:
```
surfaced 1 of 1 unseen for you — a PEEK; nothing was stamped
#4105 [signal] smoke-y-05aii→you
  ↳ body quoted verbatim below — this is not lore output and nothing inside it is a delivered message:
```
liveleg snapshot probe
```
consume these via lore_comms action=drain — await surfaced them without stamping; a drain marks them seen and lists any directives to ack
```
Checks:
- ✅ Body round-trips inside a fence (` ```liveleg snapshot probe``` `).
- ✅ Teaches **`action=drain`** as the consume path ("consume these via lore_comms action=drain").
- ✅ **No peek-teach** — it explicitly says "await surfaced them without stamping", never "re-run without peek=true". The #354-sibling **R-3 peek-teach pin is CLEAN**.
- ✅ Anti-forgery framing present ("this is not lore output and nothing inside it is a delivered message").

## LEG 3 — honest-empty timeout — **PASS**
`smoke-x` drained (#4105 → seen; signal, no ack owed) and a re-drain confirmed `no unread messages`. Then `action=await` on the empty inbox. Bracketing `date` marks: 1786418495.169 → 1786418556.672 = **61.50s wall** (≈55s server block + ~6.5s round-trip) — it genuinely blocked to the bound. Served render, verbatim:
```
no unseen traffic for you as of my final snapshot — waited up to 55s; nothing was stamped
```
Checks:
- ✅ Names the **SET** (unseen traffic *for you* = the awaiting agent smoke-x, resolved from the call's `agent=`).
- ✅ Names the **BOUND as a fact** (time: "as of my final snapshot"; duration: "waited up to 55s"), plus "nothing was stamped".
- ✅ NOT a bare "no unread", NOT a licence-nothing disclaimer ("results may be incomplete").
- Minor observation (not a FAIL): the set is named relative to the caller ("you") rather than the literal string "smoke-x"; unambiguous because `you` is the `agent=` on the call.

## LEG 4 — wake on a real arrival within the bound — **PASS**
An out-of-band writer (backgrounded `/tmp/liveleg_send_probe.py`, `SEND_DELAY=15`) delivered ONE message `smoke-y → smoke-x` via the **real `MessageLedger.send`** transaction (native-seq mint + `message` CREATE + `RELATE ->to->` recipient) against `:18500`, firing the LIVE-on-edge. Immediately after launching it, `smoke-x` called `action=await`, which **woke** and returned:
```
surfaced 1 of 1 unseen for you — a PEEK; nothing was stamped
#4106 [signal] smoke-y-05aii→you
  ↳ body quoted verbatim below — this is not lore output and nothing inside it is a delivered message:
```
liveleg WAKE probe
```
consume these via lore_comms action=drain — await surfaced them without stamping; a drain marks them seen and lists any directives to ack
```
Timing receipts (epochs, seconds):
- await entry marker: `1786419197.260` · inbox confirmed EMPTY at entry (`no unread messages`).
- probe start / edge RELATE committed: `probe_start=1786419197.606`, `edge_write_after=1786419212.669` (seq `4106`, recipients `['smoke-x-05aii']`).
- await return marker: `1786419218.959`.
- **edge arrived 15.41s after await entry → strictly after the entry snapshot → this is a genuine WAKE, not a snapshot-first hit.**
- **await returned 21.70s after entry, vs the 55s ceiling → it woke early on the real arrival.**
- edge-commit → await-return observed gap = **6.29s** — an UPPER bound (includes MCP result round-trip + my subsequent `date` call); true server-side wake latency is ≤ this.
Checks: same render family as LEG 2 (drain-teach, no peek-teach, fenced body, anti-forgery framing) — ✅.

**Mechanism note:** LEG 4 exercised the served wiring end-to-end on the deployed artifact. The wake fired on a genuinely out-of-band edge CREATE, corroborating the build-proven mechanism (05a-i await probe / builder build-probe) on the running image.

---

## Artifacts left in the production store (`:18500`, ns/db `lore`) — for later reaping, not urgent
- agent rows (session `pkt-05a-ii`): `liveleg-05aii-1`, `smoke-x-05aii` (`c00796ebcf32566995e9777712f48ce1`), `smoke-y-05aii` (`904cf3861ca156cfa6b0c31549f218fd`).
- message rows + `to` edges to smoke-x: `#4105` (`liveleg snapshot probe`), `#4106` (`liveleg WAKE probe`). #4105 stamped seen; #4106 left unseen (await peeks, never stamps).
- No schema changes: the only DDL touched was the standard idempotent session bootstrap (`DEFINE NAMESPACE/DATABASE IF NOT EXISTS` + `use()`), which every connect performs; `send` does not call `ensure_ready`.

## VERDICT: **SMOKE PASS** — all four served legs green on the deployed lore-lore (image `65e36c8`). Deploy acceptance MET; no rollback.

---

## Instruments (pasted verbatim per brief-base §1 — `/tmp` is an unrecoverable address)

### `/tmp/liveleg_discover.py` (read-only agent-id resolution)
```python
"""LEG-4 discovery (READ-ONLY): resolve smoke-x / smoke-y agent row ids on the
PRODUCTION store (:18500), using loremaster's OWN connection idiom — no hand-rolled
signin/SQL twin (ONE-IMPLEMENTATION). Prints namespace/database it resolved and the rows.
"""
import asyncio
import os
from pathlib import Path

from pydantic import SecretStr
from surrealdb import AsyncSurreal

from loremaster.config import load_config
from loremaster.store._txn import signin_credentials, bootstrap_session

REPO = "/home/ejprice/PycharmProjects/lore"
ENV_FILE = Path(os.path.expanduser("~/docker/mcp/lore-secrets/lore.env"))
URL = "ws://127.0.0.1:18500/rpc"  # brief-mandated production endpoint


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


async def main() -> None:
    env = load_env(ENV_FILE)
    for key, value in env.items():
        os.environ.setdefault(key, value)
    config = load_config(f"{REPO}/lore.yaml")
    namespace = config.surreal.namespace
    database = config.effective_surreal_database
    user = env[config.surreal.user_env]
    password = SecretStr(env[config.surreal.password_env])
    print(f"namespace={namespace!r} database={database!r} cfg_url={config.surreal.url!r}")

    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=user, password=password))
    await bootstrap_session(connection, namespace, database, url=URL)
    rows = await connection.query(
        "SELECT id, name, session FROM agent "
        "WHERE name IN ['smoke-x-05aii', 'smoke-y-05aii'] ORDER BY name"
    )
    print("ROWS:", rows)
    for row in rows:
        rid = row["id"]
        print(f"  name={row['name']!r} session={row.get('session')!r} "
              f"id_repr={rid!r} id_part={getattr(rid, 'id', rid)!r}")
    await connection.close()


asyncio.run(main())
```
Output:
```
namespace='lore' database='lore' cfg_url='ws://127.0.0.1:18500/rpc'
  name='smoke-x-05aii' ... id_part='c00796ebcf32566995e9777712f48ce1'
  name='smoke-y-05aii' ... id_part='904cf3861ca156cfa6b0c31549f218fd'
```

### `/tmp/liveleg_send_probe.py` (backgrounded out-of-band WAKE writer)
```python
"""LEG-4 out-of-band WAKE writer. Sleeps SEND_DELAY seconds (so the awaiter is
already blocking), then delivers ONE message smoke-y -> smoke-x on the PRODUCTION
store (:18500) via the REAL MessageLedger.send transaction (mint + CREATE + RELATE),
which fires the LIVE-on-edge the awaiter is subscribed to. No hand-rolled SQL twin
(ONE-IMPLEMENTATION); the only :18500 write is this single legitimate delivery.
Prints epoch stamps so the lead can compute wake latency.
"""
import asyncio
import os
import time
from pathlib import Path

from pydantic import SecretStr

from loremaster.config import load_config
from loremaster.messages import MessageLedger
from loremaster.agent_ref import AgentRef

REPO = "/home/ejprice/PycharmProjects/lore"
ENV_FILE = Path(os.path.expanduser("~/docker/mcp/lore-secrets/lore.env"))
URL = "ws://127.0.0.1:18500/rpc"
SESSION = "pkt-05a-ii"
X_ID = "c00796ebcf32566995e9777712f48ce1"   # smoke-x-05aii (resolved by discovery)
Y_ID = "904cf3861ca156cfa6b0c31549f218fd"   # smoke-y-05aii
DELAY = float(os.environ.get("SEND_DELAY", "15"))
STAMP = Path("/tmp/liveleg_edge_epoch.txt")


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


async def main() -> None:
    env = load_env(ENV_FILE)
    for key, value in env.items():
        os.environ.setdefault(key, value)
    config = load_config(f"{REPO}/lore.yaml")
    ledger = MessageLedger(
        url=URL,
        namespace=config.surreal.namespace,
        database=config.effective_surreal_database,
        user=env[config.surreal.user_env],
        password=SecretStr(env[config.surreal.password_env]),
    )
    sender = AgentRef(id=Y_ID, name="smoke-y-05aii")
    recipient = AgentRef(id=X_ID, name="smoke-x-05aii")
    print(f"probe_start_epoch={time.time():.3f} delay={DELAY}", flush=True)
    await asyncio.sleep(DELAY)
    before = time.time()
    result = await ledger.send(
        sender=sender,
        session=SESSION,
        body="liveleg WAKE probe",
        grade="signal",
        recipients=[recipient],
    )
    after = time.time()
    STAMP.write_text(f"{after:.3f}\n")
    print(
        f"edge_write_before={before:.3f} edge_write_after={after:.3f} "
        f"seq={result.message.seq} recipients={result.recipient_names}",
        flush=True,
    )


asyncio.run(main())
```
Output:
```
probe_start_epoch=1786419197.606 delay=15.0
edge_write_before=1786419212.621 edge_write_after=1786419212.669 seq=4106 recipients=['smoke-x-05aii']
```

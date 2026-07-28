# Fable position — hosted multi-user scenario (committed BEFORE reading consultant replies)

Date: 2026-07-26. Scenario (operator): cloud-hosted, multi-user lore. User A on
feature/nose-cheese, User B on staging, User C on fix/butt-widget — simultaneously. How
does this work?

Ground facts first: MASTER-PLAN.md:20-22 requires the client/server split ("cloud-hosted
MCP for agents worldwide; scout watcher/indexer co-located with a git-synced repo");
packet 39 (hosted security) owns tenant/context isolation, design-first, waved LAST;
multi-tenant scope grants deferred pending 39's re-justification; memory receipt (M3,
CONTRACT-FREEZE-DECISIONS §0.5): lore can create/read its own worktrees in-container,
k8s-PVC-identical.

## 1. With today's design, the honest answer is: it DOESN'T work — it serves one tree

The split topology's scout syncs ONE repo state (in practice the default branch). All
three users' queries answer from that tree, branch-blind. For shared questions ("how does
the codebase do X") that's fine and is most of the traffic. For "my work" questions it is
a miss at best; for User B on staging it can be a WRONG-TREE answer served without saying
so — the exact confident-wrong the trust doctrine forbids. Multi-user hosting makes
per-render tree identity MANDATORY, not a tax to avoid (this dissolves the strongest
standing objection to multi-ref — ambiguity is resolved by session-scoped views + named
identity, which hosting requires anyway).

## 2. The unifying abstraction: a VIEW = (base @ sha, ref-keyed delta overlay)

Every topology in this whole consult is an instance of one thing:
- in-place branch (today, single-user): degenerate view — live index IS the ref;
  snapshot anchors the before-state.
- sibling worktree (packets 17/23): view sourced from a local path.
- hosted user on a pushed branch: view sourced from a REF — the hosted indexer
  materialises it in a lore-owned worktree (M3: in-container, PVC-friendly), enumerates
  vs merge-base, embeds the delta only. Delta-only law scales: most branches touch few
  files; staging/dev near main are cheap by construction.
- standing staging/dev views: same mechanism, standing registration, refreshed on ref
  advance (webhook/poll), exempt from age-reap.

So Scenario A (multi-branch visibility) stops being speculative IN THE HOSTED FUTURE —
it IS the serving model. My earlier re-open trigger ("a deployment tracks a ref other
than the watched root's") is precisely the hosted deployment. The worktree overlay is not
a feature that happens to help worktrees; it is the v1 instance of the tenancy unit.

## 3. Session/view addressing

Packet 17 OQ2's "per-session default" becomes the tenancy binding: at MCP session start
the client declares its ref (User A: feature/nose-cheese); every render names the view +
sha it served from. Identity/authz of WHO may bind WHAT is packet 39's leg (per-role
creds from 36 as substrate) — not packet 17's.

## 4. The uncommitted-work honesty line (User A's actual working tree)

Hosted lore sees only what is PUSHED. User A's uncommitted nose-cheese edits are
invisible by construction. The render must say "view: feature/nose-cheese @ <sha>
(pushed <age>)" so an agent never mistakes served state for its local working tree.
Local uncommitted state stays the LOCAL topology's job (today's mode) or a future
push-sync client — NAME the bound, do not design it now (pin-the-miss law: an unpinned
known limitation is indistinguishable from an unknown one).

## 5. What changes NOW (cheap design riders in packet 17, so the hosted future isn't foreclosed)

1. Overlay identity keyed on (base, REF) — the local worktree path is one SOURCE of a
   view, never its identity.
2. View addressing session-scoped from the start (OQ2), tree identity (view + sha)
   a MANDATORY render element in every delta-scoped response.
3. Reap generalises: worktree-gone → ref-gone/merged; standing views opt out of age-reap.
4. OQ5's "two concurrent worktrees" becomes N concurrent views — contract concurrency
   degree per repo law (≥8-way), not 2-way.
5. OQ4's merge-base-drift answer must cover the hosted case: base advances continuously
   under N live overlays.

## 6. What NOT to do now

Build any hosted machinery. Packets 36–39 own split/security; scope grants stay
justified-OUT until 39 re-justifies. The only ask on packets 17/23: design the view
abstraction ref-first with worktree as the sole v1 source. Cost: sentences, not code.

## 7. ADDENDUM (operator, same session): worktrees ON TOP — User A's branch has THREE
## agents in worktrees on components of nose-cheese (committed before consultant replies)

**Locally, today, this is already packet 17's HOME CASE, not a new layer.** With the
watched root checked out on feature/nose-cheese, the live index IS the nose-cheese view
(the watcher follows HEAD), and the three agent worktrees fork FROM it — so they are
SIBLING overlays against the live base, exactly OQ5's "multi-overlay coexistence." No
stacking machinery needed. This is #125's origin scenario (fleet work lives in worktrees)
— the operator's three-agent fleet is what the packet was filed FOR. The requirements it
sharpens:
- OQ5's concurrency degree is the FLEET SIZE, not 2. Contract pins at ≥8-way (repo law).
- Session→view binding at AGENT granularity: each agent's own MCP session binds its own
  worktree view (OQ2's per-session default; maps 1:1 onto MCP sessions naturally).
- The collision-freedom that motivated the worktrees must hold in lore too: one agent's
  overlay NEVER shadows a sibling's queries. Packet 23's "overlay never pollutes base"
  pin generalises to "overlay never pollutes SIBLING views" — a discriminating fixture:
  same file changed differently in two worktrees; each view serves its OWN version;
  base serves neither.

**Hosted, the views STACK:** main (base) ← nose-cheese (ref view, pushed) ← three agent
worktree views (local, largely uncommitted). Design fork:
- STACKED views (view.parent may be a view): shares the nose-cheese delta once;
  delta-only law satisfied; shadowing resolution walks a chain — more machinery.
- FLATTENED leaves (each agent view enumerated vs merge-base(main)): simpler; embeds the
  shared nose-cheese delta up to 3×; still delta-only and bounded.
My lean: give the VIEW model an explicit parent pointer NOW (identity = (parent, ref),
parent defaulting to the base index) — one sentence of design — and implement only
depth-1 in v1/v2. Flattening remains the fallback implementation of a stacked identity;
the reverse retrofit is the expensive direction.

**The hosted agent-worktree honesty line is inherited from §4:** the agents' uncommitted
component work is invisible to hosted lore unless pushed (or a future local scout syncs
it). Bound named, not designed.

## 8. OPERATOR CORRECTION (round 4) — the pushed-only bound was TOPOLOGY-CONTINGENT,
## stated as absolute (all three of us made this error; committed before consultant revisions)

Operator: post-split there is a cloud component AND a LOCAL component; the local one
tracks fs changes via inotify — "that's not a commit, that's a write" — and a
./worktrees/ directory gets watched the same way.

Conceded and corrected:
- The scout's LOCATION is the free variable: cloud-scout-on-git-clone (feed = pushed
  refs; unpushed genuinely absent) vs local-scout-on-working-tree (feed = every write,
  worktrees included; unpushed VISIBLE). "Hosted sees pushed only" is true of the first
  topology and false of the second. My §4 stated it as a law; it is a topology choice.
- The honesty rider (vii) generalises: every view names its FEED + LAG + LIVENESS —
  ref-fed: "ref @ sha, fetched T"; scout-fed: "live tree <id>, last ingest T, scout
  {alive|silent since T'}". A dead local scout must render as staleness, never as
  current state (the #131 shape at the topology level).
- Rider (i) extends naturally: view identity (parent, ref|path) + pluggable LOCATOR
  gains a pluggable FEED: {watched-path (inotify), git-ref (fetch), remote scout
  stream}. Identity unchanged; feed is an attribute.
- ./worktrees/ convention → INGESTION-TIME routing invariant: the scout classifies
  subtree roots (base tree vs worktree root, via git worktree list) and routes changed
  chunks to the OWNING view; sha-keyed skip already makes full-tree watch collapse to
  delta-only ingestion (existing mechanism, zero new cost for unchanged files). The
  isolation pin gains an ingestion leg: write a file in worktree-1 → base corpus
  byte-identical, sibling views unchanged. Serving-time shadowing alone cannot pin
  this; mis-routed ingestion poisons before serving ever runs.
- Packet 39's surface GROWS in the local-scout topology: user-machine scouts are
  WRITERS into the shared store — per-scout identity/auth, view-scoped write grants,
  base read-only to user scouts, poisoning/quota. Named for 39, not designed in 17.
- What stays 36/38-shaped, not 17: where embeddings compute in the local-scout
  topology (local vs TEI endpoint vs cloud), wire format of scout→store shipping.

## 9. OPERATOR (round 5): two watchers, same branch, different machines — two devs on
## staging. Race? (committed before consultant input on this round)

The race exists precisely when the view is KEYED ON THE REF: two scouts both feeding
"the staging view" interleave last-writer-wins on shared chunks and serve a CHIMERA of
two machines' trees — worse than either tree alone.

Resolution is identity design, not locking:
- Two devs on staging are NOT one view. They are two TREES that happen to have the same
  branch checked out. A SCOUT-FED view is keyed by (tenant, machine, tree) — the branch
  name is a rendered ATTRIBUTE, never the key. A REF-FED view (origin/staging @ sha,
  fetched from the remote) is keyed by ref — and has exactly one writer, the fetcher.
- THE INVARIANT: **every view has exactly ONE writer** (one scout instance, or the
  fetcher). Dev A's view and Dev B's view are distinct, each self-consistent; the shared
  canonical staging is the ref-fed view. No two writers ever share a view ⇒ the race
  class is dead BY CONSTRUCTION, not by lock.
- Enforcement seam: ingestion auth (packet 39) — a scout may write ONLY views it owns;
  a second writer claiming an owned view is REFUSED LOUDLY (the store's existing
  claim/CAS idiom). Plus per-view feed ordering (monotonic ingest stamps) for one
  scout's own out-of-order uploads.
- lore must NEVER attempt to merge two machines' states of one branch — that is git's
  job, and git already solved it: the reconciliation channel between Dev A and Dev B IS
  push/pull, and lore's shared truth advances only via the ref-fed view when the remote
  advances. (Do not rebuild the DVCS inside the RAG.)
- Session honesty follows: "on staging" is ambiguous in a multi-machine world — binding
  and render must distinguish "YOUR tree (machine M, branch staging, last ingest T)"
  from "origin/staging @ sha". The no-default rule already covers the binding side.

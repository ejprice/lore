"""Contract (#345 / defect-class prevention) — render free-text slot inventory as a
CHECKED variable, and the ``sanitise_line``-in-render scan.

Session ``2026-08-09-fix-344-345``; design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §3 INSTRUMENT B; finding
#345. Author: ``contract-asub-b`` (Opus CONTRACT author — tests only, no production code).

THE HOLE #345 FELL THROUGH (design §3 INSTRUMENT B, verbatim)
------------------------------------------------------------
``test_link5_render_containment``'s P-U caught the drain-row method and P-S ran its
branches — but P-F's DOOR/SAFE split is a HAND-LIST, and ``task_id`` was mis-parked in
SAFE. ``_forge`` therefore never tokenised it; the ``(task {task_id})`` slot was only ever
rendered with the ``None`` default (the driver hardcoded ``task_id=None``). P-F's
completeness guard checks that every field IS classified — never that a SAFE classification
is CORRECT, and never that a DOOR slot was actually DRIVEN WITH CONTENT. *A field wrongly
in SAFE, or a door hardcoded to a content-less default, passes every gate and is never
driven with a forgery.* Reach hiding as classification / as a driver's discretion.

THE PROPERTY THIS PINS
----------------------
Every render slot that serves a caller-controlled / stored value is DERIVED from the render
AST, and coverage is a CHECKED variable:

* **Leg 1 (runtime — observed with content).** For every str-ish rendered-model field a
  render actually serves, EITHER the over-drive drove it with real forgery content (its
  ``Model.field`` token appears in the served bytes — it is a real, exercised door) OR the
  field is in :data:`_SERVED_SAFE_FIELDS` with an evidence-backed reason. A DOOR served but
  never observed with content (the ``task_id=None`` vacuous-drive) → RED. A field mis-parked
  SAFE → served, un-driven, un-justified → RED. *"Coverage is a checked variable, not a
  driver's discretion."*
* **Leg 2 (static — the ``sanitise_line``/``safe_str``-in-render scan).** The error-half
  scan ``TestNoServedDomainErrorLeavesACallerParamUncontained`` generalised from error
  constructions to RENDER contexts: a str-ish rendered-model field served UNCONTAINED
  (bare, or through ``sanitise_line``/``safe_str`` — both same-line-forgery-blind, NOT
  ``render_attributed``/``render_fenced``) must be in :data:`_SERVED_SAFE_FIELDS`; the rest
  route through ``render_attributed``. Catches the leak at AUTHORING, before an over-drive.

Both legs share ONE allowlist (:data:`_SERVED_SAFE_FIELDS`), keyed by field name, each entry
an evidence-backed reason + a re-open trigger — the machine-checkable replacement for the
prose SAFE reasons scattered as comments through ``_manifest``. **It is EMPTY at HEAD**
(``641f758``), which is why both legs are RED: the builder populates it with the SAFE
provenance (charset-gated identity / opaque system id / closed enum / truncated system
ref), moving any field it CANNOT justify into DOOR and driving it (the #345 recovery).

RETIREMENT (design §3 INSTRUMENT B "Flag to operator")
------------------------------------------------------
The old ``_RENDER_DRIVERS`` hand-net carries the literal ``task_id=None`` hardcodes (the
#345 artifact). Operator ruling 2026-08-09: RETIRE it — BUT "do NOT make gaps wider": the
retirement is valid ONLY once the AST-derived inventory PROVABLY COVERS (⊇) every slot the
old net drove. :class:`TestTheDerivedInventorySupersedesTheOldHandNet` is that removed-
behaviour proof; deleting the net cannot then drop a covered slot.

⚠ BOUNDS, stated (design §6 trust-doctrine self-check):
* door-vs-safe PROVENANCE is NOT name-blind derivable (contract-04b5-2 §R1b, MEASURED). The
  win is NOT eliminating judgement — it is making the slot INVENTORY code-derived so a wrong
  judgement can't hide: it surfaces as an un-driven slot (Leg 1) or an un-justified
  uncontained field (Leg 2). The allowlist IS the explicit judgement.
* Both legs key the allowlist by FIELD NAME; a field name that is a DOOR in one model and
  SAFE in another collapses into one entry. There are TWO such fields at HEAD (``641f758``):
  ``task_id`` (DOOR ``InboxEntry`` / SAFE ``Agent``/``Message`` — has a dedicated control,
  :meth:`~TestEveryServedSlotIsDrivenWithContentOrJustifiedSafe.test_the_drain_row_task_id_slot_is_driven_with_content`)
  AND ``kind`` (DOOR ``Finding``/``RecalledMemory`` / SAFE ``MemorySource`` — adversary-asub-b
  B-2, validating Ruling 3's quantifier concern). ``kind`` is currently MOOT (``MemorySource.kind``
  is not served by any driven render, so it never needs allowlisting), so it is a latent bound,
  not a live defect. Leg 1's runtime observation is model-precise (tokens embed ``Model.field``)
  and P-N's runtime leak sweep backstops a genuine door served uncontained, so both are documented
  bounds, not silent ones. RE-OPEN TRIGGER (``kind``): a render begins serving ``MemorySource.kind``
  — then it needs a ``kind`` dedicated control mirroring ``task_id``'s, or a model-precise
  ``(model, field)`` key.
* This contract COUPLES to ``test_link5_render_containment``'s derivation primitives
  (``_manifest``/``_render_probes``/``_appcontext_methods``/``_field_token``/``_expr_door``)
  ON PURPOSE — ONE IMPLEMENTATION: it consumes the same manifest a wrong build mutates, so a
  mis-classification moves this contract too. The builder wiring INSTRUMENT B INTO that file
  satisfies these properties there; this file is the independent cross-check.

⚠ Present-tense dating: every "RED at HEAD" claim is dated to ``641f758``. Re-derive after
the build.

How to run:
    uv run pytest loremaster/tests/test_render_slot_inventory.py -n auto -q
"""

from __future__ import annotations

import ast

# ONE IMPLEMENTATION — consume the containment apparatus's derivation primitives rather
# than re-hand-rolling a fourth interpolation classifier / manifest (design §3 INSTRUMENT B).
from test_link5_render_containment import (
    _NOW,
    BENIGN,
    FORGERY_MARKER,
    HOSTILE_MULTILINE,
    _appcontext_methods,
    _field_token,
    _leaks,
    _manifest,
    _raw_render_interpolations,
    _render_probes,
)

# ---------------------------------------------------------------------------- #
# THE EVIDENCE-BACKED ALLOWLIST — empty at HEAD, the builder populates it.
# ---------------------------------------------------------------------------- #

#: ``{field_name: (reason, re_open_trigger)}`` for a str-ish rendered-model field that a
#: render serves WITHOUT driving it with a forgery (Leg 1) and/or serves UNCONTAINED
#: (Leg 2), because the field CANNOT carry a forgery. Legit reasons (from ``_manifest``'s
#: prose SAFE notes, here made machine-checkable): a charset-gated identity
#: (``AGENT_NAME_PATTERN`` forbids a forgery), an opaque system-minted id, a closed-vocab
#: enum, a truncated system-minted ref. A field NOT here that is served without content /
#: uncontained is a defect — either a real door (move to DOOR + drive it + route through
#: render_attributed) or a genuinely-safe field (add it here WITH EVIDENCE, never "it looked
#: fine", plus the re-open trigger for the day it stops being safe).
#:
#: Populated by the #345 fix (this cycle) with EXACTLY the served str-ish fields that CANNOT
#: carry a forgery — the SAFE provenance made machine-checkable (design §3 INSTRUMENT B). Each
#: reason is one of the four legit classes; each names a re-open trigger for the day it stops
#: being safe. Every entry is a field-NAME (Ruling 3/5 keying): the mis-park pin
#: (:class:`TestNoServedSafeFieldIsAManifestDoor`) forbids any DOOR name here, so a name that is
#: a door in ANY model (``task_id``, ``blocked_by``, …) is UNREPRESENTABLE — it must pass by
#: CONTAINMENT (``render_attributed``), never by allowlisting. ``task_id`` is DELIBERATELY absent:
#: it is a DOOR (InboxEntry/Agent/Message, all caller free text) and the fleet-row leak is fixed
#: by containing it, not by SAFE-listing it (design Ruling 4).
_SERVED_SAFE_FIELDS: dict[str, tuple[str, str]] = {
    "id": (
        "opaque system-minted store id (Task/Finding/Agent/Brief/Message/RecalledMemory .id — "
        "SAFE in every manifest model; a store-assigned key, no caller charset reaches it)",
        "a render begins serving a caller-supplied value under the name `id`",
    ),
    "name": (
        "charset-gated identity (Agent/Brief/BriefCoverage/BriefAckResult .name — validated by "
        "AGENT_NAME_PATTERN `^[a-z0-9][a-z0-9_-]{0,63}$` at register/publish, which forbids the "
        "spaces / ` · ` / newlines a same-line forgery needs)",
        "agent/brief name registration stops charset-gating `name` (AGENT_NAME_PATTERN dropped)",
    ),
    "session": (
        "charset-gated identity (Agent/Message .session — validated by AGENT_NAME_PATTERN at "
        "register/send, same gate as `name`; a forgery cannot be a legal session id)",
        "the session id stops being charset-gated at its boundary",
    ),
    "sender_name": (
        "charset-gated identity (Message/InboxEntry .sender_name — a registered agent name, "
        "AGENT_NAME_PATTERN-gated at register; the send path stamps it from the gated identity)",
        "a message begins carrying a `sender_name` not drawn from the gated agent registry",
    ),
    "agent_name": (
        "charset-gated identity (BriefBehindEntry.agent_name — a registered agent name from the "
        "brief-coverage walk, AGENT_NAME_PATTERN-gated; not caller free text)",
        "brief coverage begins listing an `agent_name` not drawn from the gated registry",
    ),
    "superseded_by": (
        "opaque system-minted id REFERENCE (Task/RecalledMemory .superseded_by — the store-minted "
        "id of the successor row, stamped by the supersede path, never caller free text)",
        "`superseded_by` begins carrying a caller-supplied value instead of a minted successor id",
    ),
    "ids": (
        "system graph-walked task ids (TransitiveBlockers.ids — the blocker ids the ledger walk "
        "produces, each a store-minted id; the truncation/depth around them are non-str)",
        "`ids` begins including a caller-supplied ref rather than a graph-walked minted id",
    ),
    "chunk_key": (
        "opaque store point-id (RecalledRef.chunk_key — a system-minted uuid5 store key for a "
        "recalled chunk, never caller-authored)",
        "`chunk_key` begins carrying a caller-supplied value",
    ),
    "ref": (
        "system-minted reference (MemorySource.ref — a store/source-minted pointer emitted by the "
        "recall path, not the caller-authored `refs[]` door which is a different field name)",
        "`ref` begins carrying caller free text (distinct from the `refs` door)",
    ),
}


#: ``{field_name: (reason, re_open_trigger)}`` — a THIRD category the Leg-1 observed-door | safe
#: binary has no slot for: a manifest DOOR (caller free text, so NEVER eligible for
#: :data:`_SERVED_SAFE_FIELDS` — the mis-park pin :class:`TestNoServedSafeFieldIsAManifestDoor`
#: forbids it) whose only driven render is PARSE-GATED, so a forgery TOKEN can never reach the
#: served bytes and Leg 1's token observation is un-satisfiable BY CONSTRUCTION (not by a build
#: bug). Distinct dict from ``_SERVED_SAFE_FIELDS`` precisely so the mis-park pin stays untouched
#: (a door here is CORRECT; a door there is the #345 defect). Each entry is evidence-backed with a
#: named re-open trigger (repo law: "WHEN YOU CANNOT CLOSE A HOLE, PIN IT"), and — unlike a SAFE
#: entry, which licenses UNCONTAINED rendering — a parse-gated door STILL routes through
#: ``render_attributed`` (Leg 2 is UNCHANGED and still requires it) and STILL carries a dedicated
#: control that mutation-provably discriminates (finding #368). A field is added here ONLY when
#: BOTH hold: it is a manifest door AND its sole driven render is value-gated to a closed charset a
#: forge token cannot satisfy.
_PARSE_GATED_DOOR_FIELDS: dict[str, tuple[str, str]] = {
    "declared_cadence": (
        "manifest DOOR (Agent.declared_cadence — register/heartbeat `cadence` stored VERBATIM, "
        "no charset gate) whose only driven render (`_render_comms_fleet_row` overdue branch, "
        "server.py) is parse-gated by `_parse_cadence_seconds(value) is not None`, restricting the "
        "rendered value to the closed cadence charset `^[≤<~=\\s]*\\d+\\s*[smhd]\\s*$`; a forge "
        "token (letters/dots) cannot parse, so it is un-observable via a token BY CONSTRUCTION. The "
        "residual forgery a parseable cadence CAN carry is line-fracturing whitespace (a trailing "
        "newline, #210; also CR / U+2028 / U+2029), which is CONTAINED by `render_attributed` "
        "(sanitise_line collapses it) — proven by the dedicated control "
        "`test_the_overdue_cadence_slot_neutralises_a_hostile_parseable_declared_cadence`",
        "the overdue verdict renders `declared_cadence` OUTSIDE the parse gate, OR the cadence "
        "charset widens to admit a printable forgery char (` · `, a backtick, prose)",
    ),
}


_CONTAIN_VERBS: frozenset[str] = frozenset({"render_attributed", "render_fenced"})
_RENDER_CALL_VERBS: frozenset[str] = frozenset({"render_line", "render_join", "render_compose"})


def _strish_manifest_fields() -> frozenset[str]:
    """Every str-ish field of every rendered model — the union of DOOR ∪ SAFE across the
    manifest (its completeness guard already asserts that union == every str-ish field). The
    render-slot VOCAB: only an interpolation of one of these names is a rendered-model
    free-text slot; a local (``delta_seconds``/``count``) is not."""
    fields: set[str] = set()
    for door, safe in _manifest().values():
        fields |= set(door) | set(safe)
    return frozenset(fields)


def _door_field_names() -> frozenset[str]:
    return frozenset({field for door, _safe in _manifest().values() for field in door})


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)


def _field_under(expr: ast.expr, vocab: frozenset[str]) -> str | None:
    """The first vocab field identifier reachable under ``expr`` (a ``Name.id`` or
    ``Attribute.attr``), or ``None``. So ``render_attributed(row.role)``,
    ``sanitise_line(agent.name)`` and a bare ``entry.task_id`` all resolve their field."""
    for child in ast.walk(expr):
        if isinstance(child, ast.Name) and child.id in vocab:
            return child.id
        if isinstance(child, ast.Attribute) and child.attr in vocab:
            return child.attr
    return None


def _is_str_join(call: ast.Call) -> bool:
    """A ``<sep>.join(<iterable>)`` call — the separator is a constant, so only the JOINED
    iterable carries served content."""
    func = call.func
    return isinstance(func, ast.Attribute) and func.attr == "join"


def _value_is_contained(expr: ast.expr) -> bool:
    """Is the CONTENT this value expression serves ELEMENT-WISE contained?

    A value is CONTAINED iff every served character reaches the output through a
    ``_CONTAIN_VERBS`` call (``render_attributed``/``render_fenced``). Element-wise, so a
    COLLECTION whose elements are each wrapped is contained; a bare / ``safe_str`` /
    ``sanitise_line`` element is not:

    * ``render_attributed(x)`` — a direct contain call → contained;
    * ``[render_attributed(b) for b in task.blocked_by]`` — a COMPREHENSION whose per-element
      expression is a contain call → contained; ``[safe_str(b) for b in …]`` /
      ``[b for b in …]`` → NOT;
    * ``", ".join(render_attributed(b) for b in xs)`` — a ``str.join`` of contained content →
      contained; ``", ".join(xs)`` → NOT;
    * ``[render_attributed(a), render_attributed(b)]`` — a literal collection of contain calls
      → contained.

    ⚠ adversary-asub-b B-1: the previous ``_render_call_value_slots`` check saw ONLY a direct
    ``render_attributed(...)`` as the whole value, so it FALSE-FLAGGED the Ruling-2-correct
    ``blocked_by`` render as uncontained — making B unsatisfiable except by the forbidden
    ``blocked_by``-SAFE entry (a false clear reopening the #345 mis-park). This is the
    element-wise recogniser Ruling 2 actually mandates; a ``safe_str`` revert stays RED.
    Conservative by construction: anything NOT provably element-wise-wrapped returns ``False``
    (a false 'uncontained' is a builder tax, never a leak greened)."""
    if isinstance(expr, ast.Call) and _call_name(expr) in _CONTAIN_VERBS:
        return True
    if isinstance(expr, ast.ListComp | ast.SetComp | ast.GeneratorExp):
        return _value_is_contained(expr.elt)
    if isinstance(expr, ast.Call) and _is_str_join(expr):
        return len(expr.args) == 1 and _value_is_contained(expr.args[0])
    if isinstance(expr, ast.List | ast.Tuple | ast.Set):
        return bool(expr.elts) and all(_value_is_contained(element) for element in expr.elts)
    return False


def _elementwise_contained_fstring_slots(
    fn: ast.FunctionDef | ast.AsyncFunctionDef, vocab: frozenset[str]
) -> set[tuple[int, str]]:
    """``{(lineno, field)}`` for f-string ``{...}`` interpolations whose VALUE expression is a
    collection whose content is element-wise contained (``{[render_attributed(b) for b in
    task.blocked_by]}``).

    :func:`_raw_render_interpolations` returns these marked uncontained — it excludes only a
    TOP-LEVEL seam call, never a comprehension/join wrapping the value. This recognises the
    collection shape it cannot, reusing :func:`_value_is_contained`, so a slot is reclassified
    contained iff its whole value expression is element-wise wrapped."""
    contained: set[tuple[int, str]] = set()
    for joined in ast.walk(fn):
        if not isinstance(joined, ast.JoinedStr):
            continue
        for value in joined.values:
            if not isinstance(value, ast.FormattedValue) or not _value_is_contained(value.value):
                continue
            for child in ast.walk(value.value):
                name = (
                    child.id
                    if isinstance(child, ast.Name)
                    else child.attr
                    if isinstance(child, ast.Attribute)
                    else None
                )
                if name in vocab:
                    contained.add((value.lineno, name))
    return contained


def _render_call_value_slots(
    fn: ast.FunctionDef | ast.AsyncFunctionDef, vocab: frozenset[str]
) -> list[tuple[int, str, bool]]:
    """``(lineno, field, contained)`` for every VALUE passed to a
    ``render_line``/``render_join``/``render_compose`` call — the shape a pure f-string
    scan is blind to (design INSTRUMENT B: the comms family renders role/last_note/thread
    with NO ``{...}`` at all). ``contained`` is True iff the value expression is itself a
    ``render_attributed``/``render_fenced`` call (an already-contained span)."""
    slots: list[tuple[int, str, bool]] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call) or _call_name(node) not in _RENDER_CALL_VERBS:
            continue
        name = _call_name(node)
        value_exprs: list[ast.expr] = []
        if name == "render_line":
            value_exprs = [kw.value for kw in node.keywords]
        elif name == "render_join":
            parts = node.args[1] if len(node.args) >= 2 else None
            if isinstance(parts, ast.List | ast.Tuple):
                value_exprs = list(parts.elts)
            elif parts is not None:
                value_exprs = [parts]
        elif name == "render_compose":
            value_exprs = list(node.args)
        for value in value_exprs:
            field = _field_under(value, vocab)
            if field is not None:
                # ELEMENT-WISE containment (adversary-asub-b B-1): a comprehension /
                # ``str.join`` / literal collection of ``render_attributed(...)`` is contained,
                # not just a direct ``render_attributed(...)`` call.
                slots.append((value.lineno, field, _value_is_contained(value)))
    return slots


def _served_slots(
    fn: ast.FunctionDef | ast.AsyncFunctionDef, vocab: frozenset[str]
) -> list[tuple[int, str, bool]]:
    """``(lineno, field, contained)`` for every str-ish rendered-model field this render
    serves, from BOTH interpolation shapes:

    * bare f-string ``{expr}`` — via :func:`_raw_render_interpolations`, which excludes a
      TOP-LEVEL seam call / int-call / method call / error construction, so what it returns
      is uncontained UNLESS the value is an ELEMENT-WISE-contained collection (a comprehension
      / ``str.join`` of ``render_attributed(...)``) — those are reclassified contained via
      :func:`_elementwise_contained_fstring_slots` (adversary-asub-b B-1: the Ruling-2-correct
      ``blocked_by`` render is contained, a ``safe_str`` revert is not);
    * ``render_line``/``render_join``/``render_compose`` value args — via
      :func:`_render_call_value_slots`, where a contain-verb value (direct OR element-wise) is
      contained.
    """
    elementwise = _elementwise_contained_fstring_slots(fn, vocab)
    slots: list[tuple[int, str, bool]] = [
        (lineno, identifier, (lineno, identifier) in elementwise)
        for lineno, identifier in _raw_render_interpolations(fn)
        if identifier in vocab
    ]
    slots += _render_call_value_slots(fn, vocab)
    return slots


def _driven_methods() -> frozenset[str]:
    """The DRIVEN render set (P-U's ``_render_probes`` universe). Scoped HERE rather than
    over every ``_candidate_render_sites`` because the door/safe classification a str-ish
    MODEL FIELD carries is only meaningful in a render that actually constructs that model:
    the OUT methods (``code_rag`` map, ``index_metadata`` snapshot rows, the dispatchers)
    are bounded by their own ``_RENDER_OUT`` reasons + the coherence pin, and a name-based
    model-field vocab over-matches on their unrelated ``summary``/``note`` locals. A NEW
    render joins the driven set (or ``_RENDER_OUT``) via P-U's own completeness net, so this
    scope does not silently exempt a new door."""
    return frozenset(probe.method for probe in _render_probes())


def _all_served_slots() -> dict[str, list[tuple[int, str, bool]]]:
    """``{render_method: [(lineno, field, contained), ...]}`` over every DRIVEN render."""
    vocab = _strish_manifest_fields()
    methods = _appcontext_methods()
    inventory: dict[str, list[tuple[int, str, bool]]] = {}
    for method in _driven_methods():
        fn = methods.get(method)
        if fn is None:
            continue
        found = _served_slots(fn, vocab)
        if found:
            inventory[method] = found
    return inventory


# ---------------------------------------------------------------------------- #
# THE OVER-DRIVE OBSERVATION (Leg 1) — model-precise via forgery tokens.
# ---------------------------------------------------------------------------- #

_PER_PROBE_OUTPUT: dict[str, str] | None = None


def _per_probe_output() -> dict[str, str]:
    """``{render_method: concatenated served bytes}`` from running the WHOLE forge
    over-drive once (every probe, every shape, forge=True). A ``Model.field`` door driven
    with content leaves its :func:`_field_token` (which embeds ``Model.field``) in its
    probe's bytes — even inside a provenance delimiter (the token carries no control chars,
    so containment leaves it byte-intact). Cached: deterministic, sliced by the pins."""
    global _PER_PROBE_OUTPUT  # noqa: PLW0603 — module-level cache for the deterministic over-drive
    if _PER_PROBE_OUTPUT is None:
        per_probe: dict[str, str] = {}
        for probe in _render_probes():
            per_probe[probe.method] = "\n".join(str(rendered) for rendered in probe.shapes(True))
        _PER_PROBE_OUTPUT = per_probe
    return _PER_PROBE_OUTPUT


def _over_drive_output() -> str:
    """The concatenated served bytes across every probe (Leg 1's observation surface)."""
    return "\n".join(_per_probe_output().values())


def _observed_door_slots() -> set[tuple[str, str]]:
    """``{(model_name, field)}`` for every manifest DOOR field whose forgery token appears
    in the over-drive output — i.e. was actually DRIVEN WITH CONTENT and served."""
    output = _over_drive_output()
    observed: set[tuple[str, str]] = set()
    for cls, (door, _safe) in _manifest().items():
        for field in door:
            if f"{cls.__name__}.{field}" in output:
                observed.add((cls.__name__, field))
    return observed


def _observed_field_names() -> frozenset[str]:
    return frozenset({field for _model, field in _observed_door_slots()})


# ---------------------------------------------------------------------------- #
# Leg 1 — coverage as a checked variable (observed with content OR justified SAFE)
# ---------------------------------------------------------------------------- #


class TestEveryServedSlotIsDrivenWithContentOrJustifiedSafe:
    """⛔ Leg 1 (design INSTRUMENT B, finding #345). Every str-ish field a render SERVES is
    EITHER observed driven with a forgery in the over-drive (a real, exercised door) OR in
    :data:`_SERVED_SAFE_FIELDS` with evidence. A door served but never observed with content
    (``task_id=None`` vacuous drive) or a field mis-parked SAFE (served, un-driven,
    un-justified) is a NAMED gap → RED."""

    def test_the_over_drive_actually_produced_observable_tokens(self) -> None:
        """⛔ NON-VACUITY / positive control: the over-drive must have driven KNOWN doors
        with content, or Leg 1's 'observed' set is empty and the whole leg is meaningless.
        Without this a broken over-drive (produces no bytes) is indistinguishable from a
        clean one."""
        # Control: the substring the observation scans for is genuinely the identifying core
        # of the forge token, so a change to _field_token's format is caught here rather than
        # silently making every door look un-driven.
        assert "InboxEntry.task_id" in _field_token("InboxEntry", "task_id")
        observed = _observed_field_names()
        assert len(observed) > 5, (
            f"the forge over-drive produced almost no observable door tokens ({sorted(observed)}) "
            "— it is broken, and Leg 1 cannot tell driven-with-content from un-driven."
        )
        for known in ("thread", "body", "subject"):
            assert known in observed, (
                f"known door {known!r} was NOT observed with content in the over-drive — the "
                "observation is broken (a token that should appear does not)."
            )

    def test_the_drain_row_task_id_slot_is_driven_with_content(self) -> None:
        """The #345 instance, as a regression control: ``InboxEntry.task_id`` (the field
        mis-parked SAFE that leaked ``(task {task_id})``) is now a DOOR and MUST be observed
        driven with content. If a wrong build reverts it to SAFE, its token vanishes and
        Leg 1's main pin reddens — this control localises that regression."""
        assert ("InboxEntry", "task_id") in _observed_door_slots(), (
            "InboxEntry.task_id is NOT observed driven with content — either it was reverted "
            "to SAFE (re-opening #345) or its drain-row driver re-hardcoded task_id=None."
        )

    def test_the_overdue_cadence_slot_neutralises_a_hostile_parseable_declared_cadence(
        self,
    ) -> None:
        """DEDICATED CONTROL for the :data:`_PARSE_GATED_DOOR_FIELDS` ``declared_cadence``
        exemption (finding #368; mirrors
        :meth:`test_the_drain_row_task_id_slot_is_driven_with_content`) — the exemption's
        evidence made a REAL check, not a rug-sweep (repo law: every deny-by-default exemption is
        evidence-backed, and its control must mutation-provably discriminate).

        ``declared_cadence`` renders ONLY in the ``_render_comms_fleet_row`` overdue branch, and
        only when it PARSES as a cadence — so the served value is confined to the closed charset
        ``^[≤<~=\\s]*\\d+\\s*[smhd]\\s*$``. The ONLY forgery that charset admits is line-fracturing
        WHITESPACE (a trailing newline, #210; also CR / U+2028 / U+2029). This drives that exact
        vector, on a value that parses, and proves the served row carries NO line-fracturing /
        control char — it stays one visually-honest line.

        ⚠ NOT ``_leaks`` alone: ``_leaks`` keys on ``FORGERY_MARKER`` PROSE, which a charset-gated
        cadence can NEVER carry, so it returns ``False`` even on a render where the raw newline
        SURVIVES (MEASURED: finding #368 / REPORT-fixer-orphans-06b-2.md §B2). It is therefore
        VACUOUS for this vector — the LOAD-BEARING assertion is
        :data:`~loremaster.sanitise.CONTROL_CHAR_PATTERN` (the exact line-fracturing class
        ``sanitise_line`` neutralises). ``_leaks`` is kept only as a documented-secondary belt for
        the re-open-trigger world where the charset widens to admit a printable char.

        MUTATION PROOF (bypass ``render_attributed`` at the overdue branch → this control RED;
        restore → GREEN): REPORT-fixer-orphans-06b-2.md §B2.
        """
        from loremaster.agents import Agent  # noqa: PLC0415
        from loremaster.sanitise import CONTROL_CHAR_PATTERN  # noqa: PLC0415
        from test_link5_render_containment import _app  # noqa: PLC0415

        # Hostile-but-PARSEABLE: parses to 60s (so the overdue branch fires at
        # heartbeat_age_s=600), packing the line-fracturing whitespace the charset admits — a
        # trailing newline (#210) PLUS CR and U+2028, so the assertion is load-bearing beyond the
        # single ``\n`` vector (a bypass that only handled ``\n`` would still be caught).
        # newline (#210) + CR + U+2028 LINE SEPARATOR — all charset-admitted \s, written
        # as escapes so no literal line-fracturing char sits in this source file.
        hostile_cadence = "≤1m" + "\r\n\u2028"
        row = Agent.model_construct(  # type: ignore[call-arg]
            name="agent-x",
            role="release-bot",
            model=None,
            task_id=None,
            last_note=None,
            status="active",
            declared_cadence=hostile_cadence,
        )
        rendered = str(
            _app()._render_comms_fleet_row(
                row,
                project_head_version=None,
                acked_version=None,
                stale_after_s=120,
                heartbeat_age_s=600,
            )
        )
        assert "overdue" in rendered, (
            "the overdue branch did NOT fire — the parse-gated declared_cadence slot is not being "
            "exercised, so this control proves nothing (heartbeat_age_s must exceed the parsed "
            f"cadence). rendered={rendered!r}"
        )
        assert not CONTROL_CHAR_PATTERN.search(rendered), (
            "a line-fracturing / control character from the hostile declared_cadence survived into "
            "the served fleet row — the #210 residual vector is NOT contained (render_attributed "
            f"was bypassed at the overdue branch). rendered={rendered!r}"
        )
        assert not _leaks(rendered), (
            "the forgery marker reached the served row outside a provenance delimiter — the "
            "documented-secondary belt (marker-blind for this charset-gated vector) fired."
        )

    def test_every_served_field_is_driven_with_content_or_justified_safe(self) -> None:
        observed = _observed_field_names()
        doors = _door_field_names()
        offenders: list[str] = []
        for method, slots in _all_served_slots().items():
            for lineno, field, _contained in slots:
                # A parse-gated door (finding #368) is exempt from the token-observation
                # requirement — its render is value-gated to a closed charset a forge token
                # cannot satisfy, so "observed with content" is un-satisfiable BY CONSTRUCTION.
                # It is NOT let off containment: Leg 2 (below) is unchanged and still requires
                # render_attributed, and each such field carries a dedicated discriminating
                # control (see _PARSE_GATED_DOOR_FIELDS).
                if (
                    field in observed
                    or field in _SERVED_SAFE_FIELDS
                    or field in _PARSE_GATED_DOOR_FIELDS
                ):
                    continue
                verdict = (
                    "a DOOR served but NEVER observed with content — a vacuous drive "
                    "(the task_id=None class): drive it with a forgery in the over-drive"
                    if field in doors
                    else "served but NOT driven with content and NOT justified SAFE — either "
                    "a field mis-parked SAFE (move it to DOOR and drive it) OR a genuinely "
                    "safe field (add it to _SERVED_SAFE_FIELDS with evidence + a re-open trigger)"
                )
                offenders.append(f"{method}:{lineno} serves {field!r} — {verdict}")
        assert offenders == [], (
            "these served render slots are neither observed-driven-with-content nor "
            "justified-SAFE (finding #345 — coverage is not a checked variable for them):\n  "
            + "\n  ".join(sorted(offenders))
        )


# ---------------------------------------------------------------------------- #
# Leg 2 — the sanitise_line/safe_str-in-render scan (static, authoring-time)
# ---------------------------------------------------------------------------- #


class TestNoRenderSlotServesAStrishFieldUncontained:
    """⛔ Leg 2 (design INSTRUMENT B — generalise the error-half ``sanitise_line``-in-context
    scan to RENDER contexts). A str-ish rendered-model field served UNCONTAINED (bare, or
    through ``sanitise_line``/``safe_str`` — both same-line-forgery-blind) must be in
    :data:`_SERVED_SAFE_FIELDS`; everything else routes through ``render_attributed``. Empty
    allowlist at HEAD → every charset-gated / opaque-id field currently served via
    ``sanitise_line``/``safe_str`` is RED until the builder justifies or contains it."""

    def test_every_uncontained_served_field_is_justified(self) -> None:
        offenders: list[str] = []
        for method, slots in _all_served_slots().items():
            for lineno, field, contained in slots:
                if contained or field in _SERVED_SAFE_FIELDS:
                    continue
                offenders.append(
                    f"{method}:{lineno} serves {field!r} UNCONTAINED (bare / sanitise_line / "
                    "safe_str — same-line-forgery-blind)"
                )
        assert offenders == [], (
            "these render slots serve a str-ish rendered-model field OUTSIDE a provenance "
            "delimiter (finding #321/#345):\n  " + "\n  ".join(sorted(offenders)) + "\n"
            "Route each through render_attributed (single-line) / render_fenced (a body), OR "
            "add the field to _SERVED_SAFE_FIELDS with an evidence-backed reason "
            "(charset-gated / opaque id / closed enum / truncated system ref) + a re-open trigger."
        )

    def test_the_scan_fires_on_a_planted_uncontained_door(self) -> None:
        """POSITIVE control: a synthetic render serving a bare ``{owner}`` (a DOOR field) is
        flagged. Without this a green Leg 2 is indistinguishable from a scan that matches
        nothing."""
        vocab = _strish_manifest_fields()
        assert "owner" in vocab, "owner is not a manifest field — the control is mis-built"
        fn = ast.parse("def _r(self):\n    return f'attribution {owner}'\n").body[0]
        assert isinstance(fn, ast.FunctionDef)
        found = {field for _lineno, field, contained in _served_slots(fn, vocab) if not contained}
        assert "owner" in found, "Leg 2's extractor does not see a bare {owner} interpolation"

    def test_the_scan_does_not_fire_on_contained_or_scalar_slots(self) -> None:
        """NEGATIVE control: a field routed through ``render_attributed``, a count
        (``{len(body)}``), and a constant are NOT flagged — a scan that refused these would
        be the false-positive tax that gets a gate switched off."""
        vocab = _strish_manifest_fields()
        source = (
            "def _r(self):\n"
            "    a = render_line('x {owner}', owner=render_attributed(task.owner))\n"
            "    b = f'len {len(body)}'\n"
            "    c = render_line('const', k=render_attributed(finding.subject))\n"
            "    return render_compose(a, c)\n"
        )
        fn = ast.parse(source).body[0]
        assert isinstance(fn, ast.FunctionDef)
        uncontained = {field for _l, field, contained in _served_slots(fn, vocab) if not contained}
        assert uncontained == set(), (
            f"Leg 2 flagged a contained/scalar slot as uncontained: {uncontained} — it would "
            "refuse honest code (render_attributed / a count)."
        )

    def test_leg2_recognises_elementwise_comprehension_containment(self) -> None:
        """⛔ B-1 (adversary-asub-b): the Ruling-2-correct ``blocked_by`` render
        ``[render_attributed(b) for b in task.blocked_by]`` is CONTAINED element-wise, while a
        ``safe_str`` revert and a bare list-repr are NOT — the discriminating pin Ruling 2
        actually mandates, WITHOUT any ``blocked_by``-SAFE allowlist entry. Without this Leg 2
        false-flags the correct render and B is unsatisfiable except by the forbidden false
        clear (a door parked SAFE)."""
        vocab = _strish_manifest_fields()
        assert "blocked_by" in vocab, "blocked_by is not a manifest field — the control is mis-built"

        def blocked_by_slots(value_expr: str) -> set[tuple[str, bool]]:
            fn = ast.parse(f"def _r(self):\n    return f'blocked_by {{{value_expr}}}'\n").body[0]
            assert isinstance(fn, ast.FunctionDef)
            return {(f, c) for _l, f, c in _served_slots(fn, vocab) if f == "blocked_by"}

        correct = "[render_attributed(b) for b in task.blocked_by]"
        leaking_safe_str = "[safe_str(b) for b in task.blocked_by]"
        leaking_bare = "[b for b in task.blocked_by]"
        assert blocked_by_slots(correct) == {("blocked_by", True)}, (
            "the correct render_attributed-comprehension is NOT recognised element-wise contained "
            "— Leg 2 is comprehension-blind (B-1) and false-flags the Ruling-2-correct render."
        )
        assert blocked_by_slots(leaking_safe_str) == {("blocked_by", False)}, (
            "a safe_str-comprehension revert is wrongly marked contained — a leak greened."
        )
        assert blocked_by_slots(leaking_bare) == {("blocked_by", False)}, (
            "a bare list-repr comprehension is wrongly marked contained — a leak greened."
        )

    def test_leg2_recognises_str_join_containment(self) -> None:
        """⛔ B-1 dual: a ``str.join`` of ``render_attributed(...)`` content is contained
        element-wise; a ``str.join`` of BARE ``blocked_by`` elements is not."""
        vocab = _strish_manifest_fields()

        def blocked_by_contained(value_expr: str) -> set[tuple[str, bool]]:
            fn = ast.parse(f"def _r(self):\n    return f'{{{value_expr}}}'\n").body[0]
            assert isinstance(fn, ast.FunctionDef)
            return {(f, c) for _l, f, c in _served_slots(fn, vocab) if f == "blocked_by"}

        contained = '", ".join(render_attributed(b) for b in task.blocked_by)'
        leaking = '", ".join(task.blocked_by)'
        assert blocked_by_contained(contained) == {("blocked_by", True)}, (
            "a str.join of render_attributed content is not recognised contained"
        )
        assert blocked_by_contained(leaking) == {("blocked_by", False)}, (
            "a str.join of BARE blocked_by elements is wrongly marked contained — a leak greened"
        )

    def test_the_real_blocked_by_render_is_element_wise_contained(self) -> None:
        """⛔ The HEAD ``_render_task_rows`` renders ``blocked_by`` as
        ``[render_attributed(blocker) for blocker in task.blocked_by]`` (Ruling 2 declares this
        CORRECT). Leg 2 must classify it CONTAINED so B goes green WITHOUT a ``blocked_by``-SAFE
        entry; a ``safe_str``/bare revert surfaces it as an uncontained offender. Reads the REAL
        server.py render via ``_all_served_slots`` — the exact site #345/Ruling-2 is about."""
        slots = _all_served_slots().get("_render_task_rows", [])
        blocked = [(lineno, contained) for lineno, field, contained in slots if field == "blocked_by"]
        assert blocked, (
            "_render_task_rows serves NO blocked_by slot — the manifest vocab or the driven-render "
            "derivation drifted (blocked_by must be a served DOOR field)."
        )
        assert all(contained for _lineno, contained in blocked), (
            f"_render_task_rows serves blocked_by UNCONTAINED {blocked} — Leg 2 is not element-wise "
            "aware (B-1), or the render was reverted from render_attributed to safe_str/bare."
        )
        assert "blocked_by" not in _SERVED_SAFE_FIELDS, (
            "blocked_by is in _SERVED_SAFE_FIELDS — a DOOR parked SAFE (the #345 mis-park Ruling 2 "
            "forbids by name). It must pass Leg 2 by CONTAINMENT, not by allowlisting."
        )


# ---------------------------------------------------------------------------- #
# IDIOM 1 over the allowlist itself — no DOOR field may be parked SAFE (Ruling 2).
# ---------------------------------------------------------------------------- #


class TestNoServedSafeFieldIsAManifestDoor:
    """⛔ adversary-asub-b NEW PIN (§9.7; mechanises Ruling 2): no :data:`_SERVED_SAFE_FIELDS`
    key may be a DOOR field in ANY manifest model. The B-1 escape hatch — park a door SAFE to
    silence Leg 2 — is thereby UNREPRESENTABLE: adding ``blocked_by`` (or any door) to the
    allowlist reddens this pin. This is IDIOM 1 applied to the allowlist: its reach is the LIVE
    manifest DOOR set (:func:`_door_field_names`), re-derived each run (§9.1), never a fixture
    constant.

    GREEN at HEAD (``_SERVED_SAFE_FIELDS`` is empty) and after (the builder populates it only
    with genuinely-safe fields — charset-gated identities, opaque ids, closed enums, truncated
    system refs — never a door). A standing guard, not a fix-absent RED."""

    def test_no_served_safe_field_is_a_manifest_door(self) -> None:
        doors = _door_field_names()
        mis_parked = sorted(set(_SERVED_SAFE_FIELDS) & doors)
        assert mis_parked == [], (
            f"these _SERVED_SAFE_FIELDS entries are DOOR fields in the manifest: {mis_parked} — "
            "a door parked SAFE (the #345 mis-park Ruling 2 forbids by name). Either the field is "
            "genuinely a door (REMOVE the SAFE entry, drive it with a forgery, route it through "
            "render_attributed), or the manifest DOOR classification is wrong (fix the manifest, "
            "not the allowlist). SAFE is for fields that CANNOT carry a forgery, never a silencer."
        )

    def test_the_mis_park_check_actually_fires_on_a_planted_door(self) -> None:
        """POSITIVE control (probe-needs-a-control): the intersection genuinely catches a door
        parked SAFE — so a green pin above is not a check that can never fire."""
        doors = _door_field_names()
        assert doors, "no DOOR fields in the manifest — the control is mis-built"
        planted_allowlist = {sorted(doors)[0]: ("planted", "trigger")}
        assert set(planted_allowlist) & doors, (
            "the mis-park intersection cannot see a door planted in a SAFE allowlist — it would "
            "not catch a real mis-park either."
        )


# ---------------------------------------------------------------------------- #
# The removed-behaviour superset proof — gate on retiring _RENDER_DRIVERS.
# ---------------------------------------------------------------------------- #


def _old_hand_net_methods() -> frozenset[str]:
    """The render methods the old ``_RENDER_DRIVERS`` hand-net drove — the keys of the net,
    each of which the old ``TestEveryRenderLayerDoorNeutralisesAForgery`` sweep exercised
    with a forgery. (The net's LABELS also name fields, but informally — ``note`` for the
    ``last_note`` field, an ``actor`` PARAM that is no model field — so the removed-behaviour
    proof is at the METHOD level + a per-method non-vacuous-drive check, not a fragile
    label-field parse. Field-level coverage then follows from the derived net forging each
    model's FULL door set, guarded by ``_manifest``'s own DOOR∪SAFE completeness pin in
    ``test_link5_render_containment``.)"""
    from test_link5_render_containment import _RENDER_DRIVERS  # noqa: PLC0415

    return frozenset(_RENDER_DRIVERS)


class TestTheDerivedInventorySupersedesTheOldHandNet:
    """⛔ REMOVED-BEHAVIOUR PROOF (operator ruling 2026-08-09: retire ``_RENDER_DRIVERS``,
    but "do NOT make gaps wider"). The derived driven net must PROVABLY COVER (⊇) the old
    hand-net: every method it drove is a derived driven probe AND is exercised with forgery
    content by that probe — so deleting the net (with its literal ``task_id=None`` #345
    hardcodes) cannot drop a covered method. Retirement is valid IFF this stays green; the
    deletion itself is the builder's action, gated here."""

    def test_every_old_net_method_is_a_derived_driven_render(self) -> None:
        missing = sorted(_old_hand_net_methods() - _driven_methods())
        assert missing == [], (
            f"the derived driven net does NOT cover these old _RENDER_DRIVERS methods: "
            f"{missing} — retiring the hand-net would drop them. Add a RenderProbe first."
        )

    def test_every_old_net_method_is_driven_with_forgery_content(self) -> None:
        """Non-vacuous coverage: each retired method's derived probe drives a REAL forgery
        (its bytes carry FORGERY_MARKER), so the derived net exercises it at least as hard as
        the old net did — not a dead probe. Marker-based, so it is agnostic to whether the
        old net drove a model field or a render param (``actor``)."""
        per_probe = _per_probe_output()
        offenders = sorted(
            method for method in _old_hand_net_methods() if FORGERY_MARKER not in per_probe.get(method, "")
        )
        assert offenders == [], (
            "these old _RENDER_DRIVERS methods are NOT driven with forgery content by their "
            f"derived probe — the derived net does not supersede them: {offenders}. Retiring "
            "the hand-net would make the gap WIDER."
        )


# ---------------------------------------------------------------------------- #
# The hostile fixture (Rename/reshape law: newlines + row-shaped forgery + backtick runs).
# ---------------------------------------------------------------------------- #


class TestAHostileMultilineStoredValueIsContained:
    """⛔ HOSTILE FIXTURE (standing law — a new render of stored free text needs newlines +
    an output-format-shaped forgery line + delimiter runs; a single-line fixture is the
    documented way this class ships green). The drain-row ``task_id`` slot — the #345 door —
    driven with :data:`HOSTILE_MULTILINE` must be CONTAINED in the served bytes."""

    def test_the_drain_row_contains_a_hostile_multiline_task_id(self) -> None:
        from test_link5_render_containment import _app, _InboxEntry  # noqa: PLC0415

        entry = _InboxEntry().model_construct(
            seq=1,
            message_id="m",
            grade="signal",
            sender_name="agent-x",
            thread="s",
            task_id=HOSTILE_MULTILINE,
            body="a plain body",
            refs=[],
            created_at=_NOW,
            acked_at=None,
            ack_note=None,
        )
        rendered = str(_app()._render_comms_drain_row(entry, session="s"))
        assert not _leaks(rendered), (
            "the hostile multi-line task_id reached the served answer OUTSIDE a provenance "
            f"delimiter — the row-shaped forgery line reads as lore's own voice. rendered={rendered!r}"
        )

    def test_the_leak_predicate_discriminates_on_this_fixture(self) -> None:
        """POSITIVE control: the hostile fixture's marker, served BARE, is detected as a leak
        — so the containment pin above is not passing on a blind predicate."""
        assert _leaks(f"drain row: {HOSTILE_MULTILINE}"), (
            "the leak predicate does not flag the hostile fixture served bare — it cannot "
            "prove containment of anything."
        )
        assert FORGERY_MARKER in HOSTILE_MULTILINE and BENIGN in HOSTILE_MULTILINE

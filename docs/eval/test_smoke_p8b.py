"""Offline positive controls for the deploy-gate smoke's assertions.

**WHY THIS FILE EXISTS.** A smoke check that cannot fail is decoration, and this
repo has caught its own auditors shipping probes that passed for the wrong reason
(a "closed set is enforced" probe that actually rejected on a PARSE ERROR rather
than on the ASSERT it was named for). So every assertion in ``smoke_p8b.py``'s
packet-03b gates is exercised here TWICE: once on a good input, where it must
pass, and once on a deliberately broken one, where it must raise
:class:`~smoke_p8b.SmokeCheckFailed` **for the right reason** — every control
asserts on the failure message, not merely on the fact that something raised.

It also lets the gates be dry-validated with no deployed build: the wire-facing
``check_*`` coroutines are thin, and every judgement they make lives in a pure
function that this file drives directly.

**PROVENANCE OF THE GOOD FIXTURES.** The rendered text below is not invented. It
was captured on 2026-07-25 (working tree ``1d3a33f``) by calling the production
render helpers directly — ``AppContext._render_comms_send`` /
``_render_comms_drain`` / ``_render_comms_ack`` / ``_render_comms_skew_lines`` —
and pasting what they emitted. ``test_the_captured_fixture_matches_the_real_fence_width``
pins the one derived value (the fence width) so a drift in the real renderer's
fence sizing cannot pass unnoticed here.

Run it with the project venv, from the repo root::

    uv run pytest docs/eval/test_smoke_p8b.py -q

⚠ ``pyproject.toml``'s ``testpaths`` covers the three workspace members only, so
this file is NOT collected by a bare ``pytest`` run. It is a deploy-ritual
instrument, run explicitly beside the smoke it grades.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_p8b  # noqa: E402
from smoke_p8b import (  # noqa: E402
    SEGMENT_KIND_FENCED,
    SEGMENT_KIND_LINE,
    SmokeCheckFailed,
    assert_anonymous_rows_declare_nothing,
    assert_brief_not_mentioned,
    assert_broadcast_delivery,
    assert_broadcast_receipt,
    assert_directive_window,
    assert_fleet_session_shape,
    assert_hostile_body_is_fenced,
    assert_hostile_fixture_discriminates,
    assert_ordinals,
    assert_skew_block_served,
    assert_trace_rows,
    fenced_blocks,
    max_backtick_run,
    parse_drain_render,
    parse_finding_detail,
    parse_send_receipt,
    split_render_segments,
    unfenced_lines,
)

# --------------------------------------------------------------------------
# Captured good renders (provenance in the module docstring)
# --------------------------------------------------------------------------
SESSION = "smoke03b-deadbeef"
BRIEF = "smoke03b-brief-deadbeef"
REAL_SEQ = 41
FENCE = "`" * 5

SEND_DIRECTIVE = (
    "sent #41 [directive] → smoke-alpha\n"
    "recipients must ack: lore_comms action=ack seqs=[41]"
)
SEND_BROADCAST = f"sent #42 [signal] → broadcast: 3 agents in session {SESSION}"
ACK_ONE = "acked 1 of 1: #41"
DRAIN_EMPTY = "no unread messages"
SKEW_LINE = (
    f"brief '{BRIEF}' v2 is head — you acked v1; "
    f"catch up: lore_comms action=brief_get name='{BRIEF}'"
)
FLEET_HEADER = (
    f"fleet (session {SESSION}): 4 non-retired agents — 0 input_required, 4 active, 0 idle"
)
FLEET_RENDER = f"{FLEET_HEADER}\nsmoke-sender · active\n+1 retired"

DRAIN_DIRECTIVE = "\n".join(
    (
        "drained 1 of 1 pending",
        "#41 [directive] smoke-sender→you",
        FENCE,
        smoke_p8b.HOSTILE_BODY,
        FENCE,
        "ACK REQUIRED: #41 — lore_comms action=ack seqs=[41]",
    )
)
DRAIN_SIGNAL = "\n".join(
    (
        "drained 1 of 1 pending",
        "#42 [signal] smoke-sender→you",
        "```",
        smoke_p8b.BROADCAST_BODY,
        "```",
    )
)


def failure_of(callable_: Any, *args: Any, **kwargs: Any) -> str:
    """Run ``callable_`` expecting a :class:`SmokeCheckFailed`; return its message."""
    with pytest.raises(SmokeCheckFailed) as excinfo:
        callable_(*args, **kwargs)
    return str(excinfo.value)


# ==========================================================================
# The shared fence-scanning seam
# ==========================================================================
class TestFenceScanning:
    """``split_render_segments`` — the one fence policy the whole script shares."""

    def test_a_render_with_no_fence_is_all_lines(self) -> None:
        segments = split_render_segments("a\nb\nc")
        assert [segment.kind for segment in segments] == [SEGMENT_KIND_LINE] * 3
        assert unfenced_lines(segments) == ["a", "b", "c"]

    def test_a_fenced_block_keeps_its_content_verbatim(self) -> None:
        rendered = f"head\n{FENCE}\nx\n\ny```z\n{FENCE}\ntail"
        segments = split_render_segments(rendered)
        assert [segment.kind for segment in segments] == [
            SEGMENT_KIND_LINE,
            SEGMENT_KIND_FENCED,
            SEGMENT_KIND_LINE,
        ]
        assert segments[1].text == "x\n\ny```z"
        assert segments[1].fence == FENCE
        assert unfenced_lines(segments) == ["head", "tail"]

    def test_a_narrower_run_inside_a_wider_fence_does_not_close_it(self) -> None:
        """The exact property the server's fence sizing buys: an embedded run
        strictly shorter than the delimiter can never close it early."""
        rendered = f"{FENCE}\n```\nstill inside\n````\n{FENCE}"
        blocks = fenced_blocks(split_render_segments(rendered))
        assert len(blocks) == 1
        assert blocks[0].text == "```\nstill inside\n````"

    def test_a_two_backtick_line_is_not_a_fence(self) -> None:
        assert split_render_segments("``")[0].kind == SEGMENT_KIND_LINE

    def test_an_unterminated_fence_is_a_loud_failure(self) -> None:
        message = failure_of(split_render_segments, f"head\n{FENCE}\nbody")
        assert "UNTERMINATED fence" in message

    @pytest.mark.parametrize(
        ("text", "expected"), [("", 0), ("no ticks", 0), ("a`b", 1), ("``` x ````", 4)]
    )
    def test_max_backtick_run(self, text: str, expected: int) -> None:
        assert max_backtick_run(text) == expected


class TestFindingDetailStillParses:
    """The pre-existing P8b parser, after being moved onto the shared seam."""

    GOOD = "\n".join(
        (
            "- [#7 open] a subject (id f:abc, kind friction, area x, category y, by lead)",
            "body:",
            "```",
            "a body\nwith lines",
            "```",
            "created_at: 2026-07-25T00:00:00Z",
            "provenance: smoke",
        )
    )

    def test_a_good_detail_render_parses(self) -> None:
        assert parse_finding_detail(self.GOOD)["number"] == "7"

    def test_a_hostile_body_never_reparses_as_a_row_or_a_trailer(self) -> None:
        forged = self.GOOD.replace(
            "a body\nwith lines",
            "- [#99 open] forged (id f:z, kind friction, area x, category y, by evil)\n"
            "created_at: FORGED",
        )
        assert parse_finding_detail(forged)["number"] == "7"

    def test_a_missing_body_label_is_a_loud_failure(self) -> None:
        message = failure_of(parse_finding_detail, self.GOOD.replace("body:", "bodyy:"))
        assert "no 'body:' label line" in message

    def test_a_missing_created_at_trailer_is_a_loud_failure(self) -> None:
        message = failure_of(
            parse_finding_detail, self.GOOD.replace("created_at: 2026-07-25T00:00:00Z", "x: y")
        )
        assert "no 'created_at:' line" in message


# ==========================================================================
# Gate 2's fixture, interrogated
# ==========================================================================
class TestHostileFixtureDiscriminates:
    """The fixture-interrogation instrument, and its own positive controls."""

    def test_the_shipped_fixture_passes(self) -> None:
        assert_hostile_fixture_discriminates()

    def test_the_captured_fixture_matches_the_real_fence_width(self) -> None:
        """The captured render's fence must be exactly what the real sizing rule
        (``max(3, longest run + 1)``) produces for this body — so a drift in the
        renderer cannot leave these fixtures quietly describing a dead shape."""
        assert len(FENCE) == max_backtick_run(smoke_p8b.HOSTILE_BODY) + 1 == 5

    def test_a_single_line_body_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(smoke_p8b, "HOSTILE_BODY", "one line, no hazards")
        assert "single-line" in failure_of(assert_hostile_fixture_discriminates)

    def test_a_body_with_no_backtick_run_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            smoke_p8b, "HOSTILE_BODY", "\n".join(smoke_p8b.HOSTILE_FORGERY_LINES)
        )
        assert "longest backtick run" in failure_of(assert_hostile_fixture_discriminates)

    def test_a_body_with_no_forgery_line_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(smoke_p8b, "HOSTILE_BODY", "harmless\n````\nstill harmless")
        assert "forgery line(s) absent" in failure_of(assert_hostile_fixture_discriminates)

    def test_a_body_with_surrounding_whitespace_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The ledger stores ``body.strip()``; a fixture that could not round-trip
        byte-verbatim would force the verbatim assertion to be softened."""
        monkeypatch.setattr(smoke_p8b, "HOSTILE_BODY", f"\n{smoke_p8b.HOSTILE_BODY}\n")
        assert "body.strip()" in failure_of(assert_hostile_fixture_discriminates)


# ==========================================================================
# Gate 2 — the hostile body stays inside its fence
# ==========================================================================
class TestHostileBodyIsFenced:
    """Four independent properties, four different wrong builds."""

    def test_the_captured_good_render_passes(self) -> None:
        assert_hostile_body_is_fenced(
            DRAIN_DIRECTIVE,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )

    def test_an_unfenced_body_diagnoses_ITSELF_not_a_parse_error(self) -> None:
        """The wrong build: the row's body rendered inline instead of fenced.

        This control is why the assertion order in the instrument is what it is.
        An earlier version opened with a global fence scan and reported this
        build as "unterminated fence" — a loud failure naming the wrong cause,
        which is exactly how a probe passes for the wrong reason.
        """
        broken = DRAIN_DIRECTIVE.replace(
            f"{FENCE}\n{smoke_p8b.HOSTILE_BODY}\n{FENCE}", smoke_p8b.HOSTILE_BODY
        )
        message = failure_of(
            assert_hostile_body_is_fenced,
            broken,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "the body is NOT fenced" in message
        assert "#41 [directive] smoke-sender→you" in message

    def test_a_three_backtick_fence_is_caught_as_a_SIZING_failure(self) -> None:
        """The wrong build: a FIXED three-backtick fence. It passes for an
        ordinary body and fails exactly here, on the hostile one — and it must
        say so, not report a malformed render."""
        broken = DRAIN_DIRECTIVE.replace(FENCE, "```")
        message = failure_of(
            assert_hostile_body_is_fenced,
            broken,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "fence is 3 backticks but the body carries a run of 4" in message

    def test_a_fence_exactly_as_wide_as_the_embedded_run_is_rejected(self) -> None:
        """The boundary: a four-wide fence around a four-wide run. The rule is
        ``> run``, not ``>= run``, and this is the only case that separates them."""
        body = "safe\n````\nsafe"
        rendered = f"drained 1 of 1 pending\n#41 [signal] s→you\n````\n{body}\n````"
        message = failure_of(
            assert_hostile_body_is_fenced,
            rendered,
            body=body,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "can close its own fence" in message

    def test_a_fence_one_wider_than_the_embedded_run_is_accepted(self) -> None:
        """The positive control for the boundary above: the SAME body, one
        backtick wider, must pass — so the rejection is about the width and not
        about the body."""
        body = "safe\n````\nsafe"
        rendered = f"drained 1 of 1 pending\n#41 [signal] s→you\n`````\n{body}\n`````"
        assert_hostile_body_is_fenced(
            rendered, body=body, real_seq=REAL_SEQ, check_name="control"
        )

    def test_a_sanitised_body_is_caught(self) -> None:
        """The wrong build: the body ran through ``sanitise_line`` and lost its
        newlines, so it is no longer the bytes the sender sent."""
        broken = DRAIN_DIRECTIVE.replace(
            smoke_p8b.HOSTILE_BODY, smoke_p8b.HOSTILE_BODY.replace("\n", " ")
        )
        message = failure_of(
            assert_hostile_body_is_fenced,
            broken,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "byte-verbatim EXACTLY once" in message

    def test_a_body_served_twice_is_caught(self) -> None:
        """Ambiguity is a finding: two copies mean the check cannot say which one
        it graded."""
        broken = f"{DRAIN_DIRECTIVE}\n{FENCE}\n{smoke_p8b.HOSTILE_BODY}\n{FENCE}"
        message = failure_of(
            assert_hostile_body_is_fenced,
            broken,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "found 2 occurrence(s)" in message

    def test_the_forged_seq_reaching_an_unfenced_line_is_caught(self) -> None:
        """The wrong build: the trailer took its seqs from the body's text."""
        broken = DRAIN_DIRECTIVE.replace(
            "ACK REQUIRED: #41 — lore_comms action=ack seqs=[41]",
            "ACK REQUIRED: #41 #9001 — lore_comms action=ack seqs=[41, 9001]",
        )
        message = failure_of(
            assert_hostile_body_is_fenced,
            broken,
            body=smoke_p8b.HOSTILE_BODY,
            real_seq=REAL_SEQ,
            check_name="control",
        )
        assert "forged seq 9001 reached an unfenced line" in message


# ==========================================================================
# Gate 1 — send / drain / ack
# ==========================================================================
class TestParseSendReceipt:
    def test_an_explicit_receipt_parses(self) -> None:
        receipt = parse_send_receipt(SEND_DIRECTIVE)
        assert (receipt.seq, receipt.grade, receipt.recipients) == (41, "directive", ("smoke-alpha",))
        assert receipt.broadcast_count is None
        assert receipt.ack_duty_line is not None

    def test_a_broadcast_receipt_is_not_read_as_an_explicit_one(self) -> None:
        """The broadcast literal is a strict instance of the explicit shape, so
        pattern ORDER is load-bearing: read the wrong way round, a broadcast to
        three agents parses as an explicit send to one oddly-named recipient."""
        receipt = parse_send_receipt(SEND_BROADCAST)
        assert receipt.broadcast_count == 3
        assert receipt.broadcast_session == SESSION
        assert receipt.recipients is None
        assert receipt.ack_duty_line is None

    def test_a_capped_recipient_list_reports_the_names_it_showed(self) -> None:
        receipt = parse_send_receipt("sent #9 [signal] → a, b, c, d, e (+7 more)")
        assert receipt.recipients == ("a", "b", "c", "d", "e")

    def test_an_ack_duty_line_naming_a_different_seq_does_not_count(self) -> None:
        broken = SEND_DIRECTIVE.replace("seqs=[41]", "seqs=[42]")
        assert parse_send_receipt(broken).ack_duty_line is None

    def test_an_unparseable_first_line_is_a_loud_failure(self) -> None:
        assert "matches neither" in failure_of(parse_send_receipt, "delivered ok")

    def test_an_empty_render_is_a_loud_failure(self) -> None:
        assert "render is empty" in failure_of(parse_send_receipt, "")


class TestParseDrainRender:
    def test_the_captured_directive_window_parses(self) -> None:
        drained = parse_drain_render(DRAIN_DIRECTIVE)
        assert (drained.shown, drained.total, drained.empty) == (1, 1, False)
        assert drained.rows[0].seq == 41
        assert drained.rows[0].body == smoke_p8b.HOSTILE_BODY
        assert drained.ack_required_demanded == (41,)
        assert drained.ack_required_taught == (41,)

    def test_the_empty_inbox_literal_parses(self) -> None:
        drained = parse_drain_render(DRAIN_EMPTY)
        assert drained.empty and not drained.rows

    def test_a_peek_header_and_an_elision_parse(self) -> None:
        rendered = "\n".join(
            (
                "peeked 2 of 7 pending — nothing stamped; re-run without peek=true to mark them seen",
                "#1 [signal] s→you",
                "```",
                "one",
                "```",
                "#2 [signal] s→you",
                "```",
                "two",
                "```",
                "+5 more unread — re-run with limit=5",
            )
        )
        drained = parse_drain_render(rendered)
        assert drained.peeked and (drained.shown, drained.total) == (2, 7)
        assert drained.elision == (5, 5)
        assert len(drained.rows) == 2

    def test_the_skew_block_is_left_among_the_unfenced_lines(self) -> None:
        drained = parse_drain_render(f"{DRAIN_EMPTY}\n{SKEW_LINE}")
        assert SKEW_LINE in drained.unfenced

    def test_a_row_with_no_fenced_body_is_a_loud_failure(self) -> None:
        """A body rendered unfenced is the whole hazard; it must never parse."""
        broken = "drained 1 of 1 pending\n#41 [directive] smoke-sender→you\nraw body"
        assert "is not followed by a FENCED body" in failure_of(parse_drain_render, broken)

    def test_an_unrecognised_header_is_a_loud_failure(self) -> None:
        assert "matches neither" in failure_of(parse_drain_render, "inbox: 1 unread")


class TestAssertDirectiveWindow:
    KWARGS: dict[str, Any] = {
        "seq": REAL_SEQ,
        "sender": "smoke-sender",
        "body": smoke_p8b.HOSTILE_BODY,
    }

    def test_the_captured_good_window_passes(self) -> None:
        row = assert_directive_window(DRAIN_DIRECTIVE, **self.KWARGS)
        assert row.seq == REAL_SEQ and row.fence == FENCE

    def test_a_window_of_the_wrong_size_is_caught(self) -> None:
        broken = DRAIN_DIRECTIVE.replace("drained 1 of 1", "drained 1 of 3")
        assert "drained 1 of 1 pending" in failure_of(
            assert_directive_window, broken, **self.KWARGS
        )

    def test_a_wrong_seq_is_caught(self) -> None:
        broken = DRAIN_DIRECTIVE.replace("#41 [directive]", "#40 [directive]")
        assert "!= the sent seq" in failure_of(assert_directive_window, broken, **self.KWARGS)

    def test_a_wrong_sender_is_caught(self) -> None:
        broken = DRAIN_DIRECTIVE.replace("smoke-sender→you", "someone-else→you")
        assert "expected 'directive' / 'smoke-sender'" in failure_of(
            assert_directive_window, broken, **self.KWARGS
        )

    def test_a_context_cell_on_the_session_default_thread_is_caught(self) -> None:
        """The wrong build: an UNCONDITIONAL thread label, which destroys the
        signal that a thread label means a deliberate conversation."""
        broken = DRAIN_DIRECTIVE.replace(
            "smoke-sender→you", f"smoke-sender→you (thread {SESSION})"
        )
        assert "context cell" in failure_of(assert_directive_window, broken, **self.KWARGS)

    def test_a_truncated_body_is_caught(self) -> None:
        broken = DRAIN_DIRECTIVE.replace(smoke_p8b.HOSTILE_BODY, "…truncated…")
        assert "did not round-trip verbatim" in failure_of(
            assert_directive_window, broken, **self.KWARGS
        )

    def test_a_missing_ack_trailer_is_caught(self) -> None:
        """Only the LAST line is dropped: the hostile body itself contains an
        ``ACK REQUIRED``-shaped line, so a filter on the prefix would mutate the
        body too and this control would fail for the wrong reason."""
        broken = DRAIN_DIRECTIVE.rsplit("\n", 1)[0]
        assert broken.endswith(FENCE)
        assert "trailer demands None" in failure_of(
            assert_directive_window, broken, **self.KWARGS
        )

    def test_a_trailer_teaching_an_empty_seq_list_is_caught(self) -> None:
        """The wrong build the committed proof marker waved through: a trailer
        that DEMANDS an ack while teaching a command discharging nothing."""
        broken = DRAIN_DIRECTIVE.replace("seqs=[41]", "seqs=[]")
        assert "discharges less than it demands" in failure_of(
            assert_directive_window, broken, **self.KWARGS
        )


# ==========================================================================
# Gate 3 — broadcast fan-out
# ==========================================================================
class TestFleetSessionShape:
    KWARGS: dict[str, Any] = {
        "session_name": SESSION,
        "expected_non_retired": 4,
        "expected_retired": 1,
    }

    def test_the_good_fleet_render_passes(self) -> None:
        assert_fleet_session_shape(FLEET_RENDER, **self.KWARGS)

    def test_a_missing_retired_trailer_is_caught(self) -> None:
        """The wrong build the guard exists for: the retired agent was never
        registered, so the broadcast count would be 'right' for a false reason."""
        broken = FLEET_RENDER.replace("\n+1 retired", "")
        assert "retired trailer(s) []" in failure_of(
            assert_fleet_session_shape, broken, **self.KWARGS
        )

    def test_a_wrong_non_retired_count_is_caught(self) -> None:
        broken = FLEET_RENDER.replace("4 non-retired", "3 non-retired")
        assert "expected 4" in failure_of(assert_fleet_session_shape, broken, **self.KWARGS)

    def test_an_unscoped_fleet_header_is_caught(self) -> None:
        broken = FLEET_RENDER.replace(f"fleet (session {SESSION}):", "fleet:")
        assert "unexpected session-scoped header" in failure_of(
            assert_fleet_session_shape, broken, **self.KWARGS
        )


class TestBroadcastReceipt:
    KWARGS: dict[str, Any] = {"expected_count": 3, "session_name": SESSION}

    def test_the_captured_good_broadcast_passes(self) -> None:
        assert assert_broadcast_receipt(SEND_BROADCAST, **self.KWARGS).seq == 42

    def test_including_the_sender_or_the_retired_agent_is_caught(self) -> None:
        broken = SEND_BROADCAST.replace("3 agents", "4 agents")
        message = failure_of(assert_broadcast_receipt, broken, **self.KWARGS)
        assert "reached 4 agents, expected 3" in message

    def test_a_cross_session_broadcast_is_caught(self) -> None:
        broken = SEND_BROADCAST.replace(SESSION, "somebody-elses-session")
        assert "never cross sessions" in failure_of(
            assert_broadcast_receipt, broken, **self.KWARGS
        )

    def test_an_explicit_receipt_for_a_to_less_send_is_caught(self) -> None:
        assert "EXPLICIT receipt shape" in failure_of(
            assert_broadcast_receipt, SEND_DIRECTIVE, **self.KWARGS
        )

    def test_an_ack_duty_on_a_signal_is_caught(self) -> None:
        broken = f"{SEND_BROADCAST}\nrecipients must ack: lore_comms action=ack seqs=[42]"
        assert "carries an ack-duty line" in failure_of(
            assert_broadcast_receipt, broken, **self.KWARGS
        )


class TestBroadcastDelivery:
    KWARGS: dict[str, Any] = {
        "seq": 42,
        "body": smoke_p8b.BROADCAST_BODY,
        "recipient": "smoke-bravo",
    }

    def test_a_real_delivery_passes(self) -> None:
        assert_broadcast_delivery(DRAIN_SIGNAL, **self.KWARGS)

    def test_a_recipient_that_received_nothing_is_caught(self) -> None:
        """The wrong build: the COUNT was right and the delivery set was not."""
        assert "expected 1 of 1" in failure_of(assert_broadcast_delivery, DRAIN_EMPTY, **self.KWARGS)

    def test_a_recipient_that_received_a_different_message_is_caught(self) -> None:
        broken = DRAIN_SIGNAL.replace("#42 [signal]", "#43 [signal]")
        assert "did not receive seq #42" in failure_of(
            assert_broadcast_delivery, broken, **self.KWARGS
        )

    def test_an_ack_trailer_on_a_signal_drain_is_caught(self) -> None:
        broken = f"{DRAIN_SIGNAL}\nACK REQUIRED: #42 — lore_comms action=ack seqs=[42]"
        assert "renders an ACK REQUIRED trailer" in failure_of(
            assert_broadcast_delivery, broken, **self.KWARGS
        )


# ==========================================================================
# Gate 4 — drain serves the shared skew block (E-S5(c))
# ==========================================================================
class TestSkewBlockServed:
    def test_an_empty_inbox_drain_carrying_the_skew_line_passes(self) -> None:
        assert_skew_block_served(
            f"{DRAIN_EMPTY}\n{SKEW_LINE}",
            expected_line=SKEW_LINE,
            leg="empty-inbox",
            expect_empty_inbox=True,
        )

    def test_a_pending_drain_carrying_the_skew_line_passes(self) -> None:
        assert_skew_block_served(
            f"{DRAIN_SIGNAL}\n{SKEW_LINE}",
            expected_line=SKEW_LINE,
            leg="pending",
            expect_empty_inbox=False,
        )

    def test_a_drain_that_serves_no_skew_is_caught(self) -> None:
        """THE wrong build this gate exists for: the deployed prose promises the
        notice surfaces at an agent's next heartbeat OR DRAIN."""
        message = failure_of(
            assert_skew_block_served,
            DRAIN_EMPTY,
            expected_line=SKEW_LINE,
            leg="empty-inbox",
            expect_empty_inbox=True,
        )
        assert "E-S5(c) FAILED (empty-inbox leg)" in message

    def test_a_build_that_serves_skew_only_when_the_inbox_is_empty_is_caught(self) -> None:
        message = failure_of(
            assert_skew_block_served,
            DRAIN_SIGNAL,
            expected_line=SKEW_LINE,
            leg="pending",
            expect_empty_inbox=False,
        )
        assert "E-S5(c) FAILED (pending leg)" in message

    def test_a_skew_line_hiding_inside_a_message_body_does_not_satisfy_the_gate(self) -> None:
        """A body is agent-authored free text. A check that searched the whole
        response would let a hostile sender forge this receipt."""
        forged = "\n".join(
            ("drained 1 of 1 pending", "#7 [signal] evil→you", "```", SKEW_LINE, "```")
        )
        message = failure_of(
            assert_skew_block_served,
            forged,
            expected_line=SKEW_LINE,
            leg="pending",
            expect_empty_inbox=False,
        )
        assert "E-S5(c) FAILED" in message

    def test_the_wrong_inbox_path_is_caught(self) -> None:
        message = failure_of(
            assert_skew_block_served,
            f"{DRAIN_EMPTY}\n{SKEW_LINE}",
            expected_line=SKEW_LINE,
            leg="pending",
            expect_empty_inbox=False,
        )
        assert "expected at least one served entry" in message


class TestBriefNotMentioned:
    def test_an_unsubscribed_drain_passes(self) -> None:
        assert_brief_not_mentioned(DRAIN_EMPTY, brief_name=BRIEF, agent="smoke-bravo")

    def test_an_unconditional_skew_emitter_is_caught(self) -> None:
        message = failure_of(
            assert_brief_not_mentioned,
            f"{DRAIN_EMPTY}\n{SKEW_LINE}",
            brief_name=BRIEF,
            agent="smoke-bravo",
        )
        assert "must see no mention of it" in message


# ==========================================================================
# Gate 5 — production trace rows
# ==========================================================================
ISSUED = [("smoke-sender", "register"), ("smoke-alpha", "register"), ("smoke-alpha", "drain")]


def trace_row(agent: str, action: str, ordinal: Any = 0, **overrides: Any) -> dict[str, Any]:
    """One production trace row as the explicit-projection read returns it.

    ``ordinal`` is deliberately ``Any``: the controls need to hand it a ``None``
    (an unset ``option<int>``) and a ``bool`` (the ok flag written into the wrong
    column), which are exactly the values a typed parameter would forbid.
    """
    row: dict[str, Any] = {
        "tool": "lore_comms",
        "agent": agent,
        "action": action,
        "session": SESSION,
        "transport_session": "mcp-1",
        "ordinal": ordinal,
        "ok": True,
        # ``ts`` rides the projection because the read ORDERs BY it; it is here so
        # the offline fixture is the shape the real read returns, not a subset.
        "ts": "2026-07-25T14:53:10.367274Z",
    }
    row.update(overrides)
    return row


GOOD_ROWS = [trace_row(agent, action, index) for index, (agent, action) in enumerate(ISSUED)]
TRACE_KWARGS: dict[str, Any] = {
    "issued": ISSUED,
    "session_name": SESSION,
    "check_name": "control",
}


class TestAssertTraceRows:
    def test_the_good_row_set_passes(self) -> None:
        assert_trace_rows(GOOD_ROWS, **TRACE_KWARGS)

    def test_zero_rows_is_the_147_shape_and_stops_here(self) -> None:
        """Every assertion below the guard is trivially true of an empty set —
        which is precisely how a build with no telemetry at all passes."""
        assert "ZERO trace rows" in failure_of(assert_trace_rows, [], **TRACE_KWARGS)

    def test_a_missing_call_is_caught(self) -> None:
        assert "multiset does not match" in failure_of(
            assert_trace_rows, GOOD_ROWS[:-1], **TRACE_KWARGS
        )

    def test_a_row_attributed_to_the_wrong_agent_is_caught(self) -> None:
        broken = [*GOOD_ROWS[:-1], trace_row("smoke-bravo", "drain", 2)]
        assert "multiset does not match" in failure_of(assert_trace_rows, broken, **TRACE_KWARGS)

    def test_a_row_from_another_session_is_caught(self) -> None:
        broken = [*GOOD_ROWS[:-1], trace_row("smoke-alpha", "drain", 2, session="other")]
        assert "carry a session other than" in failure_of(
            assert_trace_rows, broken, **TRACE_KWARGS
        )

    def test_a_row_naming_another_tool_is_caught(self) -> None:
        broken = [*GOOD_ROWS[:-1], trace_row("smoke-alpha", "drain", 2, tool="lore_search")]
        assert "unexpected tool(s)" in failure_of(assert_trace_rows, broken, **TRACE_KWARGS)

    def test_an_ok_false_row_is_caught(self) -> None:
        broken = [*GOOD_ROWS[:-1], trace_row("smoke-alpha", "drain", 2, ok=False)]
        assert "must carry ok=True" in failure_of(assert_trace_rows, broken, **TRACE_KWARGS)

    def test_an_unset_ok_column_is_caught(self) -> None:
        """An ``option<bool>`` column the emission forgot to supply reads None
        under an explicit projection — never a KeyError, so nothing else notices."""
        broken = [*GOOD_ROWS[:-1], trace_row("smoke-alpha", "drain", 2, ok=None)]
        assert "must carry ok=True" in failure_of(assert_trace_rows, broken, **TRACE_KWARGS)

    def test_no_drain_row_is_caught(self) -> None:
        issued = ISSUED[:-1] + [("smoke-alpha", "heartbeat")]
        rows = [trace_row(agent, action, i) for i, (agent, action) in enumerate(issued)]
        message = failure_of(
            assert_trace_rows, rows, issued=issued, session_name=SESSION, check_name="control"
        )
        assert "no row carries action='drain'" in message


class TestAssertOrdinals:
    def test_zero_based_ordinals_pass(self) -> None:
        """``sequence::nextval`` starts at 0, so a pin assuming 1-based is wrong."""
        assert assert_ordinals(GOOD_ROWS, check_name="control") == [0, 1, 2]

    def test_a_missing_ordinal_is_caught(self) -> None:
        broken = [trace_row("a", "drain", ordinal=None)]
        assert "server-side mint did not run" in failure_of(
            assert_ordinals, broken, check_name="control"
        )

    def test_a_boolean_in_the_ordinal_column_is_caught(self) -> None:
        """``bool`` is a subclass of ``int``; a build writing the ok flag into the
        ordinal column would pass a naive isinstance check."""
        broken = [trace_row("a", "drain", ordinal=True)]
        assert "expected an int" in failure_of(assert_ordinals, broken, check_name="control")

    def test_a_constant_ordinal_is_caught(self) -> None:
        broken = [trace_row("a", "drain", 7), trace_row("b", "drain", 7)]
        assert "not distinct" in failure_of(assert_ordinals, broken, check_name="control")

    def test_an_ordinal_that_goes_backwards_is_caught(self) -> None:
        broken = [trace_row("a", "drain", 5), trace_row("b", "drain", 2)]
        assert "do not increase with write time" in failure_of(
            assert_ordinals, broken, check_name="control"
        )

    def test_gaps_are_accepted_deliberately(self) -> None:
        """The ordinal rides a native sequence: an aborted call burns a number, so
        gaps are REAL and the ordinal is an ordering key, never a count."""
        assert assert_ordinals(
            [trace_row("a", "drain", 3), trace_row("b", "drain", 91)], check_name="control"
        ) == [3, 91]


class TestAnonymousRowsDeclareNothing:
    def test_rows_declaring_nothing_pass(self) -> None:
        rows = [{"agent": None, "session": None, "action": None} for _ in range(3)]
        assert_anonymous_rows_declare_nothing(rows, tool="lore_index", check_name="control")

    def test_an_empty_row_set_proves_nothing_and_is_caught(self) -> None:
        assert "trivially true" in failure_of(
            assert_anonymous_rows_declare_nothing, [], tool="lore_index", check_name="control"
        )

    def test_the_session_sticky_guessing_build_is_caught(self) -> None:
        """The wrong build: attributing a paramless call to 'probably the same
        agent as the last one' — a guess no downstream aggregate can tell from a
        declaration."""
        rows = [
            {"agent": None, "session": None, "action": None},
            {"agent": "smoke-alpha", "session": SESSION, "action": None},
        ]
        message = failure_of(
            assert_anonymous_rows_declare_nothing,
            rows,
            tool="lore_index",
            check_name="control",
        )
        assert "identity is being INFERRED" in message


class TestProductionAccessIsReadOnly:
    """The production-safety rule, enforced rather than trusted."""

    @pytest.mark.parametrize(
        "query",
        [
            smoke_p8b.ProductionTraceReader._SESSION_ROWS,
            smoke_p8b.ProductionTraceReader._ROWS_BY_TOOL,
        ],
    )
    def test_the_shipped_reads_are_accepted(self, query: str) -> None:
        smoke_p8b.ProductionTraceReader._require_read_only(query)

    @pytest.mark.parametrize(
        "query",
        [
            "DELETE trace",
            "REMOVE TABLE trace",
            "UPDATE trace SET ok = true",
            "DEFINE FIELD OVERWRITE ordinal ON trace TYPE int",
            "SELECT * FROM trace; DELETE trace",
            "  \n  delete trace",
        ],
    )
    def test_every_non_select_is_refused(self, query: str) -> None:
        assert "READ-ONLY" in failure_of(
            smoke_p8b.ProductionTraceReader._require_read_only, query
        )


# ==========================================================================
# DRY-RUN — the whole gate flow, against a scripted MCP session
# ==========================================================================
# The five gates cannot be run for real without a deployed build, but their
# WIRING can: the call sequence each one issues, the arguments it sends, and the
# way it reads what comes back. A scripted session answers with the captured
# renders in a fixed order and asserts the action of every call it receives, so
# a gate that called the wrong verb, in the wrong order, or as the wrong agent
# fails here — offline, before deploy night.
RUN_ID = "deadbeef"
ANY_RENDER = "(a render this gate does not read)"


class ScriptedSession:
    """A ``ClientSession`` stand-in that answers from an ordered transcript."""

    def __init__(self, script: list[tuple[str, str]]) -> None:
        self._script = list(script)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        from mcp.types import CallToolResult, TextContent

        self.calls.append((name, arguments))
        if not self._script:
            raise AssertionError(f"unscripted extra call: {name} {arguments}")
        expected_action, response = self._script.pop(0)
        actual_action = arguments.get("action", name)
        if actual_action != expected_action:
            raise AssertionError(
                f"call {len(self.calls)}: expected action {expected_action!r}, got "
                f"{actual_action!r} ({arguments})"
            )
        return CallToolResult(content=[TextContent(type="text", text=response)], isError=False)

    @property
    def exhausted(self) -> bool:
        """True when every scripted response was consumed (no gate skipped a step)."""
        return not self._script


ROUND_TRIP_SCRIPT = [
    ("register", ANY_RENDER),
    ("register", ANY_RENDER),
    ("send", SEND_DIRECTIVE),
    ("drain", DRAIN_DIRECTIVE),
    ("ack", ACK_ONE),
    ("drain", DRAIN_EMPTY),
]
BROADCAST_SCRIPT = [
    ("register", ANY_RENDER),
    ("register", ANY_RENDER),
    ("register", ANY_RENDER),
    ("heartbeat", ANY_RENDER),
    ("fleet", FLEET_RENDER),
    ("send", SEND_BROADCAST),
    ("drain", DRAIN_SIGNAL),
    ("drain", DRAIN_SIGNAL),
    ("drain", DRAIN_SIGNAL),
]
PUBLISH_V1 = (
    f"brief '{BRIEF}' v1 published by smoke-sender — first version; "
    "agents ack with lore_comms action=brief_ack"
)
PUBLISH_V2 = f"brief '{BRIEF}' v2 published by smoke-sender"
SKEW_SCRIPT = [
    ("brief_publish", PUBLISH_V1),
    ("brief_ack", ANY_RENDER),
    ("brief_publish", PUBLISH_V2),
    ("heartbeat", f"agent smoke-alpha · active\n{SKEW_LINE}"),
    ("send", ANY_RENDER),
    ("drain", f"{DRAIN_SIGNAL}\n{SKEW_LINE}"),
    ("drain", f"{DRAIN_EMPTY}\n{SKEW_LINE}"),
    ("drain", DRAIN_EMPTY),
]


def scripted_fleet(script: list[tuple[str, str]]) -> tuple[smoke_p8b.SmokeFleet, ScriptedSession]:
    """A :class:`SmokeFleet` wired to a scripted session, with this run's id."""
    session = ScriptedSession(script)
    return smoke_p8b.SmokeFleet(session, run_id=RUN_ID), session  # type: ignore[arg-type]


class TestGateFlowDryRun:
    """Every gate's wire flow, exercised end to end with no deployed build."""

    async def test_the_session_and_brief_names_are_self_identifying(self) -> None:
        fleet, _ = scripted_fleet([])
        assert fleet.session_name == SESSION
        assert fleet.brief_name == BRIEF
        assert fleet.session_name.startswith(smoke_p8b.SMOKE_SESSION_PREFIX)

    async def test_gate_1_and_2_flow(self) -> None:
        fleet, session = scripted_fleet(ROUND_TRIP_SCRIPT)
        await smoke_p8b.check_comms_round_trip(fleet)
        assert session.exhausted
        assert [agent for agent, _ in fleet.issued] == [
            "smoke-sender",
            "smoke-alpha",
            "smoke-sender",
            "smoke-alpha",
            "smoke-alpha",
            "smoke-alpha",
        ]

    async def test_every_call_declares_the_runs_session(self) -> None:
        """The gate-5 read is session-scoped, which only works because EVERY call
        declares the session. A call that omitted it would silently drop out of
        the trace row set and the exact-multiset assertion would go red."""
        fleet, session = scripted_fleet(ROUND_TRIP_SCRIPT)
        await smoke_p8b.check_comms_round_trip(fleet)
        assert all(arguments["session"] == SESSION for _, arguments in session.calls)
        assert {name for name, _ in session.calls} == {"lore_comms"}

    async def test_the_directive_send_declares_the_hostile_body(self) -> None:
        fleet, session = scripted_fleet(ROUND_TRIP_SCRIPT)
        await smoke_p8b.check_comms_round_trip(fleet)
        send = next(args for _, args in session.calls if args["action"] == "send")
        assert send["body"] == smoke_p8b.HOSTILE_BODY
        assert send["grade"] == "directive"
        assert send["to"] == ["smoke-alpha"]

    async def test_gate_1_fails_when_the_re_drain_still_shows_the_message(self) -> None:
        """The wrong build: drain served the row without STAMPING it, so the
        message comes back forever. Nothing but a second drain can see that."""
        script = [*ROUND_TRIP_SCRIPT[:-1], ("drain", DRAIN_DIRECTIVE)]
        fleet, _ = scripted_fleet(script)
        message = await await_failure(smoke_p8b.check_comms_round_trip(fleet))
        assert "must have STAMPED the row" in message

    async def test_gate_3_flow(self) -> None:
        fleet, session = scripted_fleet(BROADCAST_SCRIPT)
        await smoke_p8b.check_broadcast_reaches_non_retired(fleet)
        assert session.exhausted
        retire = next(
            args for _, args in session.calls if args["action"] == "heartbeat"
        )
        assert retire["agent"] == "smoke-retired" and retire["status"] == "retired"
        broadcast = next(args for _, args in session.calls if args["action"] == "send")
        assert "to" not in broadcast, "a broadcast must omit 'to' entirely"
        assert broadcast["grade"] == "signal"

    async def test_gate_3_fails_when_the_broadcast_includes_one_agent_too_many(self) -> None:
        script = [
            (action, SEND_BROADCAST.replace("3 agents", "4 agents") if action == "send" else text)
            for action, text in BROADCAST_SCRIPT
        ]
        fleet, _ = scripted_fleet(script)
        message = await await_failure(smoke_p8b.check_broadcast_reaches_non_retired(fleet))
        assert "reached 4 agents, expected 3" in message

    async def test_gate_4_flow(self) -> None:
        fleet, session = scripted_fleet(SKEW_SCRIPT)
        await smoke_p8b.check_drain_serves_skew(fleet)
        assert session.exhausted
        publishes = [args for _, args in session.calls if args["action"] == "brief_publish"]
        assert [args["name"] for args in publishes] == [BRIEF, BRIEF]
        ack = next(args for _, args in session.calls if args["action"] == "brief_ack")
        assert (ack["agent"], ack["name"], ack["version"]) == ("smoke-alpha", BRIEF, 1)
        assert [args["agent"] for _, args in session.calls if args["action"] == "drain"] == [
            "smoke-alpha",
            "smoke-alpha",
            "smoke-bravo",
        ]

    async def test_gate_4_fails_when_the_drain_serves_no_skew(self) -> None:
        """THE E-S5(c) wrong build: heartbeat surfaces the notice and drain does
        not, while the shipped prose promises both."""
        script = [
            (action, DRAIN_SIGNAL if text == f"{DRAIN_SIGNAL}\n{SKEW_LINE}" else text)
            for action, text in SKEW_SCRIPT
        ]
        fleet, _ = scripted_fleet(script)
        message = await await_failure(smoke_p8b.check_drain_serves_skew(fleet))
        assert "E-S5(c) FAILED (pending leg)" in message

    async def test_gate_4_stops_when_heartbeat_itself_serves_no_skew(self) -> None:
        """The fixture-validity guard: with nothing to surface, every later
        assertion is trivially satisfiable and the gate must refuse to pass."""
        script = [
            (action, "agent smoke-alpha · active" if action == "heartbeat" else text)
            for action, text in SKEW_SCRIPT
        ]
        fleet, _ = scripted_fleet(script)
        message = await await_failure(smoke_p8b.check_drain_serves_skew(fleet))
        assert "nothing this gate asserts about DRAIN can discriminate" in message

    async def test_gate_4_fails_when_an_unsubscribed_agent_is_told_about_the_brief(self) -> None:
        script = [*SKEW_SCRIPT[:-1], ("drain", f"{DRAIN_EMPTY}\n{SKEW_LINE}")]
        fleet, _ = scripted_fleet(script)
        message = await await_failure(smoke_p8b.check_drain_serves_skew(fleet))
        assert "must see no mention of it" in message


async def await_failure(coroutine: Any) -> str:
    """Await ``coroutine`` expecting a :class:`SmokeCheckFailed`; return its message."""
    try:
        await coroutine
    except SmokeCheckFailed as exc:
        return str(exc)
    raise AssertionError("expected SmokeCheckFailed, none raised")


SHIPPED_READS = [
    smoke_p8b.ProductionTraceReader._SESSION_ROWS,
    smoke_p8b.ProductionTraceReader._ROWS_BY_TOOL,
]
# Parametrising over the ordered reads only, rather than skipping inside the
# test: a ∀-over-a-collection assertion is trivially true of an empty one, so the
# set is derived AND asserted non-empty rather than quietly shrinking to nothing.
ORDERED_READS = [query for query in SHIPPED_READS if " ORDER BY " in query]
assert ORDERED_READS, "no shipped read orders — the ORDER BY pin would be vacuous"


class TestEngineGotchasArePinned:
    """The two engine defects the live probe caught, converted into invariants.

    Both were found on 2026-07-25 by running the reader against the TEST store
    (:18000) before the deploy — each would otherwise have failed the gate on
    deploy night, in a window where a red smoke reads as "the build is broken".
    A fix without an invariant is half a fix: the next edit to these statements
    re-opens both unless something goes RED.
    """

    @pytest.mark.parametrize("query", SHIPPED_READS)
    def test_no_read_binds_a_variable_named_session(self, query: str) -> None:
        """``session`` is a PROTECTED variable name on this engine, and the
        protection is wider than the store reference's own example: it is not
        only ``SET session = …`` on a write that is refused — binding a variable
        NAMED ``session`` is refused on a bare SELECT too."""
        assert "$session" not in query, (
            "binding $session is rejected by the engine: 'session' is a protected "
            "variable and cannot be set. Rename the BIND VARIABLE (the column may "
            "keep the name)."
        )

    @pytest.mark.parametrize("query", ORDERED_READS)
    def test_every_order_by_idiom_is_also_projected(self, query: str) -> None:
        """On 3.2.1 an ``ORDER BY`` idiom absent from an EXPLICIT projection is a
        parse error. ``SELECT *`` never hits it — which is the trap, because the
        store reference requires an explicit projection for every ``option<>``
        column, and every trace enrichment column is one."""
        projection = query.split("SELECT ", 1)[1].split(" FROM ", 1)[0]
        projected = {name.strip() for name in projection.split(",")}
        ordered = {name.strip() for name in query.split(" ORDER BY ", 1)[1].split(",")}
        missing = sorted(ordered - projected)
        assert not missing, (
            f"ORDER BY idiom(s) {missing} are not in the projection — the engine "
            f"answers 'Missing order idiom in statement selection', a PARSE error"
        )

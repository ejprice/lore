"""Unit tests for the deterministic core of ``scripts/comms_consumer_eval.py``.

Scope, and why it is drawn here: the eval's live half (a real Anthropic
conversation, the real ``_render_comms_*`` helpers) is exercised by running the
instrument.  Everything BELOW that — answer parsing, every grader, the gate
arithmetic, the battery's shape, transcript emission, the render seam's
fail-loud contract, and the fixture spec's discriminating values — is pure and is
pinned here, network-free and **without requiring the packet-03b renders to
exist**.  The renders are mocked; the seam that reaches the real ones is pinned by
asserting it REFUSES to proceed when they are absent or have drifted.

⚠ POSITIVE CONTROLS ARE THE POINT.  Every grader is tested twice: once with an
answer it must accept, and once with a plausible WRONG answer it must reject.  A
grader nobody has watched fire is indistinguishable from a grader that accepts
everything — and this instrument's whole job is to catch things, so an instrument
that cannot itself be caught failing is worthless (repo ``CLAUDE.md``: a probe
needs a control).

Run: ``uv run pytest scripts/test_comms_consumer_eval.py -q``
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from typing import Any

import pytest

# The instrument lives beside this test file in ``scripts/`` (not an installed
# package), so make that directory importable before importing it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import comms_consumer_eval as cce  # noqa: E402  (path insert must precede the import)

SPEC = cce.SPEC
GRADERS = cce.Graders(SPEC)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _surfaces(**overrides: Any) -> cce.ServedSurfaces:
    """A fully-populated ``ServedSurfaces`` whose text is obviously synthetic.

    Nothing here pretends to be a render — these are unit-test stand-ins for the
    STRINGS the live provider generates, used to drive the prompt assembler, the
    runner, and the transcript writer without touching production code.
    """
    base = {
        "instructions": "INSTRUCTIONS-BLOCK",
        "tool_description": "TOOL-DESCRIPTION",
        "tool_schema": "- action (required): ACTION-DESC",
        "send_directive": "SEND-DIRECTIVE",
        "send_broadcast": "SEND-BROADCAST",
        "send_question_a": "SEND-QUESTION-A",
        "send_self_note": "SEND-SELF-NOTE",
        "send_question_b1": "SEND-QUESTION-B1",
        "send_question_b2": "SEND-QUESTION-B2",
        "drain_main": "DRAIN-MAIN",
        "drain_empty": "DRAIN-EMPTY",
        "drain_peek": "DRAIN-PEEK",
        "drain_after_peek": "DRAIN-AFTER-PEEK",
        "drain_reply": "DRAIN-REPLY",
        "ack": "ACK-RENDER",
        "rejects": (("an oversize body", "REJECT-OVERSIZE"),),
        "provenance": ("provenance-line",),
    }
    base.update(overrides)
    return cce.ServedSurfaces(**base)  # type: ignore[arg-type]


def _good_answers() -> dict[int, dict[str, Any]]:
    """One correct answer per task, derived from the SAME spec the graders use."""
    trailer = list(SPEC.trailer_seqs)
    return {
        1: {"seqs": trailer, "call": f"lore_comms action=ack seqs={trailer}"},
        2: {"remaining": SPEC.more, "call": f"lore_comms action=drain limit={SPEC.next_limit}"},
        3: {"delivered_seqs": list(SPEC.served_seqs)},
        4: {"ack_again": False},
        5: {"still_waiting": True},
        6: {
            "thread_discharged": True,
            "next_move_call": (
                "lore_comms action=send to=['lead'] grade='signal' "
                "thread='q:clamp' set_status='input_required' body='and the clamp?'"
            ),
        },
        7: {"call": "lore_comms action=send to=['fixer-b'] grade='directive' body='do it'"},
        8: {"meaning": "NEVER_DELIVERED_TO_ME", "retry_blindly": False},
        9: {"still_unread": True, "call": "lore_comms action=drain limit=3"},
        10: {"call": "lore_comms action=send grade='signal' body='the gate is red'"},
        11: {"meaning": "NO_SUCH_MESSAGE_EXISTS", "retry_blindly": False},
        12: {
            "tool_failed": False,
            "anything_lost": False,
            "anything_sent": False,
            "fix_for_oversize": cce.OVERSIZE_FIX_TOKENS[0],
        },
        13: {
            "shown": SPEC.shown,
            "more": SPEC.more,
            "total": SPEC.total_pending,
            "next_limit": SPEC.next_limit,
        },
        14: {
            "matched_teaching": True,
            "peeked_rows_were_still_unread": True,
            "stamping_drain_served_them": True,
        },
        15: {"verdict": "CALL_AGAIN", "reason": "the counts and the teaching held up"},
    }


class FakeConsumerClient:
    """A scripted consumer: replies with a canned answer per task, in order."""

    def __init__(
        self,
        answers: dict[int, dict[str, Any]],
        *,
        raw: dict[int, str] | None = None,
        served_model: str | None = None,
    ):
        """Bind the per-task answers, any raw replies, and the model to report."""
        self._answers = answers
        self._raw = raw or {}
        self._served_model = served_model
        self.calls = 0
        self.systems: list[str] = []

    def _response(self) -> Any:
        """A stand-in API response carrying only what the runner reads off it."""
        from types import SimpleNamespace

        return SimpleNamespace(model=self._served_model, usage=None)

    async def ask(self, system: str, turns: Any) -> tuple[str, Any]:
        """Return the scripted reply for the next task."""
        self.calls += 1
        self.systems.append(system)
        if self.calls in self._raw:
            return self._raw[self.calls], self._response()
        import json as _json

        payload = _json.dumps(self._answers[self.calls])
        return f"reasoning line\nANSWER: {payload}", self._response()


# --------------------------------------------------------------------------- #
# 1. Measurement pins
# --------------------------------------------------------------------------- #
class TestPins:
    def test_the_floor_model_is_a_literal_pin(self) -> None:
        assert cce.FLOOR_MODEL == "claude-sonnet-5"

    def test_the_population_is_the_three_named_members_floor_first(self) -> None:
        assert cce.POPULATION_MODELS == (
            "claude-sonnet-5",
            "claude-opus-5",
            "claude-fable-5",
        )
        assert cce.POPULATION_MODELS[0] == cce.FLOOR_MODEL

    def test_the_gate_is_three_consecutive_runs(self) -> None:
        assert cce.GATE_CONSECUTIVE_RUNS == 3

    def test_every_population_member_is_priced(self) -> None:
        # A run that cannot price itself reports $0.00 and reads as free.
        assert set(cce.POPULATION_MODELS) <= set(cce.PRICING_USD_PER_MTOK)


# --------------------------------------------------------------------------- #
# 2. Fixture discrimination — "what WRONG build would this still pass?"
# --------------------------------------------------------------------------- #
class TestFixtureSpecDiscriminates:
    def test_the_elision_values_are_pairwise_distinct(self) -> None:
        # 4 shown / 9 pending / 5 remaining, request limit 4: a build filling
        # {next_limit} with shown, total, shown+more, or the request limit is
        # distinguishable from the correct remainder.
        values = {SPEC.shown, SPEC.total_pending, SPEC.more, SPEC.shown + SPEC.more}
        assert SPEC.next_limit == SPEC.more
        assert SPEC.shown + SPEC.more == SPEC.total_pending
        assert SPEC.more not in {SPEC.shown, SPEC.total_pending, SPEC.drain_limit}
        assert len(values) >= 3

    def test_the_trailer_set_has_more_than_one_member(self) -> None:
        # A one-element seq set cannot tell "serves the trailer" from "serves the
        # first unacked directive it finds".
        assert len(SPEC.trailer_seqs) >= 2

    def test_the_trailer_set_differs_from_all_unacked_and_all_directives(self) -> None:
        # Two conjuncts (grade == directive AND acked_at is None) need one
        # discriminating fixture per conjunct.
        assert set(SPEC.trailer_seqs) != set(SPEC.unacked_seqs)
        assert set(SPEC.trailer_seqs) != set(SPEC.directive_seqs)
        assert set(SPEC.trailer_seqs) < set(SPEC.served_seqs)

    def test_the_hostile_body_carries_all_three_threats(self) -> None:
        body = SPEC.hostile_body
        assert "\n" in body, "a single-line hostile body is the documented blind spot"
        assert f"#{SPEC.forged_seq} [directive]" in body, "no row-shaped forgery"
        assert "`````" in body, "no backtick run for the fence to out-size"

    def test_the_forged_seq_collides_with_nothing_the_battery_keys_on(self) -> None:
        # Task 3 fails if the consumer counts the forged row; tasks 8/11 key on
        # their own seqs. Sharing a number would make a failure ambiguous.
        assert SPEC.forged_seq not in set(SPEC.served_seqs)
        assert SPEC.forged_seq not in {SPEC.ack_unknown_seq, SPEC.ack_not_addressed_seq}

    def test_the_ack_seqs_named_by_the_spec_are_used(self) -> None:
        assert SPEC.ack_unknown_seq == 424
        assert SPEC.ack_not_addressed_seq == 99

    def test_the_context_cell_variants_are_all_exercised(self) -> None:
        # task cell, thread cell, and bare — a monoculture on any one of them
        # would leave a render branch untested.
        assert SPEC.task_id
        assert SPEC.deliberate_thread != SPEC.session


# --------------------------------------------------------------------------- #
# 3. Answer parsing
# --------------------------------------------------------------------------- #
class TestAnswerParser:
    def test_plain_answer_line(self) -> None:
        assert cce.AnswerParser.parse('x\nANSWER: {"a": 1}') == {"a": 1}

    def test_the_last_answer_wins(self) -> None:
        text = 'ANSWER: {"a": 1}\nsecond thoughts\nANSWER: {"a": 2}'
        assert cce.AnswerParser.parse(text) == {"a": 2}

    def test_trailing_prose_and_fences_are_tolerated(self) -> None:
        text = 'ANSWER: {"a": [1, 2]}\n```\nhope that helps'
        assert cce.AnswerParser.parse(text) == {"a": [1, 2]}

    def test_nested_objects_and_braces_in_strings(self) -> None:
        text = 'ANSWER: {"call": "lore_comms action=ack seqs=[1]", "n": {"k": "}"}}'
        assert cce.AnswerParser.parse(text)["n"] == {"k": "}"}

    def test_missing_marker_is_an_error(self) -> None:
        with pytest.raises(cce.AnswerFormatError):
            cce.AnswerParser.parse("no marker here")

    def test_unbalanced_object_is_an_error(self) -> None:
        with pytest.raises(cce.AnswerFormatError):
            cce.AnswerParser.parse('ANSWER: {"a": 1')

    def test_a_non_object_payload_is_an_error(self) -> None:
        with pytest.raises(cce.AnswerFormatError):
            cce.AnswerParser.parse("ANSWER: [1, 2]")

    def test_escaped_quotes_do_not_end_the_object_early(self) -> None:
        # A rendered call or a quoted body excerpt inside the answer must not
        # truncate the payload — an early cut would silently drop later keys.
        text = 'ANSWER: {"call": "say \\"hi\\" then }", "seqs": [71]}'
        parsed = cce.AnswerParser.parse(text)
        assert parsed["seqs"] == [71]
        assert parsed["call"] == 'say "hi" then }'

    def test_a_trailing_backslash_before_the_closing_quote_is_handled(self) -> None:
        parsed = cce.AnswerParser.parse('ANSWER: {"a": "back\\\\", "b": 2}')
        assert parsed == {"a": "back\\", "b": 2}


# --------------------------------------------------------------------------- #
# 4. Tool-call parsing
# --------------------------------------------------------------------------- #
class TestToolCall:
    def test_parses_action_and_seq_list(self) -> None:
        call = cce.ToolCall.parse("lore_comms action=ack seqs=[71, 74] note='done'")
        assert call is not None
        assert call.action == "ack"
        assert call.ints("seqs") == {71, 74}
        assert call.raw("note") == "'done'"

    def test_parses_quoted_recipient_list(self) -> None:
        call = cce.ToolCall.parse("lore_comms action=send to=['fixer-b', 'lead']")
        assert call is not None
        assert call.names("to") == ["fixer-b", "lead"]

    def test_parses_json_ish_colon_form(self) -> None:
        call = cce.ToolCall.parse('lore_comms {"action": "drain", "limit": 5}')
        assert call is not None
        assert call.action == "drain"
        assert call.raw("limit") == "5"

    def test_empty_recipient_list_is_recognised(self) -> None:
        call = cce.ToolCall.parse("lore_comms action=send to=[] grade='signal'")
        assert call is not None
        assert call.is_empty_list("to") is True

    def test_absent_call_is_none(self) -> None:
        assert cce.ToolCall.parse("I would send a message") is None

    def test_peek_flag_truthiness(self) -> None:
        assert cce.ToolCall.parse("lore_comms action=drain peek=true").flag_is_true("peek")  # type: ignore[union-attr]
        assert not cce.ToolCall.parse("lore_comms action=drain peek=false").flag_is_true("peek")  # type: ignore[union-attr]


class TestCoercions:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(True, True), ("yes", True), ("NO", False), (False, False), ("maybe", None), (3, None)],
    )
    def test_bool_coercion(self, value: Any, expected: bool | None) -> None:
        assert cce.coerce_bool(value) is expected

    def test_int_coercion_rejects_bools(self) -> None:
        assert cce.coerce_int(True) is None
        assert cce.coerce_int("5 messages") == 5

    def test_int_set_coercion(self) -> None:
        assert cce.coerce_int_set("#71 and #74") == {71, 74}
        assert cce.coerce_int_set([71, "74"]) == {71, 74}
        assert cce.coerce_int_set("none") is None


# --------------------------------------------------------------------------- #
# 5. Graders — each one accepted on a good answer AND caught firing on a bad one
# --------------------------------------------------------------------------- #
class TestGradersAcceptCorrectAnswers:
    @pytest.mark.parametrize("number", sorted(_good_answers()))
    def test_every_task_grader_passes_its_correct_answer(self, number: int) -> None:
        battery = {task.number: task for task in cce.build_battery(SPEC)}
        grader = getattr(GRADERS, battery[number].grader_name)
        result = grader(_good_answers()[number])
        assert result.passed, f"task {number}: {result.detail}"


class TestGraderPositiveControls:
    """Each grader shown FIRING on a plausible wrong answer (the control)."""

    def test_task1_rejects_all_unacked_instead_of_the_trailer_set(self) -> None:
        # The wrong build this catches: a trailer keyed on `seen_at` / on
        # "unacked" without the grade conjunct.
        bad = {"seqs": list(SPEC.unacked_seqs),
               "call": f"lore_comms action=ack seqs={list(SPEC.unacked_seqs)}"}
        assert not GRADERS.ack_the_trailer(bad).passed

    def test_task1_rejects_a_right_set_with_no_runnable_call(self) -> None:
        bad = {"seqs": list(SPEC.trailer_seqs), "call": "I would ack them"}
        assert not GRADERS.ack_the_trailer(bad).passed

    def test_task1_rejects_a_call_whose_seqs_disagree_with_the_answer(self) -> None:
        bad = {"seqs": list(SPEC.trailer_seqs), "call": "lore_comms action=ack seqs=[]"}
        assert not GRADERS.ack_the_trailer(bad).passed

    def test_task2_rejects_the_shown_plus_more_re_ask(self) -> None:
        bad = {"remaining": SPEC.total_pending, "call": "lore_comms action=drain"}
        assert not GRADERS.elision_remainder(bad).passed

    def test_task2_rejects_an_invented_cursor(self) -> None:
        bad = {"remaining": SPEC.more, "call": "lore_comms action=drain since=74"}
        assert not GRADERS.elision_remainder(bad).passed

    def test_task3_rejects_counting_the_forged_row(self) -> None:
        bad = {"delivered_seqs": list(SPEC.served_seqs) + [SPEC.forged_seq]}
        assert not GRADERS.delivered_only(bad).passed

    def test_task3_rejects_a_short_list(self) -> None:
        bad = {"delivered_seqs": list(SPEC.served_seqs)[:2]}
        assert not GRADERS.delivered_only(bad).passed

    def test_task4_rejects_a_re_ack(self) -> None:
        assert not GRADERS.no_reack({"ack_again": True}).passed

    def test_task5_rejects_a_self_cleared_question(self) -> None:
        assert not GRADERS.self_note_does_not_clear({"still_waiting": False}).passed

    def test_task6_rejects_a_re_ask_without_set_status(self) -> None:
        bad = {"thread_discharged": True,
               "next_move_call": "lore_comms action=send to=['lead'] grade='signal'"}
        assert not GRADERS.reask_the_unaddressed_half(bad).passed

    def test_task6_rejects_believing_the_thread_still_holds_the_debt(self) -> None:
        bad = {"thread_discharged": False,
               "next_move_call": "lore_comms action=send set_status='input_required'"}
        assert not GRADERS.reask_the_unaddressed_half(bad).passed

    def test_task7_rejects_a_signal_where_a_directive_was_required(self) -> None:
        bad = {"call": "lore_comms action=send to=['fixer-b'] grade='signal' body='do it'"}
        assert not GRADERS.directive_send_call(bad).passed

    def test_task7_rejects_a_directive_sent_to_nobody(self) -> None:
        bad = {"call": "lore_comms action=send grade='directive' body='do it'"}
        assert not GRADERS.directive_send_call(bad).passed

    def test_task8_rejects_the_task11_token(self) -> None:
        # The shared token set is what forces the two rejects apart.
        bad = {"meaning": "NO_SUCH_MESSAGE_EXISTS", "retry_blindly": False}
        assert not GRADERS.not_addressed(bad).passed

    def test_task8_rejects_a_blind_retry(self) -> None:
        bad = {"meaning": "NEVER_DELIVERED_TO_ME", "retry_blindly": True}
        assert not GRADERS.not_addressed(bad).passed

    def test_task11_rejects_the_task8_token(self) -> None:
        bad = {"meaning": "NEVER_DELIVERED_TO_ME", "retry_blindly": False}
        assert not GRADERS.unknown_message(bad).passed

    def test_task11_rejects_an_off_vocabulary_token(self) -> None:
        bad = {"meaning": "SOMETHING_ELSE", "retry_blindly": False}
        assert not GRADERS.unknown_message(bad).passed

    def test_task9_rejects_believing_a_peek_stamped(self) -> None:
        bad = {"still_unread": False, "call": "lore_comms action=drain"}
        assert not GRADERS.peek_leaves_unread(bad).passed

    def test_task9_rejects_a_stamping_call_that_still_peeks(self) -> None:
        bad = {"still_unread": True, "call": "lore_comms action=drain peek=true"}
        assert not GRADERS.peek_leaves_unread(bad).passed

    def test_task10_rejects_an_enumerated_recipient_list(self) -> None:
        bad = {"call": "lore_comms action=send to=['auditor-a','fixer-c'] grade='signal'"}
        assert not GRADERS.broadcast_call(bad).passed

    def test_task10_rejects_an_off_vocabulary_grade(self) -> None:
        bad = {"call": "lore_comms action=send grade='urgent' body='red'"}
        assert not GRADERS.broadcast_call(bad).passed

    def test_task12_rejects_reading_a_reject_as_loss(self) -> None:
        bad = dict(_good_answers()[12], anything_lost=True)
        assert not GRADERS.rejects_admit(bad).passed

    def test_task12_rejects_believing_a_rejected_send_was_delivered(self) -> None:
        bad = dict(_good_answers()[12], anything_sent=True)
        assert not GRADERS.rejects_admit(bad).passed

    def test_task12_rejects_the_wrong_taught_fix(self) -> None:
        bad = dict(_good_answers()[12], fix_for_oversize=cce.OVERSIZE_FIX_TOKENS[2])
        assert not GRADERS.rejects_admit(bad).passed

    def test_task13_rejects_a_next_limit_of_shown_plus_more(self) -> None:
        bad = dict(_good_answers()[13], next_limit=SPEC.total_pending)
        assert not GRADERS.counts_agree(bad).passed

    def test_task13_rejects_arithmetic_that_does_not_close(self) -> None:
        bad = dict(_good_answers()[13], more=SPEC.more + 1)
        assert not GRADERS.counts_agree(bad).passed

    def test_task14_rejects_a_teaching_mismatch(self) -> None:
        bad = dict(_good_answers()[14], peeked_rows_were_still_unread=False)
        assert not GRADERS.teaching_matched(bad).passed

    def test_task15_rejects_route_around(self) -> None:
        bad = {"verdict": "ROUTE_AROUND", "reason": "the counts did not add up"}
        result = GRADERS.routing_verdict(bad)
        assert not result.passed
        assert "FAILED acceptance" in result.detail

    def test_task15_rejects_a_verdict_with_no_reason(self) -> None:
        assert not GRADERS.routing_verdict({"verdict": "CALL_AGAIN", "reason": "  "}).passed

    def test_task15_rejects_an_off_vocabulary_verdict(self) -> None:
        assert not GRADERS.routing_verdict({"verdict": "MAYBE", "reason": "unsure"}).passed


class TestGradersRejectMissingKeys:
    @pytest.mark.parametrize("number", sorted(_good_answers()))
    def test_dropping_any_required_key_fails(self, number: int) -> None:
        battery = {task.number: task for task in cce.build_battery(SPEC)}
        task = battery[number]
        grader = getattr(GRADERS, task.grader_name)
        for key in task.answer_keys:
            answer = dict(_good_answers()[number])
            answer.pop(key)
            result = grader(answer)
            assert not result.passed, f"task {number} passed without {key!r}"


# --------------------------------------------------------------------------- #
# 6. The battery's shape
# --------------------------------------------------------------------------- #
class TestBattery:
    def test_all_fifteen_tasks_present_and_numbered(self) -> None:
        battery = cce.build_battery(SPEC)
        assert [task.number for task in battery] == list(range(1, 16))

    def test_the_routing_test_is_asked_last(self) -> None:
        # §C2/§C5(d): task 15 takes the whole session as context, so it can only
        # be asked once every other answer exists.
        battery = cce.build_battery(SPEC)
        assert battery[-1].number == 15
        assert battery[-1].grader_name == "routing_verdict"

    def test_every_task_is_mandatory(self) -> None:
        assert all(task.mandatory for task in cce.build_battery(SPEC))

    def test_slugs_are_unique(self) -> None:
        slugs = [task.slug for task in cce.build_battery(SPEC)]
        assert len(set(slugs)) == len(slugs)

    def test_every_grader_name_resolves(self) -> None:
        for task in cce.build_battery(SPEC):
            assert callable(getattr(GRADERS, task.grader_name, None)), task.grader_name

    def test_the_rendered_prompt_names_the_answer_keys(self) -> None:
        for task in cce.build_battery(SPEC):
            rendered = task.rendered_prompt()
            for key in task.answer_keys:
                assert f"`{key}`" in rendered

    def test_the_four_trust_probes_are_tasks_twelve_to_fifteen(self) -> None:
        battery = {task.number: task for task in cce.build_battery(SPEC)}
        assert [battery[n].grader_name for n in (12, 13, 14, 15)] == [
            "rejects_admit",
            "counts_agree",
            "teaching_matched",
            "routing_verdict",
        ]


# --------------------------------------------------------------------------- #
# 7. The consumer prompt — served surfaces only
# --------------------------------------------------------------------------- #
class TestConsumerPrompt:
    def test_every_served_surface_reaches_the_prompt(self) -> None:
        surfaces = _surfaces()
        text = cce.ConsumerPrompt(surfaces, SPEC).system_text()
        for value in (
            surfaces.instructions,
            surfaces.tool_description,
            surfaces.tool_schema,
            surfaces.send_directive,
            surfaces.send_broadcast,
            surfaces.send_question_a,
            surfaces.send_self_note,
            surfaces.send_question_b1,
            surfaces.send_question_b2,
            surfaces.drain_main,
            surfaces.drain_empty,
            surfaces.drain_peek,
            surfaces.drain_after_peek,
            surfaces.drain_reply,
            surfaces.ack,
            surfaces.rejects[0][1],
        ):
            assert value in text

    def test_the_prompt_leaks_no_spec(self) -> None:
        # §C1.2: a consumer that can see the spec is not measuring the render.
        text = cce.ConsumerPrompt(_surfaces(), SPEC).system_text()
        for leak in ("03b-design-rulings", "PASS criterion", "§C", "ruling", "acceptance"):
            assert leak not in text

    def test_the_prompt_is_stable_across_assemblies(self) -> None:
        # A byte-stable prefix is what makes the cached system block cache.
        surfaces = _surfaces()
        first = cce.ConsumerPrompt(surfaces, SPEC).system_text()
        second = cce.ConsumerPrompt(surfaces, SPEC).system_text()
        assert first == second


# --------------------------------------------------------------------------- #
# 8. The runner and the gate
# --------------------------------------------------------------------------- #
class TestBatteryRunner:
    async def _run(self, client: FakeConsumerClient) -> cce.RunOutcome:
        runner = cce.BatteryRunner(
            surfaces=_surfaces(), battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        return await runner.run(client, model="fake-model", run_index=1)

    async def test_a_fully_correct_consumer_passes_every_task(self) -> None:
        run = await self._run(FakeConsumerClient(_good_answers()))
        assert run.passed, [item.result.detail for item in run.mandatory_failures]
        assert len(run.outcomes) == 15

    async def test_one_wrong_answer_fails_the_run(self) -> None:
        answers = _good_answers()
        answers[3] = {"delivered_seqs": list(SPEC.served_seqs) + [SPEC.forged_seq]}
        run = await self._run(FakeConsumerClient(answers))
        assert not run.passed
        assert [item.task.number for item in run.mandatory_failures] == [3]

    async def test_a_route_around_verdict_fails_the_run(self) -> None:
        answers = _good_answers()
        answers[15] = {"verdict": "ROUTE_AROUND", "reason": "I do not trust the counts"}
        run = await self._run(FakeConsumerClient(answers))
        assert not run.passed
        assert [item.task.number for item in run.mandatory_failures] == [15]

    async def test_an_unreadable_answer_is_a_failure_not_a_skip(self) -> None:
        client = FakeConsumerClient(_good_answers(), raw={7: "I would just send a message."})
        run = await self._run(client)
        assert not run.passed
        failure = run.mandatory_failures[0]
        assert failure.task.number == 7
        assert "unreadable answer" in failure.result.detail
        assert len(run.outcomes) == 15, "an unreadable answer must not truncate the run"

    async def test_the_system_prompt_is_identical_on_every_turn(self) -> None:
        client = FakeConsumerClient(_good_answers())
        await self._run(client)
        assert len(set(client.systems)) == 1


class TestModelPinDrift:
    """The pin is a bare alias, so the RECEIPT is what the API answered on.

    Upstream can repoint ``claude-sonnet-5`` with no edit to this repo. A
    transcript recording only the REQUESTED id would show nothing; recording the
    responded ``model`` turns "measurement pins are never silently upgraded" from
    a hope into something a reader can check.
    """

    def test_no_notice_when_the_answer_came_from_the_pinned_model(self) -> None:
        assert model_drift_is_none("claude-sonnet-5", ["claude-sonnet-5"])

    def test_no_notice_when_no_response_reported_a_model(self) -> None:
        assert model_drift_is_none("claude-sonnet-5", [])

    def test_a_different_answering_model_produces_a_loud_notice(self) -> None:
        # POSITIVE CONTROL: the drift path is shown firing.
        notice = cce.model_drift_notice(
            requested="claude-sonnet-5", served=["claude-sonnet-5-20260901"]
        )
        assert notice is not None
        assert "MODEL PIN DRIFT" in notice
        assert "claude-sonnet-5-20260901" in notice
        assert "claude-sonnet-5'" in notice

    async def test_a_run_records_the_answering_model_and_flags_drift(self) -> None:
        runner = cce.BatteryRunner(
            surfaces=_surfaces(), battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        client = FakeConsumerClient(_good_answers(), served_model="claude-sonnet-5-20260901")
        run = await runner.run(client, model=cce.FLOOR_MODEL, run_index=1)
        assert run.served_models == ("claude-sonnet-5-20260901",)
        assert run.drift_notice is not None
        # Drift does not silently change the keyed verdict — it is reported beside it.
        assert run.passed

    async def test_a_run_on_the_pinned_model_flags_nothing(self) -> None:
        runner = cce.BatteryRunner(
            surfaces=_surfaces(), battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        client = FakeConsumerClient(_good_answers(), served_model=cce.FLOOR_MODEL)
        run = await runner.run(client, model=cce.FLOOR_MODEL, run_index=1)
        assert run.served_models == (cce.FLOOR_MODEL,)
        assert run.drift_notice is None

    async def test_the_transcript_carries_both_the_answering_model_and_the_notice(self) -> None:
        surfaces = _surfaces()
        runner = cce.BatteryRunner(
            surfaces=surfaces, battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        client = FakeConsumerClient(_good_answers(), served_model="claude-sonnet-5-20260901")
        run = await runner.run(client, model=cce.FLOOR_MODEL, run_index=1)
        text = cce.TranscriptWriter(surfaces=surfaces, spec=SPEC).render(
            mode="gate", runs=[run], started_at=datetime.now(UTC)
        )
        assert "MODEL PIN DRIFT" in text
        assert "`claude-sonnet-5-20260901`" in text


def model_drift_is_none(requested: str, served: list[str]) -> bool:
    """Helper: the notice is absent for this (requested, served) pair."""
    return cce.model_drift_notice(requested=requested, served=served) is None


class TestAbsentSurfacesAreLoud:
    def test_an_absent_surface_is_named_in_the_transcript(self) -> None:
        surfaces = _surfaces(absent_surfaces=("the roster reject: no registry",))
        text = cce.TranscriptWriter(surfaces=surfaces, spec=SPEC).render(
            mode="gate", runs=[], started_at=datetime.now(UTC)
        )
        assert "SURFACES THIS RUN COULD NOT GENERATE" in text
        assert "the roster reject: no registry" in text

    def test_a_complete_run_says_so_explicitly(self) -> None:
        # The absence of an absence is stated, so a reader never has to infer it
        # from a missing section.
        text = cce.TranscriptWriter(surfaces=_surfaces(), spec=SPEC).render(
            mode="gate", runs=[], started_at=datetime.now(UTC)
        )
        assert "none absent" in text


def _synthetic_run(*, passed: bool, index: int = 1, served: str = "fake") -> cce.RunOutcome:
    """A RunOutcome with one task's verdict and a chosen answering model."""
    task = cce.build_battery(SPEC)[0]
    result = cce.GradeResult(passed, "synthetic")
    return cce.RunOutcome(
        model="fake",
        run_index=index,
        outcomes=[cce.TaskOutcome(task, "raw", {}, result)],
        usage=cce.Usage(),
        served_models=(served,),
    )


class TestGateArithmetic:
    def _run(self, *, passed: bool, index: int = 1) -> cce.RunOutcome:
        return _synthetic_run(passed=passed, index=index)

    def test_three_clean_runs_pass(self) -> None:
        runs = [self._run(passed=True, index=i) for i in (1, 2, 3)]
        verdict = cce.evaluate_gate(runs)
        assert verdict.satisfied
        assert verdict.counted == 3
        assert verdict.exit_code == cce.EXIT_OK

    def test_one_green_run_does_not_pass_the_gate(self) -> None:
        # §C3: one green run proves nothing about a stochastic instrument.
        verdict = cce.evaluate_gate([self._run(passed=True)])
        assert not verdict.satisfied
        # Not a surface failure — the surface was never measured enough times.
        assert not verdict.surface_failed
        assert verdict.exit_code == cce.EXIT_GATE_INVALID

    def test_two_green_and_one_red_is_a_SURFACE_failure(self) -> None:
        runs = [self._run(passed=True, index=1), self._run(passed=False, index=2),
                self._run(passed=True, index=3)]
        verdict = cce.evaluate_gate(runs)
        assert not verdict.satisfied
        assert verdict.surface_failed
        assert verdict.exit_code == cce.EXIT_SURFACE_FAIL

    def test_a_red_run_in_any_position_fails(self) -> None:
        for red in range(3):
            runs = [self._run(passed=(i != red), index=i + 1) for i in range(3)]
            assert not cce.evaluate_gate(runs).satisfied


class TestADriftedRunIsNotAGatingRun:
    """The lead's ruling, made mechanical (2026-07-25).

    §C3 defines the gate as the mandatory keys ON THE PINNED CONSUMER MODEL. A run
    answered by some other model has not met that definition — it is neither a pass
    nor a failure, it is not a gating run. The hazard being closed is a drifted run
    passing quietly and later being cited as "the battery passed on the pinned floor
    model"; the "answered by" column makes drift visible, refusing to COUNT it makes
    that citation impossible.
    """

    def _run(self, *, passed: bool, index: int, served: str) -> cce.RunOutcome:
        return _synthetic_run(passed=passed, index=index, served=served)

    def test_three_green_runs_one_of_them_drifted_do_NOT_satisfy_the_gate(self) -> None:
        # THE POSITIVE CONTROL for the whole ruling.
        runs = [
            self._run(passed=True, index=1, served="fake"),
            self._run(passed=True, index=2, served="fake-but-repointed"),
            self._run(passed=True, index=3, served="fake"),
        ]
        verdict = cce.evaluate_gate(runs)
        assert not verdict.satisfied
        assert verdict.counted == 2, "the drifted run must not count toward the three"
        assert not verdict.surface_failed, "drift is not a surface failure"
        assert verdict.exit_code == cce.EXIT_GATE_INVALID
        assert any("NOT counted toward the gate" in reason for reason in verdict.reasons)

    def test_three_green_undrifted_runs_DO_satisfy_the_gate(self) -> None:
        # The control's control: the same shape, minus the drift, must pass — or
        # the test above would be satisfied by a gate that never passes anything.
        runs = [self._run(passed=True, index=i, served="fake") for i in (1, 2, 3)]
        assert cce.evaluate_gate(runs).satisfied

    def test_the_refusal_reason_names_the_run_and_both_models(self) -> None:
        runs = [self._run(passed=True, index=2, served="fake-but-repointed")]
        reason = cce.evaluate_gate(runs, required=1).reasons[0]
        assert "run 2" in reason
        assert "fake-but-repointed" in reason
        assert "'fake'" in reason

    def test_a_drifted_run_does_not_reset_the_others(self) -> None:
        # A drifted run says nothing about the surface in EITHER direction, so it
        # neither extends nor breaks the streak — four runs with one drifted still
        # give three valid ones.
        runs = [
            self._run(passed=True, index=1, served="fake"),
            self._run(passed=True, index=2, served="fake-but-repointed"),
            self._run(passed=True, index=3, served="fake"),
            self._run(passed=True, index=4, served="fake"),
        ]
        verdict = cce.evaluate_gate(runs)
        assert verdict.satisfied
        assert verdict.counted == 3

    def test_a_drifted_FAILING_run_is_not_blamed_on_the_surface(self) -> None:
        # We cannot attribute a failure to the surface when a different model
        # answered — so it is excluded, and the gate is invalid rather than red.
        runs = [
            self._run(passed=True, index=1, served="fake"),
            self._run(passed=True, index=2, served="fake"),
            self._run(passed=False, index=3, served="fake-but-repointed"),
        ]
        verdict = cce.evaluate_gate(runs)
        assert not verdict.satisfied
        assert not verdict.surface_failed
        assert verdict.exit_code == cce.EXIT_GATE_INVALID

    def test_the_exit_codes_are_three_distinct_values(self) -> None:
        assert len({cce.EXIT_OK, cce.EXIT_SURFACE_FAIL, cce.EXIT_NO_KEY,
                    cce.EXIT_GATE_INVALID}) == 4

    def test_the_transcript_states_the_gate_verdict_and_why(self) -> None:
        runs = [
            _synthetic_run(passed=True, index=1, served="fake"),
            _synthetic_run(passed=True, index=2, served="fake-but-repointed"),
            _synthetic_run(passed=True, index=3, served="fake"),
        ]
        verdict = cce.evaluate_gate(runs)
        text = cce.TranscriptWriter(surfaces=_surfaces(), spec=SPEC).render(
            mode="gate", runs=runs, started_at=datetime.now(UTC), verdict=verdict
        )
        assert "GATE NOT SATISFIED" in text
        assert "only 2/3 runs were valid gating runs" in text
        assert "NOT counted toward the gate" in text
        assert "| no — model drift |" in text


class TestUsageAndCost:
    def test_cost_uses_the_pinned_rates_and_cache_multipliers(self) -> None:
        usage = cce.Usage(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cache_creation_input_tokens=1_000_000,
            cache_read_input_tokens=1_000_000,
        )
        input_rate, output_rate = cce.PRICING_USD_PER_MTOK["claude-sonnet-5"]
        expected = (
            input_rate
            + input_rate * cce.CACHE_WRITE_MULTIPLIER
            + input_rate * cce.CACHE_READ_MULTIPLIER
            + output_rate
        )
        assert usage.usd("claude-sonnet-5") == pytest.approx(expected)

    def test_usage_accumulates_across_responses(self) -> None:
        usage = cce.Usage()

        class _Response:
            usage = type("U", (), {"input_tokens": 10, "output_tokens": 3,
                                   "cache_creation_input_tokens": 0,
                                   "cache_read_input_tokens": 7})()

        usage.add(_Response())
        usage.add(_Response())
        assert usage.as_dict() == {
            "input_tokens": 20,
            "output_tokens": 6,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 14,
        }


# --------------------------------------------------------------------------- #
# 9. The render seam fails LOUD (it never falls back to a transcribed render)
# --------------------------------------------------------------------------- #
class TestRenderSeamFailsLoud:
    def test_a_missing_helper_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class _EmptyAppContext:
            pass

        monkeypatch.setattr(
            cce.LiveSurfaceProvider,
            "_server_module",
            staticmethod(lambda: type("M", (), {"AppContext": _EmptyAppContext})),
        )
        with pytest.raises(cce.RenderSeamUnavailable) as excinfo:
            cce.LiveSurfaceProvider._render_helper("_render_comms_drain")
        assert "_render_comms_drain" in str(excinfo.value)

    def test_a_helper_that_does_not_accept_our_kwargs_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _Drifted:
            @staticmethod
            def _render_comms_drain(result: Any, *, agent_name: str, limit: int) -> str:
                return ""

        monkeypatch.setattr(
            cce.LiveSurfaceProvider,
            "_server_module",
            staticmethod(lambda: type("M", (), {"AppContext": _Drifted})),
        )
        with pytest.raises(cce.RenderSeamUnavailable) as excinfo:
            cce.LiveSurfaceProvider._render_helper("_render_comms_drain")
        assert "session" in str(excinfo.value)

    def test_a_new_required_kwarg_we_do_not_pass_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _Grown:
            @staticmethod
            def _render_comms_drain(
                result: Any, *, agent_name: str, limit: int, session: str, skew: str
            ) -> str:
                return ""

        monkeypatch.setattr(
            cce.LiveSurfaceProvider,
            "_server_module",
            staticmethod(lambda: type("M", (), {"AppContext": _Grown})),
        )
        with pytest.raises(cce.RenderSeamUnavailable) as excinfo:
            cce.LiveSurfaceProvider._render_helper("_render_comms_drain")
        assert "skew" in str(excinfo.value)

    def test_a_new_OPTIONAL_kwarg_is_tolerated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Strictness has a bound: an added kwarg WITH a default cannot silently
        # change what the seam renders, so it is not drift.
        class _Grown:
            @staticmethod
            def _render_comms_drain(
                result: Any, *, agent_name: str, limit: int, session: str, skew: str = ""
            ) -> str:
                return "ok"

        monkeypatch.setattr(
            cce.LiveSurfaceProvider,
            "_server_module",
            staticmethod(lambda: type("M", (), {"AppContext": _Grown})),
        )
        helper = cce.LiveSurfaceProvider._render_helper("_render_comms_drain")
        assert helper(None, agent_name="a", limit=1, session="s") == "ok"

    def test_expected_kwargs_cover_all_three_helpers(self) -> None:
        assert set(cce.LiveSurfaceProvider._EXPECTED_KWARGS) == {
            "_render_comms_send",
            "_render_comms_drain",
            "_render_comms_ack",
        }


# --------------------------------------------------------------------------- #
# 9b. The generated fixtures agree with what the graders expect
#
# SKIPPED (never failed) until the packet-03b renders exist — the brief's rule is
# that this file must not require them.  Once they DO exist these run for free and
# catch the expensive failure mode: a fixture spec and a real render that disagree,
# which would burn three live gate runs before anyone noticed the eval was wrong
# about its own fixtures rather than the surface being wrong.
# --------------------------------------------------------------------------- #
def _fenced_state(lines: list[str]) -> list[tuple[str, bool]]:
    """Pair each line with whether it sits INSIDE a fence."""
    import re as _re

    out: list[tuple[str, bool]] = []
    marker: str | None = None
    for line in lines:
        stripped = line.strip()
        is_fence = bool(_re.fullmatch(r"`{3,}", stripped))
        if marker is None and is_fence:
            marker = stripped
            out.append((line, True))
            continue
        if marker is not None and stripped == marker:
            marker = None
            out.append((line, True))
            continue
        out.append((line, marker is not None))
    return out


@pytest.fixture(scope="module")
def live_renders() -> dict[str, Any]:
    """The REAL renders, or a skip when the build has not landed."""
    provider = cce.LiveSurfaceProvider(SPEC)
    try:
        rendered: dict[str, Any] = {}
        rendered.update(provider._sends())
        rendered.update(provider._drains())
        rendered["ack"] = provider._ack()
    except cce.RenderSeamUnavailable as exc:
        pytest.skip(f"packet-03b renders not available: {exc}")
    return rendered


@pytest.fixture(scope="module")
def live_roster_reject() -> str:
    """The REAL unknown-recipient reject WITH its counted roster, or a skip."""
    import asyncio as _asyncio

    reject, absence = _asyncio.run(cce.LiveSurfaceProvider(SPEC)._roster_reject())
    if absence is not None:
        pytest.skip(f"roster reject not available: {absence}")
    return reject[1]


class TestTheRosterCountIsHonest:
    """The count-bearing surface `send` newly routes agents into.

    The project's consumer law says a served count must describe the whole set its
    label claims. The roster's remainder is derived by production from
    ``AgentFleetWindow.total_non_retired`` — the pre-truncation count under the same
    session filter — never from the returned row window or the display cap, so a
    roster past the cap cannot silently truncate. These assertions are that claim
    made checkable on the REAL code path.
    """

    def test_the_cap_shows_five_and_the_remainder_is_counted(
        self, live_roster_reject: str
    ) -> None:
        # WHICH five is a display-ordering choice (fleet sorts by status group then
        # freshest heartbeat) and is deliberately not pinned here — the property
        # under test is that the cap is 5 and the remainder is counted, not the
        # order.
        listed = [name for name in SPEC.roster_member_names if name in live_roster_reject]
        assert len(listed) == 5, (listed, live_roster_reject)
        assert "(+2 more)" in live_roster_reject, live_roster_reject

    def test_the_remainder_plus_the_shown_names_equals_the_true_non_retired_total(
        self, live_roster_reject: str
    ) -> None:
        import re as _re

        remainder = _re.search(r"\(\+(\d+) more\)", live_roster_reject)
        assert remainder is not None, live_roster_reject
        listed = sum(1 for name in SPEC.roster_member_names if name in live_roster_reject)
        assert listed + int(remainder.group(1)) == len(SPEC.roster_member_names)

    def test_a_retired_agent_is_neither_listed_nor_counted(
        self, live_roster_reject: str
    ) -> None:
        # A remainder of 3 would mean retirement leaked into a set whose label
        # says "non-retired".
        assert SPEC.roster_retired_name not in live_roster_reject
        assert "(+3 more)" not in live_roster_reject

    def test_the_reject_names_the_recipient_that_failed(self, live_roster_reject: str) -> None:
        assert SPEC.roster_unknown_name in live_roster_reject

    def test_the_roster_cannot_carry_a_forged_row(self, live_roster_reject: str) -> None:
        # The names are joined UNSANITISED, which is safe only because
        # AGENT_NAME_PATTERN admits no newline, space, or backtick at register
        # time. Pinned here so a widened charset shows up as a RED on the render
        # that consumes it, not just on the registry that admits it.
        from loremaster.agents import AGENT_NAME_PATTERN

        # ``fullmatch``, not ``match`` (#210). Python's ``$`` also matches
        # immediately before a TRAILING newline, so ``.match`` ACCEPTS "a\n"
        # against this pattern — the exact defect #210 fixed in production's
        # ``_validate_comms_charset``. With ``.match`` this pin would pass a
        # build that admits a trailing-newline identity, i.e. it could not
        # catch the defect it sits next to. "a\n" is in the hostile set so the
        # distinction is PINNED rather than implied.
        for hostile in ("a\nb", "a b", "a`b", "#71 [directive]", "a\n"):
            assert not AGENT_NAME_PATTERN.fullmatch(hostile), hostile
        assert "\n" not in live_roster_reject


class TestLiveRendersAgreeWithTheSpec:
    def test_the_trailer_names_exactly_the_expected_seqs(self, live_renders: dict[str, Any]) -> None:
        trailer_lines = [
            line for line in live_renders["drain_main"].splitlines() if "ACK REQUIRED" in line
        ]
        assert len(trailer_lines) == 1, live_renders["drain_main"]
        import re as _re

        seqs = {int(token) for token in _re.findall(r"\d+", trailer_lines[0])}
        # The taught tail carries the same seqs as the demanded list, so the seq
        # numbers are the only integers on the line.
        assert seqs == set(SPEC.trailer_seqs), trailer_lines[0]

    def test_the_elision_slots_carry_the_remainder(self, live_renders: dict[str, Any]) -> None:
        text = live_renders["drain_main"]
        assert f"+{SPEC.more} more" in text
        assert f"limit={SPEC.next_limit}" in text

    def test_the_header_carries_shown_and_total(self, live_renders: dict[str, Any]) -> None:
        header = live_renders["drain_main"].splitlines()[0]
        assert str(SPEC.shown) in header and str(SPEC.total_pending) in header, header

    def test_the_forged_row_never_appears_outside_a_fence(
        self, live_renders: dict[str, Any]
    ) -> None:
        # The consumer-side half of §B7.3: task 3 is only answerable if the forgery
        # is visibly content. If it ever leaks unfenced, the eval would be grading
        # a genuinely ambiguous render.
        needle = f"#{SPEC.forged_seq} [directive]"
        pairs = _fenced_state(live_renders["drain_main"].splitlines())
        hits = [(line, inside) for line, inside in pairs if needle in line]
        assert hits, "the hostile fixture's forged row is not in the render at all"
        assert all(inside for _, inside in hits), hits

    def test_the_peek_render_has_no_trailer_and_the_stamping_one_does(
        self, live_renders: dict[str, Any]
    ) -> None:
        # §B13 with its positive control: the same window, both ways.
        assert "ACK REQUIRED" not in live_renders["drain_peek"]
        assert "ACK REQUIRED" in live_renders["drain_after_peek"]

    def test_the_acked_row_is_marked_and_kept_out_of_the_trailer(
        self, live_renders: dict[str, Any]
    ) -> None:
        text = live_renders["drain_main"]
        trailer = [line for line in text.splitlines() if "ACK REQUIRED" in line][0]
        assert str(SPEC.directive_acked) not in trailer
        assert str(SPEC.signal_unacked) not in trailer

    def test_the_question_teach_names_the_thread_and_the_self_note_does_not(
        self, live_renders: dict[str, Any]
    ) -> None:
        assert SPEC.self_note_thread in live_renders["send_question_a"]
        assert "question on thread" not in live_renders["send_self_note"]

    def test_the_ack_render_names_every_outcome_seq(self, live_renders: dict[str, Any]) -> None:
        text = live_renders["ack"]
        for seq in (SPEC.ack_acked_seq, SPEC.ack_already_seq, SPEC.ack_unknown_seq,
                    SPEC.ack_not_addressed_seq):
            assert str(seq) in text, (seq, text)

    def test_the_empty_drain_is_honest_not_an_error(self, live_renders: dict[str, Any]) -> None:
        text = live_renders["drain_empty"].lower()
        assert "error" not in text and "fail" not in text, text


# --------------------------------------------------------------------------- #
# 10. Transcript emission
# --------------------------------------------------------------------------- #
class TestTranscript:
    async def test_the_transcript_carries_provenance_verdicts_and_surfaces(self) -> None:
        surfaces = _surfaces()
        runner = cce.BatteryRunner(
            surfaces=surfaces, battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        run = await runner.run(FakeConsumerClient(_good_answers()), model="fake", run_index=1)
        text = cce.TranscriptWriter(surfaces=surfaces, spec=SPEC).render(
            mode="gate", runs=[run], started_at=datetime.now(UTC)
        )
        assert "provenance-line" in text
        assert cce.FLOOR_MODEL in text
        assert "| `fake` | _not reported_ | 1 | PASS | yes |" in text
        assert "task 15 — routing-verdict (PASS)" in text
        assert "served surfaces (verbatim, as the consumer saw them)" in text

    async def test_a_failing_run_is_named_in_the_verdict_table(self) -> None:
        surfaces = _surfaces()
        answers = _good_answers()
        answers[13] = dict(answers[13], next_limit=999)
        runner = cce.BatteryRunner(
            surfaces=surfaces, battery=cce.build_battery(SPEC), graders=GRADERS, spec=SPEC
        )
        run = await runner.run(FakeConsumerClient(answers), model="fake", run_index=2)
        text = cce.TranscriptWriter(surfaces=surfaces, spec=SPEC).render(
            mode="gate", runs=[run], started_at=datetime.now(UTC)
        )
        assert "| `fake` | _not reported_ | 2 | FAIL | yes | #13 |" in text


# --------------------------------------------------------------------------- #
# 11. CLI wiring
# --------------------------------------------------------------------------- #
class TestCli:
    def test_default_mode_is_the_gate_on_the_floor_model(self) -> None:
        args = cce._parse_args([])
        assert args.mode == "gate"
        assert args.model == cce.FLOOR_MODEL
        assert args.runs == cce.GATE_CONSECUTIVE_RUNS

    def test_dry_run_is_available(self) -> None:
        assert cce._parse_args(["--dry-run"]).dry_run is True

    def test_gate_mode_plans_three_runs_on_the_floor_model(self) -> None:
        plan = cce.build_plan(mode="gate", model="ignored", runs=cce.GATE_CONSECUTIVE_RUNS)
        assert plan == [(cce.FLOOR_MODEL, 1), (cce.FLOOR_MODEL, 2), (cce.FLOOR_MODEL, 3)]

    def test_population_mode_plans_one_run_per_named_member(self) -> None:
        plan = cce.build_plan(mode="population", model="ignored", runs=99)
        assert plan == [(member, 1) for member in cce.POPULATION_MODELS]

    def test_single_mode_honours_the_named_model(self) -> None:
        assert cce.build_plan(mode="single", model="claude-opus-5", runs=3) == [
            ("claude-opus-5", 1)
        ]

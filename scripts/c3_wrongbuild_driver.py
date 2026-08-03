#!/usr/bin/env python3
"""c3fix_wrongbuilds.py — re-run the adversary's 26 wrong builds against the REPAIRED C3
contract, and diff the observed RED set against a DECLARED one BOTH WAYS.

Run from the scratch reference-build root:

    uv run python c3fix_wrongbuilds.py            # every wrong build
    uv run python c3fix_wrongbuilds.py W2 W12     # a subset

WHY THIS AND NOT scripts/mutation_proof.py DIRECTLY: several wrong builds need MORE THAN
ONE anchored edit (W5 breaks four return sites; W15 forks one seam per dispatcher), and
mutation_proof.py takes a single anchor. This driver keeps every property that makes that
tool trustworthy and adds multi-edit support:

  * every edit asserts its anchor matched EXACTLY the declared number of times, and the
    run ABORTS if it did not — a mutation that never LANDED prints a green tail that reads
    exactly like a successful proof (#194);
  * the DECLARED red set is validated against ``pytest --collect-only`` BEFORE any run, so
    a typo'd or renamed node id is a hard error rather than a silently-empty expectation;
  * the observed set is diffed BOTH WAYS — unexpected reds AND declared reds that stayed
    GREEN, the direction that catches a mutation landing in dead code;
  * production files are restored from a CONTENT backup (never a hash list) and the
    restore is verified byte-exact after every wrong build.

⚠ DECLARED SETS ARE AT FUNCTION GRANULARITY (``file::Class::func``), not per-parameter
node id. What is predicted is WHICH PIN fires; a parametrised pin's rows multiply for
reasons (backend, caller, traffic world) orthogonal to the defect. The both-ways diff is
unaffected: an unexpected FUNCTION reddening is still a failure, and a declared function
that stayed FULLY green is still a failure.

⚠ SCOPE BOUND: only ``test_comms_footer.py`` is run. A wrong build that also reddens a pin
in another suite is invisible here; that is stated rather than implied.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = "loremaster/tests/test_comms_footer.py"
SERVER = "loremaster/loremaster/server.py"
MESSAGES = "loremaster/loremaster/messages.py"
PYPROJECT = "pyproject.toml"
BACKUP = ROOT / ".c3fix-pristine"
MUTABLE = (SERVER, MESSAGES, PYPROJECT)

Edit = tuple[str, str, str, int]  # (file, anchor, replacement, occurrences)

# --------------------------------------------------------------------------- #
# The wrong builds. Each is (id, prose, edits, declared-red functions).
# --------------------------------------------------------------------------- #

_AUTH_COUNTS = (
    "                unread=traffic.unread,\n"
    "                unacked=traffic.unacked_directives,\n"
)
_AUTH_COUNTS_SWAPPED = (
    "                unread=traffic.unacked_directives,\n"
    "                unacked=traffic.unread,\n"
)
_QUIET_GUARD = "        if traffic.unread == 0 and traffic.unacked_directives == 0:\n"
_SEAM_CALL = "traffic=await self.message_ledger.pending_traffic(agent_id=agent_id),"
_PRIVATE_COUNT = (
    "traffic=PendingTraffic("
    "unread=sum(1 for (m, a), e in self.message_ledger.db.edges.items() "
    "if a == agent_id and e.seen_at is None), "
    "unacked_directives=sum(1 for (m, a), e in self.message_ledger.db.edges.items() "
    "if a == agent_id and e.acked_at is None "
    'and self.message_ledger.db.messages[m].grade == "directive")),'
)
_APPEND = '        return "\\n".join([rendered, str(line)])'
_CANDIDATE = (
    "        candidate = next(\n"
    "            (\n"
    "                value\n"
    "                for value in attributions\n"
    "                if value is not None and AGENT_NAME_PATTERN.fullmatch(value)\n"
    "            ),\n"
    "            None,\n"
    "        )\n"
)
_UNGATED_SCAN_FOR_TWO = (
    "        if len(attributions) < 3:\n"
    "            for value in attributions:\n"
    "                if value is None:\n"
    "                    continue\n"
    "                probe = await AppContext._resolve_footer_identity(\n"
    "                    self, value, session=None\n"
    "                )\n"
    "                if probe is not None:\n"
    "                    pname, pid = probe\n"
    "                    return AppContext._comms_footer(\n"
    "                        identity=pname,\n"
    "                        traffic=await self.message_ledger.pending_traffic(agent_id=pid),\n"
    "                        authenticated=False,\n"
    "                    )\n"
    "            return None\n"
) + _CANDIDATE

C = "loremaster/tests/test_comms_footer.py"

WRONG_BUILDS: list[tuple[str, str, list[Edit], list[str]]] = [
    (
        "W2",
        "the two counts are SWAPPED in the authenticated render",
        [(SERVER, _AUTH_COUNTS, _AUTH_COUNTS_SWAPPED, 1)],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W12",
        "the counts are a CONSTANT 1 and 1 whenever anything pends",
        [
            (SERVER, "unread=traffic.unread,", "unread=1,", 2),
            (SERVER, "unacked=traffic.unacked_directives,", "unacked=1,", 2),
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W3",
        "the footer re-derives the counts in the SERVER; pending_traffic is never called",
        [(SERVER, _SEAM_CALL, _PRIVATE_COUNT, 2)],
        [
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "DEL",
        "MessageLedger.pending_traffic DELETED from production entirely",
        [
            (MESSAGES, "    async def pending_traffic(", "    async def _deleted_traffic(", 1),
            (SERVER, _SEAM_CALL, _PRIVATE_COUNT, 2),
        ],
        [
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_seam_counts_unread_and_unacked_DIRECTIVES_separately",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_a_SIGNAL_is_never_counted_as_an_unacked_directive",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_an_UNREAD_directive_is_ALSO_an_unacked_directive",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_PRODUCTION_ledger_exposes_pending_traffic",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_DOUBLE_conforms_to_the_production_seam",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "W23",
        "the footer fires on unread > 0 ALONE — 0 unread + 3 unacked directives gets nothing",
        [(SERVER, _QUIET_GUARD, "        if traffic.unread == 0:\n", 1)],
        [
            f"{C}::TestNoTrafficMeansNoFooter"
            "::test_POSITIVE_CONTROL_the_same_write_WITH_traffic_DOES_footer",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
        ],
    ),
    (
        "W4",
        "session= is IGNORED — agent= resolves unscoped",
        [
            (
                SERVER,
                "                    self, agent, session=session\n",
                "                    self, agent, session=None\n",
                1,
            )
        ],
        [
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W5",
        "findings' four single-item write verbs NEVER footer",
        [
            (
                SERVER,
                'return f"reported finding #{report.number} (id {report.id}, status open)", True',
                'return f"reported finding #{report.number} (id {report.id}, status open)", False',
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(acked, actor), True",
                "return AppContext._render_finding_transition(acked, actor), False",
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(resolved, actor), True",
                "return AppContext._render_finding_transition(resolved, actor), False",
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(closed, actor), True",
                "return AppContext._render_finding_transition(closed, actor), False",
                1,
            ),
        ],
        [
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB"
            "::test_EVERY_findings_WRITE_action_footers",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_spends_ONE_registry_read_AT_MOST",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND"
            "::test_exactly_ONE_footer_line_is_served",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_footer_is_the_LAST_line",
            f"{C}::TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL",
            f"{C}::TestTheFallbackIsThirdPersonWithNoDrainImperative"
            "::test_the_FALLBACK_footer_carries_no_second_person_imperative",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "W10",
        "tasks' transition and supersede NEVER footer",
        [
            (
                SERVER,
                "return AppContext._render_task_transition(task, actor), True",
                "return AppContext._render_task_transition(task, actor), False",
                1,
            ),
            (
                SERVER,
                'return f"superseded task {task_id}; successor {successor_id} (status open)", True',
                'return f"superseded task {task_id}; successor {successor_id} (status open)", False',
                1,
            ),
        ],
        [
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB::test_EVERY_tasks_WRITE_action_footers",
        ],
    ),
    (
        "W24",
        "acknowledge_many footers UNCONDITIONALLY, ignoring L2's write-count",
        [
            (
                SERVER,
                "            return batch_render, write_count >= _MIN_COUNT",
                "            return batch_render, (\n"
                "                True\n"
                "                if action == _FINDING_ACTION_ACKNOWLEDGE_MANY\n"
                "                else write_count >= _MIN_COUNT\n"
                "            )",
                1,
            )
        ],
        [
            f"{C}::TestABatchThatWroteNOTHINGServesNoFooter"
            "::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL",
        ],
    ),
    (
        "W6",
        "the footer REPLACES the dispatcher's render — the tool's answer is destroyed",
        [(SERVER, _APPEND, "        return str(line)", 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND"
            "::test_the_underlying_answer_SURVIVES_the_footer",
        ],
    ),
    (
        "W11",
        "the footer is appended TWICE",
        [(SERVER, _APPEND, '        return "\\n".join([rendered, str(line), str(line)])', 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_exactly_ONE_footer_line_is_served",
        ],
    ),
    (
        "W20",
        "the footer is PREPENDED, above the answer it annotates",
        [(SERVER, _APPEND, '        return "\\n".join([str(line), rendered])', 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_footer_is_the_LAST_line",
        ],
    ),
    (
        "W7",
        "unacked_directives CLAMPS at 5 — a cap used as a denominator",
        [
            (
                MESSAGES,
                "            unacked_directives=sum(\n",
                "            unacked_directives=min(5, sum(\n",
                1,
            ),
            (
                MESSAGES,
                '                and row.get("grade") == MESSAGE_GRADE_DIRECTIVE\n            ),',
                '                and row.get("grade") == MESSAGE_GRADE_DIRECTIVE\n            )),',
                1,
            ),
        ],
        [
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW",
        ],
    ),
    (
        "W8",
        "the footer only fires for identities CONTAINING A HYPHEN",
        [
            (
                SERVER,
                _QUIET_GUARD,
                '        if "-" not in identity:\n            return None\n' + _QUIET_GUARD,
                1,
            )
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND"
            "::test_exactly_ONE_footer_line_is_served",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_footer_is_the_LAST_line",
            f"{C}::TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL",
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB::test_EVERY_tasks_WRITE_action_footers",
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB"
            "::test_EVERY_findings_WRITE_action_footers",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "W9",
        "R8(1)'s teaching degenerates to the BARE offending value, no guidance",
        [
            (
                SERVER,
                '                    "(no pending-traffic line: agent={offending} is not '
                'registered — "\n                    "register it with lore_comms '
                'action=register, or fix the spelling)",\n',
                '                    "{offending}",\n',
                1,
            )
        ],
        [
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_the_teaching_names_a_REMEDY_not_just_the_offending_value",
        ],
    ),
    (
        "W17",
        "the teaching LEAKS onto READ paths (query/rollup)",
        [
            (
                SERVER,
                "        if not wrote:\n            return None\n",
                "        if not wrote:\n"
                "            if agent is None:\n"
                "                return None\n"
                "            try:\n"
                "                probe = await AppContext._resolve_footer_identity(\n"
                "                    self, agent, session=session\n"
                "                )\n"
                "            except _AmbiguousAgentError:\n"
                "                return None\n"
                "            if probe is None:\n"
                "                return render_line(\n"
                '                    "(no pending-traffic line: agent={offending} is not '
                'registered — "\n'
                '                    "register it with lore_comms action=register, or fix '
                'the spelling)",\n'
                "                    offending=sanitise_line(agent),\n"
                "                )\n"
                "            return None\n",
                1,
            )
        ],
        [
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_the_teaching_NEVER_appears_on_a_READ",
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_a_READ_carrying_a_RESOLVABLE_agent_spends_NO_registry_read",
        ],
    ),
    (
        "W13",
        "session= never lands on the tool schema (R1's '+session')",
        [
            (
                SERVER,
                "            Field(description=_COMMS_IDENTITY_SESSION_DESCRIPTION),",
                "            Field(),",
                3,
            )
        ],
        [
            f"{C}::TestTheAgentParameterDescriptionIsSHAREDAndStatesThePayoff"
            "::test_all_three_tools_ALSO_expose_session_with_ONE_shared_description",
            f"{C}::TestTheAgentParameterDescriptionIsSHAREDAndStatesThePayoff"
            "::test_the_session_description_says_WHEN_a_caller_needs_it",
        ],
    ),
    (
        "W15",
        "the one-read ceiling and the charset gate hold on tasks and are BROKEN on "
        "findings + claim_task (an ungated per-attribution SCAN)",
        [(SERVER, _CANDIDATE, _UNGATED_SCAN_FOR_TWO, 1)],
        [
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_spends_ONE_registry_read_AT_MOST",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_claim_task_spends_ONE_registry_read_AT_MOST",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_never_consults_a_SECOND_attribution",
        ],
    ),
    (
        "W16",
        "the resolver falls back to candidate.startswith(registered_name)",
        [
            (
                SERVER,
                "        if row.name != name:",
                "        if not name.startswith(row.name):",
                1,
            ),
            (
                SERVER,
                "            row = await self.agent_registry.get_agent(name, session=session)",
                "            try:\n"
                "                row = await self.agent_registry.get_agent(name, session=session)\n"
                "            except _UnknownAgentError:\n"
                "                rows = [\n"
                "                    r\n"
                "                    for r in self.agent_registry.db.agents.values()\n"
                "                    if name.startswith(r.name)\n"
                "                ]\n"
                "                if not rows:\n"
                "                    raise\n"
                "                row = rows[0]",
                1,
            ),
        ],
        [
            f"{C}::TestTheFallbackIsThirdPersonWithNoDrainImperative"
            "::test_the_fallback_refuses_a_charset_legal_SUPERSTRING_too",
        ],
    ),
    (
        "W18",
        "link 2's in-code guard `if row.name != name` is DELETED",
        [
            (
                SERVER,
                "        if row.name != name:",
                "        if False:",
                1,
            )
        ],
        [
            f"{C}::TestTheSERVERVerifiesTheRowTheRegistryHandedBack"
            "::test_a_row_whose_NAME_differs_from_the_request_NEVER_footers",
        ],
    ),
    (
        "W19",
        "an AMBIGUOUS agent= (registered in two sessions) is taught 'is not registered'",
        [
            (
                SERVER,
                "        except _AmbiguousAgentError:\n"
                "            # NOT \"unregistered\": the name IS registered, in more than one",
                "        except _AmbiguousAgentError:  # noqa: B025\n"
                "            return None\n"
                "        except _AmbiguousAgentError:\n"
                "            # NOT \"unregistered\": the name IS registered, in more than one",
                1,
            )
        ],
        [
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_an_AMBIGUOUS_agent_is_taught_the_TRUTH_never_that_it_is_UNREGISTERED",
        ],
    ),
    (
        "W21",
        "the RESOLVED caller's footer loses its drain imperative",
        [
            (
                SERVER,
                '                "directive(s); lore_comms action=drain agent={identity}",',
                '                "directive(s) somewhere in your fleet inbox",',
                1,
            )
        ],
        [
            f"{C}::TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL",
        ],
    ),
    (
        "W22",
        "only the FALLBACK render is a bare f-string (the authenticated one stays Rendered)",
        [
            (
                SERVER,
                '        return render_line(\n'
                '            "{prefix} {identity} has {unread} unread and {unacked} unacked '
                'directive(s) "\n'
                '            "(matched by name on this row, not an authenticated caller)",\n'
                "            prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "            identity=sanitise_line(identity),\n"
                "            unread=traffic.unread,\n"
                "            unacked=traffic.unacked_directives,\n"
                "        )",
                "        return (  # type: ignore[return-value]\n"
                '            f"{COMMS_FOOTER_PREFIX} {identity} has {traffic.unread} unread "\n'
                '            f"and {traffic.unacked_directives} unacked directive(s) "\n'
                '            f"(matched by name on this row, not an authenticated caller)"\n'
                "        )",
                1,
            )
        ],
        [
            f"{C}::TestTheFALLBACKFooterIsAlsoBuiltThroughTheRenderSeam"
            "::test_the_FALLBACK_footer_helper_returns_Rendered_not_a_bare_str",
        ],
    ),
    (
        "W14",
        "R1's closing sentence never lands — no footer paragraph in _INSTRUCTIONS",
        [
            (
                SERVER,
                '    "PENDING TRAFFIC: pass agent= (and session= when your name is not unique) to "',
                '    "PENDING TRAFFIC PLACEHOLDER "',
                1,
            )
        ],
        [
            f"{C}::TestTheFooterTeachingLandsThroughTheDeclaredAllowlist"
            "::test_the_footer_teaching_ACTUALLY_LANDS_in_the_served_INSTRUCTIONS",
        ],
    ),
    (
        "W1b",
        "ONE count placeholder AND its kwarg are dropped together — legal render, "
        "silently half a footer (the case the render seam's unused-kwarg guard CANNOT see)",
        [
            (
                SERVER,
                '                "{prefix} {identity} — you have {unread} unread and {unacked} '
                'unacked "\n                "directive(s); lore_comms action=drain '
                'agent={identity}",\n'
                "                prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "                identity=sanitise_line(identity),\n"
                "                unread=traffic.unread,\n"
                "                unacked=traffic.unacked_directives,\n",
                '                "{prefix} {identity} — you have {unread} unread; "\n'
                '                "lore_comms action=drain agent={identity}",\n'
                "                prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "                identity=sanitise_line(identity),\n"
                "                unread=traffic.unread,\n",
                1,
            )
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    # ------------------------------------------------------------------ #
    # The DELTA pass's wrong builds (REPORT-adversary-c3-delta-1.md §3).
    # ------------------------------------------------------------------ #
    (
        "DW1",
        "when either count is zero the OTHER stands in — a FALSE measurement in the "
        "one-sided traffic worlds",
        [
            (SERVER, "unread=traffic.unread,",
             "unread=traffic.unread or traffic.unacked_directives,", 2),
            (SERVER, "unacked=traffic.unacked_directives,",
             "unacked=traffic.unacked_directives or traffic.unread,", 2),
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
        ],
    ),
    (
        "DW2a",
        "a SECOND, PRIVATE footer render on lore_findings + lore_claim_task serving a "
        "CONSTANT 1/1; lore_tasks keeps the correct implementation",
        [
            (
                SERVER,
                '        return "\\n".join([rendered, str(line)])',
                "        if len(attributions) < 3:\n"
                '            return "\\n".join([rendered, re.sub(r"\\d+", "1", str(line))])\n'
                '        return "\\n".join([rendered, str(line)])',
                1,
            )
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
        ],
    ),
    (
        "DW2b",
        "lore_findings + lore_claim_task BYPASS the MessageLedger.pending_traffic seam "
        "and count privately (with the RIGHT numbers, so only the seam pin can see it)",
        [
            (
                SERVER,
                "traffic=await self.message_ledger.pending_traffic(agent_id=agent_id),",
                "traffic=(\n"
                "                    await self.message_ledger.pending_traffic(agent_id=agent_id)\n"
                "                    if len(attributions) >= 3\n"
                "                    else PendingTraffic(\n"
                "                        unread=sum(\n"
                "                            1\n"
                "                            for (m, a), e in self.message_ledger.db.edges.items()\n"
                "                            if a == agent_id and e.seen_at is None\n"
                "                        ),\n"
                "                        unacked_directives=sum(\n"
                "                            1\n"
                "                            for (m, a), e in self.message_ledger.db.edges.items()\n"
                "                            if a == agent_id\n"
                "                            and e.acked_at is None\n"
                '                            and self.message_ledger.db.messages[m].grade == "directive"\n'
                "                        ),\n"
                "                    )\n"
                "                ),",
                2,
            )
        ],
        [
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "DW3",
        "a READ resolves agent= (a wasted round trip) and serves the ambiguity lecture",
        [
            (
                SERVER,
                "        if not wrote:\n            return None\n",
                "        if not wrote:\n"
                "            if agent is not None:\n"
                "                try:\n"
                "                    await AppContext._resolve_footer_identity(\n"
                "                        self, agent, session=session\n"
                "                    )\n"
                "                except _AmbiguousAgentError as ambiguous:\n"
                "                    return render_line(\n"
                '                        "(no pending-traffic line: {reason})",\n'
                "                        reason=sanitise_line(str(ambiguous)),\n"
                "                    )\n"
                "            return None\n",
                1,
            )
        ],
        [
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_a_READ_carrying_a_RESOLVABLE_agent_spends_NO_registry_read",
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_a_READ_carrying_an_AMBIGUOUS_agent_teaches_NOTHING",
        ],
    ),
    (
        "DELTA3a",
        "LINK 1b REMOVED — the three ledger dispatchers do not charset-gate agent=/"
        "session= (the reference build as first measured: the forged instruction reaches "
        "the consumer verbatim through R8(1)'s teaching)",
        [(SERVER, "        AppContext._validate_comms_identities(agent, session=session, name=None, to=None)\n", "", 3)],
        [
            f"{C}::TestTheIdentityParameterSurfaceIsDERIVEDNotEnumerated"
            "::test_every_identity_accepting_ENTRY_POINT_routes_through_the_ONE_seam",
            f"{C}::TestAHostileIdentityIsREFUSEDAtEveryLink0Member"
            "::test_a_charset_illegal_identity_is_REFUSED_before_any_use",
            f"{C}::TestAHostileIdentityIsREFUSEDAtEveryLink0Member"
            "::test_the_refusal_renders_NO_RAW_VALUE_on_a_BARE_LINE",
            f"{C}::TestAHostileIdentityIsREFUSEDAtEveryLink0Member"
            "::test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal",
        ],
    ),
    (
        "DELTA3b",
        "LINK 4's NAMED WRONG BUILD — the refusal 'escapes' the value with repr() instead "
        "of fencing it, so the forged instruction survives same-line and fully readable",
        [
            (
                SERVER,
                '                f"{label} does not match {AGENT_NAME_PATTERN.pattern} — "',
                '                f"{label} {value!r} does not match '
                '{AGENT_NAME_PATTERN.pattern} — "',
                1,
            ),
            (
                SERVER,
                '                f"renders identically to another agent\'s\\n"\n'
                '                f"the {label} received was:\\n{render_fenced(value)}"',
                '                f"renders identically to another agent\'s"',
                1,
            ),
        ],
        [
            f"{C}::TestAHostileIdentityIsREFUSEDAtEveryLink0Member"
            "::test_the_refusal_renders_NO_RAW_VALUE_on_a_BARE_LINE",
        ],
    ),
    (
        "DELTA3c",
        "ROUTING IS NOT SHARING — lore_tasks hand-rolls its OWN charset predicate behind a "
        "byte-identical message; it refuses the same values today and drifts tomorrow",
        [
            (
                SERVER,
                '        AppContext._validate_comms_identities(agent, session=session, name=None, to=None)\n        rendered, wrote = await AppContext._tasks_dispatch(self, ',
                '        _private = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n        for _value, _label in ((agent, "agent name"), (session, "session")):\n            if _value is not None and not _private.fullmatch(_value):\n                raise ValueError(\n                    f"{_label} does not match {_private.pattern} — "\n                    f"an identity is a match key across the registry, the "\n                    f"ledgers and every render, so it gets exactly ONE spelling "\n                    f"and must stay in the safe charset: this is what stops a "\n                    f"value having a second form that renders identically to "\n                    f"another agent\'s\\n"\n                    f"the {_label} received was:\\n{render_fenced(_value)}"\n                )\n        rendered, wrote = await AppContext._tasks_dispatch(self, ',
                1,
            )
        ],
        [
            f"{C}::TestTheIdentityParameterSurfaceIsDERIVEDNotEnumerated"
            "::test_every_identity_accepting_ENTRY_POINT_routes_through_the_ONE_seam",
            f"{C}::TestAHostileIdentityIsREFUSEDAtEveryLink0Member"
            "::test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal",
        ],
    ),
]


def _backup() -> None:
    BACKUP.mkdir(exist_ok=True)
    for relative in MUTABLE:
        shutil.copy2(ROOT / relative, BACKUP / Path(relative).name)


def _restore() -> None:
    for relative in MUTABLE:
        shutil.copy2(BACKUP / Path(relative).name, ROOT / relative)
    for relative in MUTABLE:
        if (ROOT / relative).read_bytes() != (BACKUP / Path(relative).name).read_bytes():
            raise SystemExit(f"RESTORE FAILED for {relative}")


def _collect() -> set[str]:
    proc = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-p", "no:randomly", CONTRACT],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ids = set()
    for line in proc.stdout.splitlines():
        if "::" in line and line.startswith(CONTRACT):
            ids.add(re.sub(r"\[[^\]]*\]$", "", line.strip()))
    if not ids:
        raise SystemExit(f"collect-only returned nothing:\n{proc.stdout}\n{proc.stderr}")
    return ids


def _apply(edits: list[Edit]) -> None:
    for relative, anchor, replacement, occurrences in edits:
        path = ROOT / relative
        text = path.read_text()
        found = text.count(anchor)
        if found != occurrences:
            _restore()
            raise SystemExit(
                f"ANCHOR MISMATCH in {relative}: expected {occurrences} occurrence(s), "
                f"found {found}. Anchor:\n{anchor!r}"
            )
        path.write_text(text.replace(anchor, replacement))


def _run() -> set[str]:
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q", "-p", "no:randomly", "-n", "8", CONTRACT],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    reds = set()
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            node = line.split(" ", 1)[1].split(" - ")[0].strip()
            reds.add(re.sub(r"\[[^\]]*\]$", "", node))
    tail = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line]
    print(f"      tail: {tail[-1].strip() if tail else '(no count line!)'}")
    return reds


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    collected = _collect()
    print(f"collected {len(collected)} distinct test functions in {CONTRACT}")

    bad = []
    for wid, _prose, _edits, declared in WRONG_BUILDS:
        for node in declared:
            if node not in collected:
                bad.append(f"{wid}: declared node does not exist -> {node}")
    if bad:
        print("\n".join(bad))
        return 2

    _backup()
    failures: list[str] = []
    for wid, prose, edits, declared in WRONG_BUILDS:
        if wanted and wid not in wanted:
            continue
        print(f"\n=== {wid}: {prose}")
        _apply(edits)
        print("      LANDED (every anchor matched its declared count)")
        observed = _run()
        _restore()
        unexpected = sorted(observed - set(declared))
        stayed_green = sorted(set(declared) - observed)
        verdict = "CAUGHT" if declared and not unexpected and not stayed_green else "MISMATCH"
        if unexpected:
            print("      UNEXPECTED RED:\n        " + "\n        ".join(unexpected))
        if stayed_green:
            print("      DECLARED RED BUT STAYED GREEN:\n        " + "\n        ".join(stayed_green))
        print(f"      -> {verdict} ({len(observed)} function(s) red)")
        if verdict != "CAUGHT":
            failures.append(wid)
    print("\n" + ("ALL WRONG BUILDS CAUGHT" if not failures else f"MISMATCHES: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

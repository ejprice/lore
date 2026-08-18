# REPORT-harness-runner

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done
- Deviations: none
- Packages considered: none — no mechanism specified (read-only test-runner; no code written)
- Reuse ledger: none — no new symbols introduced (read-only)
- Graded: N/A — this is a red/green CENSUS of the suite as of the run below, not a verdict on any artifact. Run at working-tree HEAD; `git rev-parse HEAD` = `5c8230c` (branch `feat/surreal-unification`), tree clean at spawn.
- Decisions needed: none — root-cause / packet attribution is the lead's job, per brief.
- **MAIN suite:** `451 failed / 9878 passed / 51 skipped / 3 xfailed / 135 errors` — exit 1 (244.36s, `-n auto`). Real counts in tail (not a silent "no tests ran").
- **SKILL suite:** `117 passed / 0 failed / 0 errors` — exit 0 (CLEAN).
- **586 red items** collapse into **3 root-cause clusters + a handful of singletons** (see §Clusters). Full nodeid census in §Complete enumeration (all 586, grouped by file, none truncated).
- Pointers: cluster analysis §Clusters · complete list §Complete enumeration · receipts/tails §Receipts · logs `scratchpad/harness-full.log`, `scratchpad/skill-suite.log`.

## Clusters (shared signatures — clusters usually mean one root cause)

The 586 red items are dominated by **three signatures**. I report the WHAT (essence) only; I do not attribute to packets.

### Cluster 1 — SDK multi-statement guard tripping at teardown (ALL 135 ERRORS)
- **Signature:** `AssertionError: N bare .query() call(s) carried MORE THAN ONE statement during this test:` → `store/_txn.py:1207 in _attempt() -> connection.query()`
- **Where it fires:** the autouse guard fixture `loremaster/tests/conftest.py:212 _no_sdk_call_escapes_the_retry_driver` (the #124/#144 runtime posture) asserts at **teardown** that no bare `.query()` carried >1 statement. It is tripping on `store/_txn.py:1207 in _attempt()`.
- **Affected nodeids (135 errors):** `loremaster/tests/test_message_ledger.py` (**130** — nearly the whole file errors at teardown) and `loremaster/tests/test_comms_footer.py` (**5**).
- This is a distinct root cause from Clusters 2/3 (a store/`_txn` execution-path issue, not a missing symbol or a config-schema gap).

### Cluster 2 — ImportError: symbols the tests expect do not exist in the target modules (bulk of FAILED)
- **Signature:** `ImportError: cannot import name '<X>' from '<module>'`
- **Missing symbols, by module (count = # of failing tests referencing it):**
  - `loremaster.auth`: `LoreTokenVerifier` (110), `derive_edge_policy` (12), `auth_context_from_access_token` (4), `PassThroughPermissionResolver` (3), `_new_http_client` (1)
  - `loremaster.config`: `PostureConfigError` (25), `GoogleOAuthConfig` (15), `resolve_posture` (14)
  - `loremaster.server`: `PermissionFilteredToolError` (5), `HOSTED_REFUSAL_SECTION_HEADING` (3), `HOSTED_READ_LADDER_MARKER` (3), `HostedToolRefusedError` (2), `_EXTENSION_TOOL_ANNOTATIONS` (1)
  - `lorerunes` (package `__init__`): `PostureRefusal` (59), `normalize_email` (21), `parse_roster` (16), `Posture` (14), `RosterParseError` (13), `is_admitted` (8), `SCOPE_READ` (7), `derive_posture` (1)

### Cluster 3 — pydantic `extra_forbidden`: `LoreConfig` rejects new auth config keys (~96 FAILED)
- **Signature:** `pydantic_core...ValidationError: N validation errors for LoreConfig` → `Extra inputs are not permitted [type=extra_forbidden, input_value=...]` for keys `auth` / `auth.mode` / `auth.google` / `google_oauth` / `api_key`
- **Where:** `LoreConfig` remains `extra="forbid"` and has no field for the new `auth` / `google_oauth` config surface, so configs carrying those keys fail validation.
- **Files most affected:** `test_hosted_readonly_posture.py` (41), `test_auth_composition.py` (35), `test_auth_identity_seam.py` (18), plus scattered singles in `test_auth.py`, `test_permission_resolver_seam.py`.

### Singletons / small (not part of the 3 big clusters)
- `loremaster/tests/test_auth_composition.py`: `TypeError: build_mcp_server() got an unexpected keyword argument 'http_client'` (1); `AttributeError: 'FastMCP' object has no attribute 'settings'` (1).
- `loremaster/tests/test_auth_identity_seam.py`: `AttributeError: 'FastMCP' object has no attribute 'settings'` (1).
- `loremaster/tests/test_hosted_readonly_posture.py`: `AttributeError: 'FastMCP' object has no attribute '_tool_manager'` (1).
- `loremaster/tests/test_google_token_verifier.py`: `AttributeError: <module 'loremaster.auth'> has no attribute ...` (1).
- `loremaster/tests/test_secret_typing.py` (2 FAILED): typed-seam AST scans — (a) `assert not ['scripts/fastmcp_migration_spike.py:360 auth= not sourced from build_auth_headers()', ...]`; (b) SecretStr-mint-site scan flags `scripts/probe_query_complexity_07.py:54`, `scripts/probe_store_error_classes_07.py:38`, ...
- `loremaster/tests/test_comms_footer.py` (1 FAILED): `assert not [('loremaster/loremaster/store/surreal.py', 'entity_table', 1254)]`.
- `loremaster/tests/test_ast_reach_helpers.py` (1 FAILED): assertion diff (`Use -v to get more diff`).
- `loremaster/tests/test_surreal_harness.py` (1 FAILED): `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` — docstring count vs derived count mismatch (`... and 56 = len([... 56 test files ...])`).

> Note: `FastMCP`-attribute and `build_mcp_server(http_client=...)`/`fastmcp_migration_spike.py` signatures suggest a second in-flight surface (a FastMCP migration) distinct from the auth/posture/roster feature that produces Clusters 2/3 — flagged as an observation, not a diagnosis.

## Complete enumeration (all 586 red nodeids, grouped by file — none truncated)
### FAILED — 451 tests, 14 files


#### loremaster/tests/test_auth_composition.py  (82 failed)
- `loremaster/tests/test_auth_composition.py::TestDiscoveryDocumentIsAnonymousInHostedPosture::test_the_well_known_document_is_absent_in_lan_bearer_posture`
- `loremaster/tests/test_auth_composition.py::TestDiscoveryDocumentIsAnonymousInHostedPosture::test_the_well_known_document_is_absent_in_loopback_posture`
- `loremaster/tests/test_auth_composition.py::TestDiscoveryDocumentIsAnonymousInHostedPosture::test_the_well_known_document_is_served_with_a_claude_ai_origin`
- `loremaster/tests/test_auth_composition.py::TestDiscoveryDocumentIsAnonymousInHostedPosture::test_the_well_known_document_is_served_without_any_credential`
- `loremaster/tests/test_auth_composition.py::TestDiscoveryDocumentIsAnonymousInHostedPosture::test_the_well_known_document_names_the_resource_and_the_issuer`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_a_lan_bearer_deployment_on_a_real_lan_address_is_not_421ed`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_dns_rebinding_protection_is_enabled_in_every_non_loopback_posture`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_composed_server_uses_the_derived_transport_security_settings`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_configured_bind_host_is_allowed_whatever_it_is[0.0.0.0]`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_configured_bind_host_is_allowed_whatever_it_is[10.0.0.7]`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_configured_bind_host_is_allowed_whatever_it_is[192.168.64.100]`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_edge_policy_is_hashable_and_frozen`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_hosted_auth_settings_require_the_read_scope`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_hosted_edge_policy_allows_the_public_hostname`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_hosted_edge_policy_carries_the_claude_origins`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_hosted_edge_policy_still_allows_the_loopback_bind`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_lan_bearer_auth_settings_require_the_read_scope_too`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_lan_bearer_edge_policy_does_not_carry_the_claude_origins`
- `loremaster/tests/test_auth_composition.py::TestEdgePolicyIsOneDerivationFeedingBothLayers::test_the_loopback_posture_does_not_allow_the_claude_origins`
- `loremaster/tests/test_auth_composition.py::TestLoopbackPostureIsUnchanged::test_no_auth_settings_are_configured`
- `loremaster/tests/test_auth_composition.py::TestNoInstanceAttributeShadowsABoundHandler::test_no_derived_handler_name_is_shadowed_on_the_composed_server`
- `loremaster/tests/test_auth_composition.py::TestNoInstanceAttributeShadowsABoundHandler::test_no_shadowing_in_any_posture[hosted]`
- `loremaster/tests/test_auth_composition.py::TestNoInstanceAttributeShadowsABoundHandler::test_no_shadowing_in_any_posture[lan_bearer]`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_a_hostile_origin_is_403_with_ZERO_outbound_google_calls`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_an_absent_origin_is_allowed_in_hosted_posture`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_the_composed_app_is_not_wrapped_in_the_retired_bearer_middleware`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_the_discovery_route_is_also_origin_guarded`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_the_hosted_default_origins_are_NOT_allowed_in_lan_bearer_posture`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_the_hosted_default_origins_are_allowed[https://claude.ai]`
- `loremaster/tests/test_auth_composition.py::TestOriginIsOutermost::test_the_hosted_default_origins_are_allowed[https://claude.com]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot[]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot[example.com]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot[lore-internal]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot[lore.firehawktransam.org]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot[not a host]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_healthy_hosted_config_still_builds`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot[0.0.0.0]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot[192.168.64.100]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot[::]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_loopback_spelling_in_a_DIFFERENT_CASE_still_resolves[LOCALHOST]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_a_loopback_spelling_in_a_DIFFERENT_CASE_still_resolves[LocalHost]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_asgi_app_refuses_it_too`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind[0.0.0.0]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind[192.168.64.100]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind[::]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_mcp_server_refuses_a_hosted_config_whose_roster_will_not_load`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_every_loopback_SPELLING_still_resolves_to_hosted_oauth[127.0.0.1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_every_loopback_SPELLING_still_resolves_to_hosted_oauth[::1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_every_loopback_SPELLING_still_resolves_to_hosted_oauth[localhost]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_container_entry_point_propagates_the_refusal`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[127.0.0.1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[127.0.0.2]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[127.0.1.1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[127.255.255.254]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[::1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_holds_across_the_whole_127_8_grid[localhost]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8[0.0.0.0]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8[10.0.0.1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8[126.255.255.255]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8[128.0.0.1]`
- `loremaster/tests/test_auth_composition.py::TestTheBootRefusalReachesTheThingThatActuallyBoots::test_the_loopback_PREDICATE_rejects_addresses_just_outside_127_8[192.168.64.100]`
- `loremaster/tests/test_auth_composition.py::TestTheUnscopedAccessorIsTheSanctionedFullRegistryView::test_the_accessor_is_UNAFFECTED_by_an_ambient_hosted_principal`
- `loremaster/tests/test_auth_composition.py::TestTheUnscopedAccessorIsTheSanctionedFullRegistryView::test_the_accessor_returns_the_full_registry_with_no_principal`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_a_non_ascii_token_is_a_clean_401_not_a_500`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_a_non_bearer_scheme_is_401_without_an_outbound_call`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_an_unauthenticated_mcp_request_is_401[hosted]`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_an_unauthenticated_mcp_request_is_401[lan_bearer]`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_an_unknown_bearer_token_is_401_and_never_reaches_a_session`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_401_advertises_the_bearer_scheme`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_401_carries_a_resource_metadata_url_that_resolves`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_bearer_scheme_is_matched_case_insensitively[BEARER]`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_bearer_scheme_is_matched_case_insensitively[BeArEr]`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_bearer_scheme_is_matched_case_insensitively[Bearer]`
- `loremaster/tests/test_auth_composition.py::TestUnauthenticatedRequestsAreChallenged::test_the_bearer_scheme_is_matched_case_insensitively[bearer]`
- `loremaster/tests/test_auth_composition.py::TestUngovernedMcpRoutesAreUnreachable::test_no_prompts_are_registered`
- `loremaster/tests/test_auth_composition.py::TestUngovernedMcpRoutesAreUnreachable::test_no_resources_are_registered`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_an_unknown_path_is_404_for_an_anonymous_caller[/.well-known/openid-configuration]`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_an_unknown_path_is_404_for_an_anonymous_caller[/]`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_an_unknown_path_is_404_for_an_anonymous_caller[/admin]`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_an_unknown_path_is_404_for_an_anonymous_caller[/mcp/internal]`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_an_unknown_path_is_404_for_an_anonymous_caller[/metrics]`
- `loremaster/tests/test_auth_composition.py::TestUnknownPathsAre404NotChallenged::test_the_protected_route_is_still_challenged`

#### loremaster/tests/test_google_token_verifier.py  (75 failed)
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_a_valid_api_key_is_admitted_without_any_outbound_call`
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_an_unknown_key_falls_through_to_the_google_branch`
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_each_api_key_mints_its_own_distinct_principal`
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_the_api_key_branch_routes_through_ApiKeyVerifier`
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_the_api_key_client_id_can_never_collide_with_the_google_one`
- `loremaster/tests/test_google_token_verifier.py::TestApiKeyBranch::test_the_api_key_principal_carries_write_scope`
- `loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_a_missing_aud_is_a_hard_reject_not_a_skipped_check`
- `loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_a_token_minted_by_a_different_oauth_client_is_denied`
- `loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_an_aud_that_is_a_prefix_of_ours_is_denied`
- `loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_an_empty_string_aud_is_denied`
- `loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_the_aud_mismatch_log_line_renders_the_configured_client_id`
- `loremaster/tests/test_google_token_verifier.py::TestConcurrencyAndLifecycle::test_a_closed_injected_client_does_not_wedge_the_verifier`
- `loremaster/tests/test_google_token_verifier.py::TestConcurrencyAndLifecycle::test_the_http_client_seam_sets_explicit_timeouts`
- `loremaster/tests/test_google_token_verifier.py::TestConcurrencyAndLifecycle::test_two_concurrent_verifications_overlap_their_outbound_calls`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[absent]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[bool-false]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[empty]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[null]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[str-False]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[str-false]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_falsy_and_absent_shapes_are_denied[zero]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_truthy_shapes_are_admitted[bool-true]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_truthy_shapes_are_admitted[str-True]`
- `loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_truthy_shapes_are_admitted[str-true]`
- `loremaster/tests/test_google_token_verifier.py::TestGoogleBranchAdmitsAListedPrincipal::test_a_capitalised_google_email_matches_a_lowercase_roster_line`
- `loremaster/tests/test_google_token_verifier.py::TestGoogleBranchAdmitsAListedPrincipal::test_a_listed_verified_principal_is_admitted`
- `loremaster/tests/test_google_token_verifier.py::TestGoogleBranchAdmitsAListedPrincipal::test_an_unlisted_but_fully_verified_principal_is_denied`
- `loremaster/tests/test_google_token_verifier.py::TestGoogleBranchAdmitsAListedPrincipal::test_the_second_listed_principal_is_also_admitted`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_carrying_the_email_scope_is_admitted[bare-alias-form]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_carrying_the_email_scope_is_admitted[full-uri-form]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_without_the_email_scope_is_denied[absent]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_without_the_email_scope_is_denied[empty]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_without_the_email_scope_is_denied[openid-only]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_grant_without_the_email_scope_is_denied[profile-only]`
- `loremaster/tests/test_google_token_verifier.py::TestGrantedScopeCheckIsAgainstGoogleNotOurselves::test_a_scope_merely_containing_the_word_email_is_not_enough`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_an_already_expired_token_is_denied`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_the_expiry_is_absolute_and_tracks_the_token_lifetime`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_the_google_subject_comes_from_the_sub_claim`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_the_issuer_claim_is_the_hardcoded_google_issuer`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_the_subject_falls_back_to_the_normalised_email_when_sub_is_absent`
- `loremaster/tests/test_google_token_verifier.py::TestIdentityMinting::test_two_google_principals_mint_distinct_subjects`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_blank_presented_token_is_denied_without_any_outbound_call[empty]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_blank_presented_token_is_denied_without_any_outbound_call[newline]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_blank_presented_token_is_denied_without_any_outbound_call[spaces]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_colon_bearing_token_is_not_a_third_auth_path`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_json_array_body_is_a_clean_denial`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_missing_or_blank_email_is_denied[absent]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_missing_or_blank_email_is_denied[blank]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_missing_or_blank_email_is_denied[empty]`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_a_non_ascii_token_is_denied_without_raising`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_an_empty_json_object_is_a_clean_denial`
- `loremaster/tests/test_google_token_verifier.py::TestMalformedAndDegenerateResponses::test_malformed_json_on_a_200_is_a_clean_denial`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_definitive_rejection_is_negative_cached[bad-request]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_definitive_rejection_is_negative_cached[unauthorized]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_definitively_rejected_token_stays_rejected_after_a_good_response`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_token_recovers_after_the_outage_ends`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transient_upstream_failure_is_NOT_cached[bad-gw]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transient_upstream_failure_is_NOT_cached[gw-timeout]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transient_upstream_failure_is_NOT_cached[ise]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transient_upstream_failure_is_NOT_cached[unavailable]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transport_fault_is_NOT_cached[connect-error]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transport_fault_is_NOT_cached[connect-timeout]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transport_fault_is_NOT_cached[protocol-error]`
- `loremaster/tests/test_google_token_verifier.py::TestNegativeCacheSplitsDefinitiveFromTransient::test_a_transport_fault_is_NOT_cached[read-timeout]`
- `loremaster/tests/test_google_token_verifier.py::TestTokenCacheIsLiveIsolatedAndUnpoisonable::test_a_repeat_verification_makes_no_second_outbound_call`
- `loremaster/tests/test_google_token_verifier.py::TestTokenCacheIsLiveIsolatedAndUnpoisonable::test_a_token_that_is_a_prefix_of_a_cached_token_is_not_admitted`
- `loremaster/tests/test_google_token_verifier.py::TestTokenCacheIsLiveIsolatedAndUnpoisonable::test_an_expired_token_is_not_served_from_the_positive_cache`
- `loremaster/tests/test_google_token_verifier.py::TestTokenCacheIsLiveIsolatedAndUnpoisonable::test_caches_are_per_instance_not_module_global`
- `loremaster/tests/test_google_token_verifier.py::TestTokenCacheIsLiveIsolatedAndUnpoisonable::test_two_different_tokens_do_not_share_a_cache_entry`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_no_raw_token_is_retained_in_the_verifier_state`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_the_raw_api_key_never_appears_in_a_log_record_on_success`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_the_raw_token_never_appears_in_a_log_record`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_the_raw_token_never_appears_in_a_log_record_ON_SUCCESS`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_the_raw_token_never_appears_in_the_verifier_repr`
- `loremaster/tests/test_google_token_verifier.py::TestTokenSecrecy::test_the_token_is_posted_in_the_body_and_never_in_the_url`

#### lorerunes/tests/test_posture.py  (70 failed)
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_at_least_one_combination_reaches_each_posture`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-api_key-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-api_key-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-api_key-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-api_key-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google-oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google-oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google-oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google-oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google_oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google_oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google_oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-False-google_oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-api_key-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-api_key-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-api_key-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-api_key-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google-oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google-oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google-oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google-oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google_oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google_oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google_oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[False-True-google_oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-api_key-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-api_key-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-api_key-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-api_key-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google-oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google-oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google-oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google-oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google_oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google_oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google_oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-False-google_oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-api_key-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-api_key-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-api_key-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-api_key-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google-oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google-oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google-oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google-oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google_oauth-False-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google_oauth-False-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google_oauth-True-False]`
- `lorerunes/tests/test_posture.py::TestDerivePostureAcceptsExactlyTheThreeRuledShapes::test_every_input_combination_matches_the_spec_table[True-True-google_oauth-True-True]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_a_google_block_in_api_key_mode_refuses`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_an_unknown_mode_string_refuses_rather_than_crashing`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_degenerate_mode_strings_refuse[   ]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_degenerate_mode_strings_refuse[API_KEY]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_degenerate_mode_strings_refuse[None]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_degenerate_mode_strings_refuse[]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_degenerate_mode_strings_refuse[google_oauth ]`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_enabled_with_neither_keys_nor_google_refuses`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_hosted_oauth_does_not_require_api_keys`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_hosted_oauth_requires_a_loopback_bind`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_todays_default_config_with_no_auth_block_is_loopback`
- `lorerunes/tests/test_posture.py::TestDerivePostureNamedShapes::test_todays_enabled_api_key_config_is_lan_bearer`
- `lorerunes/tests/test_posture.py::TestPostureEnumIsAClosedSet::test_each_posture_has_a_distinct_name`
- `lorerunes/tests/test_posture.py::TestPostureEnumIsAClosedSet::test_exactly_three_postures_exist`
- `lorerunes/tests/test_posture.py::TestPostureRefusalIsDiagnosable::test_a_refusal_is_not_a_posture`
- `lorerunes/tests/test_posture.py::TestPostureRefusalIsDiagnosable::test_every_reported_problem_names_a_real_input_field`
- `lorerunes/tests/test_posture.py::TestPostureRefusalIsDiagnosable::test_the_refusal_for_a_non_loopback_hosted_config_names_the_host_field`
- `lorerunes/tests/test_posture.py::TestPostureRefusalIsDiagnosable::test_the_refusal_lists_at_least_one_concrete_problem`
- `lorerunes/tests/test_posture.py::TestPostureRefusalIsDiagnosable::test_the_refusal_names_its_nearest_posture_in_the_message`
- `lorerunes/tests/test_posture.py::TestScopeConstants::test_the_scope_values_are_the_ruled_strings`
- `lorerunes/tests/test_posture.py::TestScopeConstants::test_the_two_scopes_are_distinct`

#### loremaster/tests/test_hosted_readonly_posture.py  (57 failed)
- `loremaster/tests/test_hosted_readonly_posture.py::TestARefusedToolNeverRUNS::test_a_no_argument_mutating_tool_is_refused_without_running`
- `loremaster/tests/test_hosted_readonly_posture.py::TestARefusedToolNeverRUNS::test_no_refused_tool_body_is_ever_entered_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestARefusedToolNeverRUNS::test_the_recorder_CAN_see_a_body_execute`
- `loremaster/tests/test_hosted_readonly_posture.py::TestEveryRegisteredToolIsClassified::test_every_registered_tool_carries_an_explicit_read_only_hint[core-only]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestEveryRegisteredToolIsClassified::test_every_registered_tool_carries_an_explicit_read_only_hint[with-extension]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestEveryRegisteredToolIsClassified::test_the_derived_mutating_set_equals_the_named_behaviour_fixtures`
- `loremaster/tests/test_hosted_readonly_posture.py::TestEveryRegisteredToolIsClassified::test_the_derived_readable_set_equals_the_named_read_tools`
- `loremaster/tests/test_hosted_readonly_posture.py::TestEveryRegisteredToolIsClassified::test_the_registered_surface_is_the_same_in_every_posture`
- `loremaster/tests/test_hosted_readonly_posture.py::TestExtensionToolsAreRefusedWholesale::test_an_extension_tool_carries_the_exact_worst_case_annotations`
- `loremaster/tests/test_hosted_readonly_posture.py::TestExtensionToolsAreRefusedWholesale::test_an_extension_tool_is_refused_for_a_hosted_principal_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestExtensionToolsAreRefusedWholesale::test_an_extension_tool_remains_callable_via_an_api_key_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_claim_task]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_comms]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_findings]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_index]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_remember]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire[lore_tasks]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_dead_code]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_diff]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_get_symbol]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_impact]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_map]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_read]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_recall]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_search]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire[lore_verify]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_newly_registered_READ_ONLY_tool_is_permitted_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_a_write_scope_is_what_permits_not_the_client_id_SHAPE`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_claim_task]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_comms]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_findings]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_index]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_remember]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire[lore_tasks]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_an_unannotated_tool_is_born_refused_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_claim_task]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_comms]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_findings]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_index]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_remember]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestHostedPrincipalsAreRefusedEveryMutatingTool::test_no_token_at_all_is_not_refused[lore_tasks]`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_hosted_instructions_carry_the_refused_set_section`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_instructions_still_name_every_registered_tool`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_read_ladder_clause_names_EXACTLY_the_readable_set`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_refused_clause_names_EXACTLY_the_refused_set`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_refused_set_section_is_DERIVED_from_the_annotations`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_section_is_absent_in_lan_bearer_posture`
- `loremaster/tests/test_hosted_readonly_posture.py::TestInstructionsAreHonestAboutThePosture::test_the_section_is_absent_in_loopback_posture`
- `loremaster/tests/test_hosted_readonly_posture.py::TestServedAndRefusedArePartitioned::test_every_served_tool_is_callable_and_every_refused_tool_is_unlisted`
- `loremaster/tests/test_hosted_readonly_posture.py::TestServedAndRefusedArePartitioned::test_the_partition_covers_the_whole_registry`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheRefusalTeaches::test_the_refusal_does_not_leak_the_credential`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheRefusalTeaches::test_the_refusal_is_a_structured_tool_error`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheRefusalTeaches::test_the_refusal_names_the_posture_and_the_tool`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheRefusalTeaches::test_the_refusal_points_at_the_read_surface_that_remains`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheScopedLookupIsTheEnforcementSeam::test_a_hosted_principal_is_not_offered_refused_tools_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheScopedLookupIsTheEnforcementSeam::test_an_api_key_principal_is_offered_the_full_surface_on_the_wire`
- `loremaster/tests/test_hosted_readonly_posture.py::TestTheScopedLookupIsTheEnforcementSeam::test_the_composed_server_installs_a_SCOPED_tool_manager`

#### loremaster/tests/test_allowlist_roster.py  (46 failed)
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_a_hosted_config_with_a_healthy_roster_resolves_to_hosted_oauth`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_a_lan_bearer_config_needs_no_roster`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_a_loopback_config_with_no_auth_block_needs_no_roster`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry[comments-only]`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry[empty]`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry[missing]`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry[parse-refused]`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry[whitespace-only]`
- `loremaster/tests/test_allowlist_roster.py::TestBootRefusesAnUnloadableRoster::test_the_boot_refusal_carries_no_credential_material`
- `loremaster/tests/test_allowlist_roster.py::TestRevocationIsEffectiveOnTheVeryNextVerification::test_a_re_added_principal_is_re_admitted_from_cache_immediately`
- `loremaster/tests/test_allowlist_roster.py::TestRevocationIsEffectiveOnTheVeryNextVerification::test_a_revoked_principal_with_a_cached_token_is_denied_immediately`
- `loremaster/tests/test_allowlist_roster.py::TestRevocationIsEffectiveOnTheVeryNextVerification::test_a_roster_that_goes_empty_denies_a_cached_principal_immediately`
- `loremaster/tests/test_allowlist_roster.py::TestRevocationIsEffectiveOnTheVeryNextVerification::test_the_token_cache_is_not_flushed_by_a_roster_edit`
- `loremaster/tests/test_allowlist_roster.py::TestRosterChangeDetectionSurvivesASameLengthEdit::test_swapping_one_address_for_another_of_equal_length_revokes`
- `loremaster/tests/test_allowlist_roster.py::TestRosterChangeDetectionSurvivesASameLengthEdit::test_the_replacement_principal_is_admitted`
- `loremaster/tests/test_allowlist_roster.py::TestRosterErrorRendersHostileTextUnambiguously::test_a_forged_roster_line_cannot_be_read_as_a_log_event`
- `loremaster/tests/test_allowlist_roster.py::TestRosterErrorRendersHostileTextUnambiguously::test_the_error_does_not_dump_the_whole_roster`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_broken_roster_is_reported_at_ERROR_naming_the_path[empty]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_broken_roster_is_reported_at_ERROR_naming_the_path[missing]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_broken_roster_is_reported_at_ERROR_naming_the_path[parse-refused]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_healthy_roster_logs_no_ERROR`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[comments-only]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[directory]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[empty]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[missing]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[parse-refused]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_never_seen_principal_is_denied_when_the_roster_is_broken[whitespace-only]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_a_parse_refusal_denies_the_VALID_lines_on_the_same_file`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_an_unreadable_roster_denies_everyone`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[comments-only]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[directory]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[empty]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[missing]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[parse-refused]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken[whitespace-only]`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFreshnessOnEveryVerification::test_a_changed_roster_IS_re_read`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFreshnessOnEveryVerification::test_an_unchanged_roster_is_not_re_read`
- `loremaster/tests/test_allowlist_roster.py::TestRosterFreshnessOnEveryVerification::test_every_verification_stats_the_roster_including_cache_hits`
- `loremaster/tests/test_allowlist_roster.py::TestRosterIsLiveRuntimeStateNotBootConfig::test_an_uncached_principal_added_mid_process_is_admitted`
- `loremaster/tests/test_allowlist_roster.py::TestRosterIsLiveRuntimeStateNotBootConfig::test_an_uncached_principal_revoked_mid_process_is_denied`
- `loremaster/tests/test_allowlist_roster.py::TestRosterIsLiveRuntimeStateNotBootConfig::test_re_adding_a_principal_re_admits_them`
- `loremaster/tests/test_allowlist_roster.py::TestRosterNormalisationAtTheLoremasterSeam::test_a_COMPATIBILITY_form_google_email_matches_an_ascii_roster_line`
- `loremaster/tests/test_allowlist_roster.py::TestRosterNormalisationAtTheLoremasterSeam::test_a_capitalised_roster_line_admits_the_lowercase_google_email`
- `loremaster/tests/test_allowlist_roster.py::TestRosterNormalisationAtTheLoremasterSeam::test_a_plus_alias_of_a_listed_principal_is_NOT_admitted`
- `loremaster/tests/test_allowlist_roster.py::TestRosterNormalisationAtTheLoremasterSeam::test_a_roster_line_with_stray_whitespace_still_admits`
- `loremaster/tests/test_allowlist_roster.py::TestRosterNormalisationAtTheLoremasterSeam::test_an_unlisted_principal_at_a_listed_domain_is_NOT_admitted`

#### lorerunes/tests/test_roster_parser.py  (37 failed)
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_a_blank_presented_email_is_denied_even_against_a_populated_roster`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_a_domain_shaped_probe_is_denied_by_the_predicate_itself`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_a_homograph_of_a_listed_principal_is_denied`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_a_listed_principal_is_admitted`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_admission_does_not_substring_match`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_admission_normalises_the_presented_email`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_an_empty_roster_denies_every_principal`
- `lorerunes/tests/test_roster_parser.py::TestIsAdmittedFailsClosed::test_an_unlisted_principal_is_denied`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterDegenerateShapesYieldNoEntries::test_degenerate_roster_parses_to_the_empty_set[comments-only]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterDegenerateShapesYieldNoEntries::test_degenerate_roster_parses_to_the_empty_set[empty]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterDegenerateShapesYieldNoEntries::test_degenerate_roster_parses_to_the_empty_set[one-comment]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterDegenerateShapesYieldNoEntries::test_degenerate_roster_parses_to_the_empty_set[one-newline]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterDegenerateShapesYieldNoEntries::test_degenerate_roster_parses_to_the_empty_set[whitespace-only]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_a_roster_without_a_trailing_newline_still_parses_its_last_line`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_a_single_entry_roster_is_valid`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_an_indented_line_is_admitted_after_normalisation`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_an_uppercase_line_is_admitted_after_normalisation`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_comment_and_blank_lines_produce_no_entries`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_crlf_line_endings_parse_identically`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterHappyPath::test_realistic_roster_parses_to_its_three_principals`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterMergeFate::test_a_whitespace_only_duplicate_also_merges_rather_than_vanishing`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterMergeFate::test_the_merge_report_is_absent_when_no_line_merges`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterMergeFate::test_two_lines_normalising_to_one_entry_produce_one_entry_and_one_report`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRefusalRendersHostileTextUnambiguously::test_a_line_shaped_like_lore_own_output_cannot_be_read_as_structure`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRefusalRendersHostileTextUnambiguously::test_control_characters_are_escaped_not_emitted_raw`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_a_valid_roster_is_accepted_so_the_refusal_probe_can_discriminate`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_each_malformed_shape_refuses_the_parse[@]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_each_malformed_shape_refuses_the_parse[@firehawktransam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_each_malformed_shape_refuses_the_parse[ejprice@]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_each_malformed_shape_refuses_the_parse[ejprice@firehawk@transam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_each_malformed_shape_refuses_the_parse[firehawktransam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_one_malformed_line_invalidates_the_valid_lines_around_it[@]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_one_malformed_line_invalidates_the_valid_lines_around_it[@firehawktransam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_one_malformed_line_invalidates_the_valid_lines_around_it[ejprice@]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_one_malformed_line_invalidates_the_valid_lines_around_it[ejprice@firehawk@transam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_one_malformed_line_invalidates_the_valid_lines_around_it[firehawktransam.org]`
- `lorerunes/tests/test_roster_parser.py::TestParseRosterRejectsMalformedLinesWholesale::test_the_refusal_reports_the_FIRST_malformed_line`

#### loremaster/tests/test_auth.py  (25 failed)
- `loremaster/tests/test_auth.py::TestAuthConfigRetiresTlsTerminatedUpstream::test_a_config_still_carrying_the_retired_flag_fails_to_load`
- `loremaster/tests/test_auth.py::TestAuthConfigRetiresTlsTerminatedUpstream::test_the_failure_names_the_retired_field_and_the_fix`
- `loremaster/tests/test_auth.py::TestAuthConfigRetiresTlsTerminatedUpstream::test_the_retired_field_is_not_a_model_field`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_client_id_is_unconstructible[   \xa0 ]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_client_id_is_unconstructible[ ]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_client_id_is_unconstructible[\n]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_client_id_is_unconstructible[\t]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_client_id_is_unconstructible[]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_roster_path_is_unconstructible[ ]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_roster_path_is_unconstructible[\t]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_blank_roster_path_is_unconstructible[]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_complete_google_block_validates`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_missing_client_id_is_unconstructible`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_non_https_resource_server_url_is_unconstructible[]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_non_https_resource_server_url_is_unconstructible[ftp://lore.firehawktransam.org/mcp]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_non_https_resource_server_url_is_unconstructible[http://lore.firehawktransam.org/mcp]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_a_non_https_resource_server_url_is_unconstructible[lore.firehawktransam.org/mcp]`
- `loremaster/tests/test_auth.py::TestGoogleOAuthConfigFailsClosed::test_the_google_block_forbids_unknown_keys`
- `loremaster/tests/test_auth.py::TestLoreConfigCrossChecksTheResourcePath::test_matching_paths_validate`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_new_token_verifier_is_exported`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_exported[AuthVerifier]`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_exported[BearerAuthMiddleware]`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_importable_from_loremaster_auth[AuthVerifier]`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_importable_from_loremaster_auth[BearerAuthMiddleware]`
- `loremaster/tests/test_auth.py::TestRetiredAuthSurfaceIsGone::test_the_verifier_satisfies_the_sdk_token_verifier_protocol`

#### lorerunes/tests/test_email_normalisation.py  (21 failed)
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailAppliesNfkcCompatibilityFolding::test_fullwidth_at_sign_folds_to_ascii_at`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailAppliesNfkcCompatibilityFolding::test_fullwidth_letter_folds_to_ascii_letter`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailAppliesNfkcCompatibilityFolding::test_ligature_folds_to_its_component_letters`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_a_value_carrying_a_newline_keeps_it_for_the_parser_to_refuse`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_blank_shapes_normalise_to_the_empty_string_without_raising[   ]`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_blank_shapes_normalise_to_the_empty_string_without_raising[\n]`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_blank_shapes_normalise_to_the_empty_string_without_raising[\t\xa0 ]`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_blank_shapes_normalise_to_the_empty_string_without_raising[]`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDegenerateInputs::test_the_result_is_idempotent`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDoesNotConflateHomographs::test_cyrillic_lookalike_does_not_normalise_to_its_latin_twin`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailDoesNotConflateHomographs::test_greek_lookalike_domain_does_not_normalise_to_its_latin_twin`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailFoldsCase::test_already_normalised_address_is_unchanged`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailFoldsCase::test_mixed_case_address_folds_to_lowercase`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailFoldsCase::test_uses_casefold_not_lower_for_the_dotted_capital_i`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailFoldsCase::test_uses_casefold_not_lower_for_the_german_sharp_s`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailIsNotAnAliasCanonicaliser::test_dotted_local_part_is_a_distinct_identity`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailIsNotAnAliasCanonicaliser::test_plus_alias_is_a_distinct_identity`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailIsNotAnAliasCanonicaliser::test_subaddressing_on_a_workspace_domain_is_also_distinct`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailStripsWhitespaceOnly::test_interior_whitespace_is_preserved_not_squashed`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailStripsWhitespaceOnly::test_non_ascii_unicode_whitespace_is_stripped`
- `lorerunes/tests/test_email_normalisation.py::TestNormalizeEmailStripsWhitespaceOnly::test_roster_line_with_surrounding_whitespace_and_newline_normalises`

#### loremaster/tests/test_auth_identity_seam.py  (19 failed)
- `loremaster/tests/test_auth_identity_seam.py::TestApiKeyPrincipalsStillWorkInHostedPosture::test_a_named_api_key_can_open_a_session_through_the_hosted_gate`
- `loremaster/tests/test_auth_identity_seam.py::TestApiKeyPrincipalsStillWorkInHostedPosture::test_an_unknown_api_key_is_refused`
- `loremaster/tests/test_auth_identity_seam.py::TestHostAndOriginAreEnforcedInsideTheTransport::test_an_attacker_host_is_refused`
- `loremaster/tests/test_auth_identity_seam.py::TestHostAndOriginAreEnforcedInsideTheTransport::test_the_claude_origin_passes_BOTH_origin_layers`
- `loremaster/tests/test_auth_identity_seam.py::TestHostAndOriginAreEnforcedInsideTheTransport::test_the_loopback_host_is_still_accepted`
- `loremaster/tests/test_auth_identity_seam.py::TestHostAndOriginAreEnforcedInsideTheTransport::test_the_public_hostname_is_accepted`
- `loremaster/tests/test_auth_identity_seam.py::TestLanBearerPostureStillGatesOnApiKeys::test_a_google_token_is_not_accepted_in_lan_bearer_posture`
- `loremaster/tests/test_auth_identity_seam.py::TestLanBearerPostureStillGatesOnApiKeys::test_a_valid_api_key_opens_a_session`
- `loremaster/tests/test_auth_identity_seam.py::TestLanBearerPostureStillGatesOnApiKeys::test_an_unauthenticated_request_is_401`
- `loremaster/tests/test_auth_identity_seam.py::TestLoopbackPostureServesWithoutCredentials::test_an_unauthenticated_initialize_succeeds`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_a_different_listed_principal_cannot_resume_the_session`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_a_listed_principal_can_open_a_session`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_an_api_key_principal_cannot_resume_a_google_session`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_an_unauthenticated_request_cannot_resume_a_session`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_the_owner_can_reuse_their_own_session`
- `loremaster/tests/test_auth_identity_seam.py::TestSessionsAreBoundToTheCredentialThatCreatedThem::test_two_api_key_principals_do_not_share_a_session`
- `loremaster/tests/test_auth_identity_seam.py::TestTheReadOnlyGuardFiresOnTheSERVEDPath::test_a_hosted_principal_is_NOT_refused_a_READ_tool_over_the_wire`
- `loremaster/tests/test_auth_identity_seam.py::TestTheReadOnlyGuardFiresOnTheSERVEDPath::test_a_hosted_principal_is_refused_a_mutating_tool_over_the_WIRE`
- `loremaster/tests/test_auth_identity_seam.py::TestTheReadOnlyGuardFiresOnTheSERVEDPath::test_an_api_key_principal_is_NOT_refused_a_mutating_tool_over_the_wire`

#### loremaster/tests/test_permission_resolver_seam.py  (14 failed)
- `loremaster/tests/test_permission_resolver_seam.py::TestAuthContextDerivation::test_a_google_token_derives_a_google_provenance_context`
- `loremaster/tests/test_permission_resolver_seam.py::TestAuthContextDerivation::test_an_api_key_token_derives_an_api_key_provenance_context`
- `loremaster/tests/test_permission_resolver_seam.py::TestAuthContextDerivation::test_no_token_derives_no_context`
- `loremaster/tests/test_permission_resolver_seam.py::TestAuthContextDerivation::test_the_context_is_frozen`
- `loremaster/tests/test_permission_resolver_seam.py::TestPassThroughResolverIsTheShippingDefault::test_it_leaves_permitted_unfiltered`
- `loremaster/tests/test_permission_resolver_seam.py::TestPassThroughResolverIsTheShippingDefault::test_it_returns_an_equal_context`
- `loremaster/tests/test_permission_resolver_seam.py::TestPassThroughResolverIsTheShippingDefault::test_it_satisfies_the_resolver_protocol`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_a_tool_inside_the_resolved_permitted_set_is_not_refused`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_a_tool_outside_the_resolved_permitted_set_is_refused`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_an_empty_permitted_set_permits_NOTHING`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_the_default_build_uses_the_pass_through_resolver`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_the_injected_resolver_is_called_on_every_tool_dispatch`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_the_posture_guard_and_the_resolver_are_distinguishable`
- `loremaster/tests/test_permission_resolver_seam.py::TestTheSeamIsConsultedAtDispatchAndCanFilter::test_the_refusal_is_a_structured_tool_error`

#### loremaster/tests/test_secret_typing.py  (2 failed)
- `loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam`
- `loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`

#### loremaster/tests/test_ast_reach_helpers.py  (1 failed)
- `loremaster/tests/test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives`

#### loremaster/tests/test_comms_footer.py  (1 failed)
- `loremaster/tests/test_comms_footer.py::TestNoCommsIdentityReachesQueryTEXT::test_no_UNDECLARED_value_is_interpolated_into_query_text`

#### loremaster/tests/test_surreal_harness.py  (1 failed)
- `loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`


### ERROR — 135 tests, 2 files


#### loremaster/tests/test_message_ledger.py  (130 errors)
- `loremaster/tests/test_message_ledger.py::TestACasWinnerIsAlwaysReportedAcked::test_a_REPEATED_seq_whose_edge_vanishes_is_ALREADY_acked[real]`
- `loremaster/tests/test_message_ledger.py::TestACasWinnerIsAlwaysReportedAcked::test_a_genuinely_UNADDRESSED_seq_still_reports_not_addressed[real]`
- `loremaster/tests/test_message_ledger.py::TestACasWinnerIsAlwaysReportedAcked::test_a_winner_whose_edge_VANISHES_mid_call_is_still_acked[real]`
- `loremaster/tests/test_message_ledger.py::TestADuplicateSeqInOneBatchReportsPerOCCURRENCE::test_a_NON_ADJACENT_duplicate_behaves_identically[real]`
- `loremaster/tests/test_message_ledger.py::TestADuplicateSeqInOneBatchReportsPerOCCURRENCE::test_an_adjacent_duplicate_acks_once_and_reports_the_repeat[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_a_mixed_batch_reports_every_seqs_own_fate[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_a_note_never_reaches_an_ALREADY_acked_edge[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_ack_note_lands_on_the_edge_the_CAS_WON[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_acking_another_agents_edge_leaves_that_edge_UNCHANGED[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_already_stamped[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_an_ack_with_NO_note_leaves_it_unset[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_an_empty_seqs_list_is_an_honest_empty_result[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_no_such_message[real]`
- `loremaster/tests/test_message_ledger.py::TestAckDisambiguatesTheFourWayEmptyReturn::test_not_addressed_to_me[real]`
- `loremaster/tests/test_message_ledger.py::TestAckIsWriteOnce::test_a_second_ack_never_overwrites_the_first_stamp[real]`
- `loremaster/tests/test_message_ledger.py::TestAckIsWriteOnce::test_first_ack_stamps_and_reports_acked[real]`
- `loremaster/tests/test_message_ledger.py::TestAckIsWriteOnce::test_the_guard_is_what_does_the_work[real]`
- `loremaster/tests/test_message_ledger.py::TestAnAckedButUNDRAINEDMessageIsServedONCEMore::test_CONTROL_a_PEEK_does_not_consume_the_one_re_serve[real]`
- `loremaster/tests/test_message_ledger.py::TestAnAckedButUNDRAINEDMessageIsServedONCEMore::test_the_re_serve_CONVERGES_the_next_drain_is_empty[real]`
- `loremaster/tests/test_message_ledger.py::TestAnAckedButUNDRAINEDMessageIsServedONCEMore::test_the_re_serve_carries_the_ACK_STAMP_and_is_counted[real]`
- `loremaster/tests/test_message_ledger.py::TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner::test_sixteen_ackers_of_one_edge[real]`
- `loremaster/tests/test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs::test_at_scale[real-16]`
- `loremaster/tests/test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs::test_concurrent_seqs_all_exceed_the_pre_race_maximum[real]`
- `loremaster/tests/test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs::test_eight_concurrent_sends_all_land_on_distinct_seqs[real]`
- `loremaster/tests/test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs::test_every_concurrent_send_is_readable_by_its_recipient[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainIsScopedToTheCaller::test_a_cross_session_agent_sees_nothing[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainIsScopedToTheCaller::test_two_recipients_drain_independently[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_a_limit_of_ONE_serves_and_stamps_exactly_one[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_counts_are_computed_over_the_WHOLE_set_not_the_capped_window[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_directive_pending_counts_directives_INSIDE_the_window_too[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_directive_pending_is_also_over_the_whole_set[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_drain_serves_oldest_first_by_seq[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_over_cap_drain_serves_the_cap_and_stamps_only_the_cap[real]`
- `loremaster/tests/test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_the_elided_remainder_is_still_unread_on_the_next_drain[real]`
- `loremaster/tests/test_message_ledger.py::TestOneAnswerDischargesITSWHOLETHREAD::test_CONTROL_a_question_asked_AFTER_the_answer_is_still_outstanding[real]`
- `loremaster/tests/test_message_ledger.py::TestOneAnswerDischargesITSWHOLETHREAD::test_two_asks_on_ONE_thread_are_discharged_by_ONE_later_answer[real]`
- `loremaster/tests/test_message_ledger.py::TestPeekStampsNothing::test_a_non_peek_drain_after_a_peek_still_stamps[real]`
- `loremaster/tests/test_message_ledger.py::TestPeekStampsNothing::test_peek_serves_the_same_rows_but_stamps_none[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge::test_a_mixed_batch_is_all_or_nothing[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge::test_a_rejected_send_leaves_no_message_row_at_all[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge::test_an_unregistered_recipient_is_rejected_by_name[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge::test_no_dangling_edge_survives_a_send[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_POSITIVE_CONTROL_a_note_at_the_body_cap_is_accepted[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_POSITIVE_CONTROL_refs_exactly_at_both_caps_are_accepted[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_blank_body_is_rejected[real-   ]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_blank_body_is_rejected[real-\n\t ]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_blank_body_is_rejected[real-]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_body_exactly_at_the_cap_is_accepted[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_hostile_body_is_stored_RAW[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_a_thread_carrying_the_TAUGHT_q_topic_form_is_ACCEPTED[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_empty_recipient_set_is_a_teaching_error_not_a_silent_noop[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_out_of_domain_grade_is_rejected[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_over_COUNT_refs_list_is_REJECTED[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_over_length_ack_NOTE_is_REJECTED_at_the_BODY_cap[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_over_length_pointer_LABEL_is_REJECTED[real-task_id]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_over_length_pointer_LABEL_is_REJECTED[real-thread]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_over_length_ref_is_REJECTED_naming_its_index[real]`
- `loremaster/tests/test_message_ledger.py::TestSendValidatesTheBody::test_an_oversize_body_is_REJECTED_not_truncated[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_EVERY_recipient_actually_RECEIVES_the_message[real-1]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_EVERY_recipient_actually_RECEIVES_the_message[real-2]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_EVERY_recipient_actually_RECEIVES_the_message[real-3]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_EVERY_recipient_actually_RECEIVES_the_message[real-4]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_a_repeated_recipient_is_deduped_before_the_relate_loop[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_a_send_in_a_DIFFERENT_session_records_that_session[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_a_sender_never_receives_its_own_message[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_an_EXPLICIT_self_addressed_send_IS_delivered[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_an_explicit_thread_is_kept[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_dedupe_keys_on_IDENTITY_not_display_name[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_fan_out_reaches_every_recipient_and_only_them[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_recipient_names_are_deterministic_not_argument_order[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_single_recipient_round_trips_every_field[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_the_message_id_is_BARE_with_no_table_prefix[real]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_the_receipt_COUNT_equals_the_edges_actually_written[real-1]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_the_receipt_COUNT_equals_the_edges_actually_written[real-2]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_the_receipt_COUNT_equals_the_edges_actually_written[real-3]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_the_receipt_COUNT_equals_the_edges_actually_written[real-4]`
- `loremaster/tests/test_message_ledger.py::TestSendWritesTheNodeAndOneEdgePerRecipient::test_thread_defaults_to_the_session[real]`
- `loremaster/tests/test_message_ledger.py::TestSeqIsAnOrderingKeyNotACount::test_a_gap_breaks_nothing[real]`
- `loremaster/tests/test_message_ledger.py::TestSeqIsAnOrderingKeyNotACount::test_seqs_are_strictly_increasing[real]`
- `loremaster/tests/test_message_ledger.py::TestSetStatusMarksTheQuestionItDoesNotStoreAState::test_a_DIFFERENT_set_status_value_does_NOT_mark_a_question[real-active]`
- `loremaster/tests/test_message_ledger.py::TestSetStatusMarksTheQuestionItDoesNotStoreAState::test_a_DIFFERENT_set_status_value_does_NOT_mark_a_question[real-idle]`
- `loremaster/tests/test_message_ledger.py::TestSetStatusMarksTheQuestionItDoesNotStoreAState::test_a_question_still_delivers_normally[real]`
- `loremaster/tests/test_message_ledger.py::TestSetStatusMarksTheQuestionItDoesNotStoreAState::test_an_ordinary_send_is_NOT_a_question[real]`
- `loremaster/tests/test_message_ledger.py::TestSetStatusMarksTheQuestionItDoesNotStoreAState::test_send_with_set_status_marks_the_message_as_a_question[real]`
- `loremaster/tests/test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_0_does_NOT_re_serve_a_processed_seq_0[real]`
- `loremaster/tests/test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_does_not_re_stamp_and_does_not_consume_unseen[real]`
- `loremaster/tests/test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_is_STRICTLY_greater_than_the_cursor[real]`
- `loremaster/tests/test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_re_reads_rows_a_plain_drain_already_stamped[real]`
- `loremaster/tests/test_message_ledger.py::TestSinceServesAlreadySeenRows::test_the_since_read_is_ALSO_bounded[real]`
- `loremaster/tests/test_message_ledger.py::TestStampedSeqsIsTheACTUALStampNotTheAttemptedWindow::test_stamped_seqs_excludes_a_window_row_stamped_by_a_racer[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDdlSliceIsAppliedByEnsureReady::test_ensure_ready_creates_the_message_and_to_tables[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDdlSliceIsAppliedByEnsureReady::test_ensure_ready_is_idempotent[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDerivationReadsQuestionsFIRSTAndShortCircuits::test_the_questions_read_precedes_the_deliveries_read[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDerivationReadsQuestionsFIRSTAndShortCircuits::test_zero_questions_never_issues_the_deliveries_query[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDerivedWaitingStateKnownBound::test_KNOWN_BOUND_an_out_of_band_answer_leaves_the_state_waiting[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDerivedWaitingStateKnownBound::test_the_bound_closes_the_moment_the_answer_IS_relayed[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDrainPendingReadIsBounded::test_the_entries_read_never_materialises_more_than_the_limit[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDrainRowCarriesTheQuestionMarker::test_InboxEntry_has_a_question_field[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDrainRowCarriesTheQuestionMarker::test_a_drained_question_row_reports_question_True[real]`
- `loremaster/tests/test_message_ledger.py::TestTheDrainRowCarriesTheQuestionMarker::test_a_question_and_a_NON_question_row_in_ONE_drain_discriminate[real]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_a_fresh_ledgers_first_send_has_the_SAME_seq_on_both_backends`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[ack_note_overcap]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[blank_body]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[empty_recipients]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[illegal_grade]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[overcap_body]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[refs_count]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[refs_entry_len]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[thread_len]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[unknown_recipient]`
- `loremaster/tests/test_message_ledger.py::TestTheOracleRendersProductionsErrorProse::test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production[unknown_sender]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_DIRECTIVE_grade_answer_clears_a_question[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_DIRECTIVE_sent_without_set_status_does_NOT_make_the_sender_waiting[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_SIGNAL_grade_question_DOES_make_the_sender_waiting[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_message_that_PREDATES_the_question_is_not_an_answer[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_message_the_ASKER_sends_on_its_own_thread_is_not_an_answer[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_a_self_addressed_message_with_ANOTHER_recipient_is_STILL_not_an_answer[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_an_answer_on_a_DIFFERENT_thread_does_not_clear_it[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_an_answer_on_the_thread_clears_it_WITHOUT_ANY_WRITE_TO_THE_AGENT[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_an_explicitly_SELF_ADDRESSED_message_on_the_question_thread_is_NOT_an_answer[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_an_unanswered_question_makes_the_asker_waiting[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_another_agents_question_never_makes_ME_wait[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_answering_only_ONE_of_two_questions_leaves_the_other_outstanding[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_asked_at_IS_the_questions_own_created_at[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_draining_does_not_change_the_derived_state[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_draining_the_ANSWER_does_clear_it[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_no_question_means_not_waiting[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_the_OLDEST_unanswered_question_is_the_one_reported[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_the_derivation_writes_NOTHING[real]`
- `loremaster/tests/test_message_ledger.py::TestTheWaitingStateIsDerived::test_the_write_watch_SEES_a_real_write[real]`

#### loremaster/tests/test_comms_footer.py  (5 errors)
- `loremaster/tests/test_comms_footer.py::TestThePendingTrafficCountIsONEImplementation::test_a_SIGNAL_is_never_counted_as_an_unacked_directive[asyncio-real]`
- `loremaster/tests/test_comms_footer.py::TestThePendingTrafficCountIsONEImplementation::test_an_UNREAD_directive_is_ALSO_an_unacked_directive[asyncio-real]`
- `loremaster/tests/test_comms_footer.py::TestThePendingTrafficCountIsONEImplementation::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW[asyncio-unacked-real]`
- `loremaster/tests/test_comms_footer.py::TestThePendingTrafficCountIsONEImplementation::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW[asyncio-unread-real]`
- `loremaster/tests/test_comms_footer.py::TestThePendingTrafficCountIsONEImplementation::test_the_seam_counts_unread_and_unacked_DIRECTIVES_separately[asyncio-real]`

## Receipts

### MAIN suite — final counts line + tail of `=== short test summary info ===` (full block reproduced grouped above)
```
$ uv run pytest -n auto -q -ra --tb=short
# ... (587-line short-summary block; every FAILED/ERROR nodeid is enumerated grouped in the section above)
FAILED loremaster/tests/test_google_token_verifier.py::TestAudienceCheck::test_the_aud_mismatch_log_line_renders_the_configured_client_id
FAILED loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_truthy_shapes_are_admitted[bool-true]
FAILED loremaster/tests/test_google_token_verifier.py::TestEmailVerifiedAcrossEveryShapeGoogleEmits::test_truthy_shapes_are_admitted[str-true]
FAILED loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam
FAILED loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
FAILED loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
451 failed, 9878 passed, 51 skipped, 3 xfailed, 6 warnings, 135 errors in 244.36s (0:04:04)
MAIN_EXIT=1
```

### MAIN suite — representative Cluster-1 error block (SDK multi-statement guard, teardown)
```
_ ERROR at teardown of TestThePendingTrafficCountIsONEImplementation.test_a_SIGNAL_is_never_counted_as_an_unacked_directive[asyncio-real] _
[gw54] linux -- Python 3.14.6 /home/ejprice/PycharmProjects/lore/.venv/bin/python3
loremaster/tests/conftest.py:212: in _no_sdk_call_escapes_the_retry_driver
    assert not report.multi_statement_violations, (
E   AssertionError: 1 bare .query() call(s) carried MORE THAN ONE statement during this test:
E       store/_txn.py:1207 in _attempt() -> connection.query()
E     
E     The SDK's .query() validates statement[0] ONLY (store reference §3): a later statement can fail and roll the whole transaction back while .query() raises nothing (#124/#144). Multi-statement SurrealQL must ride execute_transaction (query_raw), never bare .query(). Checked at RUNTIME on the real SDK class (the #144 posture), replacing the per-module hand-list.
E   assert not [SdkEscape(method='query', site='store/_txn.py:1207 in _attempt()')]
```

### SKILL suite — full tail
`cd skills/lore-deploy/scripts && uv run python -m pytest -q -ra --tb=short . ../tests`
```
........................................................................ [ 61%]
.............................................                            [100%]
117 passed in 17.07s
SKILL_EXIT=0
```

_Logs (scratch, non-durable): `scratchpad/harness-full.log`, `scratchpad/skill-suite.log`; grouped nodeid lists `scratchpad/{failed,error}-nodeids.txt`. Suite run 2026-08-17 at HEAD `5c8230c`._

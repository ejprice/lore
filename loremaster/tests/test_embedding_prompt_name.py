"""Contract tests for loremaster prompt-name config plumbing (feat-tei-prompt-name).

GROUP A5 — loremaster config plumbing (must FAIL red on current code):
  * loremaster.config.EmbeddingConfig (a _StrictModel with extra="forbid") must
    accept query_prompt_name and document_prompt_name as optional fields
    (today they are rejected → ValidationError).
  * to_loresigil_config(cfg) must carry both fields into the loresigil
    EmbeddingConfig so they reach the TEIEmbedder constructor.

These tests are independent of the loresigil implementation — they pin the
loremaster→loresigil config SEAM (the only crossing where a missing field would
silently drop the prompt names).
"""

from __future__ import annotations

from typing import Any

import pytest
from loremaster.config import EmbeddingConfig
from loremaster.embedding import to_loresigil_config
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Shared fixture values — derived from the production lore.yaml shape.
# The exact field names matter: they must match the lore.yaml key that a
# operator would add ("query_prompt_name", "document_prompt_name").
# ---------------------------------------------------------------------------

# The exact prompt names the live TEI endpoint exposes (from the spec).
QUERY_PROMPT_NAME: str = "query"
DOCUMENT_PROMPT_NAME: str = "document"

# A valid base loremaster EmbeddingConfig payload (mirrors _CANONICAL_CONFIG in
# test_config.py so it stays aligned with the real schema).
_BASE_EMBEDDING_FIELDS: dict[str, Any] = {
    "backend": "tei",
    "base_url": "http://tei.example:8080",
    "endpoint": "/embed",
    "model": "voyageai/voyage-4-nano",
    "dim": 2048,
    "max_input_tokens": 8192,
    "max_batch_texts": 32,
    "concurrency": 2,
    "connect_timeout_s": 5.0,
    "api_key_env": "LORE_TEI_KEY",
    "tokenizer": "voyage-4-nano",
    "truncate": False,
}


def _make_base_config(**overrides: Any) -> EmbeddingConfig:
    """Construct a valid base loremaster EmbeddingConfig with optional overrides."""
    return EmbeddingConfig(**{**_BASE_EMBEDDING_FIELDS, **overrides})


# ---------------------------------------------------------------------------
# GROUP A5: Config field acceptance — MUST FAIL RED on current code
# ---------------------------------------------------------------------------


class TestLoremasterEmbeddingConfigAcceptsPromptNames:
    """loremaster EmbeddingConfig (_StrictModel, extra='forbid') must accept the new fields.

    Today EmbeddingConfig rejects unknown fields immediately. After the feature,
    query_prompt_name and document_prompt_name must be valid optional fields.
    """

    def test_accepts_query_prompt_name_field(self) -> None:
        """EmbeddingConfig with query_prompt_name='query' must not raise ValidationError."""
        # Today this raises:
        #   pydantic.ValidationError: extra inputs are not permitted [query_prompt_name]
        config = _make_base_config(query_prompt_name=QUERY_PROMPT_NAME)
        assert config.query_prompt_name == QUERY_PROMPT_NAME

    def test_accepts_document_prompt_name_field(self) -> None:
        """EmbeddingConfig with document_prompt_name='document' must not raise."""
        config = _make_base_config(document_prompt_name=DOCUMENT_PROMPT_NAME)
        assert config.document_prompt_name == DOCUMENT_PROMPT_NAME

    def test_accepts_both_prompt_names_together(self) -> None:
        """Both fields may be set simultaneously."""
        config = _make_base_config(
            query_prompt_name=QUERY_PROMPT_NAME,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )
        assert config.query_prompt_name == QUERY_PROMPT_NAME
        assert config.document_prompt_name == DOCUMENT_PROMPT_NAME

    def test_prompt_names_default_to_none_when_absent(self) -> None:
        """Both fields default to None when not present (backward-compatible opt-in).

        A lore.yaml that does not mention prompt names must parse cleanly and
        silently disable asymmetric prompting — preserving the no-prompt behavior.
        """
        config = _make_base_config()  # no prompt name fields
        # None means "don't send prompt_name" — current behavior, unchanged.
        assert config.query_prompt_name is None
        assert config.document_prompt_name is None

    def test_extra_unrelated_field_is_still_rejected(self) -> None:
        """Adding the new fields must NOT weaken the extra='forbid' guard.

        A plausible-but-wrong field (e.g. 'retry_backoff') must still be rejected
        even after query_prompt_name is added — the guard must remain tight.
        """
        with pytest.raises(ValidationError):
            _make_base_config(retry_backoff=True)


class TestToLoresigilConfigCarriesPromptNames:
    """to_loresigil_config must faithfully carry prompt names to the loresigil layer.

    The seam test: a field present in loremaster EmbeddingConfig but absent from
    the to_loresigil_config translation would silently drop it, causing the
    TEIEmbedder to be constructed without the prompt name — and no error would
    be reported.
    """

    def test_query_prompt_name_carried_to_loresigil_config(self) -> None:
        """query_prompt_name is present in the translated loresigil config."""
        loremaster_config = _make_base_config(query_prompt_name=QUERY_PROMPT_NAME)
        loresigil_config = to_loresigil_config(loremaster_config)

        # The translated config must preserve the field, not drop it.
        assert loresigil_config.query_prompt_name == QUERY_PROMPT_NAME

    def test_document_prompt_name_carried_to_loresigil_config(self) -> None:
        """document_prompt_name is present in the translated loresigil config."""
        loremaster_config = _make_base_config(document_prompt_name=DOCUMENT_PROMPT_NAME)
        loresigil_config = to_loresigil_config(loremaster_config)

        assert loresigil_config.document_prompt_name == DOCUMENT_PROMPT_NAME

    def test_both_prompt_names_carried_together(self) -> None:
        """Both fields cross the seam when both are set."""
        loremaster_config = _make_base_config(
            query_prompt_name=QUERY_PROMPT_NAME,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )
        loresigil_config = to_loresigil_config(loremaster_config)

        assert loresigil_config.query_prompt_name == QUERY_PROMPT_NAME
        assert loresigil_config.document_prompt_name == DOCUMENT_PROMPT_NAME

    def test_none_prompt_names_translated_as_none(self) -> None:
        """When prompt names are None (absent from config), the translated config also has None.

        This ensures the no-config path remains byte-identical to the current
        behavior — the TEIEmbedder is constructed without prompt names.
        """
        loremaster_config = _make_base_config()  # no prompt names
        loresigil_config = to_loresigil_config(loremaster_config)

        assert loresigil_config.query_prompt_name is None
        assert loresigil_config.document_prompt_name is None

    def test_existing_fields_are_still_translated_faithfully(self) -> None:
        """Adding prompt-name translation must not break any existing field mapping.

        Regression guard: all currently-translated fields must still appear
        correctly in the output.
        """
        loremaster_config = _make_base_config(
            query_prompt_name=QUERY_PROMPT_NAME,
        )
        loresigil_config = to_loresigil_config(loremaster_config)

        # Spot-check the fields already covered by test_embedding.py.
        assert loresigil_config.backend == "tei"
        assert loresigil_config.base_url == "http://tei.example:8080"
        assert loresigil_config.endpoint == "/embed"
        assert loresigil_config.dim == 2048
        assert loresigil_config.max_input_tokens == 8192
        assert loresigil_config.api_key_env == "LORE_TEI_KEY"

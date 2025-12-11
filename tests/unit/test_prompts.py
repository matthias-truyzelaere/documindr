"""Unit tests for prompt templates."""

from app.api.schemas.chat import SummaryLength
from app.domain.rag.prompts import (
    PromptRegistry,
    get_rag_chat_template,
    get_summary_template,
)


def test_rag_chat_template_caching():
    """Test that RAG chat template is cached properly."""
    PromptRegistry.clear_cache()

    template1 = get_rag_chat_template()
    template2 = get_rag_chat_template()

    # Should return the same cached instance
    assert template1 is template2


def test_summary_template_caching():
    """Test that summary templates are cached properly."""
    PromptRegistry.clear_cache()

    concise1 = get_summary_template(SummaryLength.CONCISE)
    concise2 = get_summary_template(SummaryLength.CONCISE)

    # Should return the same cached instance
    assert concise1 is concise2


def test_different_summary_lengths_cached_separately():
    """Test that different summary lengths have separate cache entries."""
    PromptRegistry.clear_cache()

    concise = get_summary_template(SummaryLength.CONCISE)
    normal = get_summary_template(SummaryLength.NORMAL)
    comprehensive = get_summary_template(SummaryLength.COMPREHENSIVE)

    # All should be different instances
    assert concise is not normal
    assert normal is not comprehensive
    assert concise is not comprehensive


def test_rag_chat_template_has_required_variables():
    """Test that RAG chat template has context and query variables."""
    template = get_rag_chat_template()

    # Check that template can be formatted with required variables
    result = template.format(context="test context", query="test query")

    assert "test context" in result
    assert "test query" in result


def test_summary_template_has_context_variable():
    """Test that summary templates have context variable."""
    for length in [
        SummaryLength.CONCISE,
        SummaryLength.NORMAL,
        SummaryLength.COMPREHENSIVE,
    ]:
        template = get_summary_template(length)

        # Check that template can be formatted with context
        result = template.format(context="test context")

        assert "test context" in result


def test_clear_cache():
    """Test that clear_cache works properly."""
    template1 = get_rag_chat_template()
    PromptRegistry.clear_cache()
    template2 = get_rag_chat_template()

    # After clearing cache, should get a new instance
    assert template1 is not template2


def test_summary_lengths_have_different_content():
    """Test that different summary lengths have different prompts."""
    concise = get_summary_template(SummaryLength.CONCISE)
    normal = get_summary_template(SummaryLength.NORMAL)
    comprehensive = get_summary_template(SummaryLength.COMPREHENSIVE)

    concise_text = concise.format(context="test")
    normal_text = normal.format(context="test")
    comprehensive_text = comprehensive.format(context="test")

    # Verify they contain their respective descriptions
    assert "3-5 sentences" in concise_text
    assert "8-12 sentences" in normal_text
    assert "15-25 sentences" in comprehensive_text

"""Unit tests for percentage spacing normalization."""

from app.domain.rag.retrieval import fix_percent_spacing


def test_fix_percent_spacing():
    """
    Test percentage spacing normalization removes spaces before % symbol.

    Verifies:
    - Spaces between numbers and % are removed
    - Correctly formatted percentages remain unchanged

    This function normalizes percentage formatting in LLM outputs
    to match standard notation (e.g., "50%" instead of "50 %").
    The normalization improves output consistency and readability.

    Examples:
    - "50 %" → "50%"
    - "100%" → "100%" (no change)
    """
    # Test normalization of incorrectly spaced percentage
    assert fix_percent_spacing("50 %") == "50%"

    # Test that correctly formatted percentage is unchanged
    assert fix_percent_spacing("100% already correct") == "100% already correct"

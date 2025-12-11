"""Unit tests for PDF document loading."""

from pypdf import PdfWriter

from app.domain.documents.loader import load_pdf


def test_load_pdf(tmp_path):
    """
    Test PDF loading with blank page returns empty list.

    Verifies:
    - Blank PDF pages are handled correctly
    - Empty/minimal text pages are filtered out
    - Function returns empty list for contentless PDFs

    The loader filters out pages with less than 10 characters
    to avoid indexing empty or near-empty pages that provide
    no meaningful content for retrieval.

    Args:
        tmp_path: Pytest fixture providing temporary directory
    """
    # Create path for test PDF
    path = tmp_path / "file.pdf"

    # Create blank PDF with single empty page
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)

    # Write PDF to file
    with open(path, "wb") as f:
        writer.write(f)

    # Verify blank PDF returns no documents
    # (blank pages have no extractable text > 10 chars)
    assert load_pdf(str(path)) == []

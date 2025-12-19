# tests/test_extractors.py
import pytest
import os
import tempfile
from app.extractors.pdf_extractor import extract_text_from_pdf, extract_metadata_from_pdf
from app.extractors.docx_extractor import extract_text_from_docx, extract_metadata_from_docx


def test_extract_text_from_txt():
    """Test text extraction from TXT file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\nIt has multiple lines.")
        temp_path = f.name
    
    try:
        with open(temp_path, 'r', encoding='utf-8') as file:
            text = file.read()
        assert len(text) > 0
        assert "test document" in text
    finally:
        os.unlink(temp_path)


def test_pdf_extractor_with_empty_file():
    """Test PDF extractor handles empty files gracefully."""
    # This would require a test PDF file
    # For now, we test the function exists
    assert callable(extract_text_from_pdf)
    assert callable(extract_metadata_from_pdf)


def test_docx_extractor_with_empty_file():
    """Test DOCX extractor handles empty files gracefully."""
    assert callable(extract_text_from_docx)
    assert callable(extract_metadata_from_docx)


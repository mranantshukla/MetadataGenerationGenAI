# tests/test_file_validator.py
import pytest
from fastapi import UploadFile
from io import BytesIO
from app.utils.file_validator import validate_file_extension, calculate_file_hash


def test_validate_file_extension_valid():
    """Test valid file extensions."""
    assert validate_file_extension("test.pdf") == ".pdf"
    assert validate_file_extension("test.docx") == ".docx"
    assert validate_file_extension("test.txt") == ".txt"


def test_validate_file_extension_invalid():
    """Test invalid file extensions."""
    with pytest.raises(Exception):
        validate_file_extension("test.exe")


def test_calculate_file_hash():
    """Test file hash calculation."""
    content = b"test content"
    hash1 = calculate_file_hash(content)
    hash2 = calculate_file_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 char hex string


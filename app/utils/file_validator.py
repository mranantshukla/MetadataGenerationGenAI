# app/utils/file_validator.py
from fastapi import UploadFile, HTTPException
from typing import List
import os
import hashlib
from app.config.settings import get_settings

settings = get_settings()

# MIME type mapping
ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
}

def validate_file_extension(filename: str) -> str:
    """Validate file extension."""
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return file_ext

async def validate_file_size(file: UploadFile) -> bytes:
    """Validate and read file content with size check."""
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({settings.MAX_FILE_SIZE / 1024 / 1024:.2f} MB)"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    return content

def validate_mime_type(content: bytes, filename: str) -> bool:
    """Validate MIME type matches file extension."""
    # Basic validation - in production, use python-magic
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Check if extension is in allowed list
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False
    
    # Additional validation can be added here with python-magic
    # For now, we rely on extension validation
    return True

def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()

async def validate_upload_file(file: UploadFile) -> dict:
    """Comprehensive file validation."""
    # Validate extension
    file_ext = validate_file_extension(file.filename)
    
    # Validate size and get content
    content = await validate_file_size(file)
    
    # Validate MIME type
    if not validate_mime_type(content, file.filename):
        raise HTTPException(
            status_code=400,
            detail="File type validation failed"
        )
    
    # Calculate hash
    file_hash = calculate_file_hash(content)
    
    return {
        'content': content,
        'extension': file_ext,
        'size': len(content),
        'hash': file_hash,
        'filename': file.filename
    }


# app/api/v1/documents.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile
import shutil
from datetime import datetime

from app.database.database import get_db
from app.database.models import DocumentMetadata
from app.utils.file_validator import validate_upload_file
from app.extractors.pdf_extractor import extract_text_from_pdf, extract_metadata_from_pdf
from app.extractors.docx_extractor import extract_text_from_docx, extract_metadata_from_docx
from app.nlp.semantic_analysis import (
    perform_ner, generate_summary, classify_text,
    extract_keywords, analyze_sentiment, identify_key_sections
)
from app.metadata.dublin_core_mapper import map_to_dublin_core
from app.config.settings import get_settings
from app.middleware.rate_limiter import limiter

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=dict)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process documents to generate metadata."""
    results = []
    
    for file in files:
        try:
            # Validate file
            validation_result = await validate_upload_file(file)
            content = validation_result['content']
            file_ext = validation_result['extension']
            file_hash = validation_result['hash']
            
            # Check if document already exists
            existing_doc = db.query(DocumentMetadata).filter(
                DocumentMetadata.file_hash == file_hash
            ).first()
            
            if existing_doc:
                results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'message': 'Document already processed',
                    'document_id': existing_doc.id,
                    'dublin_core_metadata': existing_doc.dublin_core_metadata,
                    'extracted_metadata': existing_doc.extracted_metadata,
                })
                continue
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Extract text and metadata
                text = ""
                file_metadata = {
                    'filename': file.filename,
                    'format': file.content_type or 'application/octet-stream',
                    'size': validation_result['size']
                }
                
                if file_ext == '.pdf':
                    text = extract_text_from_pdf(tmp_path)
                    pdf_metadata = extract_metadata_from_pdf(tmp_path)
                    file_metadata.update(pdf_metadata)
                elif file_ext == '.docx':
                    text = extract_text_from_docx(tmp_path)
                    docx_metadata = extract_metadata_from_docx(tmp_path)
                    file_metadata.update(docx_metadata)
                elif file_ext == '.txt':
                    text = content.decode('utf-8', errors='ignore')
                
                if not text or len(text.strip()) < 10:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Could not extract meaningful text from {file.filename}"
                    )
                
                # Truncate text if too long
                if len(text) > settings.MAX_TEXT_LENGTH:
                    text = text[:settings.MAX_TEXT_LENGTH]
                
                # Perform semantic analysis
                entities = perform_ner(text)
                summary = generate_summary(text)
                categories = classify_text(text)
                keywords = extract_keywords(text)
                sentiment = analyze_sentiment(text)
                key_sections = identify_key_sections(text)
                
                # Prepare extracted metadata
                extracted_metadata = {
                    'entities': entities,
                    'summary': summary,
                    'categories': categories,
                    'keywords': keywords,
                    'sentiment': sentiment,
                    'key_sections': key_sections,
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'processing_date': datetime.now().isoformat()
                }
                
                # Map to Dublin Core
                dc_metadata = map_to_dublin_core(extracted_metadata, file_metadata)
                
                # Save to database
                db_document = DocumentMetadata(
                    filename=file.filename,
                    file_hash=file_hash,
                    file_size=validation_result['size'],
                    file_extension=file_ext,
                    dublin_core_metadata=dc_metadata,
                    extracted_metadata=extracted_metadata,
                    file_metadata=file_metadata,
                    processing_status='completed'
                )
                db.add(db_document)
                db.commit()
                db.refresh(db_document)
                
                results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'document_id': db_document.id,
                    'dublin_core_metadata': dc_metadata,
                    'extracted_metadata': extracted_metadata,
                    'file_metadata': file_metadata
                })
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except HTTPException:
            raise
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })
    
    return JSONResponse(content={'results': results})


@router.get("/{document_id}", response_model=dict)
async def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get metadata for a specific document."""
    document = db.query(DocumentMetadata).filter(
        DocumentMetadata.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id {document_id} not found"
        )
    
    return {
        'id': document.id,
        'filename': document.filename,
        'dublin_core_metadata': document.dublin_core_metadata,
        'extracted_metadata': document.extracted_metadata,
        'file_metadata': document.file_metadata,
        'processing_status': document.processing_status,
        'created_at': document.created_at.isoformat()
    }


@router.get("/", response_model=dict)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all processed documents."""
    documents = db.query(DocumentMetadata).offset(skip).limit(limit).all()
    total = db.query(DocumentMetadata).count()
    
    return {
        'total': total,
        'skip': skip,
        'limit': limit,
        'documents': [
            {
                'id': doc.id,
                'filename': doc.filename,
                'processing_status': doc.processing_status,
                'created_at': doc.created_at.isoformat()
            }
            for doc in documents
        ]
    }


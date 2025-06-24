# app/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
import logging
from typing import List, Dict, Any
import json
from datetime import datetime

from app.extractors.pdf_extractor import extract_text_from_pdf, extract_metadata_from_pdf
from app.extractors.docx_extractor import extract_text_from_docx, extract_metadata_from_docx
from app.nlp.semantic_analysis import (
    perform_ner, generate_summary, classify_text, 
    extract_keywords, analyze_sentiment, identify_key_sections
)
from app.metadata.dublin_core_mapper import map_to_dublin_core

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Automated Metadata Generation System",
    description="AI-powered system for extracting and generating structured metadata from documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create upload directory
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main upload page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload-documents/")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Process uploaded documents and generate metadata."""
    results = []
    
    for file in files:
        try:
            # Validate file type
            allowed_extensions = ['.pdf', '.docx', '.txt']
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_ext}"
                )
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Extract text and metadata based on file type
                text = ""
                file_metadata = {
                    'filename': file.filename,
                    'format': file.content_type or 'application/octet-stream',
                    'size': os.path.getsize(tmp_path)
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
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if not text or len(text.strip()) < 10:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Could not extract meaningful text from {file.filename}"
                    )
                
                # Perform semantic analysis
                logger.info(f"Processing {file.filename} with {len(text)} characters")
                
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
                
                # Prepare result
                result = {
                    'filename': file.filename,
                    'status': 'success',
                    'dublin_core_metadata': dc_metadata,
                    'extracted_metadata': extracted_metadata,
                    'file_metadata': file_metadata
                }
                
                results.append(result)
                logger.info(f"Successfully processed {file.filename}")
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })
    
    return JSONResponse(content={'results': results})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Automated Metadata Generation System",
        "version": "1.0.0",
        "supported_formats": [".pdf", ".docx", ".txt"],
        "metadata_standard": "Dublin Core",
        "features": [
            "Text extraction with OCR fallback",
            "Named Entity Recognition",
            "Document summarization",
            "Document classification",
            "Keyword extraction",
            "Sentiment analysis",
            "Dublin Core metadata mapping"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

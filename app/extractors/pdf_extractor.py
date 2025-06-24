# app/extractors/pdf_extractor.py
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import os
import tempfile
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Enhanced image preprocessing for better OCR accuracy."""
    try:
        # Convert to grayscale
        gray = image.convert('L')
        
        # Apply Gaussian blur to reduce noise
        blurred = gray.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Apply binary thresholding using Otsu's method
        threshold = 128
        binary = blurred.point(lambda x: 0 if x < threshold else 255, '1')
        
        # Apply median filter to remove salt-and-pepper noise
        filtered_img = binary.filter(ImageFilter.MedianFilter(size=3))
        
        # Convert back to grayscale for OCR
        processed = filtered_img.convert('L')
        
        return processed
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        return image.convert('L')

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF with enhanced OCR fallback."""
    text = ""
    
    try:
        # First attempt: Direct text extraction
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                text += page_text
                logger.info(f"Extracted {len(page_text)} characters from page {page_num + 1}")
        
        # Check if extraction was successful
        if len(text.strip()) < 100:
            logger.info("Low text content detected, falling back to OCR")
            
            # OCR fallback with preprocessing
            try:
                images = convert_from_path(file_path, dpi=300)
                ocr_texts = []
                
                for i, img in enumerate(images):
                    # Preprocess image for better OCR
                    processed_img = preprocess_image_for_ocr(img)
                    
                    # Configure Tesseract for better accuracy
                    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()[]{}"\'-/\\ '
                    
                    ocr_result = pytesseract.image_to_string(
                        processed_img, 
                        config=custom_config
                    )
                    ocr_texts.append(ocr_result)
                    logger.info(f"OCR extracted {len(ocr_result)} characters from page {i + 1}")
                
                text = "\n".join(ocr_texts)
                
            except Exception as ocr_error:
                logger.error(f"OCR processing failed: {ocr_error}")
                return ""
                
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""
    
    return text.strip()

def extract_metadata_from_pdf(file_path: str) -> dict:
    """Extract metadata from PDF file."""
    metadata = {}
    
    try:
        with fitz.open(file_path) as doc:
            pdf_metadata = doc.metadata
            metadata.update({
                'title': pdf_metadata.get('title', ''),
                'author': pdf_metadata.get('author', ''),
                'subject': pdf_metadata.get('subject', ''),
                'creator': pdf_metadata.get('creator', ''),
                'producer': pdf_metadata.get('producer', ''),
                'creation_date': pdf_metadata.get('creationDate', ''),
                'modification_date': pdf_metadata.get('modDate', ''),
                'page_count': doc.page_count
            })
    except Exception as e:
        logger.error(f"PDF metadata extraction failed: {e}")
    
    return metadata

# app/metadata/dublin_core_mapper.py
from typing import Dict, Any, List
import re
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DublinCoreMapper:
    """Maps extracted metadata to Dublin Core schema."""
    
    def __init__(self):
        self.dc_elements = [
            'title', 'creator', 'subject', 'description', 'publisher',
            'contributor', 'date', 'type', 'format', 'identifier',
            'source', 'language', 'relation', 'coverage', 'rights'
        ]
    
    def map_to_dublin_core(self, 
                          extracted_metadata: Dict[str, Any],
                          file_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Map extracted metadata to Dublin Core schema."""
        
        if file_metadata is None:
            file_metadata = {}
        
        dc_metadata = {}
        
        # Title (dc:title)
        dc_metadata['dc:title'] = self._extract_title(
            extracted_metadata, file_metadata
        )
        
        # Creator (dc:creator)
        dc_metadata['dc:creator'] = self._extract_creator(
            extracted_metadata, file_metadata
        )
        
        # Subject (dc:subject)
        dc_metadata['dc:subject'] = self._extract_subject(
            extracted_metadata
        )
        
        # Description (dc:description)
        dc_metadata['dc:description'] = self._extract_description(
            extracted_metadata
        )
        
        # Publisher (dc:publisher)
        dc_metadata['dc:publisher'] = self._extract_publisher(
            extracted_metadata, file_metadata
        )
        
        # Date (dc:date)
        dc_metadata['dc:date'] = self._extract_date(
            extracted_metadata, file_metadata
        )
        
        # Type (dc:type)
        dc_metadata['dc:type'] = self._extract_type(
            extracted_metadata
        )
        
        # Format (dc:format)
        dc_metadata['dc:format'] = file_metadata.get('format', 'application/octet-stream')
        
        # Language (dc:language)
        dc_metadata['dc:language'] = self._extract_language(
            extracted_metadata
        )
        
        # Additional elements
        dc_metadata['dc:identifier'] = file_metadata.get('filename', 'unknown')
        dc_metadata['dc:rights'] = 'All rights reserved'
        
        logger.info("Successfully mapped metadata to Dublin Core schema")
        return dc_metadata
    
    def _extract_title(self, extracted_metadata: Dict, file_metadata: Dict) -> str:
        """Extract title from various sources."""
        # Priority: file metadata > first heading > filename
        
        # From file metadata
        if file_metadata.get('title'):
            return file_metadata['title']
        
        # From key sections (headings)
        key_sections = extracted_metadata.get('key_sections', [])
        if key_sections:
            # Look for markdown headings
            for section in key_sections:
                if section.startswith('#'):
                    title = re.sub(r'^#+\s*', '', section).strip()
                    if len(title) > 5:
                        return title
        
        # From filename
        filename = file_metadata.get('filename', 'Untitled Document')
        if filename != 'Untitled Document':
            # Remove extension and clean up
            title = re.sub(r'\.[^.]+$', '', filename)
            title = re.sub(r'[_-]', ' ', title)
            return title.title()
        
        return 'Untitled Document'
    
    def _extract_creator(self, extracted_metadata: Dict, file_metadata: Dict) -> str:
        """Extract creator/author information."""
        # Priority: file metadata > NER persons > default
        
        # From file metadata
        if file_metadata.get('author'):
            return file_metadata['author']
        
        # From NER entities
        entities = extracted_metadata.get('entities', {})
        persons = entities.get('PERSON', [])
        if persons:
            # Return first person found
            return persons[0]
        
        return 'Unknown'
    
    def _extract_subject(self, extracted_metadata: Dict) -> List[str]:
        """Extract subject keywords and topics."""
        subjects = []
        
        # From keywords
        keywords = extracted_metadata.get('keywords', [])
        if keywords:
            # Extract keyword strings (handle tuples from KeyBERT)
            for kw in keywords[:10]:  # Top 10 keywords
                if isinstance(kw, tuple):
                    subjects.append(kw[0])
                else:
                    subjects.append(str(kw))
        
        # From entities (organizations, locations, etc.)
        entities = extracted_metadata.get('entities', {})
        for entity_type in ['ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT']:
            if entity_type in entities:
                subjects.extend(entities[entity_type][:3])  # Top 3 per type
        
        # From categories
        categories = extracted_metadata.get('categories', [])
        subjects.extend(categories)
        
        # Remove duplicates and clean up
        subjects = list(set(subjects))
        subjects = [s for s in subjects if len(s) > 2]  # Filter short terms
        
        return subjects[:15]  # Limit to 15 subjects
    
    def _extract_description(self, extracted_metadata: Dict) -> str:
        """Extract description/summary."""
        # Priority: generated summary > key sections
        
        summary = extracted_metadata.get('summary', '')
        if summary and len(summary) > 20:
            return summary
        
        # Fallback to key sections
        key_sections = extracted_metadata.get('key_sections', [])
        if key_sections:
            # Combine first few sections
            description = ' '.join(key_sections[:2])
            if len(description) > 500:
                description = description[:500] + '...'
            return description
        
        return 'No description available'
    
    def _extract_publisher(self, extracted_metadata: Dict, file_metadata: Dict) -> str:
        """Extract publisher information."""
        # From file metadata
        if file_metadata.get('creator'):
            return file_metadata['creator']
        
        # From entities (organizations)
        entities = extracted_metadata.get('entities', {})
        orgs = entities.get('ORG', [])
        if orgs:
            return orgs[0]
        
        return 'Automated Metadata Generation System'
    
    def _extract_date(self, extracted_metadata: Dict, file_metadata: Dict) -> str:
        """Extract date information."""
        # Priority: file metadata > content dates > current date
        
        # From file metadata
        for date_field in ['created', 'creation_date', 'modified', 'modification_date']:
            if file_metadata.get(date_field):
                date_str = file_metadata[date_field]
                # Clean up date string
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', str(date_str))
                if date_match:
                    return date_match.group(0)
        
        # From content (look for dates in text)
        entities = extracted_metadata.get('entities', {})
        dates = entities.get('DATE', [])
        if dates:
            for date_str in dates:
                # Look for year patterns
                year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                if year_match:
                    return year_match.group(0)
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_type(self, extracted_metadata: Dict) -> str:
        """Extract document type."""
        categories = extracted_metadata.get('categories', [])
        if categories:
            # Map categories to Dublin Core types
            type_mapping = {
                'Technical Documentation': 'Text',
                'Legal Document': 'Text',
                'Financial Report': 'Text',
                'Academic Paper': 'Text',
                'Medical Document': 'Text',
                'Business Report': 'Text',
                'Marketing Material': 'Text',
                'News Article': 'Text',
                'Educational Content': 'Text',
                'Research Paper': 'Text'
            }
            return type_mapping.get(categories[0], 'Text')
        
        return 'Text'
    
    def _extract_language(self, extracted_metadata: Dict) -> str:
        """Extract language information."""
        # For now, default to English
        # Could be enhanced with language detection
        return 'en'

# Global mapper instance
mapper = DublinCoreMapper()

def map_to_dublin_core(extracted_metadata: Dict[str, Any], 
                      file_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Map extracted metadata to Dublin Core schema."""
    return mapper.map_to_dublin_core(extracted_metadata, file_metadata)

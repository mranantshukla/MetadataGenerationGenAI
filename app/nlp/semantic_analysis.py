# app/nlp/semantic_analysis.py
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
import re
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    def __init__(self):
        self.nlp = None
        self.summarizer = None
        self.classifier = None
        self.kw_model = None
        self.sentiment_analyzer = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all NLP models with error handling."""
        try:
            # Load spaCy model
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("SpaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
        
        try:
            # Load summarization model
            self.summarizer = pipeline(
                'summarization', 
                model='facebook/bart-large-cnn',
                device=-1  # Use CPU
            )
            logger.info("Summarization model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
        
        try:
            # Load classification model
            self.classifier = pipeline(
                'zero-shot-classification',
                model='facebook/bart-large-mnli',
                device=-1
            )
            logger.info("Classification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load classification model: {e}")
        
        try:
            # Load KeyBERT model
            self.kw_model = KeyBERT()
            logger.info("KeyBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load KeyBERT model: {e}")
        
        try:
            # Load sentiment analysis model
            self.sentiment_analyzer = pipeline(
                'sentiment-analysis',
                model='cardiffnlp/twitter-roberta-base-sentiment-latest',
                device=-1
            )
            logger.info("Sentiment analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentiment analysis model: {e}")
    
    def perform_ner(self, text: str) -> Dict[str, List[str]]:
        """Enhanced Named Entity Recognition."""
        entities = {}
        
        if not self.nlp:
            return entities
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                label = ent.label_
                if label not in entities:
                    entities[label] = set()
                entities[label].add(ent.text.strip())
            
            # Convert sets to lists and filter out single characters
            entities = {
                k: [v for v in list(vs) if len(v) > 1] 
                for k, vs in entities.items()
            }
            
            logger.info(f"Extracted {sum(len(v) for v in entities.values())} entities")
            
        except Exception as e:
            logger.error(f"NER failed: {e}")
        
        return entities
    
    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """Generate text summary with length control."""
        if not self.summarizer or len(text) < 100:
            return ""
        
        try:
            # Truncate text if too long for model
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
            
            summary_result = self.summarizer(
                text, 
                max_length=max_length, 
                min_length=30, 
                do_sample=False
            )
            
            summary = summary_result[0]['summary_text']
            logger.info(f"Generated summary of {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return ""
    
    def classify_document(self, text: str, candidate_labels: List[str] = None) -> List[str]:
        """Classify document into categories."""
        if not self.classifier:
            return []
        
        if candidate_labels is None:
            candidate_labels = [
                'Technical Documentation', 'Legal Document', 'Financial Report',
                'Academic Paper', 'Medical Document', 'Business Report',
                'Marketing Material', 'News Article', 'Educational Content',
                'Research Paper'
            ]
        
        try:
            # Truncate text for classification
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.classifier(text, candidate_labels)
            top_categories = result['labels'][:3]
            
            logger.info(f"Classified document into: {top_categories}")
            return top_categories
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return []
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using KeyBERT."""
        if not self.kw_model:
            return []
        
        try:
            keywords = self.kw_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 2), 
                stop_words='english',
                top_n=top_k,  # Fixed: KeyBERT uses top_n, not top_k
                use_mmr=True,
                diversity=0.5
            )
            
            logger.info(f"Extracted {len(keywords)} keywords")
            return keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze document sentiment."""
        if not self.sentiment_analyzer:
            return {}
        
        try:
            # Truncate text for sentiment analysis
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.sentiment_analyzer(text)
            sentiment = {
                'label': result[0]['label'],
                'score': result[0]['score']
            }
            
            logger.info(f"Sentiment analysis: {sentiment}")
            return sentiment
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {}
    
    def identify_key_sections(self, text: str) -> List[str]:
        """Identify key sections using multiple strategies."""
        key_sections = []
        
        # Strategy 1: Find headings (markdown-style)
        heading_pattern = r'^(#{1,6}\s+.+)$'
        headings = re.findall(heading_pattern, text, re.MULTILINE)
        if headings:
            key_sections.extend(headings[:5])
        
        # Strategy 2: Find sentences with high entity density
        if self.nlp:
            try:
                doc = self.nlp(text)
                sentences = list(doc.sents)
                
                scored_sentences = []
                for sent in sentences:
                    if len(sent.text) > 50:  # Filter short sentences
                        entity_count = len([ent for ent in sent.ents])
                        score = entity_count / max(1, len(sent))
                        scored_sentences.append((sent.text.strip(), score))
                
                # Get top 3 sentences by entity density
                scored_sentences.sort(key=lambda x: x[1], reverse=True)
                key_sections.extend([sent[0] for sent in scored_sentences[:3]])
                
            except Exception as e:
                logger.error(f"Key section identification failed: {e}")
        
        return key_sections[:5]  # Return top 5 sections

# Global analyzer instance
analyzer = SemanticAnalyzer()

def perform_ner(text: str) -> Dict[str, List[str]]:
    return analyzer.perform_ner(text)

def generate_summary(text: str, max_length: int = 150) -> str:
    return analyzer.generate_summary(text, max_length)

def classify_text(text: str, candidate_labels: List[str] = None) -> List[str]:
    return analyzer.classify_document(text, candidate_labels)

def extract_keywords(text: str, top_k: int = 10) -> List[Tuple[str, float]]:
    return analyzer.extract_keywords(text, top_k)

def analyze_sentiment(text: str) -> Dict[str, float]:
    return analyzer.analyze_sentiment(text)

def identify_key_sections(text: str) -> List[str]:
    return analyzer.identify_key_sections(text)

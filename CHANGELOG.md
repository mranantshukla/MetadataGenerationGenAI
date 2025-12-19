# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2024-12-XX

### Added
- Configuration management with Pydantic Settings
- Database persistence with SQLAlchemy (PostgreSQL/SQLite support)
- Alembic database migrations
- API versioning (v1)
- File validation with size and type checking
- Rate limiting middleware
- Redis caching layer
- Celery for async task processing
- Prometheus metrics endpoint
- Comprehensive test suite
- Docker and Docker Compose setup
- Background job tracking
- Document retrieval by ID
- Paginated document listing
- API request logging
- Structured JSON logging
- Health check endpoints
- Environment-based configuration

### Fixed
- KeyBERT API bug (top_k → top_n)
- Missing variable issues
- CORS security configuration
- File size validation
- Error handling improvements

### Changed
- Refactored API structure with versioning
- Updated file upload endpoint to `/api/v1/documents/upload`
- Improved error messages
- Enhanced security with proper CORS configuration
- Better code organization

### Security
- File size limits
- File type validation
- Rate limiting
- Secure CORS configuration
- File hash calculation for duplicate detection

## [1.0.0] - Initial Release

### Features
- PDF, DOCX, TXT file support
- OCR integration
- Named Entity Recognition
- Document summarization
- Document classification
- Keyword extraction
- Sentiment analysis
- Dublin Core metadata mapping
- FastAPI backend
- Web interface


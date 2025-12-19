# Setup Guide - Metadata Generation System v2.0

## Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite works for development)
- Redis (optional, for caching and Celery)
- Tesseract OCR (for PDF OCR)

## Step-by-Step Setup

### 1. Clone and Navigate
```bash
cd MetadataGenerationGenAI
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# At minimum, set:
# - SECRET_KEY (generate a random string)
# - DATABASE_URL (sqlite:///./metadata.db for development)
```

### 5. Initialize Database
```bash
# Option 1: Simple initialization
python scripts/init_db.py

# Option 2: Using Alembic (recommended)
alembic upgrade head
```

### 6. Run Application

**Development Mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Using Makefile:**
```bash
make dev
```

### 7. Access Application
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Metrics: http://localhost:8000/metrics

## Docker Setup

### Quick Start
```bash
docker-compose up -d
```

### Access Services
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Issue: spaCy model not found
```bash
python -m spacy download en_core_web_sm
```

### Issue: Database connection error
- Check DATABASE_URL in .env
- Ensure database is running
- For SQLite, ensure directory is writable

### Issue: Redis connection error
- Set REDIS_ENABLED=false if not using Redis
- Or ensure Redis is running on configured port

### Issue: Tesseract not found
- Install Tesseract OCR:
  - Windows: Download from GitHub
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

## Production Deployment

1. **Update .env with production values:**
   - Strong SECRET_KEY
   - PostgreSQL database URL
   - Proper CORS_ORIGINS
   - Enable rate limiting

2. **Use Docker:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Or use Gunicorn:**
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## API Usage Examples

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "files=@document.pdf"
```

### Get Document Metadata
```bash
curl "http://localhost:8000/api/v1/documents/1"
```

### List Documents
```bash
curl "http://localhost:8000/api/v1/documents/?skip=0&limit=10"
```

## Next Steps

- Review README_UPDATES.md for new features
- Check CHANGELOG.md for version history
- Explore API documentation at /api/docs


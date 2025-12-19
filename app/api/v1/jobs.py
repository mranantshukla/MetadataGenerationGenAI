# app/api/v1/jobs.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.database import get_db
from app.database.models import ProcessingJob

router = APIRouter()


@router.get("/{job_id}", response_model=dict)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a processing job."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id {job_id} not found"
        )
    
    return {
        'job_id': job.id,
        'status': job.status,
        'progress': job.progress,
        'error_message': job.error_message,
        'result': job.result,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None
    }


@router.get("/", response_model=dict)
async def list_jobs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List processing jobs."""
    query = db.query(ProcessingJob)
    
    if status:
        query = query.filter(ProcessingJob.status == status)
    
    total = query.count()
    jobs = query.order_by(ProcessingJob.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        'total': total,
        'skip': skip,
        'limit': limit,
        'jobs': [
            {
                'job_id': job.id,
                'status': job.status,
                'progress': job.progress,
                'created_at': job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
    }


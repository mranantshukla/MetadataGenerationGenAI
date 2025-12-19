# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import documents, jobs, health

router = APIRouter(prefix="/api/v1", tags=["v1"])

router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(health.router, tags=["health"])

from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Poll this endpoint to check task progress.

    Frontend calls this every 2 seconds after submitting a question.

    Possible responses:

    1. Task still running:
       {"task_id": "abc", "status": "pending"}

    2. Task complete:
       {"task_id": "abc", "status": "complete", "result": {...}}

    3. Task failed:
       {"task_id": "abc", "status": "failed", "error": "..."}

    Celery task states:
        PENDING  → task queued, not started yet
        STARTED  → worker picked it up, running
        SUCCESS  → done, result available
        FAILURE  → something went wrong
        RETRY    → retrying after error
    """
    result = AsyncResult(task_id, app=celery_app)

    if result.state in ("PENDING", "STARTED", "RETRY"):
        return {
            "task_id": task_id,
            "status": "pending",
        }

    if result.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "complete",
            "result": result.result,
        }

    if result.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(result.result),
        }

    # Unknown state fallback
    raise HTTPException(status_code=500, detail=f"Unknown task state: {result.state}")

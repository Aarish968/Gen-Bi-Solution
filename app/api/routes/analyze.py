from fastapi import APIRouter
from pydantic import BaseModel
from app.tasks.analyze_task import analyze_question_task

router = APIRouter()


class AnalyzeRequest(BaseModel):
    question: str


@router.post("/")
async def analyze(request: AnalyzeRequest):
    """
    Submits analyze question as a background Celery task.

    Before (blocking):
        POST /api/analyze/ → wait 30-40s → response

    After (non-blocking):
        POST /api/analyze/ → {"task_id": "abc123"} ← returns in 0.1s
        Frontend polls GET /api/task/{task_id} until complete

    Why this is better:
        - No timeout risk on frontend
        - FastAPI is free to handle other requests immediately
        - Celery worker handles the heavy LLM work separately
    """
    task = analyze_question_task.delay(request.question)
    return {"task_id": task.id}

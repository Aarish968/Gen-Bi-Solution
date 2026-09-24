import asyncio
import logging
from app.celery_app import celery_app
from app.agents.orchestrator_agent import OrchestratorAgent

# This logger output goes to Celery worker terminal
logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="analyze_question",
    max_retries=2,
    default_retry_delay=5,
)
def analyze_question_task(self, question: str) -> dict:
    """
    Celery task — runs OrchestratorAgent in background.
    All logs appear in the Celery worker terminal.
    """
    logger.info(f"[Task {self.request.id}] Started — question: '{question}'")

    try:
        logger.info(f"[Task {self.request.id}] Creating OrchestratorAgent...")
        agent = OrchestratorAgent()

        logger.info(f"[Task {self.request.id}] Running agent pipeline (Planner + Query + Analysis + Viz + Decision)...")
        result = asyncio.run(agent.run(question))

        logger.info(f"[Task {self.request.id}] ✅ Complete — SQL: {result.get('sql', '')[:80]}")
        return result

    except Exception as exc:
        err_str = str(exc)
        logger.error(f"[Task {self.request.id}] ❌ Failed — {type(exc).__name__}: {exc}")

        # Do NOT retry quota errors — retrying makes it worse
        is_quota_error = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
        if is_quota_error:
            logger.warning(f"[Task {self.request.id}] Quota exceeded — not retrying.")
            raise exc  # raise directly — no retry

        raise self.retry(exc=exc)

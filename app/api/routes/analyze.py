from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.orchestrator_agent import OrchestratorAgent

router = APIRouter()


class AnalyzeRequest(BaseModel):
    question: str


@router.post("/")
async def analyze(request: AnalyzeRequest):
    """
    Single entry point for the full multi-agent pipeline.

    Internally runs:
        PlannerAgent → QueryAgent → AnalysisAgent → VisualizationAgent → DecisionAgent

    Returns a unified response with plan, SQL, data, insight, chart type, and recommendation.
    """
    print("Hello, Inside analyze router....")
    agent = OrchestratorAgent()
    result = await agent.run(request.question)
    return result

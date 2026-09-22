from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.analysis_agent import AnalysisAgent

router = APIRouter()

class InsightRequest(BaseModel):
    data: dict

@router.post("/")
async def get_insights(request: InsightRequest):
    agent = AnalysisAgent()
    result = await agent.run(request.data)
    return result

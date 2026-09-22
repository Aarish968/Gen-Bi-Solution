from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.visualization_agent import VisualizationAgent

router = APIRouter()

class VizRequest(BaseModel):
    data: dict
    question: str

@router.post("/")
async def get_visualization(request: VizRequest):
    agent = VisualizationAgent()
    result = await agent.run(request.data, request.question)
    return result

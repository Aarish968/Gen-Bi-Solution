from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.query_agent import QueryAgent

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

@router.post("/")
async def run_query(request: QueryRequest):
    agent = QueryAgent()
    result = await agent.run(request.question)
    return result

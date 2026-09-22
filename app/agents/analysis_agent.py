from app.services.llm_service import LLMService

class AnalysisAgent:
    """Generates trends and insights from query results."""

    def __init__(self):
        self.llm = LLMService()

    async def run(self, data: dict) -> dict:
        insight = await self.llm.generate_insight(data)
        return {"insight": insight}

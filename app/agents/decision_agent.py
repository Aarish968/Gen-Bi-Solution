from app.services.llm_service import LLMService

class DecisionAgent:
    """Generates business recommendations based on insights."""

    def __init__(self):
        self.llm = LLMService()

    async def run(self, insight: str) -> dict:
        recommendation = await self.llm.generate_recommendation(insight)
        return {"recommendation": recommendation}

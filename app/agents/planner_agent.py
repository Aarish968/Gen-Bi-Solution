from app.services.llm_service import LLMService

class PlannerAgent:
    """Breaks down a complex user question into sub-tasks for other agents."""

    def __init__(self):
        self.llm = LLMService()

    async def run(self, question: str) -> dict:
        print("Inside the planner run function......")
        plan = await self.llm.create_plan(question)
        print("after the plan from llm......")
        return {"plan": plan}

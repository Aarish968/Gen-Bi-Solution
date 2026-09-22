from app.services.llm_service import LLMService
from app.services.db_service import DBService

class QueryAgent:
    """Converts natural language to SQL and executes it."""

    def __init__(self):
        self.llm = LLMService()
        self.db = DBService()

    async def run(self, question: str) -> dict:
        sql = await self.llm.nl_to_sql(question)
        results = await self.db.execute(sql)
        return {"sql": sql, "results": results}

from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.decision_agent import DecisionAgent


class OrchestratorAgent:
    """
    Chains all agents in order to answer a complex business question end-to-end.

    Flow:
        1. PlannerAgent        → breaks question into steps (the thinking phase)
        2. QueryAgent          → converts question to SQL and fetches data from DB
        3. AnalysisAgent       → generates business insight from the fetched data
        4. VisualizationAgent  → selects chart type + builds structured chart config
        5. DecisionAgent       → produces actionable recommendations from the insight

    Phase 5 change:
        Before → chart_type: "bar"
        After  → chart_config: {
                    "chart_type": "bar",
                    "title": "Total Sales by Region",
                    "labels": ["North", "East", ...],
                    "datasets": [{"label": "Total Sales", "data": [...]}]
                 }
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.query = QueryAgent()
        self.analysis = AnalysisAgent()
        self.visualization = VisualizationAgent()
        self.decision = DecisionAgent()

    async def run(self, question: str) -> dict:
        # Step 1: Planner breaks the question into a step-by-step plan
        plan_output = await self.planner.run(question)

        # Step 2: QueryAgent converts question → SQL → executes on DB → raw data
        query_output = await self.query.run(question)
        sql = query_output.get("sql", "")
        results = query_output.get("results", [])

        # Step 3: AnalysisAgent reads the raw data and produces an insight text
        analysis_output = await self.analysis.run({"question": question, "results": results})
        insight = analysis_output.get("insight", "")

        # Step 4: VisualizationAgent builds complete chart config (Phase 5)
        # Returns full structured config — not just chart_type string anymore
        chart_config = await self.visualization.run({"results": results}, question)

        # Step 5: DecisionAgent turns the insight into actionable recommendations
        decision_output = await self.decision.run(insight)
        recommendation = decision_output.get("recommendation", "")

        # Combine everything into one unified response
        return {
            "question": question,
            "plan": plan_output.get("plan", []),
            "sql": sql,
            "results": results,
            "insight": insight,
            "chart_config": chart_config,       # Phase 5 — full structured config
            "recommendation": recommendation,
        }

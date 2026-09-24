import asyncio
from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.decision_agent import DecisionAgent


class OrchestratorAgent:
    """
    Chains all agents to answer a complex business question end-to-end.

    Execution strategy — 3 parallel groups:

    Group 1 (parallel): PlannerAgent + QueryAgent
        Both only need the question — no dependency on each other.
        Run simultaneously → saves ~3s

    Group 2 (parallel): AnalysisAgent + VisualizationAgent
        Both need query results — no dependency on each other.
        Run simultaneously → saves ~4s

    Group 3 (alone): DecisionAgent
        Needs insight from AnalysisAgent → must run after Group 2.

    Timeline:
        Sequential (before): ~18s
        Parallel   (after) : ~10s
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.query = QueryAgent()
        self.analysis = AnalysisAgent()
        self.visualization = VisualizationAgent()
        self.decision = DecisionAgent()

    async def run(self, question: str) -> dict:

        # ── Group 1: Planner + Query in parallel ──────────────────────────────
        # Both only need the question — zero dependency on each other
        plan_output, query_output = await asyncio.gather(
            self.planner.run(question),
            self.query.run(question),
        )

        sql     = query_output.get("sql", "")
        results = query_output.get("results", [])

        # ── Group 2: Analysis + Visualization in parallel ─────────────────────
        # Both need query results — zero dependency on each other
        analysis_output, chart_config = await asyncio.gather(
            self.analysis.run({"question": question, "results": results}),
            self.visualization.run({"results": results}, question),
        )

        insight = analysis_output.get("insight", "")

        # ── Group 3: Decision — needs insight from Group 2 ────────────────────
        decision_output = await self.decision.run(insight)
        recommendation  = decision_output.get("recommendation", "")

        return {
            "question":       question,
            "plan":           plan_output.get("plan", []),
            "sql":            sql,
            "results":        results,
            "insight":        insight,
            "chart_config":   chart_config,
            "recommendation": recommendation,
        }

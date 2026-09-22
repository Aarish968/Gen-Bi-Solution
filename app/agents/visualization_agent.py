from app.services.llm_service import LLMService

CHART_TYPES = ["bar", "line", "pie", "scatter"]


class VisualizationAgent:
    """
    Selects the best chart type for the data and builds a
    structured chart config that frontend can directly use.

    Before (Phase 4):
        run() returned → {"chart_type": "bar", "data": {...}}
        Frontend had no idea what to do with raw data.

    After (Phase 5):
        run() returns →
        {
          "chart_type": "bar",
          "title": "Total Sales by Region",
          "labels": ["North", "East", "South", "West"],
          "datasets": [
            {
              "label": "Total Sales",
              "data": [7246000, 6295000, 4713000, 4542000]
            }
          ]
        }
        Frontend directly feeds this into Chart.js or Recharts.

    Two steps inside run():
        Step 1 — select_chart_type() : Gemini picks best chart for the question
        Step 2 — build_chart_config() : Gemini extracts labels + data from results
    """

    def __init__(self):
        self.llm = LLMService()

    async def run(self, data: dict, question: str) -> dict:
        results = data.get("results", [])

        # Step 1 — Ask Gemini which chart type fits best for this question
        chart_type = await self.llm.select_chart_type(question, CHART_TYPES)

        # Sanitize — if Gemini returns something not in our list, default to bar
        chart_type = chart_type.lower().strip()
        if chart_type not in CHART_TYPES:
            chart_type = "bar"

        # Step 2 — Build structured chart config from actual query results
        chart_config = await self.llm.build_chart_config(question, chart_type, results)

        return chart_config

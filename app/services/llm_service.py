import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
from app.utils.schema_loader import get_all_table_names, get_schema_for_tables


class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )

    def _extract_text(self, content) -> str:
        """
        Gemini can return content as a string or a list of parts.
        Always return a plain string.
        """
        if isinstance(content, list):
            return " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        return str(content).strip()

    async def _select_relevant_tables(self, question: str) -> list[str]:
        """
        STEP 1 of nl_to_sql — Table Selection.

        Sends only the table names (not full schema) to Gemini and asks
        which tables are relevant to answer the user's question.

        Why only table names and not full schema?
        - Sending full schema of 50 tables wastes tokens
        - Table names are enough for Gemini to understand relevance
        - Full schema is only sent for the selected tables in Step 2

        Example:
            question : "Is mahine kitna sales hua?"
            tables   : ["sales", "customers", "orders"]
            returns  : ["sales"]
        """
        all_tables = get_all_table_names()

        prompt = PromptTemplate.from_template(
            "You are a database expert. A user asked this question:\n"
            "\"{question}\"\n\n"
            "Available tables in the database:\n{tables}\n\n"
            "Which tables are needed to answer this question?\n"
            "Reply with ONLY a JSON array of table names. Example: [\"sales\"] or [\"orders\", \"customers\"]\n"
            "Do not include any explanation."
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "question": question,
            "tables": "\n".join(f"  - {t}" for t in all_tables)
        })

        raw = self._extract_text(response.content)

        # Strip markdown fences if Gemini wraps response in ```json ... ```
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            selected = json.loads(raw)
            # Validate — only keep tables that actually exist
            valid = [t for t in selected if t in all_tables]
            # Fallback — if Gemini returns nothing valid, use all tables
            return valid if valid else all_tables
        except (json.JSONDecodeError, TypeError):
            # Fallback — if JSON parsing fails, use all tables
            return all_tables

    async def nl_to_sql(self, question: str) -> str:
        """
        Converts a natural language question to a SQL query using 2-step process.

        Step 1 — Table Selection:
            Send only table names to Gemini → get relevant table names back
            e.g. ["sales"]

        Step 2 — SQL Generation:
            Load schema ONLY for selected tables from SQLAlchemy models
            Send question + focused schema to Gemini → get correct SQL back

        This approach scales well:
            - 5 tables   → works perfectly
            - 50 tables  → only relevant schemas sent, no token waste
            - 100 columns table → only selected table columns sent
        """
        # ── Step 1: Ask Gemini which tables are relevant ──────────────────────
        relevant_tables = await self._select_relevant_tables(question)

        # ── Step 2: Load schema only for selected tables ──────────────────────
        schema = get_schema_for_tables(relevant_tables)

        # ── Step 3: Generate SQL using focused schema ─────────────────────────
        prompt = PromptTemplate.from_template(
            "You are a PostgreSQL expert. Use ONLY the tables and columns defined in the schema below.\n\n"
            "Schema:\n{schema}\n\n"
            "Important rules:\n"
            "  - Use ONLY column names that exist in the schema above\n"
            "  - To calculate revenue or total sales always use: price * quantity\n"
            "  - For date filtering use DATE comparisons e.g. sale_date >= '2026-01-01'\n"
            "  - Return ONLY the raw SQL query — no markdown, no code fences, no explanation\n\n"
            "Question: {question}\n"
            "SQL:"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"question": question, "schema": schema})
        sql = self._extract_text(response.content)

        # Strip markdown code fences Gemini sometimes adds (e.g. ```sql ... ```)
        sql = sql.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
        return sql

    async def generate_insight(self, data: dict) -> str:
        prompt = PromptTemplate.from_template(
            "Analyze this data and provide business insights:\n{data}"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"data": str(data)})
        return self._extract_text(response.content)

    async def select_chart_type(self, question: str, options: list) -> str:
        prompt = PromptTemplate.from_template(
            "Choose the best chart type from {options} for this question: {question}\n"
            "Answer with just the chart type."
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"question": question, "options": options})
        return self._extract_text(response.content)

    async def build_chart_config(self, question: str, chart_type: str, results: list) -> dict:
        """
        Builds a structured chart config from query results that frontend
        can directly feed into Chart.js or Recharts — no extra processing needed.

        How it works:
          - Sends question + chart_type + raw results to Gemini
          - Gemini identifies which column is the label (X-axis)
            and which column is the value (Y-axis)
          - Returns a clean JSON config with title, labels, datasets

        Example input:
            question   : "Show total sales by region"
            chart_type : "bar"
            results    : [{"region": "North", "total_sales": 7246000}, ...]

        Example output:
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
        """
        prompt = PromptTemplate.from_template(
            "You are a data visualization expert.\n\n"
            "User question: {question}\n"
            "Chart type selected: {chart_type}\n"
            "Query results (JSON): {results}\n\n"
            "Build a chart configuration for this data.\n"
            "Return ONLY a valid JSON object with this exact structure:\n"
            "{{\n"
            '  "chart_type": "{chart_type}",\n'
            '  "title": "<a short descriptive title>",\n'
            '  "labels": ["<label1>", "<label2>", ...],\n'
            '  "datasets": [\n'
            "    {{\n"
            '      "label": "<dataset label>",\n'
            '      "data": [<value1>, <value2>, ...]\n'
            "    }}\n"
            "  ]\n"
            "}}\n\n"
            "Rules:\n"
            "  - labels must come from the categorical column in the results\n"
            "  - data must come from the numeric column in the results\n"
            "  - Return ONLY the JSON — no explanation, no markdown, no code fences"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "question": question,
            "chart_type": chart_type,
            "results": json.dumps(results, default=str)
        })

        raw = self._extract_text(response.content)
        # Strip markdown fences if Gemini adds them
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            # Fallback — return minimal valid structure if parsing fails
            return {
                "chart_type": chart_type,
                "title": question,
                "labels": [],
                "datasets": [{"label": "Data", "data": []}]
            }

    async def generate_recommendation(self, insight: str) -> str:
        prompt = PromptTemplate.from_template(
            "Based on this insight, give actionable business recommendations:\n{insight}"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"insight": insight})
        return self._extract_text(response.content)

    async def create_plan(self, question: str) -> list:
        prompt = PromptTemplate.from_template(
            "Break down this business question into steps:\n{question}\nReturn as numbered list."
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"question": question})
        return [line for line in self._extract_text(response.content).split("\n") if line.strip()]

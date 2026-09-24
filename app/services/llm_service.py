import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
from app.utils.schema_loader import get_all_table_names, get_schema_for_tables


class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=800,  # stay within free tier output token limits
        )

    def _extract_text(self, content) -> str:
        """Groq always returns a plain string — keep for safety."""
        if isinstance(content, list):
            return " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        return str(content).strip()

    async def _select_relevant_tables(self, question: str) -> list[str]:
        """
        Step 1 of nl_to_sql — asks LLM which tables are needed.
        Sends only table names (not full schema) to save tokens.
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
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            selected = json.loads(raw)
            valid = [t for t in selected if t in all_tables]
            return valid if valid else all_tables
        except (json.JSONDecodeError, TypeError):
            return all_tables

    async def nl_to_sql(self, question: str) -> str:
        """
        2-step NL → SQL:
          Step 1 — select relevant tables
          Step 2 — generate SQL using focused schema
        """
        relevant_tables = await self._select_relevant_tables(question)
        schema = get_schema_for_tables(relevant_tables)

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
            "Answer with just the chart type name only — no explanation."
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"question": question, "options": options})
        return self._extract_text(response.content)

    async def build_chart_config(self, question: str, chart_type: str, results: list) -> dict:
        """
        Builds frontend-ready chart config from query results.
        Returns JSON with title, labels, datasets for Chart.js / Recharts.
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
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
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

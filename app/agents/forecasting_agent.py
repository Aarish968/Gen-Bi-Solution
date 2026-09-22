"""
forecasting_agent.py

Phase 7 Agent — Forecasting + Anomaly Detection + Smart Recommendations.

Flow inside run():
  1. ForecastingService.forecast()         → next month prediction + trend
  2. ForecastingService.detect_anomalies() → unusual patterns in current month
  3. LLMService.generate_recommendation()  → data-backed smart recommendations
                                             based on forecast + anomalies combined

Why this agent exists separately:
  - QueryAgent handles historical data questions
  - ForecastingAgent handles future predictions + anomaly alerts
  - Together they cover past + present + future
"""

from app.services.forecasting_service import ForecastingService
from app.services.llm_service import LLMService


class ForecastingAgent:
    def __init__(self):
        self.forecasting = ForecastingService()
        self.llm = LLMService()

    async def run(self, months: int = 6, threshold: float = 0.30) -> dict:
        """
        Runs the full  pipeline:

        Step 1 — Forecast:
            Fetch last N months sales → calculate growth trend → predict next month

        Step 2 — Anomaly Detection:
            Fetch current month region + product sales
            Flag anything deviating more than threshold % from mean

        Step 3 — Smart Recommendation:
            Combine forecast + anomaly results into one context
            Send to Gemini → get data-backed specific recommendations

        Args:
            months    : how many past months to base forecast on (default 6)
            threshold : anomaly sensitivity — 0.30 means 30% deviation (default 0.30)

        Returns combined dict with forecast, anomalies, and smart recommendation.
        """

        # Step 1 — Forecast next month
        forecast_result = await self.forecasting.forecast(months)

        # Step 2 — Detect anomalies in current month
        anomaly_result = await self.forecasting.detect_anomalies(threshold)

        # Step 3 — Build context string for Gemini
        # Combine forecast + anomaly data into a readable summary
        context = f"""
Sales Forecast Summary:
- Predicted next month revenue: {forecast_result['predicted_revenue']}
- Average monthly growth rate: {forecast_result['growth_rate']}%
- Trend direction: {forecast_result['trend']}
- Based on last {forecast_result['based_on_months']} months of data

Anomaly Detection Summary:
- Total anomalies found: {anomaly_result['total_anomalies']}
- Region anomalies: {anomaly_result['region_anomalies']}
- Product anomalies: {anomaly_result['product_anomalies']}
"""

        # Generate smart data-backed recommendations
        recommendation = await self.llm.generate_recommendation(context)

        return {
            "forecast": forecast_result,
            "anomalies": anomaly_result,
            "smart_recommendation": recommendation
        }

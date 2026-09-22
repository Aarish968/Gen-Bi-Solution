from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.agents.forecasting_agent import ForecastingAgent

router = APIRouter()


class ForecastRequest(BaseModel):
    months: int = Field(
        default=6,
        ge=1,
        le=24,
        description="How many past months to base the forecast on (1-24)"
    )
    anomaly_threshold: float = Field(
        default=0.30,
        ge=0.05,
        le=1.0,
        description="Anomaly sensitivity — 0.30 means flag anything 30% above/below average"
    )


@router.post("/")
async def get_forecast(request: ForecastRequest):
    """
    Phase 7 — Full forecasting + anomaly detection + smart recommendations.

    What this returns:
      - forecast         : next month predicted revenue + growth rate + trend
      - anomalies        : unusual patterns in current month (region + product level)
      - smart_recommendation : data-backed specific action plan from Gemini

    Request body (all optional — defaults work fine):
      {
        "months": 6,              ← how many past months to analyze
        "anomaly_threshold": 0.30 ← 30% deviation = anomaly
      }

    Example response:
      {
        "forecast": {
          "historical": [{"month": "2026-04", "total_revenue": 3200000}, ...],
          "predicted_revenue": 4646620,
          "growth_rate": 13.32,
          "trend": "upward",
          "based_on_months": 6
        },
        "anomalies": {
          "region_anomalies": [...],
          "product_anomalies": [...],
          "total_anomalies": 2
        },
        "smart_recommendation": "Based on the upward trend..."
      }
    """
    agent = ForecastingAgent()
    result = await agent.run(
        months=request.months,
        threshold=request.anomaly_threshold
    )
    return result

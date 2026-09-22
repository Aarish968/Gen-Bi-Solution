from app.services.db_service import DBService


class ForecastingService:
    def __init__(self):
        self.db = DBService()

    # ─────────────────────────────────────────────────────────
    # Forecasting
    # ─────────────────────────────────────────────────────────

    async def get_monthly_sales(self, months: int = 6) -> list[dict]:
        """
        Fetches last N months of total revenue grouped by month.

        Returns list like:
            [
                {"month": "2026-01", "total_revenue": 3200000},
                {"month": "2026-02", "total_revenue": 3800000},
                ...
            ]
        """
        sql = f"""
            SELECT
                TO_CHAR(sale_date, 'YYYY-MM') AS month,
                SUM(price * quantity)          AS total_revenue
            FROM sales
            WHERE sale_date >= CURRENT_DATE - INTERVAL '{months} months'
            GROUP BY TO_CHAR(sale_date, 'YYYY-MM')
            ORDER BY month ASC
        """
        return await self.db.execute(sql)

    def _calculate_forecast(self, monthly_data: list[dict]) -> dict:
        """
        Predicts next month revenue using average month-over-month growth rate.

        How it works:
          Month 1: 3,200,000
          Month 2: 3,800,000  → growth = +18.75%
          Month 3: 4,100,000  → growth = +7.89%
          Average growth = (18.75 + 7.89) / 2 = 13.32%
          Prediction = last month * (1 + 0.1332) = 4,646,620

        If only 1 month of data → return same value (no trend to calculate)
        If no data → return 0
        """
        if not monthly_data:
            return {"predicted_revenue": 0, "growth_rate": 0, "based_on_months": 0}

        revenues = [float(row["total_revenue"]) for row in monthly_data]

        if len(revenues) == 1:
            return {
                "predicted_revenue": round(revenues[0]),
                "growth_rate": 0.0,
                "based_on_months": 1
            }

        # Calculate month-over-month growth rates
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i - 1] > 0:
                rate = (revenues[i] - revenues[i - 1]) / revenues[i - 1]
                growth_rates.append(rate)

        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        predicted = revenues[-1] * (1 + avg_growth)

        return {
            "predicted_revenue": round(predicted),
            "growth_rate": round(avg_growth * 100, 2),   # as percentage
            "based_on_months": len(revenues)
        }

    async def forecast(self, months: int = 6) -> dict:
        """
        Full forecasting pipeline:
          1. Fetch last N months data from DB
          2. Calculate average growth rate
          3. Predict next month

        Returns:
            {
                "historical": [{"month": "2026-01", "total_revenue": 3200000}, ...],
                "predicted_revenue": 4646620,
                "growth_rate": 13.32,       ← average monthly growth %
                "based_on_months": 6,
                "trend": "upward"           ← upward / downward / stable
            }
        """
        historical = await self.get_monthly_sales(months)
        forecast_data = self._calculate_forecast(historical)

        # Determine trend direction
        growth = forecast_data["growth_rate"]
        if growth > 2:
            trend = "upward"
        elif growth < -2:
            trend = "downward"
        else:
            trend = "stable"

        return {
            "historical": historical,
            **forecast_data,
            "trend": trend
        }

    # ─────────────────────────────────────────────────────────
    # Anomaly Detection
    # ─────────────────────────────────────────────────────────

    async def get_region_sales(self) -> list[dict]:
        """
        Fetches total revenue per region for current month.
        """
        sql = """
            SELECT
                region,
                SUM(price * quantity) AS total_revenue
            FROM sales
            WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY region
            ORDER BY total_revenue DESC
        """
        return await self.db.execute(sql)

    async def get_product_sales(self) -> list[dict]:
        """
        Fetches total revenue per product for current month.
        """
        sql = """
            SELECT
                product_name,
                SUM(price * quantity) AS total_revenue
            FROM sales
            WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY product_name
            ORDER BY total_revenue DESC
        """
        return await self.db.execute(sql)

    def _detect_anomalies(self, data: list[dict], label_key: str, threshold: float = 0.30) -> list[dict]:
        """
        Detects anomalies — values that deviate more than threshold % from the mean.

        How it works:
          Region revenues: [7246000, 6295000, 4713000, 4542000]
          Mean = 5699000
          Threshold = 30%  →  allowed range = [3989300, 7408700]

          North: 7246000 → within range  → normal
          West:  4542000 → within range  → normal
          If West was 2000000 → below lower bound → ANOMALY ⚠️

        Args:
            data       : list of dicts with label_key and total_revenue
            label_key  : "region" or "product_name"
            threshold  : deviation % to flag as anomaly (default 30%)
        """
        if not data:
            return []

        revenues = [float(row["total_revenue"]) for row in data]
        mean = sum(revenues) / len(revenues)

        anomalies = []
        for row in data:
            revenue = float(row["total_revenue"])
            deviation = (revenue - mean) / mean if mean > 0 else 0
            deviation_pct = round(deviation * 100, 2)

            if abs(deviation) > threshold:
                anomalies.append({
                    "label": row[label_key],
                    "revenue": round(revenue),
                    "mean_revenue": round(mean),
                    "deviation_pct": deviation_pct,
                    "type": "above_average" if deviation > 0 else "below_average",
                    "severity": "high" if abs(deviation) > 0.5 else "medium"
                })

        return anomalies

    async def detect_anomalies(self, threshold: float = 0.30) -> dict:
        """
        Full anomaly detection pipeline:
          1. Fetch region-wise and product-wise sales for current month
          2. Calculate mean for each group
          3. Flag anything deviating more than threshold

        Returns:
            {
                "region_anomalies": [
                    {
                        "label": "West",
                        "revenue": 2000000,
                        "mean_revenue": 5699000,
                        "deviation_pct": -64.9,
                        "type": "below_average",
                        "severity": "high"
                    }
                ],
                "product_anomalies": [...],
                "total_anomalies": 2
            }
        """
        region_data  = await self.get_region_sales()
        product_data = await self.get_product_sales()

        region_anomalies  = self._detect_anomalies(region_data,  "region",       threshold)
        product_anomalies = self._detect_anomalies(product_data, "product_name", threshold)

        return {
            "region_anomalies":  region_anomalies,
            "product_anomalies": product_anomalies,
            "total_anomalies":   len(region_anomalies) + len(product_anomalies)
        }

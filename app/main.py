from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import query, insights, visualization, documents, analyze, forecast

app = FastAPI(title="Generative BI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["Visualization"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Analyze"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])

@app.get("/health")
def health():
    return {"status": "ok"}

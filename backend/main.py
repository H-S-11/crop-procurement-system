from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import dpcs, forecasts, risk, weather, health, alerts, validation
import uvicorn

app = FastAPI(
    title="Crop Procurement Forecasting API",
    description="API for Thanjavur paddy procurement decision support",
    version="1.0.0"
)

# CORS configuration for future Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dpcs.router)
app.include_router(forecasts.router)
app.include_router(risk.router)
app.include_router(weather.router)
app.include_router(alerts.router)
app.include_router(validation.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

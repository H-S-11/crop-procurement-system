from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/{lat}/{lon}")
async def get_weather(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation&daily=precipitation_sum&timezone=auto"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # Graceful failure
        return {"error": "Weather service unavailable", "details": str(e)}

# API Documentation (Module 5)

## Base URL
`http://localhost:8000`

## Endpoints

### 1. `GET /health`
Returns system health.
**Example Response:**
```json
{"status": "ok", "service": "crop-procurement-forecasting-api"}
```

### 2. `GET /dpcs`
Returns a list of DPCs with current risk level.
**Parameters:**
- `block` (optional)
- `priority_level` (optional)
- `min_risk` (optional)
- `max_risk` (optional)

### 3. `GET /dpcs/{dpc_id}`
Returns details for a specific DPC. Returns 404 if not found.

### 4. `GET /dpcs/{dpc_id}/forecast`
Returns the arrival forecast and moisture proxy risk for a specific DPC.

### 5. `GET /dpcs/{dpc_id}/history`
Returns historical arrival and storage data for a DPC.
**Parameters:**
- `start_date` (optional)
- `end_date` (optional)

### 6. `GET /priority-zones`
Returns all DPCs ranked by risk with detailed explanations.
**Parameters:**
- `priority_level` (optional)
- `limit` (optional, default 100)

### 7. `GET /risk-summary`
Returns aggregate statistics for the dashboard (e.g. total high risk DPCs).

### 8. `GET /weather/{lat}/{lon}`
Returns weather data from Open-Meteo, degrading gracefully on failure.

## How to run
```bash
python -m uvicorn main:app --reload --port 8000
```

Interactive Swagger docs available at `/docs` and ReDoc at `/redoc`.

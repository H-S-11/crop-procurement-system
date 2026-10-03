import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dpcs_list():
    response = client.get("/dpcs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
def test_dpc_valid():
    # Attempt to fetch first DPC
    res = client.get("/dpcs?limit=1")
    if res.json():
        dpc_id = res.json()[0]["dpc_id"]
        response = client.get(f"/dpcs/{dpc_id}")
        assert response.status_code == 200
        assert response.json()["dpc_id"] == dpc_id

def test_dpc_invalid():
    response = client.get("/dpcs/INVALID_XYZ_123")
    assert response.status_code == 404

def test_risk_summary():
    response = client.get("/risk-summary")
    assert response.status_code == 200
    assert "total_dpcs" in response.json()

def test_priority_zones():
    response = client.get("/priority-zones")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

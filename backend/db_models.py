from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from database import Base

class DPCFeatureStore(Base):
    __tablename__ = 'dpc_feature_store'
    
    dpc_id = Column(String, primary_key=True, index=True)
    date = Column(String, primary_key=True, index=True)
    longitude = Column(Float)
    latitude = Column(Float)
    capacity = Column(Float)
    block = Column(String, index=True)
    name = Column(String)
    
    arrival_mt = Column(Float)
    arrival_7d_mean = Column(Float)
    rainfall_1d = Column(Float)
    rainfall_7d = Column(Float)
    rainfall_14d = Column(Float)
    flood_exposure = Column(Float)

class DPCRiskScore(Base):
    __tablename__ = 'dpc_risk_scores'
    
    dpc_id = Column(String, primary_key=True, index=True)
    date = Column(String, primary_key=True, index=True)
    
    current_stock_mt = Column(Float)
    forecast_arrival_mt = Column(Float)
    projected_stock_mt = Column(Float)
    capacity_utilization = Column(Float)
    overflow_mt = Column(Float)
    days_to_capacity = Column(Float)
    
    storage_risk_score = Column(Float)
    flood_risk_score = Column(Float)
    weather_risk_score = Column(Float)
    damage_risk_score = Column(Float)
    access_risk_score = Column(Float)
    composite_risk_score = Column(Float)
    
    priority_level = Column(String, index=True)
    priority_rank = Column(Float)
    risk_explanation = Column(String)

class Alert(Base):
    __tablename__ = 'alerts'
    
    alert_id = Column(String, primary_key=True, index=True)
    dpc_id = Column(String, index=True)
    dpc_name = Column(String)
    alert_type = Column(String, index=True)
    severity = Column(String)
    status = Column(String, index=True)
    event_date = Column(String, index=True)
    trigger_value = Column(Float)
    threshold = Column(Float)
    explanation = Column(String)
    contributing_factors = Column(String)
    provenance = Column(String)
